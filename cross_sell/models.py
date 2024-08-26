from django.db import models
from django.db.models import JSONField


# Enums
class DataType(models.TextChoices):
    INT = 'int', 'Integer'
    STRING = 'string', 'String'
    DATETIME = 'datetime', 'Datetime'


class AppType(models.TextChoices):
    CROSS_SELL = 'cross_sell'


class Webhooks(models.Model):
    app = models.CharField(choices=AppType.choices)
    webhook_data = models.TextField(null=False)
    event_type = models.CharField(max_length=255, null=True)
    shop_id = models.CharField(max_length=255, null=False)

    class Meta:
        abstract = False
        db_table = 'webhook'


class ComparisonOperator(models.TextChoices):
    EQUAL = '=', 'Equal'
    LESS_THAN = '<', 'Less Than'
    GREATER_THAN = '>', 'Greater Than'
    LESS_THAN_EQUAL = '<=', 'Less Than or Equal'
    GREATER_THAN_EQUAL = '>=', 'Greater Than or Equal'


class ConditionType(models.TextChoices):
    IF = 'if', 'If'
    SWITCH = 'switch', 'Switch'
    IF_ELSEIF = 'if-elseif', 'If-Elseif'


class NodeType(models.TextChoices):
    CONDITION = 'condition', 'Condition'
    ACTION = 'action', 'Action'
    TRIGGER = 'trigger', 'Trigger'
    HTTP = 'http', 'HTTP'
    DELAY = 'delay', 'Delay'
    INTEGRATION = 'integration', 'Integration'


class ExecutionState(models.TextChoices):
    NEW = 'NEW', 'New'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    PAUSE = 'PAUSE', 'Pause'
    COMPLETE = 'COMPLETE', 'Complete'
    RETRY = 'RETRY', 'Retry'


class Status(models.TextChoices):
    FAILED = 'FAILED', 'Failed'
    SUCCESS = 'SUCCESS', 'Success'
    RUNNING = 'RUNNING', 'Running'


# Models

class Shop(models.Model):
    shop_id = models.IntegerField(primary_key=True)
    email = models.EmailField(max_length=255, null=False)

    class Meta:
        db_table = 'shops'


class Customer(models.Model):
    customer_id = models.IntegerField(null=False, primary_key=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='customers')
    email = models.EmailField(max_length=255, null=False)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    verified_email = models.BooleanField(default=False)
    email_marketing_consent = JSONField(blank=True, null=True)

    class Meta:
        db_table = 'customers'


class Product(models.Model):
    product_id = models.IntegerField(null=False, primary_key=True)
    title = models.CharField(max_length=255, null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        db_table = 'products'


class Order(models.Model):
    name = models.CharField(max_length=255, null=False)
    order_id = models.IntegerField(null=False, primary_key=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    payload = JSONField(blank=True, null=True)

    class Meta:
        db_table = 'orders'


class WebhookSubscribed(models.Model):
    webhook_topic = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'webhooks_subscribed'


class Integrator(models.Model):
    name = models.CharField(max_length=255, null=False)
    config_file_path = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'integrators'


class User(models.Model):
    user_id = models.CharField(max_length=255, null=False)
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'


class Template(models.Model):
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'templates'


class TemplateShopMapping(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    class Meta:
        db_table = 'templates_shop_mapping'


class Workflow(models.Model):
    name = models.CharField(max_length=255, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False)
    webhook_id = models.IntegerField(null=False)

    class Meta:
        db_table = 'workflow'


class Node(models.Model):
    node_type = models.CharField(max_length=50, choices=NodeType.choices, null=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, null=False, related_name='nodes')

    class Meta:
        db_table = 'nodes'


class Edge(models.Model):
    from_node = models.ForeignKey(Node, related_name='from_edges', on_delete=models.CASCADE)
    to_node = models.ForeignKey(Node, related_name='to_edges', on_delete=models.CASCADE)

    class Meta:
        db_table = 'edges'


class Field(models.Model):
    field_name = models.CharField(max_length=255, null=False)
    type = models.CharField(max_length=20, choices=DataType.choices, null=False)

    class Meta:
        db_table = 'fields'


class NodeFieldMapping(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)

    class Meta:
        db_table = 'nodes_fields_mapping'


class ConditionNode(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, primary_key=True)
    condition_type = models.CharField(max_length=20, choices=ConditionType.choices, null=False)
    sequence = models.IntegerField(null=False)
    operator = models.CharField(max_length=30, choices=ComparisonOperator.choices, null=False)
    left_operand = models.ForeignKey(Field, on_delete=models.CASCADE, null=False, related_name='left_operand')
    right_operand = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'condition_nodes'


class ConditionNodeMapping(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, primary_key=True)
    eval = models.BooleanField(null=False)
    next_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='next_node', null=True)

    class Meta:
        db_table = 'condition_node_mapping'


class DelayNode(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, primary_key=True)
    delay_period = models.IntegerField(null=False)

    class Meta:
        db_table = 'delay_nodes'


class IntegratorNode(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, primary_key=True)
    integrator = models.ForeignKey(Integrator, on_delete=models.CASCADE, null=False)
    context = JSONField(blank=True, null=True)

    class Meta:
        db_table = 'integrator_nodes'


class HttpNode(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, primary_key=True)
    http_method = models.CharField(max_length=10, null=False)
    http_url = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'http_nodes'


class WorkflowExecution(models.Model):
    state = models.CharField(max_length=50, choices=ExecutionState.choices, null=False)
    curr_node = models.ForeignKey(Node, on_delete=models.CASCADE, null=False, related_name='current_node_workflows')
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, null=False, related_name='workflow')
    retry = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=Status.choices, null=False)
    start_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'workflow_execution'


class NodeExecution(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, null=False)
    next_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='next_node_executions', null=True)
    wf_exec_id = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, null=False)
    state = models.CharField(max_length=20, choices=ExecutionState.choices, null=False)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    retry = models.BooleanField(default=False)

    class Meta:
        db_table = 'node_execution'
