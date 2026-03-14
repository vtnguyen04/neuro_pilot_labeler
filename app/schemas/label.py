from datetime import datetime

from pydantic import BaseModel, Field


class BBox(BaseModel):
    cx: float
    cy: float
    w: float
    h: float
    category: int
    id: str | None = None

class Waypoint(BaseModel):
    x: float
    y: float

class LabelBase(BaseModel):
    filename: str
    command: int = 0
    bboxes: list[BBox] = []
    waypoints: list[Waypoint] = []
    control_points: list[Waypoint] = []
    is_labeled: bool = False

class LabelUpdate(BaseModel):
    command: int
    bboxes: list[BBox]
    waypoints: list[Waypoint]
    control_points: list[Waypoint] | None = []

class LabelRead(LabelBase):
    id: int
    updated_at: datetime

class VersionBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None

class VersionCreate(VersionBase):
    project_id: int
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    resize_width: int | None = None
    resize_height: int | None = None

class VersionRead(VersionBase):
    id: int
    project_id: int
    created_at: datetime
    sample_count: int
    path: str

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    classes: list[str] | None = None
    commands: list[str] | None = None

class ProjectRead(ProjectCreate):
    id: int
    created_at: datetime
