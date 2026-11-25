"""Quem é o usuário logado.

AUTH_MODE=dev        -> tela de login de desenvolvimento (cookie assinado). Só aceita @gm.com.
AUTH_MODE=databricks -> o Databricks Apps faz o SSO com o Microsoft Entra ID e envia o
                        e-mail no cabeçalho X-Forwarded-Email. O perfil vem do cadastro de usuários.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response

from app.config import Settings, get_settings
from app.models import User
from app.repositories import get_repository
from app.repositories.base import Repository
from app.rules import is_email_allowed

COOKIE = "innopex_session"


def _sign(payload: str, key: str) -> str:
    return hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def encode_session(user: User, settings: Settings) -> str:
    payload = base64.urlsafe_b64encode(json.dumps(user.model_dump()).encode()).decode()
    return f"{payload}.{_sign(payload, settings.secret_key)}"


def decode_session(token: str, settings: Settings) -> Optional[User]:
    try:
        payload, signature = token.rsplit(".", 1)
        if not hmac.compare_digest(signature, _sign(payload, settings.secret_key)):
            return None
        return User.model_validate(json.loads(base64.urlsafe_b64decode(payload.encode())))
    except Exception:
        return None


def set_session(response: Response, user: User, settings: Settings) -> None:
    response.set_cookie(COOKIE, encode_session(user, settings), httponly=True, samesite="lax", max_age=60 * 60 * 12)


def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
    repo: Repository = Depends(get_repository),
) -> User:
    if settings.auth_mode == "databricks":
        email = request.headers.get("X-Forwarded-Email", "")
        if not email or not is_email_allowed(email, settings.allowed_domain):
            raise HTTPException(status_code=403, detail="Acesso restrito a contas corporativas.")
        known = repo.find_user(email)
        if known:
            return known
        name = request.headers.get("X-Forwarded-Preferred-Username", email.split("@")[0])
        return User(name=name, email=email, role="Viewer")

    user = decode_session(request.cookies.get(COOKIE, ""), settings)
    if not user:
        raise HTTPException(status_code=401, detail="Faça login para continuar.")
    if not is_email_allowed(user.email, settings.allowed_domain):
        raise HTTPException(status_code=403, detail="Acesso restrito a contas corporativas.")
    return user
