"""One-time copy of local run reports and saved questions into MongoDB.

    python -m scripts.migrate_to_mongo            # copy
    python -m scripts.migrate_to_mongo --dry-run  # just show what would be copied

Safe to run more than once: anything already in MongoDB is skipped. Nothing is deleted.
Run reports stay in results/ (git-ignored). A dataset file made up only of questions saved
from the Ask page is renamed to <name>.jsonl.migrated so its questions aren't listed twice;
built-in datasets are never changed.
"""

import argparse
import asyncio
import json

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db import store
from app.db.models import CaseDocument, RunDocument
from app.schemas.evaluation import EvalCase, RunSummary


async def migrate(dry_run: bool) -> None:
    await store.init_storage()
    if not isinstance(store.get_store(), store.MongoStore):
        raise SystemExit(f"MongoDB is not connected ({store.storage_status()}). Check MONGODB_URI.")
    settings = get_settings()
    mongo = store.get_store()
    try:
        # Run reports
        added = skipped = 0
        for path in sorted(settings.results_dir.glob("*.json")):
            summary = RunSummary.model_validate(json.loads(path.read_text(encoding="utf-8")))
            if await RunDocument.find_one(RunDocument.run_id == summary.run_id):
                skipped += 1
                continue
            if not dry_run:
                await mongo.save_run(summary)
            added += 1
        print(f"Runs: {added} copied, {skipped} already in MongoDB")

        # Questions saved from the Ask page
        for path in sorted(settings.datasets_dir.glob("*.jsonl")):
            lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            cases = [EvalCase.model_validate_json(ln) for ln in lines]
            saved = [c for c in cases if c.metadata.get("source") == "ask-page"]
            if not saved:
                continue
            copied = 0
            for case in saved:
                exists = await CaseDocument.find_one(
                    CaseDocument.dataset == path.name, {"case.id": case.id}
                )
                if not exists:
                    if not dry_run:
                        await mongo.add_case(path.name, case)
                    copied += 1
            note = ""
            if len(saved) == len(cases) and not dry_run:
                path.rename(path.with_name(path.name + ".migrated"))
                note = f" (file renamed to {path.name}.migrated)"
            print(f"{path.name}: {copied} saved question(s) copied{note}")
        if dry_run:
            print("Dry run: nothing was written.")
    finally:
        await store.close_storage()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    setup_logging("WARNING")
    asyncio.run(migrate(args.dry_run))


if __name__ == "__main__":
    main()
