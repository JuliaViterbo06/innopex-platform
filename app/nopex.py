"""Nopex, o assistente da plataforma (versão por regras).

Hoje responde com base nos dados da própria plataforma. Na etapa futura,
esta função pode chamar um modelo de IA aprovado pela GM sem mudar o front.
"""

from __future__ import annotations

import html

from app.models import User
from app.repositories.base import Repository
from app.rules import can
from app.services import featured_tuesday


def _link(project_id: str, name: str) -> str:
    return f'<a href="#/projeto/{html.escape(project_id)}">{html.escape(name)}</a>'


def _musd(v: float) -> str:
    if v >= 1:
        return f"US$ {v:.1f}M".replace(".", ",")
    return "US$ 0" if v == 0 else f"US$ {v * 1000:.0f}k"


def answer(repo: Repository, user: User, question: str) -> str:
    q = question.lower()
    projects = repo.list_projects()
    cfg = repo.get_config()

    if any(w in q for w in ("atras", "atualiz", "parado")):
        stale = [p for p in projects if p.stale_days > cfg.stale_days]
        if not stale:
            return "Nenhum projeto parado. 🎉"
        items = " e ".join(f"{_link(p.id, p.name)} ({p.stale_days} dias)" for p in stale)
        return (f"Há {len(stale)} projeto(s) sem atualização há mais de {cfg.stale_days} dias: {items}. "
                "Já notifiquei líder e Master pela central de notificações.")

    if any(w in q for w in ("pauta", "terça", "terca", "reuni")):
        day = featured_tuesday()
        items = [p for p in projects if p.meeting and p.meeting.day == day]
        names = ", ".join(html.escape(p.name) for p in items) or "nenhum projeto"
        return (f"A pauta de terça {day:%d/%m} tem {len(items)} projeto(s): {names}. "
                f'<a href="#" data-agenda="{day.isoformat()}">Abrir pauta</a>.')

    if "blue" in q or "valor" in q:
        totals: dict[str, float] = {}
        for p in projects:
            totals[p.master] = totals.get(p.master, 0) + p.value_musd
        return "Blue Value por Master: " + " · ".join(
            f"{html.escape(m)} {_musd(v)}" for m, v in sorted(totals.items(), key=lambda kv: -kv[1])) + "."

    for p in projects:
        words = [w for w in p.name.lower().split() if len(w) > 4 and w != "gmsa"]
        if p.id.lower() in q or p.name.lower() in q or any(w in q for w in words):
            nxt = f", próxima reunião {p.meeting.day:%d/%m}" if p.meeting else ""
            status = {"g": "no prazo", "y": "em atenção", "r": "crítico"}[p.status]
            return (f"{_link(p.id, p.name)} está em <b>{p.phase}</b>, Master {html.escape(p.master)}, "
                    f"{status}, valor {_musd(p.value_musd)}{nxt}.")

    if any(w in q for w in ("novo", "cadast", "criar")):
        if can(user, "edit"):
            return 'Claro! <a href="#" data-action="new-project">Abrir cadastro de projeto</a>.'
        return "Seu perfil (Viewer) não pode cadastrar projetos."

    if any(w in q for w in ("fase", "mover", "dmaic")):
        return ("Arraste o card no Kanban para a nova coluna. A partir do Measure o lucro estimado é obrigatório, "
                "e toda mudança grava autor e data no histórico.")

    return ("Posso buscar projetos por nome, mostrar quem está atrasado, montar a pauta da terça "
            "ou abrir o cadastro de um novo projeto. É só pedir.")
