from typing import Optional, Dict, Any
from pathlib import Path
from ..interfaces.repository import ISampleRepository, IProjectRepository
from ..models.label import LabelData
from ...utils.yolo_utils import save_yolo_label
from ...schemas.label import LabelUpdate

class AnnotationService:
    def __init__(self, sample_repo: ISampleRepository, project_repo: IProjectRepository):
        self.sample_repo = sample_repo
        self.project_repo = project_repo

    def get_sample_detail(self, filename: str) -> Optional[Dict[str, Any]]:
        sample = self.sample_repo.get_sample(filename)
        if not sample:
            return None

        data = sample.label_data.to_dict()

        return {
            "filename": filename,
            "is_labeled": sample.is_labeled,
            "updated_at": sample.updated_at,
            **data
        }

    def update_label(self, filename: str, update: LabelUpdate) -> Dict[str, str]:
        label_data = LabelData(
            bboxes=[b.model_dump() for b in update.bboxes],
            waypoints=[w.model_dump() for w in update.waypoints],
            control_points=[cp.model_dump() for cp in update.control_points] if hasattr(update, 'control_points') else [],
            command=update.command
        )

        sample = self.sample_repo.get_sample(filename)
        if not sample:
            return {"status": "error", "message": "Sample not found"}

        sample.update_label(label_data)
        self.sample_repo.save_label(sample)

        project_id = sample.project_id
        from ...core.config import Config
        label_dir = Config.DATA_DIR / "labels"
        label_dir.mkdir(parents=True, exist_ok=True)

        yolo_path = label_dir / (Path(filename).stem + ".txt")
        save_yolo_label(
            yolo_path,
            cls=[b.category for b in update.bboxes],
            bboxes=[[b.cx, b.cy, b.w, b.h] for b in update.bboxes],
            keypoints=[[w.x, w.y] for w in update.waypoints],
            command=update.command
        )

        return {"status": "success", "image": filename}

    def reset_label(self, filename: str) -> Dict[str, str]:
        sample = self.sample_repo.get_sample(filename)
        if sample:
            sample.reset_label()
            self.sample_repo.save_label(sample)
        return {"status": "success", "image": filename}

    def duplicate_sample(self, filename: str, new_filename: str) -> Dict[str, str]:
        self.sample_repo.duplicate_sample(filename, new_filename)
        return {"status": "success", "new_image": new_filename}
