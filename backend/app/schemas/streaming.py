"""Pydantic schemas for the streaming ingestion API."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StreamBatch(BaseModel):
    """A batch of records pushed to a stream."""

    stream_id: str = Field(..., min_length=1, max_length=128)
    records: List[Dict[str, Any]] = Field(..., min_length=1)


class StreamAck(BaseModel):
    """Acknowledgement returned after ingesting a batch."""

    stream_id: str
    accepted: int
    record_count: int
    records_per_second: float


class StreamSummary(BaseModel):
    stream_id: str
    record_count: int
    batch_count: int
    records_per_second: float
    started_at: float
    last_event_at: float
    averages: Dict[str, float] = {}
    minimums: Dict[str, float] = {}
    maximums: Dict[str, float] = {}
    null_counts: Dict[str, int] = {}


class StreamPersistRequest(BaseModel):
    """Flush buffered stream records into a persisted dataset."""

    stream_id: str
    dataset_name: Optional[str] = None
