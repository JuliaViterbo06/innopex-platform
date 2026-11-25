from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Response

from app import __version__
from app.auth import COOKIE, get_current_user, set_session
from app.config import Settings, get_settings
from app.models import DevLoginIn, User
from app.rules import PERMISSIONS, is_email_allowed

router = APIRouter(prefix="/api", tags=["acesso"])


@router.get("/meta")
def meta(settings: Settings = Depends(get_settings)) -> dict:
    return {"version": __version__, "auth_mode": settings.auth_mode, "data_mode": settings.data_mode,
            "allowed_domain": settings.allowed_domain, "today": dt.date.today()}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {**user.model_dump(), "permissions": sorted(PERMISSIONS[user.role])}


@router.post("/auth/dev-login")
def dev_login(data: DevLoginIn, response: Response, settings: Settings = Depends(get_settings)) -> dict:
    if settings.auth_mode != "dev":
        raise HTTPException(status_code=404, detail="Login de desenvolvimento desativado.")
    if not is_email_allowed(data.email, settings.allowed_domain):
        raise HTTPException(status_code=403, detail=f"Acesso negado: somente contas corporativas @{settings.allowed_domain}.")
    user = User(name=data.name.strip(), email=data.email.strip().lower(), role=data.role)
    set_session(response, user, settings)
    return user.model_dump()


@router.post("/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE)
    return {"ok": True}
