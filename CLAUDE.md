# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
python -m pip install -r requirements.txt
flask --app api/index.py run
```

Required environment variables:
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon/service key
- `SUPABASE_SECRET_API_KEY` — service role key used exclusively by the logger to bypass RLS
- `FLASK_SECRET_KEY` — session signing key (defaults to `dev-ui-secret-key` in dev)
- `APP_BASE_URL` — full base URL used for OAuth redirects (e.g. `http://localhost:5000`)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — only needed for Google Calendar OAuth

## Architecture

Flask server deployed to Vercel (`vercel.json` routes everything to `api/index.py`). The `app = calApp` alias at the bottom of `index.py` is required for Vercel to find the WSGI app.

There are two separate surfaces with different auth models:

**REST API** — routes defined directly in `api/index.py` (`/calendars`, `/events`, `/externals`, `/me`) and `api/auth_routes.py` (`/api/auth/register`, `/api/auth/login`). Protected by `@require_auth` in `utils/auth.py`, which validates a Bearer JWT against Supabase `/auth/v1/user` on every request. The authenticated user lands in `flask.g.user`.

**Server-rendered UI** — all routes under `/ui/`, split across `api/ui_routes/routes/` (one file per section: `auth`, `home`, `user`, `settings`, `admin`, `public`). Uses Flask sessions. `_ui_user()` reads the session; `@ui_login_required` and `@ui_admin_required` are the auth decorators. Templates in `api/templates/`, static files in `api/static/`.

## Supabase Clients

Two different clients are used depending on context:

- `get_supabase_client()` (`utils/supabase_client.py`) — unauthenticated client from env vars. Used by REST routes, models, and `public.py`.
- `_get_ui_supabase_client()` (`api/ui_routes/helpers.py`) — calls `get_supabase_client()` then calls `.postgrest.auth(token)` with the session user's access token. This scopes all queries to the logged-in user so Supabase RLS applies. Used by every authenticated UI route.

Never use `get_supabase_client()` directly in UI routes — always use `_get_ui_supabase_client()` so RLS is enforced.

## Database Tables

- `calendars` — `id`, `name`, `owner_id`, `member_ids` (array), `events` (array), `age_timestamp`, `guest_link_token`, `guest_link_role`, `guest_link_active`
- `events` — `id`, `title`, `description`, `owner_id`, `calendar_ids` (array), `start_timestamp`, `end_timestamp`
- `externals` — `id`, `user_id`, `provider`, `url`, `access_token`, `refresh_token`
- `logs` — written to by `logEvent()` using the service role key; columns match the kwargs of `logEvent()`

Array membership is queried with `.overlaps("member_ids", [uid])` or `.overlaps("calendar_ids", [ids])`. A user's calendars are fetched as two queries (owned + member) then merged with dedup, because PostgREST doesn't cleanly OR across column types.

## Models (`models/`)

Thin Python classes (`Calendar`, `Event`, `External`, `User`) with `save()` methods. Used only by the REST API routes in `index.py`. UI routes bypass models entirely and query Supabase directly.

## UI Route Helpers (`api/ui_routes/helpers.py`)

- `render_page(title, role, nav, template, **kwargs)` — wraps `render_template`, injects `ui_user`, `features_nav`, and `build_info` into every template via `_inject_globals()`
- `user_nav()` / `admin_nav()` / `guest_nav()` — nav link lists passed explicitly to `render_page`
- `features_nav()` — injected globally into every template; drives the hamburger menu (logged-in users see different links than guests)
- `_ui_user()` — returns session user dict or `None`
- `ui_login_required` / `ui_admin_required` — route decorators; admin version also checks `role == "admin"` and aborts 403
- `_resolve_app_base_url()` — resolves base URL from `APP_BASE_URL` env var or falls back to `request.url_root`

## Logging

`logEvent(level, eventType, message, ...)` in `utils/logger.py` writes to the `logs` Supabase table using the service role key (`SUPABASE_SECRET_API_KEY`). Called from `before_request`/`after_request` hooks in `index.py` for every HTTP request. Log failures are swallowed so they never crash a request.

## Google Calendar OAuth (Settings)

Full OAuth2 flow in `api/ui_routes/routes/settings.py`: Connect → Google login → callback stores tokens in `externals`. Sync pulls Google events into a local "Google Calendar (Synced)" calendar. Push exports local calendars to Google. Uses `requests_oauthlib`.

## Deployment

Vercel builds `api/index.py` as a Python serverless function. Push to any branch creates a preview deployment. The `main` branch is production.
