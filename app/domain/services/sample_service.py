from typing import List, Optional, Dict, Any
from pathlib import Path
import os
from ..interfaces.repository import ISampleRepository
from ..models.sample import Sample

class SampleService:
    def __init__(self, sample_repo: ISampleRepository):
        self.sample_repo = sample_repo

    def get_stats(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        return self.sample_repo.get_stats(project_id)

    def get_samples(self, limit: int = 100, offset: int = 0, is_labeled: Optional[bool] = None,
                    split: Optional[str] = None, project_id: Optional[int] = None,
                    class_id: Optional[int] = None, command: Optional[int] = None) -> List[dict]:
        samples = self.sample_repo.get_all_samples(limit, offset, is_labeled, split, project_id, class_id, command)
        
        result = []
        for s in samples:
            item = {
                "filename": s.filename,
                "is_labeled": s.is_labeled,
                "updated_at": s.updated_at,
                "data": s.label_data.to_dict()
            }
            item.update(s.label_data.to_dict())
            result.append(item)
            
        return result

    def delete_sample(self, filename: str) -> Dict[str, Any]:
        sample = self.sample_repo.get_sample(filename)
        if not sample:
            return {"status": "error", "message": "Sample not found"}

        image_path = sample.image_path

        self.sample_repo.delete_sample(filename)

        ref_count = self.sample_repo.count_references_to_path(image_path)
        deleted_file = False
        if ref_count == 0:
            try:
                p = Path(image_path)
                if p.exists() and p.is_file():
                    os.remove(p)
                    deleted_file = True
            except Exception as e:
                print(f"Warning: Failed to delete physical file {image_path}: {e}")

        try:
            from ...core.config import Config
            json_path = Config.PROCESSED_DIR / (Path(filename).stem + ".json")
            if json_path.exists():
                os.remove(json_path)
        except Exception:
            pass

        return {"status": "deleted", "physical_file_removed": deleted_file}

    def delete_batch(self, filenames: List[str]) -> Dict[str, Any]:
        deleted_count = 0
        files_removed = 0
        errors = []

        from ...core.config import Config

        for filename in filenames:
            try:
                sample = self.sample_repo.get_sample(filename)
                if not sample:
                    errors.append(f"{filename}: not found")
                    continue

                image_path = sample.image_path

                self.sample_repo.delete_sample(filename)
                deleted_count += 1

                ref_count = self.sample_repo.count_references_to_path(image_path)
                if ref_count == 0:
                    try:
                        p = Path(image_path)
                        if p.exists() and p.is_file():
                            os.remove(p)
                            files_removed += 1
                    except Exception as e:
                        errors.append(f"{filename}: failed to delete file - {e}")

                try:
                    json_path = Config.DATA_DIR / "processed" / (Path(filename).stem + ".json")
                    if json_path.exists():
                        os.remove(json_path)
                except Exception:
                    pass

            except Exception as e:
                errors.append(f"{filename}: {str(e)}")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "files_removed": files_removed,
            "errors": errors if errors else None
        }
