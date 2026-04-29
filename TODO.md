# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

---

## UI / UX

- [ ] **Format timestamps in local timezone across all user pages**
  Event start/end times are displayed as raw UTC timestamp strings in several places (e.g. manage events). Replace with human-readable local-timezone formatting throughout all user-facing UI.
  - **Plan:** Do it in JavaScript so the browser's local timezone is used. In the base template add a `<script>` that finds every `<span class="local-time" data-utc="...">` and replaces its text with `new Date(el.dataset.utc).toLocaleString()`. Then in every template that prints a raw timestamp (grep `start_timestamp` and `end_timestamp` across `api/templates/`), wrap the output: `<span class="local-time" data-utc="{{ event.start_timestamp }}">{{ event.start_timestamp }}</span>`. The raw value is the fallback if JS is off.

- [ ] **Add "Copy Link" button for guest/shareable calendar links**
  Add a clipboard copy button next to the shareable URL on each calendar card so users don't have to manually select and copy it.
  - **Plan:** In `api/templates/user/calendars.html` around line 100, give the link element an `id="link-{{ cal.id }}"` and add `<button onclick="copyLink('{{ cal.id }}')">Copy</button>` next to it. In a `<script>` define `function copyLink(id) { navigator.clipboard.writeText(document.getElementById('link-' + id).innerText); }`.

- [ ] **Consolidate guest link controls onto one line**
  Move the "Rotate", "Revoke", and Viewer/Editor dropdown onto a single line at the bottom of the calendar card. Drop the word "Link" from both button labels.
  - **Plan:** In `api/templates/user/calendars.html` lines 107–117, wrap the role `<select>`, the Generate/Rotate `<button>`, and the Revoke `<button>` in a single `<div style="display:flex; gap:8px; align-items:center;">`. Change the button text from "Rotate Link" to "Rotate" and "Revoke Link" to "Revoke".

- [ ] **Add member from existing calendar card**
  Add an "Add Member" input directly on existing calendar cards in the manage calendars page so members can be added without leaving the card.
  - **Plan:** In `api/templates/user/calendars.html` Members tab (around line 119), add `<input type="text" id="add-member-{{ cal.id }}">` and `<button onclick="addMember('{{ cal.id }}')">Add</button>`. Write `addMember(calId)` in JS that reads the input and POSTs to a new UI endpoint `/ui/calendars/<id>/members` with body `{ "member": value }`. In `api/ui_routes/routes/user.py` add the route handler that calls the existing `Calendar.add_member()` method.

- [ ] **Add members by email or userId everywhere**
  Members should be addable by email or userId on both the "Create a new calendar" form and existing calendar cards.
  - **Plan:** Add a helper `resolve_member_id(value)` in `api/ui_routes/helpers.py`:
    ```python
    def resolve_member_id(value):
        db = get_supabase_client()
        if "@" in value:
            result = db.table("users").select("id").eq("email", value).limit(1).execute()
            if result.data:
                return result.data[0]["id"]
            return None
        return value
    ```
    Call it from the "Create a new calendar" POST handler and from the new add-member handler in item 6 before invoking the model.

- [ ] **Add friend by email, display name, or userId**
  Update the friends feature so users can search/add friends by any of: email, display name, or userId — not just one identifier type.
  - **Plan:** In `models/user.py` `addFriend()` (lines 79–90), replace the email-only branch with three sequential lookups:
    ```python
    if friendId is None:
        db = get_supabase_client()
        r = db.table("users").select("id").eq("email", value).limit(1).execute()
        if r.data:
            friendId = r.data[0]["id"]
        else:
            r = db.table("users").select("id").eq("display_name", value).limit(1).execute()
            if r.data:
                friendId = r.data[0]["id"]
            else:
                friendId = value
    ```
    Update the friends template input placeholder to "email, display name, or user ID".

---

## Incomplete Features

- [ ] **Deduplicate synced calendars**
  Both Google and Outlook sync currently append events on every pull. Re-syncing creates duplicates. The pull should clear existing events in the "(Synced)" calendar before inserting fresh ones.
  - **Plan:** In `models/external.py`, after the synced calendar id is found/created and BEFORE `db.table("events").insert(rows).execute()`, delete the old events:
    ```python
    db.table("events").delete().contains("calendar_ids", [calId]).execute()
    ```
    Apply this in both the Google branch (around lines 121–144) and the Outlook branch (around lines 173–196). Also reset the synced calendar's `events` list to `[]` and then refill it with the new ids (ties into item 1).

- [ ] **Admin — Unlink External Calendars page uses placeholder data**
  `/admin/unlink` in `ui_routes/routes/admin.py` passes a hardcoded `placeholder_externals` list to the template instead of fetching real provider data from the database.
  - **Plan:** Delete the `placeholder_externals = ["Google Calendar", "Outlook Calendar"]` constant in `api/ui_routes/helpers.py:44`. In `admin_unlink()` (`api/ui_routes/routes/admin.py:107`), fetch real rows: `db.table("externals").select("id, provider, user_id, url").execute()`. Pass them as `externals=result.data or []`. Update `api/templates/admin/unlink.html` to loop over `externals` and render provider, user_id, and a delete button per row.

- [ ] **Live syncing of external calendars**
  Currently sync is manual (user clicks Pull). Add background or webhook-based syncing so external calendar changes are reflected automatically without user action.
  - **Plan (webhooks):** Webhooks mean Google/Outlook call OUR server when a user's calendar changes — instead of us polling them. We register a "subscription" per user; they POST to our endpoint on change.
    1. Public URL required — webhooks need HTTPS. Use the deployed Vercel URL. Local dev needs a tunnel like ngrok. Document this.
    2. Schema — add columns to `externals`: `subscription_id TEXT`, `subscription_expires TIMESTAMP`, `resource_id TEXT` (Google only).
    3. Google: after OAuth link, POST to `https://www.googleapis.com/calendar/v3/calendars/primary/events/watch` with body `{"id": "<uuid>", "type": "web_hook", "address": "https://<domain>/api/webhooks/google", "token": "<externals.id>"}`. Save returned `id`, `resourceId`, `expiration`.
    4. Outlook: POST to `https://graph.microsoft.com/v1.0/subscriptions` with body `{"changeType": "created,updated,deleted", "notificationUrl": "https://<domain>/api/webhooks/outlook", "resource": "me/events", "expirationDateTime": "<now+3 days ISO>", "clientState": "<externals.id>"}`. Microsoft sends a one-time validation request; our endpoint must echo `validationToken` query param as `text/plain` within 10 seconds.
    5. Receivers in `api/api_routes/`:
       - `POST /api/webhooks/google` — read `X-Goog-Channel-Token` header (it's our externals.id), look up the External, call `ext.pullCalData()`, return 200.
       - `POST /api/webhooks/outlook` — if `?validationToken=...` exists, return it as plain text. Else parse JSON body, read `value[0].clientState`, look up External, call `pullCalData()`, return 202.
    6. Renewal — subscriptions expire. Add a daily job (Vercel cron, or a background `threading.Thread` with `time.sleep(86400)`) that re-registers any subscription expiring within 24 hours.
    7. Depends on item 9 (dedup), or each webhook will duplicate every event.
    8. On unlink — call Google `channels.stop` (needs `id` + `resourceId`) or Outlook `DELETE /subscriptions/{id}` before deleting the row.

---

## Architecture / Cleanup

- [ ] **Refactor admin role to `is_admin` column on `users` table**
  Replace the current manual `app_metadata` edit in Supabase with a dedicated `is_admin` boolean column. Update `@ui_admin_required` and the session user dict (set at login in `auth.py`) to read from this column. Add an admin UI action to promote/demote users so it no longer requires direct DB access.
  - **Plan:**
    1. SQL migration (run manually in Supabase): `ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT false;`
    2. In the login flow (`auth.py` near line 73 where `session["ui_user"]` is built), after fetching the user row do `db.table("users").select("is_admin").eq("id", uid).limit(1).execute()` and set `session["ui_user"]["is_admin"] = bool(result.data[0]["is_admin"]) if result.data else False`.
    3. In `api/ui_routes/helpers.py` `@ui_admin_required` (line 93), change the check from `usr.get("role") != "admin"` to `not usr.get("is_admin")`.
    4. Add admin route `/admin/users/<id>/toggle-admin` that calls `db.table("users").update({"is_admin": True}).eq("id", id).execute()` (or `False`).
    5. Add an admin template/page that lists users with a toggle button.

- [ ] **Separate API and UI route responsibilities clearly**
  Architecture direction: the website uses UI routes exclusively (session cookie auth, no Bearer token). The REST API is reserved for live syncing — webhook receivers from Google/Outlook that arrive with no user session.
  - **Plan:**
    1. Audit `api/api_routes/` — list every endpoint.
    2. For each endpoint that is only called from a UI template (search templates for fetch URLs), move the handler into `api/ui_routes/`.
    3. Leave only webhook receivers (`/api/webhooks/google`, `/api/webhooks/outlook`) under `/api`.
    4. Add a one-line comment at the top of `api/api_routes/__init__.py`: `# REST API: webhook receivers only — UI uses session auth via ui_routes`.

- [ ] **Add structured JSON error responses to UI JSON endpoints**
  The UI JSON routes in `ui_routes/routes/user.py` currently return plain HTTP status codes on failure (400/403/404). Templates show generic `alert()` messages. Upgrade to return `{"error": "descriptive message"}` so the JS can surface meaningful errors to the user.
  - **Plan:** In `api/ui_routes/routes/user.py`, replace each `abort(400)` / `abort(403)` / `abort(404)` in JSON-returning handlers with:
    ```python
    return jsonify({"error": "descriptive message here"}), 400
    ```
    Add `from flask import jsonify` if not already imported. Then in the templates that call these endpoints, update the `.catch(...)` blocks to parse the response body as JSON and show `data.error` in the alert instead of a generic message.

- [ ] **Remove `email` from `User.__init__`**
  `self.email` is stored but never read on any `User` instance. Drop the param and update both call sites: `api/api_routes/helpers.py:9` and `api/ui_routes/helpers.py:276`.
  - **Plan:** In `models/user.py` lines 10–13, delete the `email` parameter and the `self.email = email` line. Update the two call sites to drop `email=...`. Before doing so, grep the repo for `self.email` and `User(.*email=` to confirm nothing else reads it.

- [ ] **`_refresh_access_token` should call `updateTokens` instead of writing inline**
  In `models/external.py` around line 91, the method writes to the DB directly. It should call `updateTokens` to consolidate token persistence into one place.
  - **Plan:** In `models/external.py` `_refresh_access_token` (~line 91), find the inline `db.table("externals").update({...}).eq("id", ...).execute()` call and replace it with `self.updateTokens(new_access_token, new_refresh_token)`. If `updateTokens`'s current signature does not accept those two args, adjust it minimally so it does.

- [ ] **Refactor `External.__init__` to minimal params**
  Keep only `id`, `supabaseClient`, and `userId` as instance variables. Move `url`, `provider`, `accessToken`, and `refreshToken` into `save()` as parameters — `pullCalData`/`pushCalData` already re-fetch them from the DB and never touch instance fields.
  - **Plan:**
    1. Change `External.__init__` (`models/external.py:7–23`) to accept only `id`, `supabaseClient`, `userId`. Set those three on `self`. Drop the others.
    2. Change `save()` to accept `url`, `provider`, `accessToken`, `refreshToken` as parameters and use them instead of `self.*`.
    3. Update every `External(...)` call site (~11 sites in `api/ui_routes/routes/settings.py` and `api/api_routes/routes/external.py`) to use the new signature.
    4. For call sites that previously created an External then called `save()`, now they call `External(id=..., supabaseClient=..., userId=...).save(url=..., provider=..., accessToken=..., refreshToken=...)`.
