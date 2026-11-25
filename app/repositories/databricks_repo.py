"""Fonte de dados oficial (ETAPA FUTURA): Databricks SQL Warehouse, catálogo `innopex`.

Este arquivo já existe para mostrar ONDE a integração vai entrar.
Quando a camada gold estiver pronta:
  1. `pip install databricks-sql-connector`
  2. No .env: DATA_MODE=databricks, DATABRICKS_HOST e DATABRICKS_WAREHOUSE_ID
  3. Implementar cada método abaixo devolvendo os MESMOS modelos de app/models.py

Nada nas telas, nas rotas ou nas regras precisa mudar.
"""

from __future__ import annotations

from typing import Optional

from app.config import Settings
from app.models import Config, Notification, Project, User
from app.repositories.base import Repository

_TODO = "Integração com o Databricks ainda não implementada. Use DATA_MODE=mock por enquanto."


class DatabricksRepository(Repository):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.catalog = settings.databricks_catalog

    def _connect(self):  # pragma: no cover - etapa futura
        # Exemplo de conexão (Databricks Apps injeta as credenciais do service principal):
        # from databricks import sql
        # from databricks.sdk.core import Config as DbConfig
        # cfg = DbConfig()
        # return sql.connect(server_hostname=cfg.host,
        #                    http_path=f"/sql/1.0/warehouses/{self.settings.databricks_warehouse_id}",
        #                    credentials_provider=lambda: cfg.authenticate)
        raise NotImplementedError(_TODO)

    def list_projects(self) -> list[Project]:
        # SELECT * FROM {catalog}.gold.projects WHERE region = 'GMSA' AND is_active
        raise NotImplementedError(_TODO)

    def get_project(self, project_id: str) -> Optional[Project]:
        raise NotImplementedError(_TODO)

    def save_project(self, project: Project) -> Project:
        # MERGE INTO {catalog}.gold.projects ... (+ insert em gold.project_history)
        # Escrever de volta no OpEx Global depende de autorização (decisão pendente).
        raise NotImplementedError(_TODO)

    def next_project_id(self, prefix: str) -> str:
        raise NotImplementedError(_TODO)

    def list_notifications(self) -> list[Notification]:
        raise NotImplementedError(_TODO)

    def add_notification(self, notification: Notification) -> Notification:
        raise NotImplementedError(_TODO)

    def save_notification(self, notification: Notification) -> Notification:
        raise NotImplementedError(_TODO)

    def get_config(self) -> Config:
        raise NotImplementedError(_TODO)

    def save_config(self, config: Config) -> Config:
        raise NotImplementedError(_TODO)

    def list_users(self) -> list[User]:
        raise NotImplementedError(_TODO)

    def find_user(self, email: str) -> Optional[User]:
        raise NotImplementedError(_TODO)

    def reset(self) -> None:
        raise NotImplementedError("Reset não é permitido na fonte oficial.")
