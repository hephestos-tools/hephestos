import copy
import json
import logging
from unittest.mock import patch, MagicMock, ANY, call
from django.test import TestCase
from django.db import transaction, DatabaseError
from google.cloud.pubsub_v1.subscriber.message import Message
from datetime import datetime, timezone, timedelta

from cross_sell.models import WebhookEvents, SavedTemplate, ShopifyEventType # Assume SavedTemplate is needed
from cross_sell.management.commands import subscriber # Import the module
from cross_sell import processor # Import processor module

# Disable logging during tests unless needed
logging.disable(logging.CRITICAL)

# Use a fixed datetime for reproducible tests
# Note: The sample payload uses a specific offset (-05:00). 
# Be mindful of timezone handling. Using timezone.utc for consistency in tests.
TEST_CREATED_AT_ISO = "2025-03-08T18:04:33+00:00" # Equivalent to 13:04:33-05:00
TEST_CREATED_AT_DT = datetime.fromisoformat(TEST_CREATED_AT_ISO)

# Updated Sample Payload with corrected timestamp format for direct parsing
sample_webhook_payload = {
    "id": 5369501515856,
    "app_id": 1354745,
    "buyer_accepts_marketing": False,
    "created_at": TEST_CREATED_AT_ISO, # Use consistent ISO format
    "currency": "EUR",
    "current_total_price": "49.95",
    "email": "ayumu.hirano@example.com", 
    "name": "#1007",
    "order_number": 1007,
    # Simplified URL for easier parsing in tests if needed, or mock _parse_shop_info directly
    "order_status_url": "https://hephytest.myshopify.com/56305123408/orders/0dfa0f4cac234a00246ce1a0bc9ca591/authenticate?key=dd8cba65401ff178a2fe6e76c69cf6df",
    "user_id": 74698129488,
    "line_items": [ {"id": 13095462994000, "name": "Test Item", "price": "49.95"} ] # Simplified line items
}


# --- Tests for subscriber.py --- 

class SubscriberCallbackTests(TestCase):

    def _create_mock_message(self, payload=None):
        if payload is None:
            payload = sample_webhook_payload
        encoded_message = json.dumps(payload).encode("utf-8")
        mock_message = MagicMock(spec=Message)
        mock_message.data = encoded_message
        mock_message.ack = MagicMock()
        mock_message.nack = MagicMock()
        mock_message.message_id = 'test-message-id' # For logging clarity
        return mock_message

    # Patch the dependencies of the callback/handler functions
    @patch('cross_sell.management.commands.subscriber._handle_message_data', return_value=True) # Patch helper
    def test_callback_calls_handler_and_acks_on_success(self, mock_handle_data):
        """Test that callback calls handler and acks on success"""
        mock_message = self._create_mock_message()
        subscriber.callback(mock_message)
        mock_handle_data.assert_called_once_with(mock_message.data)
        mock_message.ack.assert_called_once()
        mock_message.nack.assert_not_called()

    @patch('cross_sell.management.commands.subscriber._handle_message_data', return_value=False)
    def test_callback_calls_handler_and_nacks_on_failure(self, mock_handle_data):
        """Test that callback calls handler and nacks on failure"""
        mock_message = self._create_mock_message()
        subscriber.callback(mock_message)
        mock_handle_data.assert_called_once_with(mock_message.data)
        mock_message.nack.assert_called_once()
        mock_message.ack.assert_not_called()

    @patch('cross_sell.management.commands.subscriber._handle_message_data', side_effect=Exception("Unexpected error"))
    def test_callback_nacks_on_handler_exception(self, mock_handle_data):
        """Test that callback nacks if the handler raises an exception"""
        mock_message = self._create_mock_message()
        subscriber.callback(mock_message)
        mock_handle_data.assert_called_once_with(mock_message.data)
        mock_message.nack.assert_called_once()
        mock_message.ack.assert_not_called()


class SubscriberHandleMessageDataTests(TestCase):
    
    def _create_mock_message_data(self, payload=None):
         if payload is None:
            payload = sample_webhook_payload
         return json.dumps(payload).encode("utf-8")

    # --- Patching Strategy --- 
    # For _handle_message_data, we need to patch its direct dependencies:
    # - json.loads (implicitly tested by data creation, but can patch for errors)
    # - datetime.fromisoformat (implicitly tested, but can patch for errors)
    # - WebhookEvents.objects.filter
    # - _parse_shop_info
    # - transaction.atomic (mock its context manager behavior)
    # - extract_shopify_data
    # - WebhookEvents.save
    # - process (patched where it's used, not where it's defined)

    @patch('cross_sell.management.commands.subscriber.process')
    @patch('cross_sell.management.commands.subscriber.WebhookEvents.save')
    @patch('cross_sell.management.commands.subscriber.extract_shopify_data')
    @patch('cross_sell.management.commands.subscriber.transaction.atomic') # Mock transaction
    @patch('cross_sell.management.commands.subscriber._parse_shop_info')
    @patch('cross_sell.management.commands.subscriber.WebhookEvents.objects.filter')
    def test_handle_message_success_path(self, mock_filter, mock_parse_info, mock_atomic, mock_extract, mock_save, mock_process):
        """Test the successful processing path of _handle_message_data"""
        mock_message_data = self._create_mock_message_data()
        
        # Configure mocks for success path
        mock_filter.return_value.exists.return_value = False # Not a duplicate
        mock_parse_info.return_value = ("hephytest", "56305123408") # Successful parse
        mock_shop = MagicMock(domain="hephytest.myshopify.com") # Mock shop object
        mock_order = MagicMock(id=sample_webhook_payload['id']) # Mock order object
        mock_extract.return_value = (mock_shop, mock_order) # Successful extraction
        
        # Mock transaction context manager
        mock_atomic_context = MagicMock()
        mock_atomic.return_value = mock_atomic_context
        mock_atomic_context.__enter__.return_value = None
        mock_atomic_context.__exit__.side_effect = lambda exc_type, exc_val, exc_tb: False

        # Call the function
        result = subscriber._handle_message_data(mock_message_data)

        # Assertions
        self.assertTrue(result) # Should return True for success (ack)
 #       mock_filter.assert_called_once_with(order_id=sample_webhook_payload['id'], created_at=TEST_CREATED_AT_DT)
        mock_parse_info.assert_called_once_with(sample_webhook_payload['order_status_url'])
        mock_atomic.assert_called_once() # Ensure transaction was used
        mock_extract.assert_called_once_with(ANY, "hephytest", "56305123408") # ANY for payload dict
        self.assertEqual(mock_extract.call_args[0][0]['id'], sample_webhook_payload['id']) # Verify payload passed
        mock_save.assert_called_once() # Should save the WebhookEvent
        # Verify context passed to process
        expected_context = {"order": mock_order, "shop": mock_shop, "raw_payload": sample_webhook_payload}
        mock_process.assert_called_once_with(workflow_context=expected_context)

    @patch('cross_sell.management.commands.subscriber.WebhookEvents.objects.filter')
    def test_handle_message_duplicate_event(self, mock_filter):
        """Test that duplicate events are detected and skipped, returning True (ack)"""
        mock_message_data = self._create_mock_message_data()
        mock_filter.return_value.exists.return_value = True # Simulate duplicate
        
        result = subscriber._handle_message_data(mock_message_data)
        
        self.assertTrue(result) # Duplicate means successful handling (ack)
        mock_filter.assert_called_once_with(order_id=sample_webhook_payload['id'], created_at=TEST_CREATED_AT_DT)
        # Other mocks (save, process, etc.) should NOT be called

    # --- Add tests for failure scenarios --- 

    @patch('cross_sell.management.commands.subscriber.json.loads', side_effect=json.JSONDecodeError("Bad JSON", "", 0))
    def test_handle_message_invalid_json(self, mock_json_loads):
        """Test handling of invalid JSON payload"""
        mock_message_data = b'{"invalid json'
        result = subscriber._handle_message_data(mock_message_data)
        self.assertFalse(result) # Should return False (nack)

    def test_handle_message_missing_required_fields(self):
        """Test handling payload missing id or created_at"""
        payload_no_id = sample_webhook_payload.copy(); del payload_no_id['id']
        payload_no_ts = sample_webhook_payload.copy(); del payload_no_ts['created_at']
        
        result_no_id = subscriber._handle_message_data(self._create_mock_message_data(payload_no_id))
        result_no_ts = subscriber._handle_message_data(self._create_mock_message_data(payload_no_ts))
        
        self.assertFalse(result_no_id)
        self.assertFalse(result_no_ts)

    @patch('cross_sell.management.commands.subscriber.datetime')
    def test_handle_message_invalid_timestamp_format(self, mock_datetime):
        """Test handling invalid created_at format"""
        payload = sample_webhook_payload.copy()
        payload['created_at'] = "invalid-date-format"
        mock_datetime.fromisoformat.side_effect = ValueError("Invalid format")
        # Need to prevent the real fromisoformat from running by mocking the whole class or module
        # For simplicity, let's assume the ValueError is caught as planned.
        
        # Re-import datetime inside the function if needed, or patch the specific usage point.
        # Here, we rely on the ValueError catch within _handle_message_data
        result = subscriber._handle_message_data(self._create_mock_message_data(payload))
        self.assertFalse(result)

    @patch('cross_sell.management.commands.subscriber.WebhookEvents.objects.filter', side_effect=DatabaseError("DB down"))
    def test_handle_message_duplicate_check_db_error(self, mock_filter):
        """Test DB error during duplicate check"""
        result = subscriber._handle_message_data(self._create_mock_message_data())
        self.assertFalse(result)
        mock_filter.assert_called_with(order_id=ANY, created_at=ANY)

    @patch('cross_sell.management.commands.subscriber.WebhookEvents.objects.filter')
    @patch('cross_sell.management.commands.subscriber._parse_shop_info', return_value=(None, None))
    def test_handle_message_parse_shop_info_failure(self, mock_parse_info, mock_filter):
        """Test failure when _parse_shop_info cannot extract domain"""
        mock_filter.return_value.exists.return_value = False # Not duplicate
        result = subscriber._handle_message_data(self._create_mock_message_data())
        self.assertFalse(result)
        mock_parse_info.assert_called_once()

    @patch('cross_sell.management.commands.subscriber.process', side_effect=Exception("Process error"))
    @patch('cross_sell.management.commands.subscriber.WebhookEvents.save')
    @patch('cross_sell.management.commands.subscriber.extract_shopify_data')
    @patch('cross_sell.management.commands.subscriber.transaction.atomic')
    @patch('cross_sell.management.commands.subscriber._parse_shop_info')
    @patch('cross_sell.management.commands.subscriber.WebhookEvents.objects.filter')
    def test_handle_message_process_exception(self, mock_filter, mock_parse_info, mock_atomic, mock_extract, mock_save, mock_process):
        """Test exception during the call to process"""
        mock_filter.return_value.exists.return_value = False
        mock_parse_info.return_value = ("hephytest", "56305123408")
        mock_shop = MagicMock()
        mock_order = MagicMock()
        mock_extract.return_value = (mock_shop, mock_order)
        
        # Simulate transaction success up to the point of calling process
        mock_atomic_context = MagicMock()
        mock_atomic.return_value = mock_atomic_context
        mock_atomic_context.__enter__.return_value = None
        # Simulate exception during __exit__ or within the block handled by the try/except
        # The side_effect on mock_process simulates the error within the transaction block
        mock_atomic_context.__exit__.side_effect = lambda exc_type, exc_val, exc_tb: False

        result = subscriber._handle_message_data(self._create_mock_message_data())
        self.assertFalse(result)
        mock_process.assert_called_once() # Ensure process was called
        # Transaction should ideally be rolled back implicitly by the exception


# --- Tests for processor.py --- 

# Sample workflow structure for processor tests
sample_workflow_json_condition = {
    "trigger": "task0",
    "tasks": {
        "task0": {"type": "condition", "properties": {"condition_logic": "example"}, "next": ["task1"]},
        "task1": {"type": "action", "properties": {}, "next": None}
    }
}
sample_workflow_json_no_trigger = {
    "tasks": {"task1": {"type": "action", "properties": {}, "next": None}}
}
sample_workflow_json_wrong_trigger_type = {
    "trigger": "task0",
    "tasks": {
        "task0": {"type": "action", "properties": {}, "next": None}
    }
}

class ProcessorEvaluateTriggerTests(TestCase):

    @patch('cross_sell.processor.execute_condition_task', return_value=True)
    def test_evaluate_trigger_success(self, mock_execute_condition):
        """Test trigger evaluation success for a condition task"""
        context = {"shop": MagicMock(), "order": MagicMock()}
        result = processor.evaluate_trigger(sample_workflow_json_condition, context)
        self.assertTrue(result)
        mock_execute_condition.assert_called_once_with({"condition_logic": "example"}, context)

    @patch('cross_sell.processor.execute_condition_task', return_value=False)
    def test_evaluate_trigger_condition_false(self, mock_execute_condition):
        """Test trigger evaluation when condition task returns False"""
        context = {}
        result = processor.evaluate_trigger(sample_workflow_json_condition, context)
        self.assertFalse(result)
        mock_execute_condition.assert_called_once()

    def test_evaluate_trigger_missing_trigger_task(self):
        """Test workflow missing the specified trigger task"""
        workflow = copy.deepcopy(sample_workflow_json_condition)
        del workflow["tasks"]["task0"] # Remove the trigger task
        result = processor.evaluate_trigger(workflow, {})
        self.assertFalse(result)

    def test_evaluate_trigger_wrong_type(self):
        """Test trigger task that is not of type 'condition'"""
        result = processor.evaluate_trigger(sample_workflow_json_wrong_trigger_type, {})
        self.assertFalse(result)

    @patch('cross_sell.processor.execute_condition_task', side_effect=Exception("Cond Error"))
    def test_evaluate_trigger_condition_exception(self, mock_execute_condition):
        """Test exception during condition task execution"""
        result = processor.evaluate_trigger(sample_workflow_json_condition, {})
        self.assertFalse(result)
        mock_execute_condition.assert_called_once()


class ProcessorProcessTests(TestCase):

    def setUp(self):
        """Common setup for processor tests"""
        self.mock_shop = MagicMock(domain="testshop.myshopify.com")
        self.mock_order = MagicMock(id=12345)
        self.workflow_context = {"shop": self.mock_shop, "order": self.mock_order, "raw_payload": {}}
        # Create a sample SavedTemplate object mock
        self.saved_template_mock = MagicMock(spec=SavedTemplate)
        self.saved_template_mock.id = 1
        self.saved_template_mock.name = "Test Workflow"
        # Assign a deep copy to prevent accidental modification of the original
        self.saved_template_mock.workflow_json = copy.deepcopy(sample_workflow_json_condition)

    @patch('cross_sell.processor.execute_workflow')
    @patch('cross_sell.processor.evaluate_trigger', return_value=True)
    @patch('cross_sell.processor.SavedTemplate.objects.filter')
    def test_process_success_path(self, mock_filter, mock_evaluate, mock_execute):
        """Test the main success path of the process function"""
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.__iter__.return_value = [self.saved_template_mock] # Simulate finding one workflow
        mock_qs.count.return_value = 1
        mock_filter.return_value = mock_qs
        
        mock_execute.return_value = {"status": "completed"} # Simulate successful execution

        processor.process(self.workflow_context)

        mock_filter.assert_called_once_with(shop=self.mock_shop.domain)
        mock_evaluate.assert_called_once_with(self.saved_template_mock.workflow_json, self.workflow_context)
        mock_execute.assert_called_once_with(self.saved_template_mock.workflow_json, self.workflow_context)

    @patch('cross_sell.processor.logger.error')
    def test_process_no_shop_in_context(self, mock_logger_error):
        """Test process function when shop is missing from context"""
        context_no_shop = {"order": self.mock_order}
        
        processor.process(context_no_shop)
        
        mock_logger_error.assert_called_once()
        error_message = mock_logger_error.call_args[0][0]
        self.assertIn("Shop information missing", error_message)

    @patch('cross_sell.processor.logger.info')
    @patch('cross_sell.processor.SavedTemplate.objects.filter')
    def test_process_no_workflows_found(self, mock_filter, mock_logger_info):
        """Test process when no workflows are found for the shop"""
        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        mock_qs.count.return_value = 0
        mock_filter.return_value = mock_qs
        
        processor.process(self.workflow_context)
        
        mock_filter.assert_called_once_with(shop=self.mock_shop.domain)
        
        # Check for the specific info log about no workflows found
        log_calls = [call_args[0][0] for call_args in mock_logger_info.call_args_list]
        matching_logs = [log for log in log_calls if f"No workflows found for shop {self.mock_shop.domain}" in log]
        self.assertTrue(len(matching_logs) > 0, "Expected log message about no workflows not found")

    @patch('cross_sell.processor.logger.error')
    @patch('cross_sell.processor.SavedTemplate.objects.filter', side_effect=DatabaseError("DB Error"))
    def test_process_db_error_fetching_workflows(self, mock_filter, mock_logger_error):
        """Test DB error when fetching workflows"""
        processor.process(self.workflow_context)
        mock_filter.assert_called_once_with(shop=self.mock_shop.domain)
        mock_logger_error.assert_called_once()
        # Check that the error message contains the expected text
        error_message = mock_logger_error.call_args[0][0]
        self.assertIn(f"Database error fetching workflows for shop {self.mock_shop.domain}", error_message)
        self.assertIn("DB Error", error_message)

    @patch('cross_sell.processor.execute_workflow')
    @patch('cross_sell.processor.evaluate_trigger', return_value=False) # Trigger returns false
    @patch('cross_sell.processor.SavedTemplate.objects.filter')
    def test_process_trigger_evaluates_false(self, mock_filter, mock_evaluate, mock_execute):
        """Test when the workflow trigger evaluates to false"""
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.__iter__.return_value = [self.saved_template_mock]
        mock_qs.count.return_value = 1
        mock_filter.return_value = mock_qs

        processor.process(self.workflow_context)

        mock_filter.assert_called_once_with(shop=self.mock_shop.domain)
        mock_evaluate.assert_called_once_with(self.saved_template_mock.workflow_json, self.workflow_context)
        mock_execute.assert_not_called() # Workflow should not be executed

    @patch('cross_sell.processor.logger.error')
    @patch('cross_sell.processor.execute_workflow', return_value={"status": "failed", "error": "Task failed"})
    @patch('cross_sell.processor.evaluate_trigger', return_value=True)
    @patch('cross_sell.processor.SavedTemplate.objects.filter')
    def test_process_workflow_execution_fails(self, mock_filter, mock_evaluate, mock_execute, mock_logger_error):
        """Test when execute_workflow reports a failure"""
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.__iter__.return_value = [self.saved_template_mock]
        mock_qs.count.return_value = 1
        mock_filter.return_value = mock_qs
        
        processor.process(self.workflow_context)
        
        mock_execute.assert_called_once_with(self.saved_template_mock.workflow_json, self.workflow_context)
        mock_logger_error.assert_called_once()
        error_message = mock_logger_error.call_args[0][0]
        self.assertIn(f"Workflow {self.saved_template_mock.name} failed: Task failed", error_message)

    @patch('cross_sell.processor.logger.error')
    @patch('cross_sell.processor.execute_workflow', side_effect=Exception("Exec Error"))
    @patch('cross_sell.processor.evaluate_trigger', return_value=True)
    @patch('cross_sell.processor.SavedTemplate.objects.filter')
    def test_process_execute_workflow_exception(self, mock_filter, mock_evaluate, mock_execute, mock_logger_error):
        """Test when calling execute_workflow itself raises an exception"""
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.__iter__.return_value = [self.saved_template_mock]
        mock_qs.count.return_value = 1
        mock_filter.return_value = mock_qs
        
        processor.process(self.workflow_context)
        
        mock_execute.assert_called_once()
        mock_logger_error.assert_called_once()
        error_message = mock_logger_error.call_args[0][0]
        self.assertIn(f"Error processing workflow {self.saved_template_mock.name}", error_message)
        self.assertIn("Exec Error", error_message)
