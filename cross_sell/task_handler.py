# cross_sell/task_handlers.py
from core.task_registry import TaskRegistry


def execute_http_task(task_data):
    print(f"Executing HTTP task with data: {task_data}")
    # Add HTTP request logic here


def execute_delay_task(task_data):
    print(f"Delaying task execution for {task_data['delay']} {task_data['units']}")
    # Add delay logic here


def evaluate_if(task_data):
    if task_data["field"] == ">":
        return False


# returns next task after evaluating condition
def evaluate_elif(task_data):
    #TODO: logic will be evolved version of evaluate_if, except the arguments to evaluate would be multiple
    pass


def evaluate_switch(task_data):
    #TODO: logic will be simple version of elif where we just need to do equals check for each case, will leverage evaluate_if here as well since fundamentally its just if evaluation
    pass


def execute_condition_task(properties):
    print(f"Evaluating condition: {properties[0]}")
    condition_type = properties["condition_type"]
    match condition_type:
        case "if":
            return evaluate_if(properties)
        case "else-if":
            return evaluate_elif(properties)
        case "switch":
            return evaluate_switch(properties)


# Register handlers in CrossSell
TaskRegistry.register("http", execute_http_task)
TaskRegistry.register("delay", execute_delay_task)
TaskRegistry.register("condition", execute_condition_task)
