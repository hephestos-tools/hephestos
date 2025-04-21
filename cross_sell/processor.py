import logging
from typing import Dict, Any

# this function is responsible for calling core
from core.workflow_executor import execute_workflow
from cross_sell.models import SavedTemplate
from cross_sell.task_provider import execute_condition_task

logger = logging.getLogger(__name__)

# TODO: Enhance trigger evaluation logic
# - Pass context (order, shop) to the trigger condition?
# - Support different trigger types beyond 'condition'?
def evaluate_trigger(workflow: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Evaluates the workflow's trigger condition."""
    trigger_id = workflow.get("trigger", "task0") # Default trigger task ID
    trigger_task = workflow.get("tasks", {}).get(trigger_id)

    if not trigger_task:
        logger.warning(f"Workflow missing trigger task with ID: {trigger_id}")
        return False

    # Simple condition check for now - potentially expand based on context
    if trigger_task.get("type") == "condition":
        try:
            # Assuming execute_condition_task might need context in the future
            # Currently, it seems to only use task properties.
            return execute_condition_task(trigger_task.get("properties", {}), context) 
        except Exception as e:
            logger.error(f"Error executing trigger task {trigger_id}: {e}", exc_info=True)
            return False # Fail trigger evaluation on error
    else:
        logger.warning(f"Unsupported trigger task type '{trigger_task.get("type")}' for task ID: {trigger_id}")
        return False

# Updated process function to accept context
def process(workflow_context: Dict[str, Any]):
    """Fetches and executes workflows relevant to the incoming event context."""
    shop = workflow_context.get("shop")
    order = workflow_context.get("order") # Extract order if needed for logging/logic

    if not shop or not shop.domain:
        logger.error("Shop information missing in workflow_context. Cannot fetch workflows.")
        return # Or raise an error

    logger.info(f"Processing event for shop: {shop.domain}, order_id: {order.id if order else 'N/A'}")

    try:
        saved_workflows = SavedTemplate.objects.filter(shop=shop.domain)
        logger.info(f"Found {saved_workflows.count()} saved workflows for shop: {shop.domain}")

        if not saved_workflows.exists():
            logger.info(f"No workflows found for shop {shop.domain}. Nothing to process.")
            return

    except Exception as db_exc:
        logger.error(f"Database error fetching workflows for shop {shop.domain}: {db_exc}", exc_info=True)
        # Depending on desired behavior, maybe re-raise or handle differently
        return

    # TODO: Implement async/parallel execution (e.g., using Celery/Django-Q)
    # Example: tasks = [process_single_workflow.delay(wf.id, workflow_context) for wf in saved_workflows]
    
    executed_count = 0
    for workflow_template in saved_workflows:
        workflow_json = workflow_template.workflow_json
        logger.debug(f"Evaluating workflow: {workflow_template.name} (ID: {workflow_template.id})")
        try:
            # Pass context to trigger evaluation
            is_executable = evaluate_trigger(workflow_json, workflow_context)
            if is_executable:
                logger.info(f"Trigger evaluated true for workflow {workflow_template.name}. Executing...")
                # Pass context to the executor
                execution_result = execute_workflow(workflow_json, workflow_context)
                logger.info(f"Workflow {workflow_template.name} execution result: {execution_result.get('status')}")
                # TODO: Handle execution result (e.g., log errors, update status)
                if execution_result.get('status') == 'failed':
                     logger.error(f"Workflow {workflow_template.name} failed: {execution_result.get('error')}")
                executed_count += 1
            else:
                logger.info(f"Trigger evaluated false for workflow {workflow_template.name}. Skipping.")
                continue
        except Exception as exec_exc:
            logger.error(f"Error processing workflow {workflow_template.name} (ID: {workflow_template.id}): {exec_exc}", exc_info=True)
            # Decide if one workflow failure should stop others

    logger.info(f"Finished processing for shop {shop.domain}. Executed {executed_count} workflows.")
