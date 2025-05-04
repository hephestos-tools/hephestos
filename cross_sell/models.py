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


class WorkflowTemplate(models.Model):
    """
    Base template for workflows that defines the structure and available options.
    These are predefined templates that users can customize.
    """
    name = models.CharField(max_length=255, null=False)
    description = models.JSONField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cross_sell_workflow_template'


class Workflow(models.Model):
    """
    Represents a customized workflow created by a shop based on a template.
    This is the actual workflow that will be executed with shop-specific settings.
    """
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, to_field='domain', on_delete=models.CASCADE, related_name='workflows')
    workflow_json = models.JSONField(null=False)
    last_executed = models.DateTimeField(null=True)
    execution_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cross_sell_workflow'
        indexes = [
            models.Index(fields=['shop', 'is_active']),
            models.Index(fields=['last_executed'])
        ]
