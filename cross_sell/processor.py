# this function is responsible for calling core
from core.workflow_executor import execute_workflow
from cross_sell.models import SavedTemplate
from cross_sell.task_provider import execute_condition_task


def evaluate_trigger(workflow):
    # Get the trigger task ID from the workflow
    trigger_id = workflow.get("trigger", "task0")
    
    # Get the task from the tasks dictionary
    trigger_task = workflow.get("tasks", {}).get(trigger_id)
    
    if trigger_task and trigger_task.get("type") == "condition":
        # Execute the condition task to determine if workflow should run
        return execute_condition_task(trigger_task.get("properties", {}))
    return False


def process(webhook_data, shop, order):
    saved_workflows = SavedTemplate.objects.filter(shop=shop.domain)

    if not saved_workflows:
        return
    else:
        # TODO: Make execution async and parallelize
        for workflow in saved_workflows:
            is_executable = evaluate_trigger(workflow.workflow_json)
            if is_executable:
                execute_workflow(workflow.workflow_json)
            else:
                continue
