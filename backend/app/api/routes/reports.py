"""Report routes: download analysis reports as PDF or Excel."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Dataset, User
from app.schemas.schemas import ReportRequest
from app.services import data_service, pipeline_service, report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
def generate_report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and stream a PDF or Excel report for a dataset."""
    dataset = db.get(Dataset, payload.dataset_id)
    if dataset is None or dataset.owner_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found.")

    try:
        df = data_service.load_dataframe(
            dataset.file_path, dataset.source_type.value
        )
    except data_service.DataLoadError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    result = pipeline_service.analyse_dataframe(df)
    title = payload.title or f"{dataset.name} - BI Report"
    summary = result["executive_summary"]["summary"]
    quality = result["quality"]
    insights = result["insights"]

    if payload.fmt == "pdf":
        content = report_service.build_pdf_report(title, summary, quality, insights)
        media_type = "application/pdf"
        filename = f"{dataset.name}_report.pdf"
    else:
        content = report_service.build_excel_report(
            title, summary, quality, insights, df
        )
        media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"{dataset.name}_report.xlsx"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
