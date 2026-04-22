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
- `FLASK_SECRET_KEY` — session signing key (defaults to `dev-ui-secret-key` in dev)
- `APP_BASE_URL` — full base URL used for OAuth redirects (e.g. `http://localhost:5000`)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — only needed for Google Calendar OAuth

## Architecture

The app is a Flask server deployed to Vercel (`vercel.json` routes everything to `api/index.py`).

There are two separate surface areas with different auth models:

**REST API** — routes defined directly in `api/index.py` (`/calendars`, `/events`, `/externals`, `/me`) plus `api/auth_routes.py` (`/api/auth/register`, `/api/auth/login`). Protected by `@require_auth` in `utils/auth.py`, which validates a Bearer JWT by calling Supabase `/auth/v1/user` on every request. The authenticated user is stored in `flask.g.user`.

**Server-rendered UI** — all routes under `/ui/`, defined in `api/ui_routes/routes/` (one file per section: `auth`, `home`, `user`, `settings`, `admin`, `public`). Uses Flask sessions for auth. `_ui_user()` in helpers reads the session; `@ui_login_required` is the decorator equivalent of `@require_auth`. Templates live in `api/templates/`, static files in `api/static/`.

## Supabase Client vs UI Client

`get_supabase_client()` (`utils/supabase_client.py`) — creates a Supabase client from env vars. Used directly by REST routes, models, and `public.py`.

`_get_ui_supabase_client()` (`api/ui_routes/helpers.py`) — calls `get_supabase_client()` then calls `.postgrest.auth(token)` with the session user's access token before returning it. This scopes the client to the logged-in user so Supabase row-level security applies. Used by all authenticated UI routes.

## Database Tables

- `calendars` — `id`, `name`, `owner_id`, `member_ids` (array), `events` (array), `age_timestamp`, `guest_link_token`, `guest_link_role`, `guest_link_active`
- `events` — `id`, `title`, `description`, `owner_id`, `calendar_ids` (array), `start_timestamp`, `end_timestamp`
- `externals` — `id`, `user_id`, `provider`, `url`, `access_token`, `refresh_token`

Events and calendars use Postgres array overlap queries (`.overlaps("calendar_ids", [...])`) to find records belonging to a user.

## Models

`models/` contains thin Python classes (`Calendar`, `Event`, `External`, `User`) with `save()` methods that call `get_supabase_client()`. They are used by the REST API in `index.py` but largely bypassed by the UI routes, which query Supabase directly.

## UI Route Helpers (`api/ui_routes/helpers.py`)

- `render_page(title, role, nav, template, **kwargs)` — wraps `render_template`, injects nav, role, build info
- `user_nav()` / `admin_nav()` / `guest_nav()` — return nav link lists for each role
- `_ui_user()` — returns the session user dict or `None`
- `ui_login_required` — decorator that redirects to `/ui/login` if no session
- `_resolve_app_base_url()` — resolves base URL from env or request context
- `_google_oauth_config()` — returns `(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)` from env

## Google Calendar OAuth (Settings)

The full OAuth2 flow lives in `api/ui_routes/routes/settings.py`. Connect → login → callback stores tokens in `externals`. Sync pulls Google events into a "Google Calendar (Synced)" calendar. Push exports local calendars to Google. The `requests_oauthlib` package handles the OAuth session.

## Deployment

Vercel builds `api/index.py` as a Python serverless function and routes all traffic to it. The `app` alias at the bottom of `index.py` (`app = calApp`) is required for Vercel to find the WSGI app.
