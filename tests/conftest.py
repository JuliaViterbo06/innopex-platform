"""Prepara um ambiente de teste isolado (não mexe no seu data/state.json)."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="innopex-test-"))
os.environ["DATA_MODE"] = "mock"
os.environ["AUTH_MODE"] = "dev"
os.environ["STATE_FILE"] = str(_TMP / "state.json")


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import app
    from app.repositories import get_repository

    get_settings.cache_clear()
    get_repository.cache_clear()
    get_repository().reset()
    with TestClient(app) as c:
        yield c
    get_repository.cache_clear()


def login(client, role: str = "Admin", email: str = "julia.viterbomoreira@gm.com"):
    r = client.post("/api/auth/dev-login", json={"name": "Julia Viterbo", "email": email, "role": role})
    return r


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP, ignore_errors=True)
