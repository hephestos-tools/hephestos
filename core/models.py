from django.db import models
from django.db.models import JSONField


# Create your models here.

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


class Status(models.TextChoices):
    FAILED = 'FAILED', 'Failed'
    SUCCESS = 'SUCCESS', 'Success'
    RUNNING = 'RUNNING', 'Running'


class ExecutionState(models.TextChoices):
    NEW = 'NEW', 'New'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    PAUSE = 'PAUSE', 'Pause'
    COMPLETE = 'COMPLETE', 'Complete'
    RETRY = 'RETRY', 'Retry'


class WorkflowExecution(models.Model):
    state = models.CharField(max_length=50, choices=ExecutionState.choices, null=False)
    retry = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=Status.choices, null=False)
    workflow_data = models.JSONField(null=False)
    start_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'core_workflow_execution'
