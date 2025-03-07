from django.utils import timezone

from django.db import models
from shopify.models import Shop


# Enums
class AppType(models.TextChoices):
    CROSS_SELL = 'cross_sell'


class ShopifyEventType(models.TextChoices):
    ORDERS_CREATE = 'orders/create'


class WebhookEvents(models.Model):
    order_id = models.BigIntegerField(null=False, default=0)
    created_at = models.DateTimeField(null=False, default=timezone.now)
    webhook_data = models.TextField(null=False)
    event_type = models.CharField(choices=ShopifyEventType.choices)
    shop_domain = models.CharField(max_length=100, null=False)

    class Meta:
        abstract = False
        db_table = 'cross_sell_webhook_events'


class SubscribedWebhooks(models.Model):
    webhook_topic = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'cross_sell_subscribed_webhooks'


class Template(models.Model):
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'cross_sell_template'


class SavedTemplate(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, to_field='domain', on_delete=models.CASCADE, related_name='saved_templates')
    workflow_json = models.JSONField(null=False)

    class Meta:
        db_table = 'cross_sell_saved_template'


# creates an n-to-n mapping of webhooks and template
class WebhookTemplateMap(models.Model):
    webhook_id = models.ForeignKey(SubscribedWebhooks, on_delete=models.CASCADE)
    template_id = models.ForeignKey(Template, on_delete=models.CASCADE)

    class Meta:
        db_table = 'cross_sell_webhook_template_map'
