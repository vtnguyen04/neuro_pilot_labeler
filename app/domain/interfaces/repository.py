from abc import ABC, abstractmethod
from typing import Any

from ..models.project import Project
from ..models.sample import Sample


class IProjectRepository(ABC):
    @abstractmethod
    def create_project(self, project: Project) -> int:
        pass

    @abstractmethod
    def get_projects(self) -> list[Project]:
        pass

    @abstractmethod
    def get_project(self, project_id: int) -> Project | None:
        pass

    @abstractmethod
    def delete_project(self, project_id: int) -> None:
        pass

    @abstractmethod
    def update_project(self, project: Project) -> None:
        pass


class IVersionRepository(ABC):
    @abstractmethod
    def create_version(self, name: str, description: str, project_id: int, path: str) -> int:
        pass

    @abstractmethod
    def get_version(self, version_id: int) -> dict | None:
        pass

    @abstractmethod
    def list_versions(self, project_id: int | None = None) -> list[dict]:
        pass

    @abstractmethod
    def delete_version(self, version_id: int) -> None:
        pass

    @abstractmethod
    def add_item_to_version(self, version_id: int, filename: str, data: str, split: str) -> None:
        pass

    @abstractmethod
    def update_sample_count(self, version_id: int, count: int) -> None:
        pass


class ISampleRepository(ABC):
    @abstractmethod
    def get_all_samples(
        self,
        limit: int = 100,
        offset: int = 0,
        is_labeled: bool | None = None,
        split: str | None = None,
        project_id: int | None = None,
        class_id: int | None = None,
        command: int | None = None,
        has_control_points: bool | None = None,
    ) -> list[Sample]:
        pass

    @abstractmethod
    def get_sample(self, filename: str) -> Sample | None:
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
    def get_stats(self, project_id: int | None = None) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_analytics(self, project_id: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_raw_samples_for_project(self, project_id: int) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def update_raw_sample_data(self, sample_id: int, raw_data_str: str) -> None:
        pass

    @abstractmethod
    def copy_sample_to_project(
        self,
        filename: str,
        new_filename: str,
        new_project_id: int,
        class_map: dict[int, int],
        command_map: dict[int, int],
    ) -> None:
        pass
