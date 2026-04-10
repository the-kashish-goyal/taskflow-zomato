"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums using raw SQL to avoid any ORM double-creation issues
    op.execute("CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done')")
    op.execute("CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high')")

    # Users
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.create_index("ix_users_email", "users", ["email"])

    # Projects
    op.execute("""
        CREATE TABLE projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            owner_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    # Tasks
    op.execute("""
        CREATE TABLE tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status task_status NOT NULL DEFAULT 'todo',
            priority task_priority NOT NULL DEFAULT 'medium',
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            assignee_id UUID REFERENCES users(id),
            due_date DATE,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_assignee_id", "tasks", ["assignee_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("projects")
    op.drop_table("users")
    sa.Enum(name="task_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="task_priority").drop(op.get_bind(), checkfirst=True)
