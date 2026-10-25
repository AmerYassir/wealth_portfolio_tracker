# Wealth Portfolio Tracker — Development Plan

---

## 1. What This Is Really About

The short version of why this prototype exists:

> **The permission model is the product. The AI agent is the stress test that proves it.**

A multi-user financial app is only as trustworthy as its weakest data-access path. Most agent demos leak data for boring reasons — a tool handler forgot a `where` clause, or the model got to pass a `user_id`, or a middleware check quietly doesn't run on internal calls. This prototype removes that whole class of bug by construction: there is one data-access path (`core/services.py`), and both the REST API and the agent tools go through it. Identity is injected server-side from `request.user`. The model never supplies identity, and it has no privileges of its own.

Everything else in this plan is downstream of that one decision.

---

## 2. Scope — What Was Built, What Wasn't

### 2.1 Built — P0 (Core Product)

| Feature | Notes |
|---|---|
| Multi-asset portfolios | Stocks, crypto, real estate, cash. |
| Transaction history | Per asset: buy / sell / dividend. |
| Three-role membership | `OWNER`, `EDITOR`, `VIEWER`; unique `(user, portfolio)`. |
| Object-level permissions | `IsPortfolioMember` + mandatory queryset filtering. |
| Single data-access layer | `core/services.py` — every view and every tool calls it. |
| JWT auth | `djangorestframework-simplejwt`; open signup. |
| DRF CRUD APIs | Portfolio / Asset / Transaction / Membership. |
| Seed command | Idempotent `seed_demo`: `owner` / `editor` / `viewer` plus "Shared Household" and "Owner Only" portfolios. |
| Django admin | Includes audit log inspection. |

### 2.2 Built — P1 (Agent, Read *and* Write)

| Feature | Notes |
|---|---|
| Agent endpoint | `/agent/` via `django-ag-ui` + Pydantic-AI, mounted as an AG-UI SSE endpoint. |
| Read tools | `list_my_portfolios`, `get_portfolio_summary`, `query_transactions`. |
| Write tools | `add_asset`, `log_transaction` — Editor/Owner only, checked at the service layer. |
| Audit log | `audit` app with `DatabaseAuditLogger`; records tool name, user, success/failure, arguments. Visible in admin. |
| Streaming | Thinking / tool-call indicators in the chat panel. |
| Permission-aware UI | Viewers see no write controls; only Owners see the invite form. |

### 2.3 Built — P1 (UI/UX)

- Dashboard with portfolio grid, portfolio detail (stat cards, asset table, transaction table, members, chat panel).
- Streaming chat panel with tool-call feedback.
- Theme toggle persisted in `localStorage`.
- Same-origin in dev (Vite proxy) and prod (nginx reverse proxy), so no CORS to manage.

### 2.4 Deferred — And Why

| Feature | Reason |
|---|---|
| Live market data / valuation sync | Needs scheduled jobs (celery + Redis), rate-limited external calls, and a valuation cache. Async plumbing doesn't test the permission thesis, so it lost the time budget. |
| Realtime collaboration / presence | Needs WebSockets (or Liveblocks/PartyKit) and a state-reconciliation model. SSE covers the agent stream only. |
| Charts and net-worth-over-time | Transactions have timestamps, but there's no aggregation endpoint or chart UI yet. |
| Invite-by-email / invite tokens | Membership is invite-by-username from the portfolio page. Email invites need a mailer, token model, and expiry flow. |
| Owner transfer | Once a portfolio has an owner, they can't be removed and ownership can't be handed over. That's a deliberate safety default, not an oversight. |
| Agent delete tools | The agent can add assets and log transactions, but can't delete anything. Irreversible agent actions are the riskiest class and need an approval workflow we didn't build in scope. |
| Liabilities / net worth | Assets-only model. |
| SQLite support | The stack leans on Postgres features (JSONField, `distinct` on joins); compose pins Postgres 16., it could be switched easilly if you you are running a 1 VPS (preformence boost) |

### 2.5 How the Scope Line Was Drawn

The assessment explicitly rewards what you defer and why. The line I used was: **"does this test the agent-permission interaction?"** Async jobs, realtime, and charts don't. Making the agent write safely, and proving the read path is structurally non-bypassable, does. That's where the time went.

---

## 3. Architecture — The Invariant and How It Holds

### 3.1 The Invariant

> Every portfolio, asset, transaction, and membership access — from a DRF view, a serializer, a management command, or an agent tool — goes through `core/services.py`. Every function in that module takes `user` as its first parameter and filters by membership internally. No view or tool builds its own queryset.

### 3.2 How It Holds

| Concern | Mechanism |
|---|---|
| Object-level permission | `IsPortfolioMember` with `has_object_permission`, backed by `user_role_on_portfolio(user, portfolio_id)`. |
| List-level permission | Every `get_queryset()` delegates to `get_portfolios_for_user(user)` / `get_assets_for_user(user, pid)` / `get_transactions_for_user(user, pid, ...)`. No `objects.all()` on tenant data. |
| Identity in agent tools | Injected via `django-ag-ui`'s `get_user(request)`, which calls `JWTAuthentication().authenticate(request)`. Tool signatures have no `user_id` parameter. The model can't forge identity. |
| Write authorization | Service functions raise `PermissionDenied` when the role is insufficient (`EDITOR` for assets/transactions, `OWNER` for membership). Tools catch it and return a safe error to the model. |
| Failure mode | Unauthorized access returns empty / `None` — not a leak, not a stack trace. The agent reports `"not found or access denied"`. |

### 3.3 Why This Shape

- **One enforcement point** means the security proof is one test family (`core/tests/test_services.py`, `agent/tests/test_tools.py`) rather than a spread of per-endpoint checks that drift over time.
- **Adding a new tool** is one function in `core/services.py` and one wrapper in `agent/agent_tools.py`. No restructuring. That was the whole point of splitting the modules early.
- **The audit log** is an independent signal: every tool call is recorded whether it succeeded or not, so "the agent *tried*" is visible even when it was denied.

### 3.4 What a Reviewer Should Check

If you want to try to break the invariant, the quickest paths are:

1. Grep for `objects.all()` and `objects.filter(` on tenant models outside `core/services.py`. If any show up, the invariant is broken.
2. Grep `agent/agent_tools.py` for `user_id`, `role`, or `request.user` as a tool parameter. If any show up, identity can be forged.
3. Run `agent/tests/test_tools.py` — the Viewer-denied-on-Owner-Only test should pass.

None of those should find a violation.

---

## 4. Stack and Trade-offs

| Layer | Choice | Why |
|---|---|---|
| Backend | **Django 5.1 + DRF** | Batteries-included auth, admin, ORM, migrations. The interesting problem is the permission boundary, not rebuilding auth. FastAPI would have cost hours re-implementing what Django gives for free. |
| Auth | **JWT (`simplejwt`)** | Stateless, sufficient for an SPA. JWT is *identity*, not authorization — the actual access boundary lives in `core/services.py`. That distinction is the whole point. |
| Permissions | **DRF permission classes + `core/services.py`** | Object-level check via `has_object_permission`; list-level check via mandatory queryset filtering. Two layers, one source of truth. |
| Agent | **`django-ag-ui` + Pydantic-AI** | First-class Django integration. `require_authenticated` and `get_user(request)` give server-side identity injection without a custom auth middleware, and the SSE endpoint comes for free — streaming didn't turn into a research project. |
| DB | **Postgres 16** | JSONField for transaction metadata; `distinct on` on joins. The stack assumes it. |
| Cache | **Redis 7.4** | Backs `django-ag-ui` throttling. It's in `docker-compose.yml` because it has a real job, not as decoration. |
| ASGI | **Uvicorn** | Required for SSE. WSGI (plain Gunicorn, `runserver`) won't stream the agent. Called out in the README so it isn't a hidden landmine. |
| Frontend | **React 18 + Vite** | Fastest path to a permission-aware dashboard with an SSE chat panel. Vite's proxy keeps dev and prod same-origin — no CORS to fight. |
| Orchestration | **Docker Compose (dev / prod split)** | Reproducibility, `.env.base` / `.env.dev` / `.env.prod` layering, `:z` bind mounts for Fedora Silverblue (safe on non-SELinux). |

### 4.1 Choices Worth Explaining

- **No ZenStack, no Next.js Server Actions.** Both are TypeScript-only and their main value is a security *invariant* we already get in Django. Copying their ergonomics without their ecosystem would have been cargo cult.
- **No separate Express / FastAPI tier.** The interesting boundary is the *authorization* boundary inside every data access, not the HTTP routing. A second API tier would have duplicated the policy surface without strengthening it.
- **No free-tier LLM aggregators.** Unreliable inference in a time-constrained assessment is a liability. A direct provider key is used.
- **No BullMQ / Redis queues.** Deferred — async jobs don't test the thesis (see §2).

---

## 5. How AI Coding Tools Were Used

The assessment asks how AI was used to produce production-minded code rather than unchecked boilerplate. Here's what actually happened.

### 5.1 Delegated to the AI

- Docker Compose base/override/prod files and the entrypoint wait-loop.
- Django project skeleton (`config/`, `core/`, `agent/`, `audit/`), `requirements.txt`, `Dockerfile`.
- Serializer and ViewSet boilerplate for standard DRF CRUD.
- React scaffolding (`pages/`, `components/`, `api/client.js`), CSS, theme toggle.
- Test file scaffolding — before every assertion was reviewed.

### 5.2 Refused to the AI

- **`core/services.py`.** Every function was written or rewritten by hand, because it's the security boundary. The AI's first drafts had the usual shortcut (`objects.filter(id=pid).first()`), which would have leaked data. Each was corrected to `objects.filter(id=pid, membership__user=user).first()` before review.
- **`IsPortfolioMember`.** The `has_object_permission` logic was reviewed line by line. The AI's draft used `request.user.portfolio_set`; replaced with `user_role_on_portfolio(user, portfolio_id)` so there's exactly one lookup path.
- **Agent tool signatures.** The AI's first `get_portfolio_summary` took `user_id: str` as an argument. Removed and replaced with `get_user(request)` injection. Any tool signature with identity as a parameter is a red flag.
- **`agent/urls.py`'s `get_user`.** Confirmed it calls `JWTAuthentication().authenticate(request)`. An AI's first pass is often `request.user`, which is `AnonymousUser` under ASGI without explicit auth.

### 5.3 What the AI Got Wrong (and How It Was Caught)

1. **Middleware-as-authorization.** The AI initially proposed a middleware auth check. Rejected: middleware doesn't cover internal calls (including agent tools) and is bypassable (CVE-2025-29927 in Next.js; the same reasoning applies in Django). Moved the check to the data layer.
2. **`objects.all()` in a list view.** The first `PortfolioViewSet.get_queryset` used `Portfolio.objects.all()` and relied on permission classes. Rejected: list views must filter, not check. Replaced with a service call.
3. **`SynchronousOnlyOperation` in the audit logger.** The AI's first `DatabaseAuditLogger` called the ORM from an async context. Fixed by running the ORM write on a `threading.Thread` daemon. The README troubleshooting section documents the symptom.
4. **Tool signature accepting `user_id`.** Rejected as above.
5. **`get_user` returning `request.user`.** Rejected; replaced with an explicit `JWTAuthentication` call.

### 5.4 Where This Is Written Down

`AI_LOG.md` records what was delegated, what was refused, what went wrong, and how each issue was caught. The README troubleshooting section documents the two bugs whose symptoms a reviewer could realistically hit — the `SynchronousOnlyOperation` case and the `runserver` WSGI-for-SSE case — so the fix is discoverable from the error.

---

## 6. What the Tests Actually Prove

The test suite is the security proof, not just a regression net. About 80 tests across seven files:

| File | What It Proves |
|---|---|
| `core/tests/test_services.py` | Service-layer isolation: `get_portfolios_for_user(viewer)` returns only shared; `get_portfolio_for_user(viewer, owner_only_id)` returns `None`; `user_role_on_portfolio` returns the right role or `None`. |
| `core/tests/test_api.py` | DRF role matrix: Viewer gets 403/404 on Owner-Only portfolio, can't list it, can't write. |
| `core/tests/test_auth.py` | JWT issuance and refresh. |
| `core/tests/test_register.py` | Signup flow; new users land on an empty portfolio list. |
| `core/tests/test_membership.py` | Invite/remove rules: only Owner can invite; Owner can't be removed; role is checked at the service layer. |
| `agent/tests/test_tools.py` | **The security proof:** Viewer invokes the agent about the Owner-Only portfolio → tool returns access-denied; Owner → succeeds. Write tools: Viewer denied, Editor allowed. |
| `audit/tests/test_logger.py` | Audit log writes; failures don't break the tool call; log entries are readable from admin. |

The one to show in the video is in `agent/tests/test_tools.py`: the Viewer-denied-on-Owner-Only case. It's the only test in the suite that wouldn't exist in a normal agent demo, and it's the one that proves the thesis.

---

## 7. How It Was Delivered

The plan was executed in about 20 hours across Fri–Sun, with a buffer kept for overruns and the video. Each phase ended with a manual test and a code review before moving on. The written plan (this document) was drafted **first** — the assessment accepts a plan alone as a deliverable, so making the plan a first-class artifact (not a retrospective) was intentional.

| Phase | Deliverable | Time |
|---|---|---|
| 0 | Docker Compose skeleton — dev/prod split, env layering, Redis, Postgres, ASGI, `:z` bind mounts, `backend/` + `frontend/` placeholders, `core/services.py` stub, `agent/` stub, minimal README | 1 h |
| 1 | Domain models, migrations, admin registration, idempotent `seed_demo` | 2.5 h |
| 2 | JWT auth; `IsPortfolioMember`; `core/services.py` (the enforcement point); service-layer isolation tests | 3 h |
| 3 | CRUD APIs for Portfolio / Asset / Transaction / Membership; serializers reject foreign IDs; API role-matrix tests | 2 h |
| 4 | `django-ag-ui` mount; read tools; identity injection via `get_user`; agent security test (Viewer denied) | 3 h |
| 5 | Streaming chat panel; permission-aware dashboard; theme; tool-call indicator | 2 h |
| 6 | Write tools (`add_asset`, `log_transaction`) with role check + audit log | 1.5 h |
| 7 | Hardening: clean-machine test, README, `AI_LOG.md`, known-limitations section | 2 h |
| 8 | Video walkthrough (10–15 min) | 2 h |

The **anti-refactor promise** held: Phase 4 filled in `agent/agent_tools.py` and `agent/urls.py` but didn't touch `core/`; Phase 6 added functions to `core/services.py` and `agent/agent_tools.py` without rewriting Phase 3 or 4. Every phase built on the placeholders created in Phase 0.

---

## 8. What I'd Do Next

If there were another week, in priority order:

1. **Valuation sync.** A scheduled job (celery + Redis queue) pulling market prices for stocks and crypto, updating a `Valuation` model, and exposing `portfolio.total_value()` via the API and agent tools. Most user-visible missing feature, and the natural place for a background worker to earn its keep.
2. **Approval flow for destructive agent actions.** The agent has no delete tools by design; the natural next step is an agent-initiated `delete_asset` behind an approval card. `django-ag-ui`'s tool metadata (`destructive=True`, `confirm`) supports this without new infrastructure.
3. **Net-worth-over-time.** A read-only aggregate endpoint over transactions plus a lightweight chart. Data is already there; the missing piece is the aggregation.
4. **Realtime collaboration.** WebSocket presence and multi-client sync on the portfolio detail page. Requires a state-reconciliation design that would have eaten the schedule.
5. **Email invites with tokens.** A new `Invitation` model, token flow, mailer. Small scope creep from the current invite-by-username.
6. **Owner transfer.** An ownership handover flow. Deferred because it needs careful rules (e.g. can't demote the last owner) and a UI I chose not to build.

Each of these is genuinely useful and each was deliberately deferred to keep the thesis testable in the time budget.

---

## 9. In One Paragraph

The interesting question isn't "can I build a portfolio tracker?" It's **"can I build a system where an AI agent — non-deterministic and prompt-injectable — operates on multi-tenant financial data without ever violating the authorization model?"** The answer here is to push authorization into one data-access layer (`core/services.py`), inject identity server-side via `django-ag-ui`'s `get_user(request)`, and never treat the model's intent or a middleware check as a security boundary. The agent can be helpful, but it's structurally incapable of being privileged. If the permission model holds under the agent's access — which the tests and the demo show it does — the architecture is credible. Everything else (streaming UX, permission-aware UI, audit log) exists to make that visible and usable, not to substitute for it.