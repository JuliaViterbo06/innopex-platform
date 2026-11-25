"""Reuniões de terça, Meeting Notes e decks."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import DeckIn, MeetingNoteIn, Project, User
from app.repositories import get_repository
from app.repositories.base import Repository
from app import services

router = APIRouter(prefix="/api", tags=["governança"])


@router.get("/schedule")
def schedule(weeks: int = 6, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.schedule(repo, weeks)


@router.get("/schedule/{day}/agenda")
def agenda(day: dt.date, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.agenda(repo, day)


@router.post("/projects/{project_id}/notes", response_model=Project)
def register_notes(project_id: str, data: MeetingNoteIn, user: User = Depends(get_current_user),
                   repo: Repository = Depends(get_repository)):
    return services.register_notes(repo, user, project_id, data)


@router.post("/projects/{project_id}/meeting/accept", response_model=Project)
def accept(project_id: str, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.accept_meeting(repo, user, project_id)


@router.post("/projects/{project_id}/meeting/decline", response_model=Project)
def decline(project_id: str, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.decline_meeting(repo, user, project_id)


@router.get("/decks")
def decks(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    """Último deck de cada projeto; destaque automático para a próxima terça."""
    featured = services.featured_tuesday()
    items = []
    for p in repo.list_projects():
        if not p.decks:
            continue
        last = p.decks[-1]
        items.append({"project_id": p.id, "project_name": p.name, **last.model_dump(mode="json"),
                      "featured": bool(p.meeting and p.meeting.day == featured)})
    items.sort(key=lambda d: (not d["featured"], d["days_old"]))
    return {"featured_day": featured, "items": items}


@router.post("/decks", response_model=Project, status_code=201)
def upload_deck(data: DeckIn, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.upload_deck(repo, user, data)
