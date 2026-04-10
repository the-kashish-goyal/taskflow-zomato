"""Add created_by column to tasks

Revision ID: 002
Revises: 001
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_by as nullable first, backfill from project owner, then set NOT NULL
    op.add_column("tasks", sa.Column("created_by", sa.UUID(), nullable=True))

    # Backfill: set created_by to the project owner for existing tasks
    op.execute(
        """
        UPDATE tasks
        SET created_by = projects.owner_id
        FROM projects
        WHERE tasks.project_id = projects.id
        """
    )

    # Now enforce NOT NULL
    op.alter_column("tasks", "created_by", nullable=False)

    op.create_foreign_key("fk_tasks_created_by", "tasks", "users", ["created_by"], ["id"])
    op.create_index("ix_tasks_created_by", "tasks", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_tasks_created_by", table_name="tasks")
    op.drop_constraint("fk_tasks_created_by", "tasks", type_="foreignkey")
    op.drop_column("tasks", "created_by")
