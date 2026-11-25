"""Configurações da aplicação, lidas de variáveis de ambiente.

Para trocar o comportamento sem mexer no código, altere o arquivo `.env`
(copiado de `.env.example`). O VS Code carrega esse arquivo ao apertar F5.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"


@dataclass(frozen=True)
class Settings:
    # mock = dados de exemplo em data/seed.json | databricks = SQL Warehouse (etapa futura)
    data_mode: str
    # dev = tela de login de desenvolvimento | databricks = SSO Entra ID via Databricks Apps
    auth_mode: str
    allowed_domain: str
    secret_key: str
    seed_file: Path
    state_file: Path
    port: int
    databricks_host: str
    databricks_warehouse_id: str
    databricks_catalog: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        data_mode=os.getenv("DATA_MODE", "mock").lower(),
        auth_mode=os.getenv("AUTH_MODE", "dev").lower(),
        allowed_domain=os.getenv("ALLOWED_DOMAIN", "gm.com").lower(),
        secret_key=os.getenv("SECRET_KEY", "troque-esta-chave-em-producao"),
        seed_file=Path(os.getenv("SEED_FILE", str(DATA_DIR / "seed.json"))),
        state_file=Path(os.getenv("STATE_FILE", str(DATA_DIR / "state.json"))),
        port=int(os.getenv("DATABRICKS_APP_PORT", os.getenv("PORT", "8000"))),
        databricks_host=os.getenv("DATABRICKS_HOST", ""),
        databricks_warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID", ""),
        databricks_catalog=os.getenv("DATABRICKS_CATALOG", "innopex"),
    )
