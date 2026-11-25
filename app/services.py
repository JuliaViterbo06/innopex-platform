"""Casos de uso da plataforma: aplicam as regras e registram autor, histórico e notificações.

As rotas da API chamam estas funções. Elas só falam com o `Repository`,
então funcionam igual com os dados de exemplo ou com o Databricks.
"""

from __future__ import annotations

import datetime as dt
import uuid
from collections import defaultdict
from typing import Optional

from app.models import (
    Config, Deck, DeckIn, HistoryEntry, Meeting, MeetingNote, MeetingNoteIn, Notification,
    Project, ProjectIn, User,
)
from app.repositories.base import Repository
from app.rules import (
    PHASES, BusinessRuleError, NotFound, check_profit, check_single_master, first_free_tuesday,
    next_tuesdays, require,
)


# ---------------- utilidades ----------------
def _now() -> dt.datetime:
    return dt.datetime.now().replace(microsecond=0)


def _author(user: User) -> str:
    return f"{user.name} ({user.role})"


def _log(project: Project, user: User, text: str, touch: bool = True) -> None:
    """Toda mudança grava o autor. `touch` zera o contador de material parado."""
    project.history.insert(0, HistoryEntry(at=_now(), author=_author(user), text=text))
    if touch:
        project.last_update = dt.date.today()


def notify(repo: Repository, kind: str, title: str, text: str, project_id: Optional[str] = None) -> Notification:
    """Cria a notificação na central. O envio de e-mail entra aqui na etapa de integração."""
    n = Notification(id=f"N{uuid.uuid4().hex[:10]}", kind=kind, title=title, text=text,
                     created_at=_now(), project_id=project_id)
    return repo.add_notification(n)


def get_project_or_404(repo: Repository, project_id: str) -> Project:
    project = repo.get_project(project_id)
    if not project:
        raise NotFound(f"Projeto {project_id} não encontrado.")
    return project


def _fmt(day: dt.date) -> str:
    return day.strftime("%d/%m")


# ---------------- projetos ----------------
def create_project(repo: Repository, user: User, data: ProjectIn) -> Project:
    require(user, "edit")
    check_single_master(data.master)
    check_profit(data.phase, data.value_musd)
    prefix = "OP" if data.type == "Opex" else "GP"
    project = Project(id=repo.next_project_id(prefix), last_update=dt.date.today(), **data.model_dump())
    _log(project, user, f"Projeto criado na fase {data.phase}.")
    repo.save_project(project)
    notify(repo, "mail", f"Novo projeto cadastrado: {project.name}",
           f"Master {project.master} e líder {project.leader} notificados por e-mail", project.id)
    return project


def update_project(repo: Repository, user: User, project_id: str, data: ProjectIn) -> Project:
    require(user, "edit")
    project = get_project_or_404(repo, project_id)
    check_single_master(data.master)
    check_profit(data.phase, data.value_musd)
    changes = [k for k, v in data.model_dump().items() if getattr(project, k) != v]
    for k, v in data.model_dump().items():
        setattr(project, k, v)
    if changes:
        _log(project, user, "Campos alterados: " + ", ".join(changes) + ".")
        repo.save_project(project)
        notify(repo, "move", f"Projeto atualizado: {project.name}",
               f"Autor: {user.name} · {', '.join(changes)}", project.id)
    return project


def move_phase(repo: Repository, user: User, project_id: str, phase: str) -> Project:
    require(user, "move")
    project = get_project_or_404(repo, project_id)
    if project.phase == phase:
        return project
    check_profit(phase, project.value_musd)
    previous = project.phase
    project.phase = phase
    _log(project, user, f"Fase alterada de {previous} para {phase} (sincronização com a origem pendente de autorização).")
    repo.save_project(project)
    notify(repo, "move", f"{project.name} mudou de {previous} para {phase}",
           f"Autor: {user.name} · e-mail para {project.master} (Master) e {project.leader} (líder)", project.id)
    return project


# ---------------- decks ----------------
def upload_deck(repo: Repository, user: User, data: DeckIn) -> Project:
    require(user, "edit")
    project = get_project_or_404(repo, data.project_id)
    same = [d.version for d in project.decks if d.name == data.name]
    version = max(same) + 1 if same else 1
    project.decks.append(Deck(file_type=data.file_type, name=data.name, version=version,
                              author=user.name, updated_on=dt.date.today()))
    _log(project, user, f"Documento enviado: {data.file_type} · {data.name} v{version}.")
    repo.save_project(project)
    for n in repo.list_notifications():
        if n.project_id == project.id and n.kind == "alert" and "sem atualização" in n.title and not n.read:
            n.read = True
            repo.save_notification(n)
    return project


def featured_tuesday() -> dt.date:
    """A terça da semana atual de reunião: os decks desses projetos ficam em destaque."""
    return next_tuesdays(1)[0]


# ---------------- reuniões de terça ----------------
def register_notes(repo: Repository, user: User, project_id: str, data: MeetingNoteIn) -> Project:
    require(user, "decide")
    project = get_project_or_404(repo, project_id)
    cfg = repo.get_config()
    start = dt.date.today() + dt.timedelta(weeks=data.return_weeks)
    day = first_free_tuesday(start, repo.list_projects(), cfg.max_per_tuesday, except_id=project.id)
    project.notes.append(MeetingNote(day=dt.date.today(), text=data.text,
                                     return_weeks=data.return_weeks, author=user.name))
    project.missing_notes = False
    project.meeting = Meeting(day=day, state="aguardando")
    _log(project, user, f"Meeting Notes registradas; retorno em {data.return_weeks} semanas; proposta para {_fmt(day)}.")
    repo.save_project(project)
    for n in repo.list_notifications():
        if n.project_id == project.id and "Meeting Notes" in n.title and not n.read:
            n.read = True
            repo.save_notification(n)
    notify(repo, "mail", f"Proposta de data enviada: {project.name} em {_fmt(day)}",
           f"Aguardando aceite do líder {project.leader}", project.id)
    return project


def accept_meeting(repo: Repository, user: User, project_id: str) -> Project:
    require(user, "decide")
    project = get_project_or_404(repo, project_id)
    if not project.meeting:
        raise BusinessRuleError("Este projeto não tem data proposta.")
    project.meeting.state = "confirmado"
    project.meeting.note = None
    _log(project, user, f"Data de governança aceita: {_fmt(project.meeting.day)}.", touch=False)
    repo.save_project(project)
    notify(repo, "mail", f"Data confirmada: {project.name} em {_fmt(project.meeting.day)}",
           f"Aceite de {user.name} · convite enviado ao líder e ao Master", project.id)
    return project


def decline_meeting(repo: Repository, user: User, project_id: str) -> Project:
    require(user, "decide")
    project = get_project_or_404(repo, project_id)
    if not project.meeting:
        raise BusinessRuleError("Este projeto não tem data proposta.")
    old = project.meeting.day
    cfg = repo.get_config()
    new = first_free_tuesday(old + dt.timedelta(days=1), repo.list_projects(), cfg.max_per_tuesday, project.id)
    project.meeting = Meeting(day=new, state="aguardando",
                              note=f"Recusado para {_fmt(old)} · realocado automaticamente")
    _log(project, user, f"Data {_fmt(old)} recusada; nova proposta automática para {_fmt(new)}.", touch=False)
    repo.save_project(project)
    notify(repo, "mail", f"Proposta de data enviada: {project.name} em {_fmt(new)}",
           f"Aguardando aceite do líder {project.leader}", project.id)
    return project


def schedule(repo: Repository, weeks: int = 6) -> dict:
    cfg = repo.get_config()
    projects = repo.list_projects()
    slots = []
    for day in next_tuesdays(weeks):
        items = [p for p in projects if p.meeting and p.meeting.day == day]
        slots.append({"day": day, "capacity": cfg.max_per_tuesday, "free": cfg.max_per_tuesday - len(items),
                      "projects": [{"id": p.id, "name": p.name, "leader": p.leader, "master": p.master,
                                    "state": p.meeting.state, "note": p.meeting.note} for p in items]})
    blocked = [{"id": p.id, "name": p.name} for p in projects if p.missing_notes]
    return {"slots": slots, "blocked": blocked, "meeting_time": cfg.meeting_time}


def agenda(repo: Repository, day: dt.date) -> list[dict]:
    cfg = repo.get_config()
    hh, mm = (int(x) for x in cfg.meeting_time.split(":"))
    clock = dt.datetime.combine(day, dt.time(hh, mm))
    step = dt.timedelta(minutes=cfg.minutes_per_project)
    rows = [{"time": clock.strftime("%H:%M"), "project": "Abertura", "purpose": "Kick-off da reunião",
             "gv_musd": None, "presenter": "Time InnOpEx"}]
    for p in [p for p in repo.list_projects() if p.meeting and p.meeting.day == day]:
        clock += step
        rows.append({"time": clock.strftime("%H:%M"), "project": p.name,
                     "purpose": f"{p.phase} · {'update' if p.meeting.state == 'confirmado' else 'a confirmar'}",
                     "gv_musd": p.value_musd, "presenter": p.leader})
    clock += step
    rows.append({"time": clock.strftime("%H:%M"), "project": "Encerramento", "purpose": "Adjourn · próximos passos",
                 "gv_musd": None, "presenter": "Time InnOpEx"})
    return rows


# ---------------- automações ----------------
def run_stale_check(repo: Repository) -> int:
    """Alerta de material parado: cria 1 alerta por projeto acima do limite (sem duplicar)."""
    cfg = repo.get_config()
    open_alerts = {n.project_id for n in repo.list_notifications()
                   if n.kind == "alert" and "sem atualização" in n.title and not n.read}
    created = 0
    for p in repo.list_projects():
        if p.stale_days > cfg.stale_days and p.id not in open_alerts:
            notify(repo, "alert", f"{p.name} está há {p.stale_days} dias sem atualização",
                   f"Para: {p.master} (Master) e {p.leader} (líder) · regra: {cfg.stale_days} dias sem alteração · e-mail enviado",
                   p.id)
            created += 1
    return created


# ---------------- notificações ----------------
def mark_read(repo: Repository, notification_id: Optional[str] = None) -> None:
    for n in repo.list_notifications():
        if not n.read and (notification_id is None or n.id == notification_id):
            n.read = True
            repo.save_notification(n)


# ---------------- admin ----------------
def save_config(repo: Repository, user: User, cfg: Config) -> Config:
    require(user, "admin")
    repo.save_config(cfg)
    notify(repo, "move", "Parâmetros atualizados",
           f"Autor: {user.name} · alerta {cfg.stale_days} dias · {cfg.max_per_tuesday} projetos por terça")
    return cfg


# ---------------- dashboard ----------------
def dashboard(repo: Repository) -> dict:
    projects = repo.list_projects()
    cfg = repo.get_config()
    by_master: dict[str, float] = defaultdict(float)
    for p in projects:
        by_master[p.master] += p.value_musd
    types = ["Opex", "Inovação"]
    return {
        "kpis": {
            "active": len(projects),
            "opex": sum(p.type == "Opex" for p in projects),
            "innovation": sum(p.type == "Inovação" for p in projects),
            "blue_total": round(sum(p.value_musd for p in projects), 3),
            "green_total": round(sum(p.green_musd for p in projects), 3),
            "stale": sum(p.stale_days > cfg.stale_days for p in projects),
            "open_alerts": sum(n.kind == "alert" and not n.read for n in repo.list_notifications()),
        },
        "by_phase": {ph: sum(p.phase == ph for p in projects) for ph in PHASES},
        "by_master": dict(sorted(by_master.items(), key=lambda kv: kv[1])),
        "by_type": {t: {"count": sum(p.type == t for p in projects),
                        "value": round(sum(p.value_musd for p in projects if p.type == t), 3)} for t in types},
        "by_status": {s: sum(p.status == s for p in projects) for s in ("g", "y", "r")},
    }
