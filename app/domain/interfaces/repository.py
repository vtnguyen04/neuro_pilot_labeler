from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models.project import Project
from ..models.sample import Sample

class IProjectRepository(ABC):
    @abstractmethod
    def create_project(self, project: Project) -> int:
        pass

    @abstractmethod
    def get_projects(self) -> List[Project]:
        pass

    @abstractmethod
    def get_project(self, project_id: int) -> Optional[Project]:
        pass

    @abstractmethod
    def delete_project(self, project_id: int) -> None:
        pass

    @abstractmethod
    def update_project(self, project: Project) -> None:
        pass


class ISampleRepository(ABC):
    @abstractmethod
    def get_all_samples(self, limit: int = 100, offset: int = 0, is_labeled: Optional[bool] = None,
                       split: Optional[str] = None, project_id: Optional[int] = None,
                       class_id: Optional[int] = None, command: Optional[int] = None) -> List[Sample]:
        pass

    @abstractmethod
    def get_sample(self, filename: str) -> Optional[Sample]:
        pass

    @abstractmethod
    def add_sample(self, sample: Sample) -> None:
        pass

    @abstractmethod
    def save_label(self, sample: Sample) -> None:
        pass

    @abstractmethod
    def delete_sample(self, filename: str) -> None:
        pass

    @abstractmethod
    def delete_by_project(self, project_id: int) -> None:
        pass

    @abstractmethod
    def count_references_to_path(self, image_path: str) -> int:
        pass

    @abstractmethod
    def get_stats(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_analytics(self, project_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_raw_samples_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_raw_sample_data(self, sample_id: int, raw_data_str: str) -> None:
        pass
