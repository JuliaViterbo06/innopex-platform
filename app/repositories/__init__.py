"""Escolhe a fonte de dados conforme DATA_MODE (mock ou databricks)."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.repositories.base import Repository


@lru_cache
def get_repository() -> Repository:
    settings = get_settings()
    if settings.data_mode == "databricks":
        from app.repositories.databricks_repo import DatabricksRepository

        return DatabricksRepository(settings)
    from app.repositories.json_repo import JsonRepository

    return JsonRepository(settings.seed_file, settings.state_file)
