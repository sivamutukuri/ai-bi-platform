"""Analysis routes: run full analysis, NL query, executive summary."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Analysis, Dataset, User
from app.schemas.schemas import (
    ExecutiveSummaryResponse,
    NLQueryRequest,
    NLQueryResponse,
)
from app.services import data_service, llm_service, pipeline_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _load_owned_df(dataset_id: str, db: Session, user: User):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found.")
    try:
        df = data_service.load_dataframe(
            dataset.file_path, dataset.source_type.value
        )
    except data_service.DataLoadError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return dataset, df


@router.post("/{dataset_id}/run")
def run_analysis(
    dataset_id: str,
    target: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Run the full analysis pipeline and cache the result."""
    dataset, df = _load_owned_df(dataset_id, db, current_user)
    result = pipeline_service.analyse_dataframe(df, target)

    record = Analysis(kind="full", result_json=result, dataset_id=dataset.id)
    db.add(record)
    db.commit()
    return result


@router.post("/query", response_model=NLQueryResponse)
def natural_language_query(
    payload: NLQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NLQueryResponse:
    """Answer a natural-language question about a dataset."""
    _, df = _load_owned_df(payload.dataset_id, db, current_user)
    result = llm_service.answer_question(df, payload.question)
    return NLQueryResponse(**result)


@router.post("/{dataset_id}/summary", response_model=ExecutiveSummaryResponse)
def executive_summary(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutiveSummaryResponse:
    """Generate an executive summary for a dataset."""
    _, df = _load_owned_df(dataset_id, db, current_user)
    result = pipeline_service.analyse_dataframe(df)
    summary = result["executive_summary"]
    return ExecutiveSummaryResponse(**summary)
