from django.db import models
from django.db.models import JSONField


class Shop(models.Model):
    shop_id = models.BigIntegerField(primary_key=True)
    domain = models.TextField(max_length=100, null=False, unique=True)
    email = models.EmailField(max_length=255, null=True)


class Customer(models.Model):
    shop_customer_id = models.BigIntegerField(null=False)
    domain = models.ForeignKey(Shop, to_field='domain', on_delete=models.CASCADE, related_name='customers')
    email = models.EmailField(max_length=255, null=False)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    verified_email = models.BooleanField(default=False)
    email_marketing_consent = JSONField(blank=True, null=True)


class Order(models.Model):
    name = models.CharField(max_length=255, null=False)
    order_id = models.BigIntegerField(null=False, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    domain = models.ForeignKey(Shop, to_field='domain', on_delete=models.CASCADE, related_name='orders')
    customer_email = models.TextField(max_length=100, null=True)
    app_id = models.BigIntegerField(null=True)
    payload = JSONField(blank=True, null=True)


class Integrator(models.Model):
    name = models.CharField(max_length=255, null=False)
    config_file_path = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'shopify_integrator'
