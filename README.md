# Intranet DGH

Centralized Intranet Portal for the **DGH** (Direction Générale de l'Hydraulique) — a PFA (*Projet de Fin d'Année*).

## Tech Stack

**Django 5.2 LTS** · **PostgreSQL** (prod) / **SQLite** (dev) · server-rendered Django templates + **Bootstrap 5** · no DRF / separate API layer — see [ADR-0001](docs/architecture.md#adr-0001-monolith-no-separate-api-layer) for why.

## Screenshots

<!-- TODO: add screenshot -->
**Documents list view**

![Documents list view]()

<!-- TODO: add screenshot -->
**Login page**

![Login page]()

<!-- TODO: add screenshot -->
**Admin panel**

![Admin panel]()

## Quickstart

### Docker (recommended)

```bash
docker compose up --build
```

On first run, the `web` container waits for Postgres to accept connections, then automatically runs `migrate` and `seed_demo_data` before starting the dev server — no manual setup steps needed. The app is available at [http://localhost:8000](http://localhost:8000).

### Native (venv)

```powershell
git clone <repo-url>
cd dgh_intranet
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

## Demo Users

Seeded by `seed_demo_data` (idempotent — safe to re-run). All three share the same password.

| Username | Password | Role | Department |
|---|---|---|---|
| `admin_demo` | `DemoPass123!` | Admin | — (org-wide) |
| `chef_demo` | `DemoPass123!` | Chef de Département | Ressources Humaines |
| `employe_demo` | `DemoPass123!` | Employé | Ressources Humaines |

## Running Tests

**Native:**

```powershell
python manage.py test accounts documents core
```

**Docker:**

```bash
docker compose exec web python manage.py test accounts documents core
```

Current status: **41 tests passing**.

## Project Structure

```
accounts/    Custom User model, RBAC role field, login/logout/password-reset flows
documents/   Document model, department-scoped upload/download/soft-delete
audit/       Append-only AuditLog model, auth-event signals, log_action() service
core/        Department model, Announcement model, shared app-level concerns
```

## Documentation

See [docs/architecture.md](docs/architecture.md) for design rationale, Architecture Decision Records, the data model, and known limitations.
