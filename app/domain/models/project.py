from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Project(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    classes: List[str] = Field(default_factory=list)
    commands: List[str] = Field(default_factory=lambda: ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"])
    created_at: Optional[datetime] = None

    def remove_class(self, class_index: int) -> bool:
        if 0 <= class_index < len(self.classes):
            del self.classes[class_index]
            return True
        return False
