"""Regras de negócio aprovadas da InnOpEx — funções puras, fáceis de testar."""

from __future__ import annotations

import datetime as dt
import re
from typing import Iterable, Optional

from app.models import Project, User

PHASES: tuple[str, ...] = ("Define", "Measure", "Analyze", "Improve", "Control")

PERMISSIONS: dict[str, set[str]] = {
    "Admin": {"view", "edit", "move", "decide", "admin"},
    "Master": {"view", "edit", "move", "decide"},
    "Leader": {"view", "edit", "move", "decide"},
    "Viewer": {"view"},
}


class BusinessRuleError(Exception):
    """Uma regra de governança foi violada (vira HTTP 422)."""


class PermissionDenied(Exception):
    """O perfil do usuário não permite a ação (vira HTTP 403)."""


class NotFound(Exception):
    """Registro não encontrado (vira HTTP 404)."""


def can(user: User, action: str) -> bool:
    return action in PERMISSIONS.get(user.role, set())


def require(user: User, action: str) -> None:
    if not can(user, action):
        raise PermissionDenied(f"O perfil {user.role} não pode realizar esta ação.")


def is_email_allowed(email: str, domain: str) -> bool:
    return bool(re.fullmatch(rf"[^@\s]+@{re.escape(domain)}", email.strip().lower()))


def requires_profit(phase: str) -> bool:
    """Lucro estimado é obrigatório a partir do Measure."""
    return PHASES.index(phase) >= PHASES.index("Measure")


def check_profit(phase: str, value_musd: float) -> None:
    if requires_profit(phase) and not value_musd > 0:
        raise BusinessRuleError(
            "A partir do Measure o lucro estimado é obrigatório. Preencha o valor no cadastro do projeto."
        )


def check_single_master(master: str) -> None:
    if re.search(r"[,;/&+]|\s+e\s+", master.strip()):
        raise BusinessRuleError("Informe apenas um Master: a regra é um único responsável por projeto.")


def next_tuesdays(n: int, start: Optional[dt.date] = None) -> list[dt.date]:
    """As próximas `n` terças-feiras a partir de `start` (inclusive)."""
    day = start or dt.date.today()
    day += dt.timedelta(days=(1 - day.weekday()) % 7)  # weekday(): segunda=0, terça=1
    return [day + dt.timedelta(weeks=i) for i in range(n)]


def used_slots(day: dt.date, projects: Iterable[Project], except_id: Optional[str] = None) -> int:
    return sum(1 for p in projects if p.meeting and p.meeting.day == day and p.id != except_id)


def first_free_tuesday(
    start: dt.date, projects: list[Project], capacity: int, except_id: Optional[str] = None
) -> dt.date:
    """Primeira terça a partir de `start` com vaga, respeitando a capacidade por reunião."""
    candidates = next_tuesdays(52, start)
    for day in candidates:
        if used_slots(day, projects, except_id) < capacity:
            return day
    return candidates[-1]
