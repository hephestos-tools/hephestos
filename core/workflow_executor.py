# core/workflow_executor.py
from core.task_registry import TaskRegistry

class Task:
    #TODO: verify if using Task is going to be a problem
    def __init__(self, type, properties, next):
        self.type = type
        self.properties = properties
        self.next = next

def execute_workflow(workflow):
    #TODO: think about workflow execution and how to use next field in task, this will get complicated.
    return None


def execute_task(task):
    task = Task(task["type"], task["properties"], task["next"])
    handler = TaskRegistry.get_handler(task.type)
    handler(task.properties)  # Executes the correct function dynamically
