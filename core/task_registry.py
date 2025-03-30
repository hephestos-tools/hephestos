# core/task_registry.py
class TaskRegistry:
    _registry = {}

    @classmethod
    def register(cls, task_type, handler):
        """Registers a handler for a specific task type."""
        cls._registry[task_type] = handler

    @classmethod
    def get_handler(cls, task_type):
        """Retrieves the handler for a task type."""
        if task_type not in cls._registry:
            raise ValueError(f"No handler registered for task type: {task_type}")
        return cls._registry[task_type]

