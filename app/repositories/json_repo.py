"""Fonte de dados de desenvolvimento: lê data/seed.json e grava em data/state.json.

- seed.json  = dados de exemplo (versionado no Git, não muda sozinho)
- state.json = o que você alterou usando a plataforma (fica fora do Git)

As datas do seed são relativas ("há 41 dias", "terça 0 = próxima terça"),
então a demonstração sempre parece atual, em qualquer dia que você abrir.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
from pathlib import Path
from typing import Any, Optional

from app.models import Config, Notification, Project, User
from app.repositories.base import Repository
from app.rules import next_tuesdays


def _days_ago(n: int) -> str:
    return (dt.date.today() - dt.timedelta(days=int(n))).isoformat()


def build_state_from_seed(seed: dict[str, Any]) -> dict[str, Any]:
    """Converte as datas relativas do seed em datas reais."""
    tuesdays = next_tuesdays(8)
    now = dt.datetime.now().replace(microsecond=0)
    projects = []
    for raw in seed["projects"]:
        p = dict(raw)
        p["last_update"] = _days_ago(p.pop("last_update_days_ago", 0))
        meeting = p.pop("meeting", None)
        if meeting:
            note = meeting.get("note")
            if note:
                note = note.replace("{prev}", tuesdays[max(meeting["tuesday"] - 1, 0)].strftime("%d/%m"))
            p["meeting"] = {"day": tuesdays[meeting["tuesday"]].isoformat(), "state": meeting["state"], "note": note}
        p["decks"] = [
            {"file_type": d["file_type"], "name": d["name"], "version": d["version"],
             "author": d["author"], "updated_on": _days_ago(d["days_ago"])}
            for d in p.get("decks", [])
        ]
        p["notes"] = [
            {"day": _days_ago(n["days_ago"]), "text": n["text"], "return_weeks": n["return_weeks"], "author": n["author"]}
            for n in p.get("notes", [])
        ]
        origin = "OpEx Global · Projects" if p["type"] == "Opex" else "GMSA · Growth Project"
        p["history"] = [{"at": now.isoformat(), "author": "Carga inicial (dados de exemplo)",
                         "text": f"Projeto importado da lista {origin} na fase {p['phase']}."}]
        projects.append(p)

    notifications = []
    for i, n in enumerate(seed.get("notifications", []), start=1):
        created = now - dt.timedelta(hours=n.get("hours_ago", 0))
        title = n["title"].replace("{t1}", tuesdays[1].strftime("%d/%m"))
        notifications.append({"id": f"N{i:04d}", "kind": n["kind"], "title": title, "text": n["text"],
                              "created_at": created.isoformat(), "read": n.get("read", False),
                              "project_id": n.get("project_id")})
    return {"projects": projects, "notifications": notifications, "config": seed["config"],
            "users": seed["users"], "sequence": seed.get("sequence", 20000)}


class JsonRepository(Repository):
    def __init__(self, seed_file: Path, state_file: Path) -> None:
        self.seed_file = seed_file
        self.state_file = state_file
        self._lock = threading.RLock()
        self._state: dict[str, Any] = {}
        self._load()

    # ----- arquivo -----
    def _load(self) -> None:
        with self._lock:
            if self.state_file.exists():
                self._state = json.loads(self.state_file.read_text(encoding="utf-8"))
            else:
                self.reset()

    def _persist(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        tmp.replace(self.state_file)

    def reset(self) -> None:
        with self._lock:
            seed = json.loads(self.seed_file.read_text(encoding="utf-8"))
            self._state = build_state_from_seed(seed)
            self._persist()

    # ----- projetos -----
    def list_projects(self) -> list[Project]:
        with self._lock:
            return [Project.model_validate(p) for p in self._state["projects"]]

    def get_project(self, project_id: str) -> Optional[Project]:
        with self._lock:
            for p in self._state["projects"]:
                if p["id"] == project_id:
                    return Project.model_validate(p)
        return None

    def save_project(self, project: Project) -> Project:
        data = project.model_dump(mode="json", exclude={"stale_days"})
        for d in data.get("decks", []):
            d.pop("days_old", None)
        with self._lock:
            items = self._state["projects"]
            for i, p in enumerate(items):
                if p["id"] == project.id:
                    items[i] = data
                    break
            else:
                items.append(data)
            self._persist()
        return project

    def next_project_id(self, prefix: str) -> str:
        with self._lock:
            self._state["sequence"] += 1
            self._persist()
            return f"{prefix}-{self._state['sequence']}"

    # ----- notificações -----
    def list_notifications(self) -> list[Notification]:
        with self._lock:
            items = [Notification.model_validate(n) for n in self._state["notifications"]]
        return sorted(items, key=lambda n: n.created_at, reverse=True)

    def add_notification(self, notification: Notification) -> Notification:
        with self._lock:
            self._state["notifications"].append(notification.model_dump(mode="json"))
            self._persist()
        return notification

    def save_notification(self, notification: Notification) -> Notification:
        with self._lock:
            for i, n in enumerate(self._state["notifications"]):
                if n["id"] == notification.id:
                    self._state["notifications"][i] = notification.model_dump(mode="json")
            self._persist()
        return notification

    # ----- parâmetros e perfis -----
    def get_config(self) -> Config:
        with self._lock:
            return Config.model_validate(self._state["config"])

    def save_config(self, config: Config) -> Config:
        with self._lock:
            self._state["config"] = config.model_dump()
            self._persist()
        return config

    def list_users(self) -> list[User]:
        with self._lock:
            return [User.model_validate(u) for u in self._state["users"]]

    def find_user(self, email: str) -> Optional[User]:
        email = email.strip().lower()
        return next((u for u in self.list_users() if u.email.lower() == email), None)
