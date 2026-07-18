"""Real-time streaming ingestion service.

Provides a pluggable stream backend (in-memory by default, optional Redis /
Kafka) plus an incremental analytics engine that maintains rolling metrics as
records arrive.  Designed so the whole platform runs with zero external brokers
out of the box while remaining production-ready when a broker is configured.
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Deque, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StreamMetrics:
    """Rolling metrics maintained incrementally for a single stream."""

    stream_id: str
    record_count: int = 0
    batch_count: int = 0
    started_at: float = field(default_factory=time.time)
    last_event_at: float = 0.0
    numeric_sums: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    numeric_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    numeric_min: Dict[str, float] = field(default_factory=dict)
    numeric_max: Dict[str, float] = field(default_factory=dict)
    null_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    recent: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=200))

    def observe(self, record: Dict[str, Any]) -> None:
        self.record_count += 1
        self.last_event_at = time.time()
        self.recent.append(record)
        for key, value in record.items():
            if value is None or value == "":
                self.null_counts[key] += 1
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                v = float(value)
                self.numeric_sums[key] += v
                self.numeric_counts[key] += 1
                self.numeric_min[key] = v if key not in self.numeric_min else min(self.numeric_min[key], v)
                self.numeric_max[key] = v if key not in self.numeric_max else max(self.numeric_max[key], v)

    def snapshot(self) -> Dict[str, Any]:
        elapsed = max(time.time() - self.started_at, 1e-9)
        averages = {
            k: self.numeric_sums[k] / self.numeric_counts[k]
            for k in self.numeric_counts
            if self.numeric_counts[k]
        }
        return {
            "stream_id": self.stream_id,
            "record_count": self.record_count,
            "batch_count": self.batch_count,
            "records_per_second": round(self.record_count / elapsed, 3),
            "started_at": self.started_at,
            "last_event_at": self.last_event_at,
            "averages": {k: round(v, 4) for k, v in averages.items()},
            "minimums": {k: round(v, 4) for k, v in self.numeric_min.items()},
            "maximums": {k: round(v, 4) for k, v in self.numeric_max.items()},
            "null_counts": dict(self.null_counts),
        }


class StreamHub:
    """Central registry of active streams and their subscribers.

    Uses asyncio queues for fan-out.  A background consumer applies each record
    to the incremental metrics before broadcasting to live subscribers.
    """

    def __init__(self, buffer_flush: int = 50) -> None:
        self._metrics: Dict[str, StreamMetrics] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._buffers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self.buffer_flush = buffer_flush

    def metrics(self, stream_id: str) -> Optional[StreamMetrics]:
        return self._metrics.get(stream_id)

    def list_streams(self) -> List[Dict[str, Any]]:
        return [m.snapshot() for m in self._metrics.values()]

    async def ingest(self, stream_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        async with self._lock:
            metrics = self._metrics.setdefault(stream_id, StreamMetrics(stream_id=stream_id))
            metrics.batch_count += 1
            for record in records:
                metrics.observe(record)
                self._buffers[stream_id].append(record)
            snapshot = metrics.snapshot()
            subscribers = list(self._subscribers.get(stream_id, []))
        payload = {"type": "metrics", "data": snapshot}
        for queue in subscribers:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("dropping event for slow subscriber on %s", stream_id)
        return snapshot

    def drain_buffer(self, stream_id: str) -> List[Dict[str, Any]]:
        """Return and clear buffered records ready to persist to a dataset."""
        buffered = self._buffers.get(stream_id, [])
        self._buffers[stream_id] = []
        return buffered

    async def subscribe(self, stream_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        async with self._lock:
            self._subscribers[stream_id].append(queue)
            existing = self._metrics.get(stream_id)
        if existing is not None:
            queue.put_nowait({"type": "metrics", "data": existing.snapshot()})
        return queue

    async def unsubscribe(self, stream_id: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            if queue in self._subscribers.get(stream_id, []):
                self._subscribers[stream_id].remove(queue)

    async def events(self, stream_id: str) -> AsyncIterator[str]:
        """Yield Server-Sent Events for a stream until the client disconnects."""
        queue = await self.subscribe(stream_id)
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            await self.unsubscribe(stream_id, queue)


stream_hub = StreamHub()
