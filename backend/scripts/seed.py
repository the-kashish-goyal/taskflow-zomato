"""Seed script: creates test user, project, and tasks."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import User, Project, Task, TaskStatus, TaskPriority  # noqa: E402
from app.auth import hash_password  # noqa: E402


def seed():
    db = SessionLocal()
    try:
        # Check if seed user already exists
        existing = db.query(User).filter(User.email == "test@example.com").first()
        if existing:
            print("Seed data already exists, skipping.")
            return

        # Create test user
        user = User(
            name="Test User",
            email="test@example.com",
            password=hash_password("password123"),
        )
        db.add(user)
        db.flush()

        # Create project
        project = Project(
            name="Website Redesign",
            description="Q2 website redesign project",
            owner_id=user.id,
        )
        db.add(project)
        db.flush()

        # Create 3 tasks with different statuses
        tasks = [
            Task(
                title="Design homepage mockup",
                description="Create wireframes and high-fidelity mockups for the new homepage",
                status=TaskStatus.todo,
                priority=TaskPriority.high,
                project_id=project.id,
                created_by=user.id,
                assignee_id=user.id,
                due_date="2026-04-20",
            ),
            Task(
                title="Implement authentication flow",
                description="Build login and registration pages with JWT integration",
                status=TaskStatus.in_progress,
                priority=TaskPriority.high,
                project_id=project.id,
                created_by=user.id,
                assignee_id=user.id,
                due_date="2026-04-15",
            ),
            Task(
                title="Write API documentation",
                description="Document all REST endpoints with request/response examples",
                status=TaskStatus.done,
                priority=TaskPriority.medium,
                project_id=project.id,
                created_by=user.id,
                assignee_id=None,
                due_date=None,
            ),
        ]
        db.add_all(tasks)
        db.commit()
        print("Seed data created successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
