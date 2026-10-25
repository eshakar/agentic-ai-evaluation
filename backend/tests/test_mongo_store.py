"""Integration test for the MongoDB store, against a real MongoDB.

Skipped unless MONGODB_TEST_URI is set. It uses a throwaway database (dropped at the end),
so it never touches your real data:

    MONGODB_TEST_URI="mongodb+srv://..." pytest tests/test_mongo_store.py
"""

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pymongo.errors import DuplicateKeyError

from app.core.config import get_settings
from app.db import store
from app.db.models import CaseDocument
from app.schemas.evaluation import AgentTrace, CaseResult, EvalCase, MetricResult, RunSummary

URI = os.environ.get("MONGODB_TEST_URI")
pytestmark = pytest.mark.skipif(not URI, reason="set MONGODB_TEST_URI to run MongoDB tests")


def _summary(run_id: str, minutes_ago: int) -> RunSummary:
    trace = AgentTrace(output="4", latency_ms=12.5)
    metric = MetricResult(name="contains", score=1.0, passed=True)
    return RunSummary(
        run_id=run_id,
        created_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
        agent="echo",
        evaluators=["contains"],
        num_cases=1,
        num_scored=1,
        pass_rate=1.0,
        mean_scores={"contains": 1.0},
        mean_latency_ms=12.5,
        results=[CaseResult(case_id="q1", trace=trace, metrics=[metric])],
    )


@pytest.fixture
async def mongo(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "mongodb_uri", URI)
    monkeypatch.setattr(settings, "mongodb_db", f"agentic_eval_test_{uuid.uuid4().hex[:8]}")
    await store.init_storage()
    assert isinstance(store.get_store(), store.MongoStore), store.storage_status()
    yield store.get_store()
    await store._client.drop_database(settings.mongodb_db)
    await store.close_storage()


async def test_runs_round_trip(mongo):
    await mongo.save_run(_summary("aaa111", minutes_ago=5))
    await mongo.save_run(_summary("bbb222", minutes_ago=1))

    loaded = await mongo.load_run("aaa111")
    assert loaded is not None and loaded.results[0].trace.output == "4"
    assert [r.run_id for r in await mongo.list_runs(10)] == ["bbb222", "aaa111"]  # newest first
    assert len(await mongo.list_runs(1)) == 1

    assert await mongo.delete_run("aaa111") is True
    assert await mongo.load_run("aaa111") is None
    assert await mongo.delete_run("aaa111") is False


async def test_saved_cases(mongo):
    await mongo.add_case("mine.jsonl", EvalCase(id="q1", input="2+2?", expected_output="4"))
    await mongo.add_case("mine.jsonl", EvalCase(id="q2", input="3+3?", expected_output="6"))
    await mongo.add_case("other.jsonl", EvalCase(id="q1", input="hi", rubric="greets"))

    assert [c.id for c in await mongo.saved_cases("mine.jsonl")] == ["q1", "q2"]
    assert await mongo.saved_dataset_names() == ["mine.jsonl", "other.jsonl"]
    # The unique index stops the same id twice in one dataset.
    with pytest.raises(DuplicateKeyError):
        await CaseDocument(dataset="mine.jsonl", case=EvalCase(id="q1", input="dup")).insert()
