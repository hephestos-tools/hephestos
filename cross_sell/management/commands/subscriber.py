from datetime import datetime, timezone
import json

from django.core.management.base import BaseCommand
from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPIError
from hephestos.settings import GOOGLE_SUBSCRIPTION_ID
from hephestos.settings import GOOGLE_PROJECT_ID
from cross_sell.models import WebhookEvents, ShopifyEventType
from shopify.processor import extract_shopify_data


def callback(message):
    try:
        # Process the message
        try:
            print(f'[{datetime.now(timezone.utc)}] Received message: {message.data.decode("utf-8")}')
            order_create_payload = json.loads(message.data.decode("utf-8"))
            order_id = order_create_payload.get("id")
            created_at = order_create_payload.get("created_at")

            print(f"[{datetime.now(timezone.utc)}] order_id: {order_id}, created_at: {created_at}")

            if order_id is not None and created_at is not None:
                is_duplicate = WebhookEvents.objects.filter(order_id=order_id, created_at=created_at).exists()

                print(f"[{datetime.now(timezone.utc)}] Is duplicate: {is_duplicate}")

                if not is_duplicate:
                    shop_url = order_create_payload.get("order_status_url")

                    print(f"[{datetime.now(timezone.utc)}] shop_url: {shop_url}")

                    try:
                        if shop_url:
                            shop_domain = shop_url.split("//")[1].split(".")[0]
                            shop_id = shop_url.split("//")[1].split("/")[1]

                            print(f" [{datetime.now(timezone.utc)}] shop_domain: {shop_domain}, shop_id: {shop_id}")

                            event = WebhookEvents(order_id=order_id,
                                                  created_at=created_at,
                                                  webhook_data=order_create_payload,
                                                  shop_domain=shop_domain,
                                                  event_type=ShopifyEventType.ORDERS_CREATE)
                            extract_shopify_data(order_create_payload, shop_domain, shop_id)
                            event.save()
                            message.ack()
                    except IndexError as idx_error:
                        message.nack()
                        print(f" [{datetime.now(timezone.utc)}] Error parsing shop URL: {idx_error}")
                else:
                    print(f"[{datetime.now(timezone.utc)}] Duplicate order detected, skipping...")
        except (json.JSONDecodeError, KeyError):
            message.nack()
            print(f"[{datetime.now(timezone.utc)}] Invalid JSON payload received")
            return False
    except Exception as ex:
        message.nack()
        print(f'[{datetime.now(timezone.utc)}] Error processing message: {ex}')


class Command(BaseCommand):
    help = 'Subscribe to a Google Pub/Sub topic and handle message'

    def handle(self, *args, **options):
        subscription_id = GOOGLE_SUBSCRIPTION_ID
        project_id = GOOGLE_PROJECT_ID  # Replace with your project ID

        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project_id, subscription_id)
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        print(f'Listening for messages on {subscription_path}...')

        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print('Stopped listening due to Keyboard interrupt.')
        except GoogleAPIError as e:
            print(f'Pub/Sub API error: {e}')

