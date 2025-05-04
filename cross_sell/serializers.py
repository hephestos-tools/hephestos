from rest_framework import serializers
from .models import Workflow, WorkflowTemplate
from shopify.models import Shop

class CreateTemplateSerializer(serializers.Serializer):
    template_id = serializers.IntegerField()
    shop_domain = serializers.CharField(max_length=100)
    workflow_json = serializers.JSONField()
    is_active = serializers.BooleanField(default=True)

    def validate_template_id(self, value):
        try:
            WorkflowTemplate.objects.get(id=value)
            return value
        except WorkflowTemplate.DoesNotExist:
            raise serializers.ValidationError("Template does not exist")

    def validate_shop_domain(self, value):
        try:
            Shop.objects.get(domain=value)
            return value
        except Shop.DoesNotExist:
            raise serializers.ValidationError("Shop does not exist") 