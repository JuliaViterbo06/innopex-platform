from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import PhaseMoveIn, Project, ProjectIn, User
from app.repositories import get_repository
from app.repositories.base import Repository
from app import services

router = APIRouter(prefix="/api/projects", tags=["projetos"])


@router.get("", response_model=list[Project])
def list_projects(user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return repo.list_projects()


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.get_project_or_404(repo, project_id)


@router.post("", response_model=Project, status_code=201)
def create_project(data: ProjectIn, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    return services.create_project(repo, user, data)


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, data: ProjectIn, user: User = Depends(get_current_user),
                   repo: Repository = Depends(get_repository)):
    return services.update_project(repo, user, project_id, data)


@router.post("/{project_id}/phase", response_model=Project)
def move_phase(project_id: str, data: PhaseMoveIn, user: User = Depends(get_current_user),
               repo: Repository = Depends(get_repository)):
    return services.move_phase(repo, user, project_id, data.phase)
