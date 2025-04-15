from django.utils import timezone

from django.db import models
from shopify.models import Shop


# Enums
class AppType(models.TextChoices):
    CROSS_SELL = 'cross_sell'


class Status(models.TextChoices):
    """Status of a workflow or task."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class ShopifyEventType(models.TextChoices):
    """Types of Shopify webhook events supported for CrossSell."""
    ORDERS_CREATE = 'orders/create'


class WebhookEvents(models.Model):
    """
    Stores webhook events received from Shopify.
    """
    order_id = models.BigIntegerField(null=False, default=0)
    created_at = models.DateTimeField(null=False, auto_now_add=True)
    webhook_data = models.JSONField(null=False)
    event_type = models.CharField(max_length=50, choices=ShopifyEventType.choices)
    shop_domain = models.CharField(max_length=100, null=False)
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(null=True)

    class Meta:
        db_table = 'cross_sell_webhook_events'
        indexes = [
            models.Index(fields=['shop_domain', 'created_at']),
            models.Index(fields=['order_id']),
            models.Index(fields=['processed'])
        ]


class Template(models.Model):
    """
    Base template for workflows.
    """
    name = models.CharField(max_length=255, null=False)
    description = models.JSONField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cross_sell_template'


class SavedTemplate(models.Model):
    """
    Represents a saved workflow template.
    """
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, to_field='domain', on_delete=models.CASCADE, related_name='saved_templates')
    workflow_json = models.JSONField(null=False)
    last_executed = models.DateTimeField(null=True)
    execution_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cross_sell_saved_template'
        indexes = [
            models.Index(fields=['shop', 'is_active']),
            models.Index(fields=['last_executed'])
        ]
