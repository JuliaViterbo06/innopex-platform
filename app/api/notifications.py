from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import Notification, User
from app.repositories import get_repository
from app.repositories.base import Repository
from app import services

router = APIRouter(prefix="/api/notifications", tags=["notificações"])


@router.get("", response_model=list[Notification])
def list_notifications(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return repo.list_notifications()


@router.post("/read-all")
def read_all(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    services.mark_read(repo)
    return {"ok": True}


@router.post("/{notification_id}/read")
def read_one(notification_id: str, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    services.mark_read(repo, notification_id)
    return {"ok": True}
