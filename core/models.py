from django.db import models
from django.utils import timezone


# Create your models here.

class ComparisonOperator(models.TextChoices):
    """Available comparison operators for conditions."""
    EQUAL = '=', 'Equal'
    LESS_THAN = '<', 'Less Than'
    GREATER_THAN = '>', 'Greater Than'
    LESS_THAN_EQUAL = '<=', 'Less Than or Equal'
    GREATER_THAN_EQUAL = '>=', 'Greater Than or Equal'


class ConditionType(models.TextChoices):
    """Types of conditions supported in workflows."""
    IF = 'if', 'If'
    SWITCH = 'switch', 'Switch'
    IF_ELSEIF = 'if-elseif', 'If-Elseif'


class TaskType(models.TextChoices):
    """Types of tasks supported in workflows."""
    CONDITION = 'condition', 'Condition'
    ACTION = 'action', 'Action'
    TRIGGER = 'trigger', 'Trigger'
    HTTP = 'http', 'HTTP'
    DELAY = 'delay', 'Delay'
    INTEGRATION = 'integration', 'Integration'


class Status(models.TextChoices):
    """Possible statuses of workflow execution."""
    FAILED = 'FAILED', 'Failed'
    SUCCESS = 'SUCCESS', 'Success'
    RUNNING = 'RUNNING', 'Running'
    PENDING = 'PENDING', 'Pending'


class ExecutionState(models.TextChoices):
    """Possible states of workflow execution."""
    NEW = 'NEW', 'New'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    PAUSE = 'PAUSE', 'Pause'
    COMPLETE = 'COMPLETE', 'Complete'
    RETRY = 'RETRY', 'Retry'


class WorkflowExecution(models.Model):
    """
    Tracks the execution of workflows.
    """
    state = models.CharField(max_length=50, choices=ExecutionState.choices, null=False)
    retry = models.BooleanField(default=False)
    retry_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=50, choices=Status.choices, null=False)
    workflow_data = models.JSONField(null=False)
    execution_history = models.JSONField(default=list)
    error_message = models.TextField(null=True)
    start_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(null=True)  # Calculated field

    class Meta:
        db_table = 'core_workflow_execution'
        indexes = [
            models.Index(fields=['status', 'state']),
            models.Index(fields=['start_time']),
            models.Index(fields=['retry_count'])
        ]

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)
