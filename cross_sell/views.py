from core.repository.workflow_repository import WebhookRepository
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
import hmac
import hashlib
from hephestos.settings import SHOPIFY_SHARED_SECRET
from cross_sell.models import *


# Create your views here.
@csrf_exempt
def index(request):
    return HttpResponse("Hello, world. You're at the cross-sell home page.")


@csrf_exempt
def webhook(request):
    # verify webhook signature

    if request.method == "POST" and request.content_type == "application/json":
        event_type = request.headers.get('X-Shopify-Topic')

        if event_type != str(ShopifyEventType.ORDERS_CREATE.value):
            return JsonResponse({'status': 'success'}, status=200)
        # TODO: verify not working right now
        # if not verify_webhook_signature(request):
        #     return JsonResponse({'error': 'Invalid signature'}, status=400)

        # persist data
        body_data = json.loads(request.body.decode('utf-8'))
        webhook_data = Webhooks(
            webhook_data=str(body_data),
            shop_id='some_id',
            app=str(AppType.CROSS_SELL.value),
            event_type=event_type
        )
        WebhookRepository.save(webhook_data)

        # send this data for further processing

        return JsonResponse({'status': 'success'}, status=200)
    elif request.method == "GET":

        items = (WebhookRepository.get_all()).values()
        json_data = list(items)

        return JsonResponse(json_data, safe=False)
    # unidentified webhook received log this to errors
    else:
        return JsonResponse({'status': 'success'}, status=200)


def verify_webhook_signature(request):
    # Get the signature from the header
    received_signature = request.headers.get('X-Shopify-Hmac-Sha256')

    # Compute the HMAC-SHA256 hash of the request body
    computed_signature = hmac.new(
        SHOPIFY_SHARED_SECRET.encode('utf-8'),
        request.get_data(),
        hashlib.sha256
    ).digest()

    # Encode the computed signature to base64
    computed_signature_base64 = computed_signature.hex()

    # Compare the computed signature with the received signature
    return hmac.compare_digest(received_signature, computed_signature_base64)
