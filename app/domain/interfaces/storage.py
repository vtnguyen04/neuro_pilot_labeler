from abc import ABC, abstractmethod
from pathlib import Path


class IStorageProvider(ABC):
    @abstractmethod
    def save_file(self, content: bytes, filename: str) -> str:
        pass

    @abstractmethod
    def get_object(self, object_name: str) -> bytes | None:
        pass

    @abstractmethod
    def resolve_file_path(self, filename: str, sample_uri: str | None = None) -> bytes | Path | None:
        pass
