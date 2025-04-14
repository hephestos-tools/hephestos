# cross_sell/task_provider.py
from typing import Dict, Any, List
from core.task_handler import task


def validate_http_properties(properties: Dict[str, Any]) -> bool:
    """Validate properties for HTTP task."""
    return (
        "url" in properties and 
        isinstance(properties["url"], str) and
        "method" in properties and
        properties["method"] in ["GET", "POST", "PUT", "DELETE"]
    )

@task("http", validator=validate_http_properties)
def execute_http_task(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an HTTP request task.
    
    Args:
        properties: {
            "url": str,
            "method": str,
            "headers": Dict[str, str],  # optional
            "body": Dict[str, Any]      # optional
        }
        
    Returns:
        Dict containing response data or error
    """
    try:
        # TODO: Implement actual HTTP request logic
        print(f"Executing HTTP {properties['method']} request to {properties['url']}")
        return {
            "status": "completed",
            "response": {
                "status_code": 200,  # Mock response
                "data": "Success"
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

def validate_delay_properties(properties: Dict[str, Any]) -> bool:
    """Validate properties for delay task."""
    return (
        "duration" in properties and 
        isinstance(properties["duration"], (int, float)) and
        properties["duration"] > 0 and
        "unit" in properties and
        properties["unit"] in ["seconds", "minutes", "hours"]
    )

@task("delay", validator=validate_delay_properties)
def execute_delay_task(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a delay task.
    
    Args:
        properties: {
            "duration": float,
            "unit": str  # "seconds", "minutes", "hours"
        }
        
    Returns:
        Dict containing delay status
    """
    try:
        # TODO: Implement actual delay logic
        print(f"Delaying execution for {properties['duration']} {properties['unit']}")
        return {
            "status": "completed",
            "delayed_for": f"{properties['duration']} {properties['unit']}"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

def validate_condition_properties(properties: Dict[str, Any]) -> bool:
    """Validate properties for condition task."""
    return (
        "condition_type" in properties and
        properties["condition_type"] in ["if", "else-if", "switch"] and
        "conditions" in properties and
        isinstance(properties["conditions"], list) and
        len(properties["conditions"]) > 0
    )

@task("condition", validator=validate_condition_properties)
def execute_condition_task(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a condition evaluation task.
    
    Args:
        properties: {
            "condition_type": str,  # "if", "else-if", "switch"
            "conditions": List[Dict[str, Any]],  # List of conditions to evaluate
            "context": Dict[str, Any]  # Variables available for evaluation
        }
        
    Returns:
        Dict containing evaluation results
    """
    try:
        condition_type = properties["condition_type"]
        conditions = properties["conditions"]
        context = properties.get("context", {})
        
        match condition_type:
            case "if":
                result = evaluate_if(conditions[0], context)
            case "else-if":
                result = evaluate_elif(conditions, context)
            case "switch":
                result = evaluate_switch(conditions, context)
            case _:
                raise ValueError(f"Unknown condition type: {condition_type}")
                
        return {
            "status": "completed",
            "result": result,
            "matched_condition": result.get("matched_index") if isinstance(result, dict) else None
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

def evaluate_if(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Evaluate a single if condition.
    
    Args:
        condition: {
            "field": str,
            "operator": str,  # ">", "<", "==", etc.
            "value": Any
        }
        context: Variables available for evaluation
        
    Returns:
        bool: True if condition is met
    """
    field = condition["field"]
    operator = condition["operator"]
    value = condition["value"]
    
    # Get the actual value from context
    actual_value = context.get(field)
    
    # Evaluate the condition
    match operator:
        case ">":
            return actual_value > value
        case "<":
            return actual_value < value
        case "==":
            return actual_value == value
        case _:
            raise ValueError(f"Unsupported operator: {operator}")

def evaluate_elif(conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate multiple elif conditions.
    
    Args:
        conditions: List of condition dictionaries
        context: Variables available for evaluation
        
    Returns:
        Dict containing evaluation result and matched index
    """
    for i, condition in enumerate(conditions):
        if evaluate_if(condition, context):
            return {
                "matched": True,
                "matched_index": i,
                "result": True
            }
    
    return {
        "matched": False,
        "result": False
    }

def evaluate_switch(conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate switch conditions (equality checks).
    
    Args:
        conditions: List of condition dictionaries
        context: Variables available for evaluation
        
    Returns:
        Dict containing evaluation result and matched index
    """
    for i, condition in enumerate(conditions):
        # For switch, we only do equality checks
        condition["operator"] = "=="
        if evaluate_if(condition, context):
            return {
                "matched": True,
                "matched_index": i,
                "result": True
            }
    
    return {
        "matched": False,
        "result": False
    }
