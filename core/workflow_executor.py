# core/workflow_executor.py
import logging
from typing import Dict, Any, Optional
from .task_registry import TaskRegistry
from .task_handler import TaskHandler
from .task_node import TaskNode

logger = logging.getLogger(__name__)

def execute_workflow(workflow: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Standalone function to execute a workflow, passing along context.
    Creates a WorkflowExecutor instance and executes the workflow.
    
    Args:
        workflow: Workflow definition containing tasks
        context: Optional dictionary containing execution context (e.g., order, shop)
        
    Returns:
        Dict containing execution results and status
    """
    executor = WorkflowExecutor()
    return executor.execute_workflow(workflow, context)


class WorkflowExecutor:
    """
    Executes workflows composed of tasks, utilizing context.
    """
    def __init__(self):
        self.task_registry = TaskRegistry()
        self.task_handler = TaskHandler()
        self.execution_history: Dict[str, Any] = {}

    def execute_workflow(self, workflow: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a complete workflow, passing context to tasks.
        
        Args:
            workflow: Workflow definition containing tasks
            context: Optional dictionary containing execution context
            
        Returns:
            Dict containing execution results and status
        """
        tasks: Dict[str, TaskNode] = {}
        execution_path: list[str] = []
        
        try:
            logger.info(f"Starting workflow execution. Context keys: {list(context.keys()) if context else 'None'}")
            # Convert workflow tasks to TaskNode objects
            tasks = {
                task_id: TaskNode.from_dict(task_data)
                for task_id, task_data in workflow.get("tasks", {}).items()
            }
            
            # Start with the trigger task
            current_task_id = workflow.get("trigger")
            if not current_task_id:
                logger.error("Workflow definition missing 'trigger' task ID.")
                raise ValueError("No trigger task specified in workflow")
                
            logger.debug(f"Initial trigger task ID: {current_task_id}")
            
            while current_task_id:
                task = tasks.get(current_task_id)
                if not task:
                    logger.error(f"Task ID '{current_task_id}' not found in workflow definition.")
                    raise ValueError(f"Task {current_task_id} not found in workflow")
                    
                execution_path.append(current_task_id)
                logger.info(f"Executing task ID: {current_task_id}, Type: {task.type}")
                
                try:
                    # Execute the current task using TaskHandler, passing context
                    result = self.task_handler.execute_task(task, context)
                    logger.debug(f"Task {current_task_id} result: {result}")
                    
                    # Update task status and result based on handler's output
                    task.status = result.get("status", "failed") # Default to failed if status missing
                    task.result = result # Store the entire result dictionary
                    
                    # Determine next task
                    next_task_id = None
                    if task.status == "completed":
                        if task.next: 
                            # Simple logic: take the first defined next task
                            # TODO: Add logic to handle multiple next tasks
                            next_task_id = task.next[0] 
                            logger.info(f"Task {current_task_id} completed. Next task: {next_task_id}")
                        else:
                            logger.info(f"Task {current_task_id} completed. No next task defined. Workflow ends.")
                    else: # Task failed or other non-completed status
                        logger.warning(f"Task {current_task_id} did not complete successfully (status: {task.status}). Stopping workflow branch.")
                        # TODO: Implement error handling paths if defined in workflow
                        
                    current_task_id = next_task_id # Move to the next task or None to end
                
                except Exception as task_exc:
                    logger.error(f"Error executing task {current_task_id}: {task_exc}", exc_info=True)
                    task.status = "failed"
                    task.result = {"status": "failed", "error": str(task_exc)}
                    # Stop workflow execution on task error
                    current_task_id = None 
                    # Re-raise or handle differently if needed
                    raise task_exc # Propagate exception to the outer handler
            
            logger.info(f"Workflow execution finished. Final status: completed")
            return {
                "status": "completed",
                "execution_path": execution_path,
                "tasks": {task_id: task.to_dict() for task_id, task in tasks.items()}
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            # Ensure partial results/status are included if possible
            return {
                "status": "failed",
                "error": str(e),
                "execution_path": execution_path,
                "tasks": {task_id: task.to_dict() for task_id, task in tasks.items()} # Include task states up to the failure
            }
