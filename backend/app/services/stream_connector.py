"""Pluggable stream connector backends."""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StreamConnector(Protocol):
    """Interface every stream backend implements."""

    async def publish(self, topic: str, records: List[Dict[str, Any]]) -> None: ...

    async def consume(self, topic: str) -> AsyncIterator[Dict[str, Any]]: ...


class InMemoryConnector:
    """Zero-dependency default connector backed by asyncio queues."""

    def __init__(self) -> None:
        self._topics: Dict[str, asyncio.Queue] = {}

    def _queue(self, topic: str) -> asyncio.Queue:
        return self._topics.setdefault(topic, asyncio.Queue())

    async def publish(self, topic: str, records: List[Dict[str, Any]]) -> None:
        queue = self._queue(topic)
        for record in records:
            await queue.put(record)

    async def consume(self, topic: str) -> AsyncIterator[Dict[str, Any]]:
        queue = self._queue(topic)
        while True:
            record = await queue.get()
            yield record


class RedisConnector:
    """Redis Streams backend used when REDIS_URL is configured.

    Imported lazily so the dependency is optional.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self._redis: Optional[Any] = None

    async def _client(self):
        if self._redis is None:
            import redis.asyncio as redis  # type: ignore

            self._redis = redis.from_url(self.url, decode_responses=True)
        return self._redis

    async def publish(self, topic: str, records: List[Dict[str, Any]]) -> None:
        client = await self._client()
        for record in records:
            await client.xadd(topic, {"payload": json.dumps(record)})

    async def consume(self, topic: str) -> AsyncIterator[Dict[str, Any]]:
        client = await self._client()
        last_id = "$"
        while True:
            response = await client.xread({topic: last_id}, block=5000, count=100)
            for _stream, messages in response or []:
                for message_id, fields in messages:
                    last_id = message_id
                    yield json.loads(fields["payload"])


def build_connector() -> StreamConnector:
    """Factory that selects a backend based on settings."""
    url = getattr(settings, "REDIS_URL", None)
    if url:
        logger.info("using Redis stream connector")
        return RedisConnector(url)
    logger.info("using in-memory stream connector")
    return InMemoryConnector()


connector: StreamConnector = build_connector()
