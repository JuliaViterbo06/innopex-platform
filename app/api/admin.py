from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.config import Settings, get_settings
from app.models import Config, User
from app.repositories import get_repository
from app.repositories.base import Repository
from app.rules import BusinessRuleError, require
from app import services

router = APIRouter(prefix="/api", tags=["admin"])

PENDING_DECISIONS = [
    "Autorização de escrita de volta no OpEx Global",
    "Número máximo de projetos por reunião de terça",
    "Critério oficial de filtro GMSA na lista global",
    "Quem aprova a reclassificação entre Opex e Inovação",
    "Quem administra prazos e perfis",
]


@router.get("/config", response_model=Config)
def get_config(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return repo.get_config()


@router.put("/config", response_model=Config)
def put_config(cfg: Config, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.save_config(repo, user, cfg)


@router.get("/admin/users", response_model=list[User])
def users(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    require(user, "admin")
    return repo.list_users()


@router.get("/admin/pending-decisions")
def pending(user: User = Depends(get_current_user)):
    return PENDING_DECISIONS


@router.post("/admin/run-automations")
def run_automations(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    require(user, "admin")
    return {"stale_alerts_created": services.run_stale_check(repo)}


@router.post("/admin/reset")
def reset(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository),
          settings: Settings = Depends(get_settings)):
    if settings.data_mode != "mock":
        raise BusinessRuleError("Reiniciar só é permitido com dados de exemplo.")
    repo.reset()
    services.run_stale_check(repo)
    return {"ok": True}
