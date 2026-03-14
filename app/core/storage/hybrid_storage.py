import logging
import re
from pathlib import Path

from ...domain.interfaces.storage import IStorageProvider
from ..config import Config
from .storage_provider import StorageProvider

logger = logging.getLogger("uvicorn")

class HybridImageProvider(IStorageProvider):
    def __init__(self, minio_provider: StorageProvider):
        self.minio = minio_provider

    def save_file(self, content: bytes, filename: str) -> str:
        return self.minio.save_file(content, filename)

    def get_object(self, object_name: str) -> bytes | None:
        return self.minio.get_object(object_name)

    def resolve_file_path(self, filename: str, sample_uri: str | None = None) -> bytes | Path | None:
        base_filename = re.sub(r'_dup\d+', '', filename)
        for name in [filename, base_filename]:
            try:
                content = self.get_object(name)
                if content:
                    logger.info(f"Serving {filename} from MinIO Storage")
                    return content
            except Exception:
                pass

        if sample_uri:
            if sample_uri.startswith("minio://"):
                try:
                    obj_name = sample_uri.split("/", 3)[-1]
                    content = self.get_object(obj_name)
                    if content:
                        logger.info(f"Serving {filename} from referenced MinIO object: {obj_name}")
                        return content
                except Exception as e:
                    logger.error(f"Failed to fetch {obj_name} from MinIO: {e}")

            local_p = Path(sample_uri)
            if local_p.exists():
                logger.info(f"Serving {filename} from local path: {local_p}")
                return local_p

            if base_filename != filename:
                alt_local_p = Path(str(local_p).replace(filename, base_filename))
                if alt_local_p.exists():
                    logger.info(f"Serving {filename} from original local path: {alt_local_p}")
                    return alt_local_p

        search_dirs = [Config.RAW_DIR, Config.TRAIN_DIR, Config.VAL_DIR, Config.TEST_DIR]
        for d in search_dirs:
            for name in [filename, base_filename]:
                p = d / name
                if p.exists():
                    logger.info(f"Serving {filename} from search dir: {p}")
                    return p

        for d in search_dirs:
            if d.exists():
                for name in [filename, base_filename]:
                    matches = list(d.glob(f"*_{name}"))
                    if matches:
                        logger.info(f"Serving {filename} via fuzzy match: {matches[0]}")
                        return matches[0]

        if Config.LEGACY_IMAGES_DIR.exists():
            for name in [filename, base_filename]:
                matches = list(Config.LEGACY_IMAGES_DIR.rglob(name))
                if matches:
                    logger.info(f"Serving {filename} from legacy images: {matches[0]}")
                    return matches[0]

        return None
