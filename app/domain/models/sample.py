from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .label import LabelData


class Sample(BaseModel):
    filename: str
    image_path: str
    project_id: int
    label_data: LabelData = Field(default_factory=LabelData)
    is_labeled: bool = False
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Sample":
        raw_data = row.get("data")
        label_data = LabelData.create_and_heal(raw_data)

        return cls(
            filename=row["filename"] if "filename" in row else row["image_name"],
            image_path=row.get("image_path", ""),
            project_id=row.get("project_id", 0),
            label_data=label_data,
            is_labeled=bool(row.get("is_labeled", False)),
            updated_at=row.get("updated_at"),
        )

    def update_label(self, new_label_data: LabelData):
        self.label_data = new_label_data
        self.is_labeled = True

    def reset_label(self):
        self.label_data = LabelData()
        self.is_labeled = False
