# this function is responsible for calling core
from core.workflow_executor import execute_workflow
from cross_sell.models import SavedTemplate
from cross_sell.task_provider import execute_condition_task


def evaluate_trigger(workflow):
    trigger = workflow.get("task0")
    if trigger is None and trigger.get("type") == "condition":
        return execute_condition_task(trigger)
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
