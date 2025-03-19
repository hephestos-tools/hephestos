import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from google.cloud.pubsub_v1.subscriber.message import Message
from datetime import datetime
from cross_sell.models import WebhookEvents  # Replace `myapp` with your actual app name
from cross_sell.management.commands.subscriber import \
    callback  # Replace `module` with the file where `callback` is defined

sample_webhook_payload = {"id": 5369501515856, "app_id": 1354745,
                          "buyer_accepts_marketing": False,
                          "created_at": "2025-03-08T13:04:33-05:00",
                          "currency": "EUR",
                          "current_total_price": "49.95",
                          "current_total_price_set":
                              {"shop_money": {"amount": "49.95", "currency_code": "EUR"},
                               "presentment_money": {"amount": "49.95", "currency_code": "EUR"}},
                          "email": "ayumu.hirano@example.com", "name": "#1007",
                          "order_number": 1007,
                          "order_status_url": "https://hephytest.myshopify.com/56305123408/orders"
                                              "/0dfa0f4cac234a00246ce1a0bc9ca591/authenticate?key"
                                              "=dd8cba65401ff178a2fe6e76c69cf6df",
                          "user_id": 74698129488,
                          "line_items": [
                              {"id": 13095462994000,
                               "admin_graphql_api_id": "gid://shopify/LineItem/13095462994000", "attributed_staffs": [],
                               "current_quantity": 1, "fulfillable_quantity": 1,
                               "fulfillment_service": "manual",
                               "fulfillment_status": None, "gift_card": False, "grams": 71,
                               "name": "Selling Plans Ski Wax - Special Selling Plans Ski Wax",
                               "price": "49.95",
                               "price_set": {"shop_money": {"amount": "49.95", "currency_code": "EUR"},
                                             "presentment_money": {"amount": "49.95", "currency_code": "EUR"}},
                               "product_exists": True,
                               "product_id": 7037320855632,
                               "properties": [], "quantity": 1, "requires_shipping": True,
                               "sales_line_item_group_id": None, "sku": "", "taxable": True,
                               "title": "Selling Plans Ski Wax", "total_discount": "0.00",
                               "total_discount_set":
                                   {"shop_money": {"amount": "0.00", "currency_code": "EUR"},
                                    "presentment_money": {"amount": "0.00", "currency_code": "EUR"}},
                               "variant_id": 40739419324496,
                               "variant_inventory_management": "shopify",
                               "variant_title": "Special Selling Plans Ski Wax",
                               "vendor": "hephytest", "tax_lines": [], "duties": [],
                               "discount_allocations": []}
                          ]
                          }


class SubscriberTestCase(TestCase):
    @patch("cross_sell.models.WebhookEvents.objects.filter")
    @patch("cross_sell.models.WebhookEvents.save", autospec=True)
    def test_callback_processes_message(self, mock_save, mock_filter):
        # Sample payload similar to what your function expects
        encoded_message = json.dumps(sample_webhook_payload).encode("utf-8")

        # Mocking a Google Pub/Sub Message object
        mock_message = MagicMock(spec=Message)
        mock_message.data = encoded_message
        mock_message.ack = MagicMock()

        # Mock DB check (assuming no duplicate exists)
        mock_filter.return_value.exists.return_value = False

        # Call the function with the mocked message
        callback(mock_message)

        # Assertions to verify expected behavior
        # Ensure message is acknowledged
        mock_message.ack.assert_called_once()
        # Check DB lookup
        mock_filter.assert_called_once_with(order_id=5369501515856, created_at="2025-03-08T13:04:33-05:00")
        # Ensure save() is called to store event in DB
        mock_save.assert_called_once()

    @patch("myapp.models.WebhookEvents.objects.filter")
    def test_callback_skips_duplicate(self, mock_filter):
        """Ensure duplicate messages are skipped"""
        encoded_message = json.dumps(sample_webhook_payload).encode("utf-8")

        mock_message = MagicMock(spec=Message)
        mock_message.data = encoded_message
        mock_message.ack = MagicMock()

        # Simulate duplicate detection
        mock_filter.return_value.exists.return_value = True

        # Call function
        callback(sample_webhook_payload)

        # Ensure message is acknowledged, but no save() is performed
        mock_message.ack.assert_called_once()
        mock_filter.assert_called_once()
