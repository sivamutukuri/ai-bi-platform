"""Tests for the real-time streaming ingestion service."""
import asyncio

import pytest

from app.services.streaming import StreamHub, StreamMetrics


def test_metrics_observe_tracks_numeric_aggregates():
    metrics = StreamMetrics(stream_id="s1")
    metrics.observe({"temp": 10, "label": "a"})
    metrics.observe({"temp": 20, "label": None})
    snap = metrics.snapshot()
    assert snap["record_count"] == 2
    assert snap["averages"]["temp"] == 15
    assert snap["minimums"]["temp"] == 10
    assert snap["maximums"]["temp"] == 20
    assert snap["null_counts"]["label"] == 1


def test_metrics_ignores_booleans_and_empty_strings():
    metrics = StreamMetrics(stream_id="s2")
    metrics.observe({"flag": True, "note": ""})
    snap = metrics.snapshot()
    assert "flag" not in snap["averages"]
    assert snap["null_counts"]["note"] == 1


@pytest.mark.asyncio
async def test_hub_ingest_and_snapshot():
    hub = StreamHub()
    snap = await hub.ingest("orders", [{"amount": 100}, {"amount": 300}])
    assert snap["record_count"] == 2
    assert snap["batch_count"] == 1
    assert snap["averages"]["amount"] == 200
    assert hub.metrics("orders") is not None
    assert len(hub.list_streams()) == 1


@pytest.mark.asyncio
async def test_hub_buffer_drain():
    hub = StreamHub()
    await hub.ingest("buf", [{"x": 1}, {"x": 2}])
    drained = hub.drain_buffer("buf")
    assert len(drained) == 2
    assert hub.drain_buffer("buf") == []


@pytest.mark.asyncio
async def test_hub_subscriber_receives_events():
    hub = StreamHub()
    queue = await hub.subscribe("live")
    await hub.ingest("live", [{"v": 1}])
    payload = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert payload["type"] == "metrics"
    assert payload["data"]["record_count"] >= 1
    await hub.unsubscribe("live", queue)
