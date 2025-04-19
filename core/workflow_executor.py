# core/workflow_executor.py
from typing import Dict, Any
from .task_registry import TaskRegistry
from .task_handler import TaskHandler
from .task_node import TaskNode


def execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standalone function to execute a workflow.
    Creates a WorkflowExecutor instance and executes the workflow.
    
    Args:
        workflow: Workflow definition containing tasks
        
    Returns:
        Dict containing execution results and status
    """
    executor = WorkflowExecutor()
    return executor.execute_workflow(workflow)


class WorkflowExecutor:
    """
    Executes workflows composed of tasks.
    """
    def __init__(self):
        self.task_registry = TaskRegistry()
        self.task_handler = TaskHandler()
        self.execution_history: Dict[str, Any] = {}

    def execute_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow: Workflow definition containing tasks
            
        Returns:
            Dict containing execution results and status
        """
        try:
            # Convert workflow tasks to TaskNode objects
            tasks = {
                task_id: TaskNode.from_dict(task_data)
                for task_id, task_data in workflow.get("tasks", {}).items()
            }
            
            # Start with the trigger task
            current_task_id = workflow.get("trigger")
            if not current_task_id:
                raise ValueError("No trigger task specified in workflow")
                
            execution_path = []
            
            while current_task_id:
                task = tasks.get(current_task_id)
                if not task:
                    raise ValueError(f"Task {current_task_id} not found in workflow")
                    
                execution_path.append(current_task_id)
                
                # Execute the current task using TaskHandler
                result = self.task_handler.execute_task(task)
                
                # Update task status and result
                task.status = "completed" if result.get("status") != "failed" else "failed"
                task.result = result
                
                # Determine next task
                if task.status == "completed" and task.next:
                    current_task_id = task.next[0]  # For now, take first next task
                else:
                    current_task_id = None
            
            return {
                "status": "completed",
                "execution_path": execution_path,
                "tasks": {task_id: task.to_dict() for task_id, task in tasks.items()}
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
