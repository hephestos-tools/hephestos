import json

from django.core.management.base import BaseCommand
from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPIError
from hephestos.settings import GOOGLE_SUBSCRIPTION_ID
from hephestos.settings import GOOGLE_PROJECT_ID
from cross_sell.models import WebhookEvents, ShopifyEventType


class Command(BaseCommand):
    help = 'Subscribe to a Google Pub/Sub topic and handle message'

    def handle(self, *args, **options):
        subscription_id = GOOGLE_SUBSCRIPTION_ID
        project_id = GOOGLE_PROJECT_ID  # Replace with your project ID

        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project_id, subscription_id)

        def callback(message):
            try:
                # Process the message
                try:
                    print(f'Received message: {message.data.decode("utf-8")} ')
                    order_create_payload = json.loads(message.data.decode("utf-8"))
                    order_id = order_create_payload.get("id")
                    created_at = order_create_payload.get("created_at")
                    is_duplicate = WebhookEvents.objects.filter(order_id=order_id, created_at=created_at).exists()
                    if is_duplicate is False:
                        shop_domain = order_create_payload.get("order_status_url")
                        shop_domain = shop_domain.split("//")[1].split(".")[0]
                        event = WebhookEvents(order_id=order_id,
                                              created_at=created_at,
                                              webhook_data=order_create_payload,
                                              shop_domain=shop_domain,
                                              event_type=ShopifyEventType.ORDERS_CREATE)
                        event.save()
                except (json.JSONDecodeError, KeyError):
                    print("Invalid JSON payload received")
                    return False
                # Acknowledge the message
                message.ack()
            except Exception as ex:
                print(f'Error processing message: {ex}')

        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        print(f'Listening for messages on {subscription_path}...')

        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print('Stopped listening due to Keyboard interrupt.')
        except GoogleAPIError as e:
            print(f'Pub/Sub API error: {e}')
