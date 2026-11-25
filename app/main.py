"""Ponto de entrada da InnOpEx Governance Platform.

Rodar localmente:  python -m app.main   (ou F5 no VS Code)
Documentação da API: http://localhost:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import admin, auth, governance, insights, notifications, projects
from app.config import STATIC_DIR, get_settings
from app.repositories import get_repository
from app.rules import BusinessRuleError, NotFound, PermissionDenied
from app.services import run_stale_check


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Automação diária de material parado (na produção vira um job agendado no Databricks).
    try:
        run_stale_check(get_repository())
    except NotImplementedError:
        pass
    yield


app = FastAPI(title="InnOpEx Governance Platform · GMSA", version=__version__, lifespan=lifespan)


@app.exception_handler(BusinessRuleError)
async def _rule(_: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(PermissionDenied)
async def _perm(_: Request, exc: PermissionDenied):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(NotFound)
async def _nf(_: Request, exc: NotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(NotImplementedError)
async def _todo(_: Request, exc: NotImplementedError):
    return JSONResponse(status_code=501, content={"detail": str(exc)})


for r in (auth.router, projects.router, governance.router, notifications.router, admin.router, insights.router):
    app.include_router(r)


@app.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok", "version": __version__}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=get_settings().port, reload=False)
