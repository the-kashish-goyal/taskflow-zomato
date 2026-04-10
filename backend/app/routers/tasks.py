import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, Task, User
from app.schemas import TaskCreate, TaskUpdate, TaskOut, PaginatedTasks

router = APIRouter(tags=["tasks"])


@router.get("/projects/{project_id}/tasks", response_model=PaginatedTasks)
def list_tasks(
    project_id: uuid.UUID,
    status_filter: str | None = Query(None, alias="status"),
    assignee: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    query = db.query(Task).filter(Task.project_id == project_id)

    if status_filter:
        query = query.filter(Task.status == status_filter)
    if assignee:
        query = query.filter(Task.assignee_id == assignee)

    total = query.count()
    tasks = query.order_by(Task.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return PaginatedTasks(
        tasks=[TaskOut.model_validate(t) for t in tasks],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: uuid.UUID,
    body: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    if body.assignee_id:
        assignee = db.query(User).filter(User.id == body.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=400,
                detail={"error": "validation failed", "fields": {"assignee_id": "user not found"}},
            )

    task = Task(
        title=body.title,
        description=body.description,
        priority=body.priority,
        project_id=project_id,
        created_by=current_user.id,
        assignee_id=body.assignee_id,
        due_date=body.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    if body.assignee_id is not None:
        assignee = db.query(User).filter(User.id == body.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=400,
                detail={"error": "validation failed", "fields": {"assignee_id": "user not found"}},
            )

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail={"error": "not found"})

    # Project owner or task creator can delete
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if project.owner_id != current_user.id and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    db.delete(task)
    db.commit()
