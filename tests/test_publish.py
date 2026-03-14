import random

from app.core.config import Config
from app.domain.models.project import Project
from app.domain.models.sample import Sample
from app.domain.services.version_service import VersionService
from app.repositories.project_repository import ProjectRepository
from app.repositories.sample_repository import SampleRepository
from app.repositories.version_repository import VersionRepository


def test_publish_version(test_db, mock_storage):
    """Test publishing a new version of the dataset."""
    v_repo = VersionRepository(test_db)
    s_repo = SampleRepository(test_db)
    p_repo = ProjectRepository(test_db)
    service = VersionService(v_repo, s_repo, p_repo, mock_storage)

    # 1. Setup a Project
    project = Project(name="Publish Test Project", classes=["A", "B"])
    project_id = p_repo.create_project(project)

    # 2. Add a labeled sample and a dummy image
    filename = "test_publish.jpg"
    Config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    dummy_img = Config.RAW_DIR / filename
    dummy_img.write_text("dummy image data")

    try:
        sample = Sample(filename=filename, image_path=str(dummy_img), project_id=project_id, is_labeled=True)
        s_repo.add_sample(sample)

        version_name = f"test_v_{random.randint(1000, 9999)}"

        res = service.publish_version(
            name=version_name,
            description="Automated Pytest",
            project_id=project_id,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
        )

        assert res["status"] == "published"
        assert res["sample_count"] == 1
        assert "version_id" in res
    finally:
        if dummy_img.exists():
            dummy_img.unlink()
