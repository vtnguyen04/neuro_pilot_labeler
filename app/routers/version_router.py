
from fastapi import APIRouter, Depends, HTTPException

from ..core.config import Config
from ..repositories.project_repository import ProjectRepository
from ..repositories.sample_repository import SampleRepository
from ..repositories.version_repository import VersionRepository
from ..schemas.label import VersionCreate
from ..services.version_service import VersionService

router = APIRouter(prefix="/api/v1/versions", tags=["versions"])

def get_version_service():
    db_path = Config.DB_PATH
    v_repo = VersionRepository(db_path)
    s_repo = SampleRepository(db_path)
    p_repo = ProjectRepository(db_path)
    return VersionService(v_repo, s_repo, p_repo)

@router.get("/")
def list_versions(
    project_id: int | None = None,
    service: VersionService = Depends(get_version_service)
):
    return service.list_versions(project_id)

@router.post("/")
def publish_version(
    version: VersionCreate,
    service: VersionService = Depends(get_version_service)
):
    try:
        return service.publish_version(
            version.name,
            version.description or "",
            version.project_id,
            version.train_ratio,
            version.val_ratio,
            version.test_ratio,
            version.resize_width,
            version.resize_height
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{version_id}")
def delete_version(
    version_id: int,
    service: VersionService = Depends(get_version_service)
):
    try:
        return service.delete_version(version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{version_id}/download")
def download_version(
    version_id: int,
    service: VersionService = Depends(get_version_service)
):
    try:
        import os

        from fastapi.responses import FileResponse
        zip_path = service.create_zip(version_id)
        return FileResponse(zip_path, media_type='application/zip', filename=os.path.basename(zip_path))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
