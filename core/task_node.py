# core/task_node.py
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class TaskNode:
    """
    Represents a task node in the workflow.
    """
    type: str
    properties: Dict[str, Any]
    next: Optional[List[str]] = None
    id: Optional[str] = None
    status: str = "pending"
    result: Optional[Any] = None

    def __post_init__(self):
        """Initialize task with default values if not provided."""
        if self.id is None:
            self.id = f"task_{id(self)}"
        if self.next is None:
            self.next = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties,
            "next": self.next,
            "status": self.status,
            "result": self.result
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskNode':
        """Create a TaskNode instance from dictionary data."""
        return cls(
            type=data["type"],
            properties=data["properties"],
            next=data.get("next"),
            id=data.get("id"),
            status=data.get("status", "pending"),
            result=data.get("result")
        ) 