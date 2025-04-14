from typing import Dict, Any, Callable, Optional
from functools import wraps
from .task_registry import TaskRegistry
from .task_node import TaskNode

class TaskHandler:
    """
    Handles task execution using handlers registered in TaskRegistry.
    """
    def __init__(self):
        self.execution_history: Dict[str, Any] = {}

    def execute_task(self, task: TaskNode) -> Dict[str, Any]:
        """
        Execute a task using the handler registered in TaskRegistry.
        
        Args:
            task: The TaskNode object to execute
            
        Returns:
            Dict containing the task execution result
            
        Raises:
            ValueError: If task validation fails or execution fails
        """
        # Validate task properties using TaskRegistry
        if not TaskRegistry.validate_task(task.type, task.properties):
            raise ValueError(f"Invalid properties for task type: {task.type}")
            
        # Get and execute handler from TaskRegistry
        handler = TaskRegistry.get_handler(task.type)
        try:
            result = handler(task.properties)
            return {
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

def task(task_type: str, validator: Optional[Callable] = None):
    """
    Decorator for registering task handlers in TaskRegistry.
    
    Args:
        task_type: The type of task to handle
        validator: Optional validator function for task properties
    """
    def decorator(func: Callable) -> Callable:
        # Register the handler with TaskRegistry
        TaskRegistry.register(task_type, func, validator)
        
        @wraps(func)
        def wrapper(properties: Dict[str, Any]) -> Any:
            return func(properties)
        return wrapper
    return decorator 