"""Contrato da camada de dados.

Qualquer fonte de dados (JSON de exemplo, Databricks, SharePoint) precisa
implementar estes métodos. As regras e as telas só conversam com este
contrato — por isso trocar a fonte não quebra o resto da plataforma.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.models import Config, Notification, Project, User


class Repository(ABC):
    # ----- projetos -----
    @abstractmethod
    def list_projects(self) -> list[Project]: ...

    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Project]: ...

    @abstractmethod
    def save_project(self, project: Project) -> Project:
        """Cria ou atualiza (upsert) um projeto."""

    @abstractmethod
    def next_project_id(self, prefix: str) -> str: ...

    # ----- notificações -----
    @abstractmethod
    def list_notifications(self) -> list[Notification]: ...

    @abstractmethod
    def add_notification(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def save_notification(self, notification: Notification) -> Notification: ...

    # ----- parâmetros e perfis -----
    @abstractmethod
    def get_config(self) -> Config: ...

    @abstractmethod
    def save_config(self, config: Config) -> Config: ...

    @abstractmethod
    def list_users(self) -> list[User]: ...

    @abstractmethod
    def find_user(self, email: str) -> Optional[User]: ...

    # ----- utilidades -----
    @abstractmethod
    def reset(self) -> None:
        """Volta aos dados iniciais (usado na demonstração)."""
