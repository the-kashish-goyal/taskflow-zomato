# TaskFlow

Task management API — users can register, create projects, add tasks, and assign them to people. Built with Python/FastAPI, PostgreSQL, and Docker.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Alembic · JWT + bcrypt · structlog · pytest · Docker Compose · [Taskfile](https://taskfile.dev)

## Quick start

```bash
git clone <repo-url> taskflow
cd taskflow
cp .env.example .env
docker compose up --build
```

API runs at `http://localhost:8000`, Swagger docs at `http://localhost:8000/docs`.

Migrations and seed data run automatically on first boot — no extra steps.

**Seed login:**
```
test@example.com / password123
```
This user has a project ("Website Redesign") with 3 tasks in different statuses so you can poke around immediately.

To populate more data for manual testing (3 extra users, 3 projects, 11 tasks):

```bash
./scripts/populate.sh
```

This creates users with known credentials:
```
alice@example.com / alice123
bob@example.com / bob12345
charlie@example.com / charlie1
```

If you have [Task](https://taskfile.dev) installed you can also use `task up`, `task test`, `task populate`, `task logs`, etc. Run `task --list` for the full list.

## High-level design

### System overview

```
┌──────────┐       ┌──────────────────┐       ┌────────────┐
│  Client  │──────▶│   FastAPI (API)   │──────▶│ PostgreSQL │
│ (Swagger │  HTTP │                  │  SQL  │   (Docker)  │
│  / curl) │◀──────│  :8000           │◀──────│   :5432     │
└──────────┘  JSON └──────────────────┘       └────────────┘
                          │
                    ┌─────┴──────┐
                    │  Alembic   │
                    │ migrations │
                    │ (on boot)  │
                    └────────────┘
```

Everything runs in Docker. The API container waits for Postgres to be healthy (via `pg_isready` healthcheck), then runs migrations, seeds the DB, and starts uvicorn.

### Request lifecycle

```
Incoming request
      │
      ▼
  CORS middleware
      │
      ▼
  Route matching ──── /auth/*  ──▶  No auth needed, handle directly
      │
      ▼
  Bearer token? ──── missing ──▶  401
      │
      ▼
  Decode JWT ──────── expired/invalid ──▶  401
      │
      ▼
  Load user from DB ── not found ──▶  401
      │
      ▼
  Route handler
      │
      ├── check ownership/permissions ── fail ──▶  403
      ├── validate request body ── fail ──▶  400
      ├── lookup resource ── not found ──▶  404
      │
      ▼
  200 / 201 / 204
```

### Data model

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│    users     │       │     projects     │       │      tasks       │
├──────────────┤       ├──────────────────┤       ├──────────────────┤
│ id       (PK)│◀──┐   │ id          (PK) │◀──┐   │ id          (PK) │
│ name         │   │   │ name             │   │   │ title            │
│ email (uniq) │   ├───│ owner_id    (FK) │   │   │ description      │
│ password     │   │   │ description      │   ├───│ project_id  (FK) │
│ created_at   │   │   │ created_at       │   │   │ created_by  (FK) │──┐
└──────────────┘   │   └──────────────────┘   │   │ assignee_id (FK) │──┤
                   │                          │   │ status           │  │
                   │                          │   │ priority         │  │
                   │                          │   │ due_date         │  │
                   └──────────────────────────┼───│ created_at       │  │
                                              │   │ updated_at       │  │
                   ┌──────────────────────────┘   └──────────────────┘  │
                   │                                                    │
                   └── both created_by and assignee_id point to users ──┘
```

Tasks cascade-delete when their project is deleted. `assignee_id` is nullable (unassigned tasks). `created_by` tracks who made the task for delete permissions.

### Project structure

```
taskflow/
├── docker-compose.yml
├── .env.example
├── Taskfile.yml
└── backend/
    ├── Dockerfile            # multi-stage build
    ├── scripts/
    │   ├── entrypoint.sh     # migrate → seed → start
    │   └── seed.py
    ├── alembic/
    │   └── versions/
    │       ├── 001_initial_schema.py
    │       └── 002_add_task_created_by.py
    ├── app/
    │   ├── main.py           # FastAPI app, CORS, error handlers
    │   ├── config.py         # env vars (fails without JWT_SECRET)
    │   ├── database.py       # engine, session, Base
    │   ├── models.py         # User, Project, Task
    │   ├── schemas.py        # Pydantic request/response models
    │   ├── auth.py           # bcrypt + JWT helpers
    │   ├── dependencies.py   # get_current_user
    │   └── routers/
    │       ├── auth.py       # register, login
    │       ├── projects.py   # CRUD + stats
    │       └── tasks.py      # CRUD + filters
    └── tests/
        ├── conftest.py       # fixtures, test DB setup
        ├── test_auth.py
        └── test_tasks.py
```

## Why Python and not Go

I know the assignment prefers Go. I went with Python/FastAPI because it's the stack I'm strongest in and I'd rather spend the time on getting the API right than wrestling with a language I'm less fluent in. FastAPI also gives you interactive docs at `/docs` for free which is nice for reviewers. The patterns I used (explicit migrations, structured logging, clean route separation) carry over to Go 1:1 — happy to discuss on the call.

## Architecture & decisions

**FastAPI** — async-capable, Pydantic validation baked in, auto-generated OpenAPI. For an API this size, Django felt heavy and Flask felt too barebones.

**SQLAlchemy 2.0 + Alembic** — I wanted real migrations, not auto-migrate. Every change has an up and down migration. I used the sync driver (not async) since there's no real concurrency pressure here — would switch for production.

**Three routers** (auth, projects, tasks) — flat structure, no over-engineering. Each file is ~100 lines.

**`created_by` on tasks** — the spec says "project owner or task creator" can delete. I added a `created_by` FK to track who made each task. Existing rows get backfilled from the project owner in the migration.

**JWT_SECRET must be set** — no hardcoded fallback. The app refuses to start without it. Keeps us away from the "secret in source code" disqualifier.

**CORS** is `*` right now. Would lock that down for production.

**No frontend** — this is a backend-only submission. The Swagger UI at `/docs` works well enough for manual testing.

## Migrations

They run on container start via the entrypoint script. If you need to run them manually:

```bash
docker compose exec api alembic upgrade head   # apply
docker compose exec api alembic downgrade -1   # rollback one
```

## Tests

15 integration tests covering auth (register, login, duplicates, bad credentials) and tasks (CRUD, filtering, delete permissions). They use SQLite in-memory so no Postgres needed:

```bash
docker compose exec api pytest -v

# or locally
cd backend && JWT_SECRET=test pytest -v
```

## API

Everything returns JSON. Protected routes need `Authorization: Bearer <token>`.

### Auth

| | Endpoint | Notes |
|---|---|---|
| POST | `/auth/register` | `{name, email, password}` → `{token, user}` |
| POST | `/auth/login` | `{email, password}` → `{token, user}` |

### Projects

| | Endpoint | Notes |
|---|---|---|
| GET | `/projects` | Paginated. Shows projects you own or have tasks in |
| POST | `/projects` | `{name, description?}` |
| GET | `/projects/:id` | Includes tasks |
| PATCH | `/projects/:id` | Owner only |
| DELETE | `/projects/:id` | Owner only, cascades tasks |
| GET | `/projects/:id/stats` | Counts by status & assignee |

### Tasks

| | Endpoint | Notes |
|---|---|---|
| GET | `/projects/:id/tasks` | Filters: `?status=`, `?assignee=`, `?page=`, `?limit=` |
| POST | `/projects/:id/tasks` | `{title, description?, priority?, assignee_id?, due_date?}` |
| PATCH | `/tasks/:id` | Any field |
| DELETE | `/tasks/:id` | Project owner or task creator |

### Errors

```
400  {"error": "validation failed", "fields": {"email": "is required"}}
401  {"error": "invalid or expired token"}
403  {"error": "forbidden"}
404  {"error": "not found"}
```

Full docs with try-it-out at `http://localhost:8000/docs`.

## What I'd do with more time

- **Async SQLAlchemy** — sync is fine here but wouldn't scale under load
- **Rate limiting** on auth endpoints — right now there's nothing stopping brute force
- **Refresh tokens** — currently just a 24h access token, no refresh flow
- **Frontend** — React/TS SPA, the whole UI spec
- **CI** — GitHub Actions: lint, test, build
- **Soft deletes** — `deleted_at` instead of hard deletes for audit
- **More test coverage** — projects CRUD, pagination edges, stats
