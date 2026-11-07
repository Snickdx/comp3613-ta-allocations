# COMP 3613 TA Allocations (Phase 2 starter)

Flawed baseline **0.2.0** built on [uwidcit/faststart](https://github.com/uwidcit/faststart) (`96ccfce`).

FastStart provides the SSR shell, JWT cookie auth, SQLModel, `manage.py`, and Render/Docker wiring. The ta-allocations scenario adds domain models/services and a JSON API under `/api` (see `/docs`).

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py init
python manage.py run
```

## Seeded API account

| Email | Password | Role |
| --- | --- | --- |
| `hod@example.com` | `hod-dev` | hod |

JSON login: `POST /api/auth/login` with `{"email","password"}`. Allocation endpoints identify the acting HOD with an `X-User-Id` header.

## Student brief

See [`ASSIGNMENT.md`](ASSIGNMENT.md) and [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md).

## Tests

```bash
python -m pytest tests -q
```
