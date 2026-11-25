"""Dashboard executivo e Nopex."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import NopexIn, User
from app.nopex import answer
from app.repositories import get_repository
from app.repositories.base import Repository
from app import services

router = APIRouter(prefix="/api", tags=["indicadores"])


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.dashboard(repo)


@router.post("/nopex")
def nopex(data: NopexIn, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return {"answer": answer(repo, user, data.question)}
