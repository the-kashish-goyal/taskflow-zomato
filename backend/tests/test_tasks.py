"""Integration tests for task endpoints."""
import uuid

from app.models import Task, User
from app.auth import hash_password


def test_create_task(client, auth_header, seed_project):
    resp = client.post(
        f"/projects/{seed_project.id}/tasks",
        json={"title": "New Task", "priority": "high"},
        headers=auth_header,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "New Task"
    assert data["priority"] == "high"
    assert data["status"] == "todo"
    assert data["project_id"] == str(seed_project.id)
    assert "created_by" in data


def test_create_task_missing_title(client, auth_header, seed_project):
    resp = client.post(
        f"/projects/{seed_project.id}/tasks",
        json={"description": "no title"},
        headers=auth_header,
    )
    assert resp.status_code == 400


def test_list_tasks_with_status_filter(client, auth_header, seed_project, db_session, seed_user):
    for s in ["todo", "in_progress", "done"]:
        task = Task(
            title=f"Task {s}",
            status=s,
            project_id=seed_project.id,
            created_by=seed_user.id,
        )
        db_session.add(task)
    db_session.commit()

    resp = client.get(
        f"/projects/{seed_project.id}/tasks?status=todo",
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["status"] == "todo" for t in data["tasks"])
    assert data["total"] == 1


def test_update_task_status(client, auth_header, seed_project, db_session, seed_user):
    task = Task(
        title="Update me",
        status="todo",
        project_id=seed_project.id,
        created_by=seed_user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    resp = client.patch(
        f"/tasks/{task.id}",
        json={"status": "done"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_delete_task_as_project_owner(client, auth_header, seed_project, db_session, seed_user):
    task = Task(
        title="Delete me",
        project_id=seed_project.id,
        created_by=seed_user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    resp = client.delete(f"/tasks/{task.id}", headers=auth_header)
    assert resp.status_code == 204


def test_delete_task_as_creator_not_owner(client, db_session, seed_project):
    """A user who created the task but doesn't own the project can still delete it."""
    other_user = User(
        id=uuid.uuid4(),
        name="Other User",
        email="other@example.com",
        password=hash_password("password123"),
    )
    db_session.add(other_user)
    db_session.flush()

    task = Task(
        title="Creator can delete",
        project_id=seed_project.id,
        created_by=other_user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Login as the other user
    resp = client.post("/auth/login", json={"email": "other@example.com", "password": "password123"})
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/tasks/{task.id}", headers=headers)
    assert resp.status_code == 204


def test_delete_task_forbidden(client, db_session, seed_project, seed_user):
    """A user who neither owns the project nor created the task gets 403."""
    other_user = User(
        id=uuid.uuid4(),
        name="Random User",
        email="random@example.com",
        password=hash_password("password123"),
    )
    db_session.add(other_user)
    db_session.flush()

    # Task created by seed_user, project owned by seed_user
    task = Task(
        title="Forbidden delete",
        project_id=seed_project.id,
        created_by=seed_user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Login as random user
    resp = client.post("/auth/login", json={"email": "random@example.com", "password": "password123"})
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/tasks/{task.id}", headers=headers)
    assert resp.status_code == 403
