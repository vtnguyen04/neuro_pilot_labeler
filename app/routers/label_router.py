from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
import io
import logging
from pathlib import Path

from ..schemas.label import LabelRead, LabelUpdate, ProjectCreate
from ..core.config import Config
from ..core.storage.storage_provider import MinioStorageProvider
from ..core.storage.hybrid_storage import HybridImageProvider

from ..repositories.sample_repository import SampleRepository
from ..repositories.project_repository import ProjectRepository

from ..domain.services.project_service import ProjectService
from ..domain.services.sample_service import SampleService
from ..domain.services.annotation_service import AnnotationService

router = APIRouter(prefix="/api/v1/labels", tags=["labels"])
logger = logging.getLogger("uvicorn")

def get_db_path():
    return Config.DB_PATH

def get_project_repo(db_path=Depends(get_db_path)):
    return ProjectRepository(db_path)

def get_sample_repo(db_path=Depends(get_db_path)):
    return SampleRepository(db_path)

def get_project_service(
    project_repo=Depends(get_project_repo), 
    sample_repo=Depends(get_sample_repo)
) -> ProjectService:
    return ProjectService(project_repo, sample_repo)

def get_sample_service(sample_repo=Depends(get_sample_repo)) -> SampleService:
    return SampleService(sample_repo)

def get_annotation_service(
    sample_repo=Depends(get_sample_repo), 
    project_repo=Depends(get_project_repo)
) -> AnnotationService:
    return AnnotationService(sample_repo, project_repo)

def get_storage_provider() -> HybridImageProvider:
    minio = MinioStorageProvider(
        endpoint=Config.MINIO_ENDPOINT,
        access_key=Config.MINIO_ACCESS_KEY,
        secret_key=Config.MINIO_SECRET_KEY,
        bucket_name=Config.MINIO_BUCKET_NAME,
        secure=Config.MINIO_SECURE
    )
    return HybridImageProvider(minio)


@router.get("/projects")
def get_projects(service: ProjectService = Depends(get_project_service)):
    return service.get_projects()

@router.get("/projects/{project_id}/analytics")
def get_analytics(project_id: int, service: ProjectService = Depends(get_project_service)):
    return service.get_analytics(project_id)

@router.post("/projects")
def create_project(project: ProjectCreate, service: ProjectService = Depends(get_project_service)):
    return service.create_project(project.name, project.description, project.classes, project.commands)

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, service: ProjectService = Depends(get_project_service)):
    service.delete_project(project_id)
    return {"status": "success"}

@router.get("/projects/{project_id}/classes")
def get_classes(project_id: int, service: ProjectService = Depends(get_project_service)):
    return service.get_classes(project_id)

@router.post("/projects/{project_id}/classes")
def update_classes(project_id: int, classes: List[str], service: ProjectService = Depends(get_project_service)):
    service.update_classes(project_id, classes)
    return {"status": "success"}

@router.delete("/projects/{project_id}/classes/{class_index}")
def delete_class(project_id: int, class_index: int, service: ProjectService = Depends(get_project_service)):
    return service.delete_class(project_id, class_index)

@router.get("/projects/{project_id}/commands")
def get_commands(project_id: int, service: ProjectService = Depends(get_project_service)):
    return service.get_commands(project_id)

@router.post("/projects/{project_id}/commands")
def update_commands(project_id: int, commands: List[str], service: ProjectService = Depends(get_project_service)):
    service.update_commands(project_id, commands)
    return {"status": "success"}


@router.get("/stats")
def get_stats(project_id: Optional[int] = None, service: SampleService = Depends(get_sample_service)):
    return service.get_stats(project_id)

@router.get("/")
def list_labels(
    limit: int = 100, 
    offset: int = 0, 
    is_labeled: Optional[bool] = None, 
    split: Optional[str] = None, 
    project_id: Optional[int] = None, 
    class_id: Optional[int] = None, 
    command: Optional[int] = None, 
    service: SampleService = Depends(get_sample_service)
):
    return service.get_samples(limit, offset, is_labeled, split, project_id, class_id, command)


@router.get("/image/{filename}")
async def get_image(
    filename: str, 
    sample_repo: SampleRepository = Depends(get_sample_repo),
    storage: HybridImageProvider = Depends(get_storage_provider)
):
    sample_uri = None
    sample = sample_repo.get_sample(filename)
    if not sample:
        import re
        base_filename = re.sub(r'_dup\d+', '', filename)
        sample = sample_repo.get_sample(base_filename)
        
    if sample:
        sample_uri = sample.image_path

    result = storage.resolve_file_path(filename, sample_uri)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Image resource not found.")
        
    if isinstance(result, bytes):
        return StreamingResponse(io.BytesIO(result), media_type="image/jpeg")
    elif isinstance(result, Path):
        return FileResponse(result)


@router.get("/{filename}")
def get_label(filename: str, service: AnnotationService = Depends(get_annotation_service)):
    res = service.get_sample_detail(filename)
    if not res:
        raise HTTPException(status_code=404)
    return res

@router.post("/{filename}")
def save_label(filename: str, update: LabelUpdate, service: AnnotationService = Depends(get_annotation_service)):
    return service.update_label(filename, update)

@router.post("/batch/delete")
def delete_batch(payload: dict, service: SampleService = Depends(get_sample_service)):
    filenames = payload.get("filenames", [])
    return service.delete_batch(filenames)

@router.delete("/{filename}")
def delete_label(filename: str, service: SampleService = Depends(get_sample_service)):
    return service.delete_sample(filename)

@router.post("/{filename}/reset")
def reset_label(filename: str, service: AnnotationService = Depends(get_annotation_service)):
    return service.reset_label(filename)

@router.post("/{filename}/duplicate")
def duplicate_label(filename: str, new_filename: str, service: AnnotationService = Depends(get_annotation_service)):
    return service.duplicate_sample(filename, new_filename)
