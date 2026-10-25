"""MongoDB document models (Beanie: Mongoose-style models on top of the async PyMongo driver)."""

from datetime import UTC, datetime

import pymongo
from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from app.schemas.evaluation import EvalCase, RunSummary


class RunDocument(Document, RunSummary):
    """One evaluation run report: the same fields as RunSummary, stored in the `runs` collection."""

    class Settings:
        name = "runs"
        indexes = [
            IndexModel([("run_id", pymongo.ASCENDING)], unique=True),
            IndexModel([("created_at", pymongo.DESCENDING)]),
        ]

    @classmethod
    def from_summary(cls, summary: RunSummary) -> "RunDocument":
        return cls(**summary.model_dump())

    def to_summary(self) -> RunSummary:
        return RunSummary.model_validate(self.model_dump(exclude={"id", "revision_id"}))


class CaseDocument(Document):
    """A question saved from the Ask page, belonging to a named dataset (`cases` collection)."""

    dataset: str
    case: EvalCase
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "cases"
        indexes = [
            # A question id is unique within its dataset.
            IndexModel(
                [("dataset", pymongo.ASCENDING), ("case.id", pymongo.ASCENDING)], unique=True
            ),
            IndexModel([("dataset", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)]),
        ]
