from django.core.management.base import BaseCommand
from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPIError
from hephestos.settings import GOOGLE_SUBSCRIPTION_ID
from hephestos.settings import GOOGLE_PROJECT_ID


class Command(BaseCommand):
    help = 'Subscribe to a Google Pub/Sub topic and handle messages'


    def handle(self, *args, **options):
        subscription_id = GOOGLE_SUBSCRIPTION_ID
        project_id = GOOGLE_PROJECT_ID # Replace with your project ID

        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project_id, subscription_id)

        def callback(message):
            try:
                # Process the message
                print(f'Received message: {message.data.decode("utf-8")}')

                # Acknowledge the message
                message.ack()
            except Exception as e:
                print(f'Error processing message: {e}')

        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        print(f'Listening for messages on {subscription_path}...')

        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print('Stopped listening.')
        except GoogleAPIError as e:
            print(f'Pub/Sub API error: {e}')
