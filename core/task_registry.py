# core/task_registry.py
from typing import Callable, Dict, Any, Optional
from functools import wraps

class TaskRegistry:
    """
    Central registry for task handlers and validators.
    Apps can register their task handlers here.
    """
    _registry: Dict[str, Callable] = {}
    _validators: Dict[str, Callable] = {}

    @classmethod
    def register(cls, task_type: str, handler: Callable, validator: Optional[Callable] = None) -> None:
        """
        Register a task handler from an app.
        
        Args:
            task_type: The type of task to register
            handler: The function that will handle the task
            validator: Optional function to validate task properties
        """
        if task_type in cls._registry:
            raise ValueError(f"Task type '{task_type}' is already registered")
        cls._registry[task_type] = handler
        if validator:
            cls._validators[task_type] = validator

    @classmethod
    def get_handler(cls, task_type: str) -> Callable:
        """
        Get the handler for a task type.
        
        Args:
            task_type: The type of task to get handler for
            
        Returns:
            The registered handler function
            
        Raises:
            ValueError: If no handler is registered for the task type
        """
        if task_type not in cls._registry:
            raise ValueError(f"No handler registered for task type: {task_type}")
        return cls._registry[task_type]

    @classmethod
    def validate_task(cls, task_type: str, properties: Dict[str, Any]) -> bool:
        """
        Validates task properties using the registered validator.
        
        Args:
            task_type: The type of task to validate
            properties: The properties to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        validator = cls._validators.get(task_type)
        if validator:
            return validator(properties)
        return True

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """
        Returns a list of all registered task types.
        """
        return list(cls._registry.keys())

