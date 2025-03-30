# crosssell/task_handlers.py
from core.task_registry import TaskRegistry


def execute_http_task(task_data):
    print(f"Executing HTTP task with data: {task_data}")
    # Add HTTP request logic here


def execute_delay_task(task_data):
    print(f"Delaying task execution for {task_data['delay']} seconds")
    # Add delay logic here


def evaluate_if(properties):
    if properties["operator"] == ">":
        return False


# returns next task after evaluating condition
def execute_condition_task(task_data):
    print(f"Evaluating condition: {task_data}")
    # Add condition logic here
    properties = task_data.get("properties")
    condition_type = properties["condition_type"]
    if condition_type == "if":
        evaluate_if(properties)



# Register handlers in CrossSell
TaskRegistry.register("http", execute_http_task)
TaskRegistry.register("delay", execute_delay_task)
TaskRegistry.register("condition", execute_condition_task)
