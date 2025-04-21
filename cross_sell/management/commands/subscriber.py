import logging
from datetime import datetime
import json
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.db import transaction
from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPIError

from cross_sell.processor import process
from hephestos.settings import GOOGLE_SUBSCRIPTION_ID
from hephestos.settings import GOOGLE_PROJECT_ID
from cross_sell.models import WebhookEvents, ShopifyEventType
from shopify.processor import extract_shopify_data

# Configure logging
logger = logging.getLogger(__name__)
# Example basic config: Add to your Django settings for proper configuration
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _parse_shop_info(shop_url: str):
    """Parses shop domain and ID from the order status URL."""
    if not shop_url:
        logger.warning("Order status URL is missing.")
        return None, None
    try:
        parsed_url = urlparse(shop_url)
        # Example: https://your-shop-name.myshopify.com/123456789/orders/abcdef...
        # domain = your-shop-name
        # path parts = ['', '123456789', 'orders', 'abcdef...']
        # shop_id = 123456789 (assuming this is the intended shop_id from the path)
        
        # Adjust domain extraction based on expected URL format if needed
        domain_parts = parsed_url.netloc.split('.') 
        if len(domain_parts) >= 2 and domain_parts[-1] == 'myshopify': # Common case
             shop_domain = domain_parts[0]
        else: # Fallback or other domain structures
             shop_domain = parsed_url.netloc.split('.')[0] # Simplistic fallback

        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) > 1 and path_parts[0].isdigit():
             shop_id = path_parts[0] # Assuming first numeric part is shop ID
        else:
             logger.warning(f"Could not reliably extract shop_id from path: {parsed_url.path}")
             shop_id = None # Or handle differently if shop_id is crucial

        logger.info(f"Extracted shop_domain: {shop_domain}, shop_id: {shop_id}")
        return shop_domain, shop_id
    except Exception as e:
        logger.error(f"Error parsing shop URL '{shop_url}': {e}", exc_info=True)
        return None, None


def _handle_message_data(message_data: bytes):
    """Processes the core logic for a single message."""
    try:
        payload = json.loads(message_data.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload received: {e}")
        return False # Indicate failure, leading to nack

    # --- Handle Budget Notifications ---
    # Check for keys specific to Google Cloud Budget Notifications
    if "budgetDisplayName" in payload and "costAmount" in payload and "budgetAmount" in payload:
        logger.info(f"Received Google Cloud Budget Notification for '{payload.get('budgetDisplayName')}' (Cost: {payload.get('costAmount')}). Acknowledging.")
        return True # Indicate success (handled), leading to ack

    # --- Existing Order Processing Logic ---
    # If it's not a budget notification, assume it's an order payload
    order_create_payload = payload # Use the parsed payload
    order_id = order_create_payload.get("id")
    created_at_str = order_create_payload.get("created_at") # Keep as string initially for DB check

    logger.info(f"Processing message for order_id: {order_id}, created_at: {created_at_str}")

    if order_id is None or created_at_str is None:
        logger.warning("Message missing order_id or created_at.")
        return False # Nack if essential data is missing

    # Check for duplicates before extensive processing
    try:
        # Assuming created_at in DB is DateTimeField, parse the string
        # Make sure the format matches ('%Y-%m-%dT%H:%M:%S%z' or similar)
        created_at_dt = datetime.fromisoformat(created_at_str) # Adjust if format differs
        
        is_duplicate = WebhookEvents.objects.filter(order_id=order_id, created_at=created_at_dt).exists()
        if is_duplicate:
            logger.info(f"Duplicate order event detected for order_id: {order_id}, skipping.")
            return True # Indicate success (duplicate found), leading to ack
    except ValueError as ve:
         logger.error(f"Error parsing created_at timestamp '{created_at_str}': {ve}")
         return False # Nack on parsing error
    except Exception as db_exc:
        logger.error(f"Database error checking for duplicate order_id {order_id}: {db_exc}", exc_info=True)
        return False # Nack on DB error


    shop_url = order_create_payload.get("order_status_url")
    shop_domain, shop_id = _parse_shop_info(shop_url)

    if not shop_domain: # shop_id might be optional depending on use case
        logger.warning(f"Could not extract shop_domain for order_id: {order_id}. Cannot process further.")
        return False # Nack if domain is essential

    try:
        # Use a transaction to ensure atomicity of saving the event and processing
        with transaction.atomic():
            logger.info(f"Extracting Shopify data for order_id: {order_id}, shop_domain: {shop_domain}")
            # Pass shop_id if available and needed by extract_shopify_data
            shop, order = extract_shopify_data(order_create_payload, shop_domain, shop_id)

            logger.info(f"Saving WebhookEvent for order_id: {order_id}")
            event = WebhookEvents(
                order_id=order_id,
                created_at=created_at_dt, # Use the parsed datetime object
                webhook_data=order_create_payload,
                shop_domain=shop_domain,
                event_type=ShopifyEventType.ORDERS_CREATE
            )
            event.save()

            logger.info(f"Calling processor for order_id: {order_id}")
            # Pass context needed by workflows (modify processor/executor accordingly)
            process(workflow_context={"order": order, "shop": shop, "raw_payload": order_create_payload})

        # If transaction completes without error, processing is considered successful for ack
        logger.info(f"Successfully processed and saved event for order_id: {order_id}")
        return True

    except Exception as processing_exc:
        logger.error(f"Error during transaction or processing for order_id {order_id}: {processing_exc}", exc_info=True)
        return False # Nack on any processing error within the transaction

def callback(message):
    """Pub/Sub message callback handler."""
    logger.info(f"Received message ID: {message.message_id}") # Log message ID for tracking
    try:
        success = _handle_message_data(message.data)
        if success:
            message.ack()
            logger.debug(f"Message {message.message_id} acknowledged.")
        else:
            message.nack()
            logger.warning(f"Message {message.message_id} nacked.")
    except Exception as e:
        # Catch unexpected errors in the handler logic itself
        logger.critical(f"Unexpected error processing message {message.message_id}: {e}", exc_info=True)
        message.nack() # Nack on critical errors


class Command(BaseCommand):
    help = 'Subscribe to a Google Pub/Sub topic and handle message'

    def handle(self, *args, **options):
        subscription_id = GOOGLE_SUBSCRIPTION_ID
        project_id = GOOGLE_PROJECT_ID

        if not subscription_id or not project_id:
            logger.error("GOOGLE_SUBSCRIPTION_ID or GOOGLE_PROJECT_ID not configured in settings.")
            return

        subscriber = None
        streaming_pull_future = None

        try:
            subscriber = pubsub_v1.SubscriberClient()
            subscription_path = subscriber.subscription_path(project_id, subscription_id)
            logger.info(f'Attempting to listen for messages on {subscription_path}...')
            
            # Increase timeout for ack/nack deadline if processing takes longer
            # flow_control = pubsub_v1.types.FlowControl(max_messages=10, max_bytes=10 * 1024 * 1024)
            # streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback, flow_control=flow_control)
            
            streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
            logger.info(f'Successfully subscribed. Listening for messages on {subscription_path}...')

            # Keep the main thread alive, listening for messages indefinitely.
            streaming_pull_future.result()

        except KeyboardInterrupt:
            logger.info('Keyboard interrupt received. Shutting down subscriber.')
            if streaming_pull_future:
                streaming_pull_future.cancel()  # Trigger the shutdown
                streaming_pull_future.result()  # Wait for the shutdown to complete.
        except GoogleAPIError as e:
            logger.error(f'Pub/Sub API error during subscription: {e}', exc_info=True)
        except Exception as e:
            logger.critical(f'An unexpected error occurred in the subscriber main loop: {e}', exc_info=True)
        finally:
            if subscriber:
                # Proper resource cleanup
                # subscriber.close() # Use close() in newer library versions if available
                pass 
            logger.info("Subscriber shutdown complete.")

