import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import TaskStatus, TaskPriority


# --- Auth ---

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: "UserOut"


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str

    model_config = {"from_attributes": True}


# --- Projects ---

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    owner_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectOut):
    tasks: list["TaskOut"] = []


# --- Tasks ---

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.medium
    assignee_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None


class TaskOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    project_id: uuid.UUID
    created_by: uuid.UUID
    assignee_id: Optional[uuid.UUID]
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Pagination ---

class PaginatedTasks(BaseModel):
    tasks: list[TaskOut]
    total: int
    page: int
    limit: int


class PaginatedProjects(BaseModel):
    projects: list[ProjectOut]
    total: int
    page: int
    limit: int
