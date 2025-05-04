from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from cross_sell.models import *
from django.views.decorators.http import require_http_methods
from shopify.models import Shop
from django.shortcuts import get_object_or_404
from .serializers import CreateTemplateSerializer


# Create your views here.
@csrf_exempt
def index(request):
    return HttpResponse("Hello, world. You're at the cross-sell home page.")


@csrf_exempt
@require_http_methods(["POST"])
def create_workflow(request):
    """
    Creates a workflow for a shop based on a template.
    
    Request body structure:
    {
        "template_id": 1,
        "shop_domain": "example.myshopify.com",
        "workflow_json": {}, // JSON representation of the workflow
        "is_active": true
    }
    """
    try:
        serializer = CreateTemplateSerializer(data=json.loads(request.body.decode('utf-8')))
        if not serializer.is_valid():
            return JsonResponse({'errors': serializer.errors}, status=400)
        
        data = serializer.validated_data
        template = get_object_or_404(WorkflowTemplate, id=data['template_id'])
        shop = get_object_or_404(Shop, domain=data['shop_domain'])
        
        workflow = Workflow.objects.create(
            template=template,
            shop=shop,
            workflow_json=data['workflow_json'],
            is_active=data['is_active']
        )
        
        return JsonResponse({
            'id': workflow.id,
            'template_id': template.id,
            'template_name': template.name,
            'shop_domain': shop.domain,
            'created_at': workflow.created_at.isoformat(),
            'is_active': workflow.is_active
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def list_shop_workflows(request):
    """
    Lists all workflows for a specific shop.
    
    URL: /cross-sell/workflow/list?shop_domain=example.myshopify.com
    
    Returns a list of all workflows for the specified shop,
    including basic information about each workflow.
    """
    try:
        # Get shop domain from query parameter
        shop_domain = request.GET.get('shop_domain')
        if not shop_domain:
            return JsonResponse({'error': 'shop_domain query parameter is required'}, status=400)
        
        # Verify shop exists
        shop = get_object_or_404(Shop, domain=shop_domain)
        
        # Get all workflows for this shop
        workflows = Workflow.objects.filter(
            shop=shop
        ).select_related('template')
        
        # Prepare response data
        workflows_data = []
        for workflow in workflows:
            workflows_data.append({
                'id': workflow.id,
                'template_id': workflow.template.id,
                'template_name': workflow.template.name,
                'is_active': workflow.is_active,
                'created_at': workflow.created_at.isoformat(),
                'updated_at': workflow.updated_at.isoformat(),
                'last_executed': workflow.last_executed.isoformat() if workflow.last_executed else None,
                'execution_count': workflow.execution_count
            })
        
        return JsonResponse({
            'shop_domain': shop_domain,
            'workflows_count': len(workflows_data),
            'workflows': workflows_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
