from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

class TaskStatus(Enum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"

@dataclass
class DocumentNode:
    text: str
    level: int
    line_number: int
    children: List['DocumentNode'] = field(default_factory=list)
    is_task: bool = False
    task_data: Optional[Dict] = None
    parent: Optional['DocumentNode'] = None
