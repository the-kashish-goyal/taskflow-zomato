import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, Task, User
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    ProjectDetail,
    PaginatedProjects,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=PaginatedProjects)
def list_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Projects the user owns or has tasks in
    query = (
        db.query(Project)
        .outerjoin(Task, Task.project_id == Project.id)
        .filter(or_(Project.owner_id == current_user.id, Task.assignee_id == current_user.id))
        .distinct()
    )
    total = query.count()
    projects = query.order_by(Project.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedProjects(
        projects=[ProjectOut.model_validate(p) for p in projects],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(name=body.name, description=body.description, owner_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .options(selectinload(Project.tasks))
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    return ProjectDetail.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "forbidden"})

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "forbidden"})

    db.delete(project)
    db.commit()


@router.get("/{project_id}/stats")
def project_stats(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})

    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    by_status: dict[str, int] = {}
    by_assignee: dict[str, int] = {}
    for t in tasks:
        by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
        key = str(t.assignee_id) if t.assignee_id else "unassigned"
        by_assignee[key] = by_assignee.get(key, 0) + 1

    return {"project_id": str(project_id), "by_status": by_status, "by_assignee": by_assignee, "total": len(tasks)}
