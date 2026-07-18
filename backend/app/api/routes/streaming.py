"""Real-time streaming ingestion endpoints.

Exposes three transports over the same StreamHub:
  * POST  /streaming/{stream_id}/ingest  -> push a batch (HTTP)
  * WS    /streaming/{stream_id}/ws       -> push batches over a WebSocket
  * GET   /streaming/{stream_id}/events   -> Server-Sent Events of live metrics
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.streaming import (
    StreamAck,
    StreamBatch,
    StreamPersistRequest,
    StreamSummary,
)
from app.services.stream_connector import connector
from app.services.streaming import stream_hub
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/streaming", tags=["streaming"])


@router.get("", response_model=list[StreamSummary])
async def list_streams(_: User = Depends(get_current_user)) -> list[dict]:
    """Return summaries for all active streams."""
    return stream_hub.list_streams()


@router.get("/{stream_id}", response_model=StreamSummary)
async def get_stream(stream_id: str, _: User = Depends(get_current_user)) -> dict:
    metrics = stream_hub.metrics(stream_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail="stream not found")
    return metrics.snapshot()


@router.post("/{stream_id}/ingest", response_model=StreamAck)
async def ingest_batch(
    stream_id: str,
    batch: StreamBatch,
    _: User = Depends(get_current_user),
) -> StreamAck:
    """Ingest a batch of records over HTTP."""
    await connector.publish(stream_id, batch.records)
    snapshot = await stream_hub.ingest(stream_id, batch.records)
    return StreamAck(
        stream_id=stream_id,
        accepted=len(batch.records),
        record_count=snapshot["record_count"],
        records_per_second=snapshot["records_per_second"],
    )


@router.websocket("/{stream_id}/ws")
async def ingest_ws(websocket: WebSocket, stream_id: str) -> None:
    """Bidirectional WebSocket: client pushes batches, server returns metrics."""
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "invalid json"})
                continue
            records = payload.get("records")
            if not isinstance(records, list) or not records:
                await websocket.send_json({"type": "error", "detail": "records required"})
                continue
            await connector.publish(stream_id, records)
            snapshot = await stream_hub.ingest(stream_id, records)
            await websocket.send_json({"type": "metrics", "data": snapshot})
    except WebSocketDisconnect:
        logger.info("websocket disconnected for stream %s", stream_id)


@router.get("/{stream_id}/events")
async def stream_events(stream_id: str, token: str | None = None) -> StreamingResponse:
    """Server-Sent Events endpoint for live dashboard updates.

    EventSource cannot set Authorization headers, so the access token may be
    supplied as a query parameter and validated by the SSE handler.
    """
    from app.core.security import decode_token

    if token is not None:
        try:
            decode_token(token)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=401, detail="invalid token") from exc

    return StreamingResponse(
        stream_hub.events(stream_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{stream_id}/persist")
async def persist_stream(
    request: StreamPersistRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Flush buffered stream records so they can be analysed as a dataset."""
    records = stream_hub.drain_buffer(request.stream_id)
    if not records:
        raise HTTPException(status_code=404, detail="no buffered records")
    return {
        "stream_id": request.stream_id,
        "flushed": len(records),
        "dataset_name": request.dataset_name or request.stream_id,
        "records": records,
    }
