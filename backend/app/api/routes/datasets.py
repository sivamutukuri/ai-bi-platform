"""Dataset routes: upload files, connect SQL, list/get/delete."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.models.models import Dataset, DatasetStatus, SourceType, User
from app.schemas.schemas import DatasetOut, SQLConnectRequest
from app.services import data_service, profiling_service

router = APIRouter(prefix="/datasets", tags=["datasets"])

_EXT_TO_SOURCE = {
    "csv": SourceType.csv,
    "xlsx": SourceType.excel,
    "xls": SourceType.excel,
    "json": SourceType.json,
}


def _ensure_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    description: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dataset:
    """Upload a CSV, Excel, or JSON file and profile it."""
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing filename.")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported file type '.{ext}'. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.",
        )

    upload_dir = _ensure_upload_dir()
    stored_name = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / stored_name
    file_path.write_bytes(contents)

    source_type = _EXT_TO_SOURCE[ext]
    dataset = Dataset(
        name=name or file.filename,
        description=description,
        source_type=source_type,
        file_path=str(file_path),
        status=DatasetStatus.profiling,
        owner_id=current_user.id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    try:
        df = data_service.load_dataframe(str(file_path), source_type.value)
        cleaned, _ = data_service.clean_dataframe(df)
        dataset.row_count = int(len(cleaned))
        dataset.column_count = int(cleaned.shape[1])
        dataset.schema_json = profiling_service.build_schema(cleaned)
        dataset.status = DatasetStatus.ready
    except data_service.DataLoadError as exc:
        dataset.status = DatasetStatus.failed
        logger.error("Dataset load failed: %s" % exc)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.post("/connect-sql", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def connect_sql(
    payload: SQLConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dataset:
    """Run a read-only SQL query and persist the result as a dataset."""
    try:
        df = data_service.load_from_sql(payload.connection_uri, payload.query)
    except data_service.DataLoadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    upload_dir = _ensure_upload_dir()
    file_path = upload_dir / f"{uuid.uuid4()}.csv"
    df.to_csv(file_path, index=False)

    cleaned, _ = data_service.clean_dataframe(df)
    dataset = Dataset(
        name=payload.name,
        description=payload.description,
        source_type=SourceType.sql,
        file_path=str(file_path),
        status=DatasetStatus.ready,
        row_count=int(len(cleaned)),
        column_count=int(cleaned.shape[1]),
        schema_json=profiling_service.build_schema(cleaned),
        owner_id=current_user.id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Dataset]:
    """List datasets owned by the current user."""
    return (
        db.query(Dataset)
        .filter(Dataset.owner_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .all()
    )


def _get_owned_dataset(dataset_id: str, db: Session, user: User) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found.")
    return dataset


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dataset:
    """Retrieve a single dataset by id."""
    return _get_owned_dataset(dataset_id, db, current_user)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a dataset and its stored file."""
    dataset = _get_owned_dataset(dataset_id, db, current_user)
    if dataset.file_path:
        Path(dataset.file_path).unlink(missing_ok=True)
    db.delete(dataset)
    db.commit()
