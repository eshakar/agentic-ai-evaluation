"""Where run reports and saved questions are kept: MongoDB (when MONGODB_URI is set) or files.

Both stores have the same async interface, so the rest of the app never needs to know which
one is active. Built-in datasets (datasets/*.jsonl in the repo) are always read from files;
the store only holds questions saved from the Ask page.
"""

import json
import logging
from typing import Protocol

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.db.models import CaseDocument, RunDocument
from app.schemas.evaluation import EvalCase, RunListItem, RunSummary

logger = logging.getLogger(__name__)


class Store(Protocol):
    name: str

    async def save_run(self, summary: RunSummary) -> None: ...
    async def load_run(self, run_id: str) -> RunSummary | None: ...
    async def delete_run(self, run_id: str) -> bool: ...
    async def list_runs(self, limit: int) -> list[RunListItem]: ...
    async def saved_cases(self, dataset: str) -> list[EvalCase]: ...
    async def add_case(self, dataset: str, case: EvalCase) -> None: ...
    async def saved_dataset_names(self) -> list[str]: ...


class FileStore:
    """Run reports as results/<run_id>.json; saved questions appended to datasets/<name>.jsonl."""

    name = "files"

    async def save_run(self, summary: RunSummary) -> None:
        results_dir = get_settings().results_dir
        results_dir.mkdir(parents=True, exist_ok=True)
        path = results_dir / f"{summary.run_id}.json"
        path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")

    async def load_run(self, run_id: str) -> RunSummary | None:
        if not run_id.isalnum():
            return None
        path = get_settings().results_dir / f"{run_id}.json"
        if not path.is_file():
            return None
        return RunSummary.model_validate(json.loads(path.read_text(encoding="utf-8")))

    async def delete_run(self, run_id: str) -> bool:
        if not run_id.isalnum():
            return False
        path = get_settings().results_dir / f"{run_id}.json"
        if not path.is_file():
            return False
        path.unlink()
        return True

    async def list_runs(self, limit: int) -> list[RunListItem]:
        items: list[RunListItem] = []
        for path in get_settings().results_dir.glob("*.json"):
            try:
                items.append(RunListItem.model_validate_json(path.read_text(encoding="utf-8")))
            except ValueError:
                logger.warning("Skipping unreadable run file %s", path.name)
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items[:limit]

    async def saved_cases(self, dataset: str) -> list[EvalCase]:
        return []  # saved questions live inside the dataset file itself

    async def add_case(self, dataset: str, case: EvalCase) -> None:
        path = get_settings().datasets_dir / dataset
        path.parent.mkdir(parents=True, exist_ok=True)
        needs_newline = (
            path.is_file() and path.stat().st_size > 0 and not path.read_bytes().endswith(b"\n")
        )
        with path.open("a", encoding="utf-8", newline="\n") as f:
            if needs_newline:
                f.write("\n")
            f.write(case.model_dump_json(exclude_defaults=True) + "\n")

    async def saved_dataset_names(self) -> list[str]:
        return []


class MongoStore:
    """Run reports in the `runs` collection; saved questions in the `cases` collection."""

    name = "mongodb"

    async def save_run(self, summary: RunSummary) -> None:
        await RunDocument.from_summary(summary).insert()

    async def load_run(self, run_id: str) -> RunSummary | None:
        doc = await RunDocument.find_one(RunDocument.run_id == run_id)
        return doc.to_summary() if doc else None

    async def delete_run(self, run_id: str) -> bool:
        result = await RunDocument.find(RunDocument.run_id == run_id).delete()
        return bool(result and result.deleted_count)

    async def list_runs(self, limit: int) -> list[RunListItem]:
        return (
            await RunDocument.find_all()
            .sort(-RunDocument.created_at)
            .limit(limit)
            .project(RunListItem)  # fetch only the list fields, not every answer
            .to_list()
        )

    async def saved_cases(self, dataset: str) -> list[EvalCase]:
        docs = (
            await CaseDocument.find(CaseDocument.dataset == dataset)
            .sort(+CaseDocument.created_at)
            .to_list()
        )
        return [d.case for d in docs]

    async def add_case(self, dataset: str, case: EvalCase) -> None:
        await CaseDocument(dataset=dataset, case=case).insert()

    async def saved_dataset_names(self) -> list[str]:
        return sorted(await CaseDocument.distinct("dataset"))


_store: Store = FileStore()
_client: AsyncMongoClient | None = None
_status = "files"


def get_store() -> Store:
    return _store


def storage_status() -> str:
    """Human-readable: which store is active (shown by /health)."""
    return _status


async def init_storage() -> None:
    """Connect to MongoDB if configured; otherwise (or if it is unreachable) use files."""
    global _store, _client, _status
    settings = get_settings()
    if not settings.mongodb_uri:
        _store, _status = FileStore(), "files"
        return
    client: AsyncMongoClient = AsyncMongoClient(
        settings.mongodb_uri, serverSelectionTimeoutMS=8000, appname="agentic-ai-evaluation"
    )
    try:
        await client.admin.command("ping")
        await init_beanie(
            database=client[settings.mongodb_db], document_models=[RunDocument, CaseDocument]
        )
    except Exception as exc:
        await client.close()
        _store = FileStore()
        _status = f"files (MongoDB unreachable: {type(exc).__name__})"
        logger.error(
            "Could not connect to MongoDB, falling back to file storage. "
            "Check MONGODB_URI and Atlas Network Access. Error: %s",
            exc,
        )
        return
    _client, _store, _status = client, MongoStore(), f"mongodb ({settings.mongodb_db})"
    logger.info("Using MongoDB database %r for runs and saved questions", settings.mongodb_db)


async def close_storage() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
