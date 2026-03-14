from datetime import datetime

from pydantic import BaseModel, Field


class Project(BaseModel):
    id: int | None = None
    name: str = Field(..., min_length=1)
    description: str | None = None
    classes: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=lambda: ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"])
    created_at: datetime | None = None

    def remove_class(self, class_index: int) -> bool:
        if 0 <= class_index < len(self.classes):
            del self.classes[class_index]
            return True
        return False
