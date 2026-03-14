from typing import Any

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

class LabelData(BaseModel):
    command: int = 0
    bboxes: list[BBox] = Field(default_factory=list)
    waypoints: list[Waypoint] = Field(default_factory=list)
    control_points: list[Waypoint] = Field(default_factory=list)

    @classmethod
    def create_and_heal(cls, raw_data: str | dict[str, Any]) -> 'LabelData':
        import json
        if isinstance(raw_data, str):
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                data = {}
        else:
            data = raw_data or {}

        raw_bboxes = data.get('bboxes', [])
        categories = data.get('categories', [])
        healed_bboxes = []

        if raw_bboxes and len(raw_bboxes) > 0:
            for i, b in enumerate(raw_bboxes):
                if isinstance(b, dict):
                    healed_bboxes.append(b)
                elif isinstance(b, (list, tuple)) and len(b) >= 4:
                    cat = categories[i] if categories and i < len(categories) else 0
                    healed_bboxes.append({
                        "cx": b[0], "cy": b[1], "w": b[2], "h": b[3],
                        "category": cat,
                        "id": f"heal_{i}"
                    })

        raw_waypoints = data.get('waypoints', [])
        healed_waypoints = []
        if raw_waypoints:
            for w in raw_waypoints:
                if isinstance(w, dict):
                    healed_waypoints.append(w)
                elif isinstance(w, (list, tuple)) and len(w) >= 2:
                    healed_waypoints.append({"x": w[0], "y": w[1]})

        raw_cp = data.get('control_points', [])
        healed_cp = []
        if raw_cp:
            for p in raw_cp:
                if isinstance(p, dict):
                    healed_cp.append(p)
                elif isinstance(p, (list, tuple)) and len(p) >= 2:
                    healed_cp.append({"x": p[0], "y": p[1]})

        safe_data = {
            "command": data.get('command', 0),
            "bboxes": healed_bboxes,
            "waypoints": healed_waypoints,
            "control_points": healed_cp
        }

        return cls(**safe_data)

    def to_dict(self) -> dict:
        return self.model_dump()

    def to_json_str(self) -> str:
        return self.model_dump_json()

    def remove_class(self, class_id_to_remove: int) -> bool:
        modified = False
        new_boxes = []
        for box in self.bboxes:
            if box.category == class_id_to_remove:
                modified = True
                continue
            elif box.category > class_id_to_remove:
                box.category -= 1
                modified = True
                new_boxes.append(box)
            else:
                new_boxes.append(box)

        if modified:
            self.bboxes = new_boxes

        return modified
