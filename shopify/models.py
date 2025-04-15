from django.db import models
from django.db.models import JSONField
from django.utils import timezone


class Shop(models.Model):
    """
    Represents a Shopify shop.
    """
    shop_id = models.BigIntegerField(primary_key=True)
    domain = models.TextField(max_length=100, null=False, unique=True)
    email = models.EmailField(max_length=255, null=True)
    access_token = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'shopify_shop'
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active'])
        ]


class Customer(models.Model):
    """
    Represents a Shopify customer.
    """
    shop_customer_id = models.BigIntegerField(null=False)
    domain = models.ForeignKey(Shop, to_field='domain', on_delete=models.CASCADE, related_name='customers')
    email = models.EmailField(max_length=255, null=False)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    verified_email = models.BooleanField(default=False)
    email_marketing_consent = JSONField(blank=True, null=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shopify_customer'
        indexes = [
            models.Index(fields=['domain', 'email']),
            models.Index(fields=['shop_customer_id']),
            models.Index(fields=['total_spend'])
        ]
        unique_together = [['domain', 'shop_customer_id']]


class Order(models.Model):
    """
    Represents a Shopify order.
    """
    name = models.CharField(max_length=255, null=False)
    order_id = models.BigIntegerField(null=False, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    domain = models.ForeignKey(Shop, to_field='domain', on_delete=models.CASCADE, related_name='orders')
    customer_email = models.TextField(max_length=100, null=True)
    app_id = models.BigIntegerField(null=True)
    payload = JSONField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    fulfillment_status = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shopify_order'
        indexes = [
            models.Index(fields=['domain', 'order_id']),
            models.Index(fields=['customer_email']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at'])
        ]
        unique_together = [['domain', 'order_id']]


class Integrator(models.Model):
    """
    Represents an integration with external services.
    """
    name = models.CharField(max_length=255, null=False)
    config_file_path = models.CharField(max_length=255, null=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shopify_integrator'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active'])
        ]
