from abc import ABC, abstractmethod
from typing import Optional, Union
from pathlib import Path

class IStorageProvider(ABC):
    @abstractmethod
    def save_file(self, content: bytes, filename: str) -> str:
        pass

    @abstractmethod
    def get_object(self, object_name: str) -> Optional[bytes]:
        pass
        
    @abstractmethod
    def resolve_file_path(self, filename: str, sample_uri: Optional[str] = None) -> Optional[Union[bytes, Path]]:
        pass
