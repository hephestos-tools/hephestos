# core/workflow_executor.py
from core.task_registry import TaskRegistry


def execute_workflow(workflow):
    return None


def execute_task(task):
    #TODO: Task should be a class
    type = task["type"]
    properties = task["properties"]
    next = task["next"]

    handler = TaskRegistry.get_handler(type)
    handler(properties)  # Executes the correct function dynamically
