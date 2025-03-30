# core/workflow_executor.py
from core.task_registry import TaskRegistry


def execute_workflow(workflow):
    return None


def execute_task(task):
    task_type = task["type"]
    task_data = task["data"]

    handler = TaskRegistry.get_handler(task_type)
    handler(task_data)  # Executes the correct function dynamically
