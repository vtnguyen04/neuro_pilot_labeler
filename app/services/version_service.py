import os
import random
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..core.config import Config
from ..repositories.project_repository import ProjectRepository
from ..repositories.sample_repository import SampleRepository
from ..repositories.version_repository import VersionRepository
from ..utils.yolo_utils import save_yolo_label


class VersionService:
    def __init__(self, version_repo: VersionRepository, sample_repo: SampleRepository, project_repo: ProjectRepository):
        self.version_repo = version_repo
        self.sample_repo = sample_repo
        self.project_repo = project_repo

    def list_versions(self, project_id: int | None = None):
        return self.version_repo.list_versions(project_id)

    def delete_version(self, version_id: int):
        version = self.version_repo.get_version(version_id)
        if not version:
            raise ValueError("Version not found")

        path_str = version.get('path')
        if path_str:
            export_path = Path(path_str)
            if export_path.exists() and export_path.is_dir() and len(path_str) > 5:
                try:
                    shutil.rmtree(export_path)
                except Exception as e:
                    print(f"Warning: Failed to delete physical directory {export_path}: {e}")
            else:
                print(
                    f"Info: Skipping directory deletion for version {version_id}, "
                    f"path {path_str} is invalid or non-existent"
                )

        self.version_repo.delete_version(version_id)
        return {"status": "deleted"}

    def publish_version(self, name: str, description: str, project_id: int,
                        train_ratio: float = 0.8, val_ratio: float = 0.1, test_ratio: float = 0.1,
                        resize_width: int | None = None, resize_height: int | None = None):
        all_samples = self.sample_repo.get_all_samples(limit=1000000, is_labeled=True, project_id=project_id)
        if not all_samples:
            raise ValueError("No labeled samples found for this project")

        try:
            from ..core.storage.storage_provider import MinioStorageProvider
        except ImportError:
            if any(s.image_path.startswith("minio://") for s in all_samples):
                raise ImportError("The 'minio' package is required. Please install it with 'uv add minio'.")
            MinioStorageProvider = None

        if MinioStorageProvider:
            storage = MinioStorageProvider(
                endpoint=Config.MINIO_ENDPOINT,
                access_key=Config.MINIO_ACCESS_KEY,
                secret_key=Config.MINIO_SECRET_KEY,
                bucket_name=Config.MINIO_BUCKET_NAME,
                secure=Config.MINIO_SECURE
            )
        else:
            storage = None

        classes = self.project_repo.get_classes(project_id)
        if not classes:
            classes = [
                "Stop", "Obstacle", "Pedestrian", "Car", "Priority", "Crosswalk", "Oneway",
                "Stop-Line", "Parking", "Highway-Entry", "Roundabout", "Highway-Exit",
                "Traffic-Light", "No-Entry"
            ]

        version_dir = Config.EXPORT_DIR / f"project_{project_id}" / name
        version_dir.mkdir(parents=True, exist_ok=True)

        for split in ['train', 'val', 'test']:
            (version_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (version_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

        class_groups = {i: [] for i in range(len(classes))}
        for s in all_samples:
            label_data = s.label_data
            primary_cat = 0
            if label_data.bboxes:
                primary_cat = label_data.bboxes[0].category

            if primary_cat < len(classes):
                class_groups[primary_cat].append(s)
            else:
                class_groups[0].append(s)

        train_samples, val_samples, test_samples = [], [], []

        for cat_id, samples in class_groups.items():
            random.shuffle(samples)
            n = len(samples)
            if n == 0:
                continue

            n_train = int(round(n * train_ratio))
            n_val = int(round(n * val_ratio))

            if n_train + n_val > n:
                if n_val > 0:
                    n_val = n - n_train
                else:
                    n_train = n

            if test_ratio <= 0:
                n_test = 0
                if n_train + n_val < n:
                    n_train = n - n_val
            else:
                n_test = n - n_train - n_val

            train_samples.extend(samples[:n_train])
            val_samples.extend(samples[n_train:n_train + n_val])
            test_samples.extend(samples[n_train + n_val:n_train + n_val + n_test])

        version_id = self.version_repo.create_version(name, description, project_id, str(version_dir))

        tasks = []
        for split, samples in [('train', train_samples), ('val', val_samples), ('test', test_samples)]:
            for s in samples:
                tasks.append((split, s))

        def process_item(item):
            import io

            from PIL import Image
            split, s = item
            filename = s.filename
            label_data = s.label_data

            img_path = s.image_path
            dest_img = version_dir / split / 'images' / filename

            data_bytes = None
            if img_path and img_path.startswith("minio://"):
                if not storage:
                    return False
                try:
                    obj_name = img_path.split("/", 3)[-1]
                    data_bytes = storage.get_object(obj_name)
                except Exception as e:
                    print(f"Error downloading from MinIO {img_path}: {e}")
                    return None
            else:
                src_img = self._find_image(filename, img_path)
                if src_img:
                    if resize_width is None and resize_height is None:
                        try:
                            shutil.copy2(src_img, dest_img)
                        except Exception as e:
                            print(f"Error copying image {filename}: {e}")
                            return None
                    else:
                        with open(src_img, "rb") as f:
                            data_bytes = f.read()
                else:
                    print(f"Warning: Image not found for {filename}, skipping...")
                    return None

            if data_bytes:
                try:
                    img = Image.open(io.BytesIO(data_bytes))
                    if resize_width and resize_height:
                        img = img.resize((resize_width, resize_height), Image.Resampling.LANCZOS)
                    img.save(dest_img, quality=95)
                except Exception as e:
                    print(f"Error processing image {filename}: {e}")
                    return None

            cat_list = []
            bboxes_list = []
            kpts_list = []

            for bbox in label_data.bboxes:
                cat_list.append(bbox.category)
                bboxes_list.append([bbox.cx, bbox.cy, bbox.w, bbox.h])
                kpts_list.append([])

            if label_data.waypoints:
                flat_wps = []
                for wp in label_data.waypoints:
                    flat_wps.extend([wp.x, wp.y])

                if len(flat_wps) >= 2:
                    kpts_list.append(flat_wps)
                    bboxes_list.append([0.5, 0.5, 0.1, 0.1])
                    cat_list.append(98)

            txt_name = Path(filename).with_suffix(".txt").name
            txt_path = version_dir / split / 'labels' / txt_name
            save_yolo_label(txt_path, cat_list, bboxes_list, kpts_list, label_data.command)

            self.version_repo.add_item_to_version(version_id, filename, label_data.to_json_str(), split)
            return True

        total_count = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(process_item, tasks))
            total_count = sum(1 for r in results if r)

        # 6. Create data.yaml
        yaml_content = {
            'path': str(version_dir.absolute()),
            'nc': len(classes),
            'names': classes
        }
        if train_samples:
            yaml_content['train'] = 'train/images'
        if val_samples:
            yaml_content['val'] = 'val/images'
        if test_samples:
            yaml_content['test'] = 'test/images'

        with open(version_dir / 'data.yaml', 'w') as f:
            import yaml
            yaml.dump(yaml_content, f)

        self.version_repo.update_sample_count(version_id, total_count)

        return {"status": "published", "version_id": version_id, "path": str(version_dir), "sample_count": total_count}

    def create_zip(self, version_id: int):
        version = self.version_repo.get_version(version_id)
        if not version:
            raise ValueError("Version not found")

        version_dir = Path(version['path'])
        zip_path = version_dir.parent / f"{version['name']}.zip"

        if not version_dir.exists():
            raise FileNotFoundError(f"Version directory {version_dir} not found")

        shutil.make_archive(str(version_dir), 'zip', version_dir)
        return str(zip_path)

    def _find_image(self, filename: str, hint_path: str | None = None) -> Path | None:
        if hint_path and os.path.exists(hint_path):
            return Path(hint_path)
        for d in [Config.RAW_DIR, Config.TRAIN_DIR, Config.VAL_DIR, Config.TEST_DIR]:
            p = d / filename
            if p.exists():
                return p
        for d in [Config.RAW_DIR, Config.TRAIN_DIR, Config.VAL_DIR, Config.TEST_DIR]:
            if d.exists():
                matches = list(d.glob(f"*_{filename}"))
                if matches:
                    return matches[0]
        if Config.LEGACY_IMAGES_DIR.exists():
            matches = list(Config.LEGACY_IMAGES_DIR.rglob(filename))
            if matches:
                return matches[0]
        return None
