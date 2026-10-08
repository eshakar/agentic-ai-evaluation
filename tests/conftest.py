import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def isolated_results(tmp_path, monkeypatch):
    """Write run reports to a temp dir so tests never touch results/."""
    monkeypatch.setattr(get_settings(), "results_dir", tmp_path)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
