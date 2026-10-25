# Wealth Portfolio Tracker

A multi-user wealth portfolio tracker with an embedded AI agent. Portfolios are protected by per-user membership and three roles (Owner / Editor / Viewer); the agent acts **as the requesting user** and enforces the same boundaries as the REST API.

---

## Table of Contents

1. [What this is](#1-what-this-is)
2. [Stack](#2-stack)
3. [Project layout](#3-project-layout)
4. [Prerequisites](#4-prerequisites)
5. [Environment files](#5-environment-files)
6. [Running with Docker — Development](#6-running-with-docker--development)
7. [Running with Docker — Production](#7-running-with-docker--production)
8. [Seeding demo data](#8-seeding-demo-data)
9. [Creating your first account](#9-creating-your-first-account)
10. [Using the app](#10-using-the-app)
11. [The AI agent](#11-the-ai-agent)
12. [Running tests](#12-running-tests)
13. [Common operations](#13-common-operations)
14. [Troubleshooting](#14-troubleshooting)
15. [Running without Docker](#15-running-without-docker)
16. [Known limitations](#16-known-limitations)

---

## 1. What this is

- **Portfolios** contain **assets** (stocks, crypto, real estate, cash).
- Each asset has a **transaction history** (buy / sell / dividend).
- Users are **members** of portfolios with a role:
  - **Owner** — full control, can invite members, rename/delete the portfolio, write data.
  - **Editor** — can add/edit/delete assets and transactions. Cannot manage members or rename the portfolio.
  - **Viewer** — read-only.
- An **AI agent** (`/agent/`) answers questions about the user's portfolios. It uses the same permission boundary as the API: a Viewer asking about a portfolio they don't belong to gets `"not found or access denied"`, never data.
- **Signup is open.** New users start with zero portfolios and can create their own.

---

## 2. Stack

| Layer          | Choice                                                    |
| -------------- | --------------------------------------------------------- |
| Backend        | Django 5.1 + Django REST Framework                        |
| Auth           | JWT (`djangorestframework-simplejwt`)                     |
| Agent          | `django-ag-ui` 0.64 + Pydantic-AI (OpenAI-compatible)     |
| Database       | PostgreSQL 16                                             |
| Cache          | Redis 7.4                                                 |
| ASGI server    | Uvicorn (dev: `--reload`, prod: `--workers 2`)            |
| Frontend       | React 18 + Vite                                           |
| Orchestration  | Docker Compose (base + dev override + prod override)      |

The backend **must** run under ASGI. WSGI/Gunicorn will not serve the agent's SSE stream.

---

## 3. Project layout

```
.
├── backend/
│   ├── config/              Django project (settings, urls, asgi)
│   ├── core/                Domain: Portfolio, Membership, Asset, Transaction
│   │   ├── services.py      ← the ONLY data-access path for portfolio data
│   │   ├── models.py
│   │   ├── views.py         DRF ViewSets
│   │   ├── permissions.py
│   │   └── tests/
│   ├── agent/               AI agent endpoint
│   │   ├── agent_tools.py   tool registry + write/read tools
│   │   └── urls.py          AGUIServer mount
│   ├── audit/               AuditLog model + DatabaseAuditLogger
│   ├── Dockerfile           multi-stage: dev / prod
│   └── entrypoint.sh        waits for Postgres → migrate → start Uvicorn
├── frontend/
│   ├── src/
│   │   ├── pages/           Login, Signup, PortfolioList, PortfolioDetail
│   │   ├── components/      AssetTable, TransactionTable, ChatPanel, Members
│   │   ├── api/client.js
│   │   ├── auth.js
│   │   └── styles.css
│   ├── Dockerfile           multi-stage: dev / prod (nginx)
│   └── nginx.conf
├── docker-compose.yml             base services
├── docker-compose.override.yml    dev (auto-loaded)
├── docker-compose.prod.yml        prod (loaded with -f)
├── .env.example
└── README.md
```

**Architectural invariant:** every data access for portfolio / asset / transaction / membership goes through `core/services.py`. DRF views and agent tools call it; neither touches the ORM directly. This is why the agent inherits the API's permissions for free.

---

## 4. Prerequisites

**For the Docker path (recommended):**

- Docker with the Compose v2 plugin (`docker compose version` should print v2.x).
- Podman + `podman-compose` also works (used on Fedora Silverblue); the compose files are compatible.
- ~2 GB free disk for images.

**For the non-Docker path:** see §15.

---

## 5. Environment files

Three env files, layered:

| File         | Purpose                                     | When loaded           |
| ------------ | ------------------------------------------- | --------------------- |
| `.env.base`  | DB / Redis / SECRET_KEY — shared            | Every environment     |
| `.env.dev`   | `DEBUG=True`, dev hosts, dev API URL        | With `docker compose up` (auto) |
| `.env.prod`  | `DEBUG=False`, prod hosts, prod API URL     | With `-f docker-compose.prod.yml` |

**First-time setup:**

```bash
cp .env.example .env.base
cp .env.example .env.dev
cp .env.example .env.prod
```

Then edit each:

- **`.env.base`** — set `POSTGRES_PASSWORD` and `DB_PASSWORD` to the same strong value, and `SECRET_KEY` to a random string.
- **`.env.dev`** — set `GOOGLE_API_KEY` **or** `OPENAI_API_KEY` (see §11).
- **`.env.prod`** — set `SECRET_KEY`, `ALLOWED_HOSTS` (your real domain), and the same DB password as `.env.base`.

The `DJANGO_AG_UI` settings in `backend/config/settings.py` read `OPENAI_API_KEY` by default. If you use OpenAI-compatible providers (e.g. Groq), also set `OPENAI_BASE_URL` in `.env.dev`:

```
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

---

## 6. Running with Docker — Development

From the project root:

```bash
docker compose up --build
```

What happens:

- `docker-compose.override.yml` is **auto-loaded** — dev targets, bind mounts, ports.
- `db` and `redis` start; healthchecks gate the rest.
- `backend` waits for Postgres, applies migrations, starts Uvicorn with `--reload`.
- `frontend` runs Vite dev server.

Endpoints:

| Service    | URL                            |
| ---------- | ------------------------------ |
| Frontend   | http://localhost:5173          |
| Backend    | http://localhost:8000          |
| Django admin | http://localhost:8000/admin/ |
| API root   | http://localhost:8000/api/v1/  |
| Agent SSE  | http://localhost:8000/agent/   |

The frontend proxies `/api/` and `/agent/` to the backend, so the browser sees one origin and CORS is not needed in dev.

**Stop:** `docker compose down`  
**Stop and wipe the database:** `docker compose down -v` ← only when you want a clean slate.

**Rebuild after dependency changes** (requirements.txt or package.json):

```bash
docker compose up --build
```

**Restart the backend without rebuilding** (after a code edit — not needed in dev, `--reload` picks it up):

```bash
docker compose restart backend
```

---

## 7. Running with Docker — Production

Production uses the base file **plus** the prod override. The override pins `build.target=prod`, removes code bind mounts, sets `restart: unless-stopped`, and exposes 80 and 8000.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Endpoints:

| Service    | URL                          |
| ---------- | ---------------------------- |
| Frontend   | http://localhost:80          |
| Backend    | http://localhost:8000        |

The frontend is served by nginx, which reverse-proxies `/api/` and `/agent/` to the backend. Same-origin in prod — no CORS required.

**Verify the prod config has no bind mounts:**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config | grep -E "source:|bind" || echo "no bind mounts (good)"
```

**Before exposing to the internet:**

1. Edit `.env.prod` — real `SECRET_KEY`, real `ALLOWED_HOSTS` (your domain).
2. Set a strong `POSTGRES_PASSWORD` in `.env.base` (and the same value in `DB_PASSWORD`).
3. Terminate TLS in front of the frontend container (or add a reverse proxy like Caddy / Traefik). The compose files do **not** include TLS.
4. Verify `DEBUG=False` in `.env.prod`.

---

## 8. Seeding demo data

The seed command is **idempotent** — safe to re-run.

```bash
docker compose exec backend python manage.py seed_demo
```

Creates:

- Users `owner`, `editor`, `viewer` — password `pass1234`.
- Portfolio **"Shared Household"** — all three are members with their roles.
- Portfolio **"Owner Only"** — only `owner` is a member (used for the isolation test).
- Assets and transactions inside both.

Re-running does not duplicate users, portfolios, assets, or transactions.

**To create a Django superuser** (for the admin panel):

```bash
docker compose exec backend python manage.py createsuperuser
```

Admin is separate from the seeded users; don't reuse `owner` for the superuser.

---

## 9. Creating your first account

Signup is open. From the browser:

1. Visit http://localhost:5173/signup
2. Pick a username and password (min 8 chars).
3. You land on an **empty portfolio list**.
4. Click **New portfolio** → it becomes **yours** (you're OWNER).
5. Open it → **Add asset** → **Add transaction**.

If you want to test the Viewer/Editor side without the seed, sign up a second account, then invite it from the first account's portfolio detail page (Members section, Owner-only).

---

## 10. Using the app

- **Portfolios page** — grid of portfolios you belong to. Each card shows your role.
- **Portfolio detail** — stat cards, asset table, transaction table, members, and the chat panel.
  - **Owner:** add/edit/delete assets and transactions, invite/remove members.
  - **Editor:** add/edit/delete assets and transactions. Cannot manage members.
  - **Viewer:** read-only. Write forms and delete buttons are hidden.
- **Members section** — visible to all members; only Owner sees the invite form and remove buttons.
- **Theme toggle** — topbar, top-right. Persisted in `localStorage`.

---

## 11. The AI agent

The agent is mounted at `/agent/`. It uses the same `core/services.py` as the API, so it inherits the permission boundary. If a Viewer asks about a portfolio they don't belong to, the agent returns `"not found or access denied"`.

**Tools available to the agent:**

| Tool                    | Type  | Purpose                                         |
| ----------------------- | ----- | ----------------------------------------------- |
| `list_my_portfolios`    | read  | List portfolios the user belongs to             |
| `get_portfolio_summary` | read  | Details + asset list (with IDs)                 |
| `query_transactions`    | read  | Transactions with optional date range           |
| `add_asset`             | write | Create an asset (Editor/Owner only)             |
| `log_transaction`       | write | Log a buy / sell / dividend (Editor/Owner only) |

**Provider configuration** lives in `backend/config/settings.py` under `DJANGO_AG_UI`:

```python
DJANGO_AG_UI = {
    "MODEL": "openai:openai/gpt-oss-120b",
    "API_KEY": _env("OPENAI_API_KEY", None),
    "MODEL_SETTINGS": {"temperature": 0.1},
    "RETRIES": 2,
}
```

To use OpenAI directly, remove `OPENAI_BASE_URL` and set `MODEL` to a real OpenAI model. To use Google Gemini, install `django-ag-ui[google]` instead of `[openai]` and change `MODEL` to `google-gla:gemini-2.0-flash`.

**Every tool call is audited** (tool name, user, success/failure, arguments) and visible in Django admin under **Audit logs**.

---

## 12. Running tests

```bash
docker compose exec backend python manage.py test -v 2
```

Expected: ~80 tests, all passing. Coverage areas:

- `core/tests/test_services.py` — service-layer isolation
- `core/tests/test_api.py` — DRF endpoint behavior (role matrix)
- `core/tests/test_auth.py` — JWT endpoints
- `core/tests/test_register.py` — signup
- `core/tests/test_membership.py` — invite/remove member rules
- `agent/tests/test_tools.py` — agent tool permission enforcement (the security proof: Viewer denied on Owner-Only portfolio)
- `audit/tests/test_logger.py` — audit log write + failure resilience

---

## 13. Common operations

**Reset the database (lose everything):**

```bash
docker compose down -v
docker compose up -d backend
docker compose exec backend python manage.py seed_demo
```

**Apply new migrations:**

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

**Open a Django shell:**

```bash
docker compose exec backend python manage.py shell
```

**Tail logs:**

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

**Restart just the backend** (after `settings.py` changes):

```bash
docker compose restart backend
```

---

## 14. Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `relation "auth_user" does not exist` | Migrations didn't run. `docker compose exec backend python manage.py migrate` |
| `ModuleNotFoundError` after editing `requirements.txt` | `docker compose build backend && docker compose up -d backend` (a `restart` won't pick up a rebuilt image) |
| Agent returns `RUN_ERROR` immediately | Check provider key and `MODEL` string; ensure `OPENAI_BASE_URL` points at the right endpoint. `docker compose logs backend --tail 30` |
| 401 on `/agent/` even with a token | Check `get_user` in `agent/urls.py` — it must call `JWTAuthentication().authenticate(request)`. |
| `SynchronousOnlyOperation` in audit log | Should not occur — `DatabaseAuditLogger` runs the ORM write on a daemon thread. If it does, the thread has an event loop; check you're using `threading.Thread`, not `sync_to_async`. |
| Frontend can't reach backend in dev | Ensure `docker compose up` (not just `up backend`) — Vite proxies `/api/` and `/agent/` via the compose network. |
| `FATAL: role "root" does not exist` in db logs | Harmless — `pg_isready` runs before the container env is applied. Migrations still succeed. |

---

## 15. Running without Docker

You can run the backend and frontend directly if you prefer. This path is **not** tested on every release; Docker is the supported deployment.

**Prerequisites:**

- Python 3.12
- Node 20
- PostgreSQL 16 running locally
- Redis 7 running locally

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DB_HOST=localhost DB_PORT=5432
export DB_NAME=wealth DB_USER=wealth DB_PASSWORD=wealth_dev_pw
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-only-secret
export DEBUG=True
export ALLOWED_HOSTS=localhost,127.0.0.1
export OPENAI_API_KEY=...        # or GOOGLE_API_KEY
export OPENAI_BASE_URL=https://api.groq.com/openai/v1   # if using Groq

python manage.py migrate
python manage.py seed_demo          # optional
python manage.py runserver 0.0.0.0:8000
```

> ⚠ `runserver` is WSGI. It will serve the REST API but **not** the agent SSE stream. For the agent to work locally without Docker, use Uvicorn:
>
> ```bash
> uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
> ```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Vite runs at `http://localhost:5173`. The `vite.config.js` proxies `/api/` and `/agent/` to `http://backend:8000`, which only resolves inside the compose network. For local (non-Docker) dev, edit `vite.config.js` and change the proxy targets to `http://localhost:8000`:

```js
proxy: {
  '/api':   { target: 'http://localhost:8000' },
  '/agent': { target: 'http://localhost:8000' },
}
```

Then `npm run dev` works without Docker.

---

## 16. Known limitations

- **No market-price integration.** Asset quantities and cost basis are manually entered; there is no live valuation.
- **No liabilities.** The data model tracks assets only.
- **No charts / history.** The API returns raw transactions; there's no net-worth-over-time view.
- **Invite by username only.** No email invitations or invite-token flow.
- **Owner role is not transferable.** Once a portfolio has an owner, that user cannot be removed and there's no UI to hand ownership over.
- **The agent has no delete tools.** It can add assets and log transactions, but cannot delete anything — a deliberate safety default.
- **SQLite is not supported.** The stack is built around Postgres features (JSONField, `distinct` on joins) and the compose files assume Postgres.