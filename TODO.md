# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

---

## Bugs / Quick Fixes

- [x] **Cascade delete orphaned events when a calendar is removed**
  When a calendar is deleted, any event whose `calendar_ids` contained that calendar should have it removed from the list. If the resulting `calendar_ids` is empty, the event has no remaining calendar and should be deleted entirely.
  - **Plan:** In `models/calendar.py` `remove()` (line 39), before the calendar row is deleted:
    1. `db = get_supabase_client()`
    2. Fetch every event linked to this calendar: `result = db.table("events").select("id, calendar_ids").contains("calendar_ids", [self.id]).execute()`
    3. Loop over `result.data or []`. For each event, build `remaining = [c for c in (row.get("calendar_ids") or []) if c != self.id]`.
    4. If `remaining` is empty: `db.table("events").delete().eq("id", row["id"]).execute()`.
    5. Otherwise: `db.table("events").update({"calendar_ids": remaining}).eq("id", row["id"]).execute()`.
    6. Then run the existing `db.table("calendars").delete().eq("id", self.id).execute()`.
    Keep it as plain loops — no comprehensions beyond the simple filter above. This complements item 1 (event-count sync): the calendar row is gone, so its `events` list doesn't need cleanup.

---

## UI / UX

- [x] **Format timestamps in local timezone across all user pages**
  Event start/end times are displayed as raw UTC timestamp strings in several places (e.g. manage events). Replace with human-readable local-timezone formatting throughout all user-facing UI.
  - **Plan:** Do it in JavaScript so the browser's local timezone is used. In the base template add a `<script>` that finds every `<span class="local-time" data-utc="...">` and replaces its text with `new Date(el.dataset.utc).toLocaleString()`. Then in every template that prints a raw timestamp (grep `start_timestamp` and `end_timestamp` across `api/templates/`), wrap the output: `<span class="local-time" data-utc="{{ event.start_timestamp }}">{{ event.start_timestamp }}</span>`. The raw value is the fallback if JS is off.

- [x] **Add "Copy Link" button for guest/shareable calendar links**
  Add a clipboard copy button next to the shareable URL on each calendar card so users don't have to manually select and copy it.
  - **Plan:** In `api/templates/user/calendars.html` around line 100, give the link element an `id="link-{{ cal.id }}"` and add `<button onclick="copyLink('{{ cal.id }}')">Copy</button>` next to it. In a `<script>` define `function copyLink(id) { navigator.clipboard.writeText(document.getElementById('link-' + id).innerText); }`.

- [x] **Consolidate guest link controls onto one line**
  Move the "Rotate", "Revoke", and Viewer/Editor dropdown onto a single line at the bottom of the calendar card. Drop the word "Link" from both button labels.
  - **Plan:** In `api/templates/user/calendars.html` lines 107–117, wrap the role `<select>`, the Generate/Rotate `<button>`, and the Revoke `<button>` in a single `<div style="display:flex; gap:8px; align-items:center;">`. Change the button text from "Rotate Link" to "Rotate" and "Revoke Link" to "Revoke".

- [x] **Add member from existing calendar card**
  Add an "Add Member" input directly on existing calendar cards in the manage calendars page so members can be added without leaving the card.
  - **Plan:** In `api/templates/user/calendars.html` Members tab (around line 119), add `<input type="text" id="add-member-{{ cal.id }}">` and `<button onclick="addMember('{{ cal.id }}')">Add</button>`. Write `addMember(calId)` in JS that reads the input and POSTs to a new UI endpoint `/ui/calendars/<id>/members` with body `{ "member": value }`. In `api/ui_routes/routes/user.py` add the route handler that calls the existing `Calendar.add_member()` method.

- [x] **Add members by email or userId everywhere**
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

- [x] **Add friend by email, display name, or userId**
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

- [x] **Deduplicate synced calendars**
  Both Google and Outlook sync currently append events on every pull. Re-syncing creates duplicates. The pull should clear existing events in the "(Synced)" calendar before inserting fresh ones.
  - **Plan:** In `models/external.py`, after the synced calendar id is found/created and BEFORE `db.table("events").insert(rows).execute()`, delete the old events:
    ```python
    db.table("events").delete().contains("calendar_ids", [calId]).execute()
    ```
    Apply this in both the Google branch (around lines 121–144) and the Outlook branch (around lines 173–196). Also reset the synced calendar's `events` list to `[]` and then refill it with the new ids (ties into item 1).

- [x] **Admin — Unlink External Calendars page uses placeholder data**
  `/admin/unlink` in `ui_routes/routes/admin.py` passes a hardcoded `placeholder_externals` list to the template instead of fetching real provider data from the database.
  - **Plan:** Delete the `placeholder_externals = ["Google Calendar", "Outlook Calendar"]` constant in `api/ui_routes/helpers.py:44`. In `admin_unlink()` (`api/ui_routes/routes/admin.py:107`), fetch real rows: `db.table("externals").select("id, provider, user_id, url").execute()`. Pass them as `externals=result.data or []`. Update `api/templates/admin/unlink.html` to loop over `externals` and render provider, user_id, and a delete button per row.

- [x] **Live syncing of external calendars** *(do third — depends on the API/UI separation below)*
  Currently sync is manual (user clicks Pull). Add webhook-based syncing so external calendar changes are reflected automatically without user action.
  - **How webhooks work:** Instead of our server polling Google/Outlook on a timer, we register a "subscription" with them at OAuth-link time. When something changes for that user, their server POSTs to our endpoint. We look up which user it is from a token we passed at registration, then run the existing `pullCalData()` flow.
  - **Prerequisites:**
    - Public HTTPS URL — webhooks won't reach localhost. Use the Vercel deployment for testing, or a tunnel (ngrok) for local dev. Document this in README.
    - Item 9 (dedup) is already done — without it, every webhook would duplicate every event.
    - The API/UI separation item below should land first to give us a clean `/api` namespace.
  - **Plan:**
    1. **Schema migration** (run manually in Supabase):
       ```sql
       ALTER TABLE externals
         ADD COLUMN subscription_id TEXT,
         ADD COLUMN subscription_expires TIMESTAMPTZ,
         ADD COLUMN resource_id TEXT;
       ```
    2. **Register a subscription on OAuth link.** In `api/ui_routes/routes/settings.py`, after the new External row is saved:
       - **Google** — POST `https://www.googleapis.com/calendar/v3/calendars/primary/events/watch` with body `{"id": "<random uuid>", "type": "web_hook", "address": "https://<APP_BASE_URL>/api/webhooks/google", "token": "<externals.id>"}`. Save the returned `id`, `resourceId`, `expiration` into the new columns. (Expiration comes back as Unix ms — convert to ISO before storing.)
       - **Outlook** — POST `https://graph.microsoft.com/v1.0/subscriptions` with `{"changeType": "created,updated,deleted", "notificationUrl": "https://<APP_BASE_URL>/api/webhooks/outlook", "resource": "me/events", "expirationDateTime": "<now+3 days ISO>", "clientState": "<externals.id>"}`. Microsoft pings the URL once with `?validationToken=...` during this call — the receiver below handles that.
    3. **Add webhook receivers** in a new file `api/api_routes/routes/webhooks.py`. Both routes use `@api_bp` and have NO `@require_auth` — they have no user session. They identify the user via the `clientState` / `X-Goog-Channel-Token` we set at registration.
       - `POST /api/webhooks/google` — read header `X-Goog-Channel-Token` → that's `externals.id`. Look up the row, instantiate the External, call `pullCalData()`. Return 200.
       - `POST /api/webhooks/outlook` — if `request.args.get("validationToken")` is set, return it as `text/plain` with status 200 (validation handshake — must finish in <10s). Otherwise parse `request.json["value"][0]["clientState"]` → `externals.id`, same flow as Google, return 202.
       Wrap both in try/except and `logEvent("ERROR", ...)` on failure — Google retries non-2xx and we don't want a flood.
    4. **Daily renewal job.** Subscriptions expire (Google ~7 days, Outlook 3 days max). Add `utils/renew_subscriptions.py` that finds any external where `subscription_expires < now() + 24 hours` and re-registers it. Trigger via Vercel Cron (preferred) by adding to `vercel.json`:
       ```json
       "crons": [{ "path": "/api/cron/renew-subscriptions", "schedule": "0 3 * * *" }]
       ```
       Protect that route with a shared-secret header check.
    5. **Cleanup on unlink.** In `models/external.py` `remove()`, BEFORE deleting the row:
       - **Google** — POST `https://www.googleapis.com/calendar/v3/channels/stop` with `{"id": subscription_id, "resourceId": resource_id}`.
       - **Outlook** — `DELETE https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}`.
       Swallow errors but log them — local row deletion shouldn't depend on this.
  - **Risks to watch for:**
    - Vercel cold starts vs. Microsoft's 10s validation timeout — test from a cold state.
    - Don't add CSRF/auth middleware to webhook receivers; they must be public.
    - Spread renewal expirations with jitter to avoid thundering-herd renewals on one day.

---

## Architecture / Cleanup

- [x] **Refactor admin role to `is_admin` column on `users` table**
  Replace the current manual `app_metadata` edit in Supabase with a dedicated `is_admin` boolean column. Update `@ui_admin_required` and the session user dict (set at login in `auth.py`) to read from this column. Add an admin UI action to promote/demote users so it no longer requires direct DB access.
  - **Plan:**
    1. SQL migration (run manually in Supabase): `ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT false;`
    2. In the login flow (`auth.py` near line 73 where `session["ui_user"]` is built), after fetching the user row do `db.table("users").select("is_admin").eq("id", uid).limit(1).execute()` and set `session["ui_user"]["is_admin"] = bool(result.data[0]["is_admin"]) if result.data else False`.
    3. In `api/ui_routes/helpers.py` `@ui_admin_required` (line 93), change the check from `usr.get("role") != "admin"` to `not usr.get("is_admin")`.
    4. Add admin route `/admin/users/<id>/toggle-admin` that calls `db.table("users").update({"is_admin": True}).eq("id", id).execute()` (or `False`).
    5. Add an admin template/page that lists users with a toggle button.

- [x] **Separate API and UI route responsibilities clearly** *(do second — sets up clean namespace for webhooks)*
  Architecture direction: the website uses UI routes exclusively (session cookie auth). The REST API is reserved for webhook receivers from Google/Outlook that arrive with no user session.
  - **Audit (done 2026-04-29):** Every endpoint currently in `api/api_routes/routes/{user,calendar,event,external}.py` is dead code — templates already call `/ui/...` equivalents instead. Only `api_routes/routes/guest.py` is actually wired up to a template (`templates/guest/calendar.html` calls `/guest/<token>/events*`).
  - **Plan:**
    1. **Delete the dead route files:** `api/api_routes/routes/user.py`, `calendar.py`, `event.py`, `external.py`. Remove their imports from `api/api_routes/__init__.py`.
    2. **Move guest endpoints out of `api_routes`.** They aren't session-authed UI calls, but they aren't webhook receivers either. The cleanest home is a new `api/ui_routes/routes/guest_api.py` (using `@ui_bp`) — but `ui_bp` is mounted at `/ui` while templates call `/guest/...` directly, so either: (a) keep them under `api_bp` and document them as legacy; or (b) override the route prefix on those handlers. Pick (a) for now — it's less invasive.
    3. **Audit `api/api_routes/helpers.py`.** `makeUser()` is the only export; if no remaining route imports it after step 1, delete the file.
    4. **Add header comment** at the top of `api/api_routes/__init__.py`:
       ```python
       # REST API: webhook receivers + guest token endpoints only.
       # UI uses session auth via ui_routes — DO NOT add UI handlers here.
       ```
    5. **Update CLAUDE.md** "Blueprint layout" section to reflect the new convention.
  - **Verification:** Grep templates for `fetch(` and confirm every URL still resolves. Manually exercise: login → list/create/edit/delete events and calendars, friends add/remove, account remove, guest event edit.
  - **Side effect:** `@require_auth` and `makeUser()` may become unused after the deletions. Leave `require_auth` in `utils/auth.py` (webhooks won't use it but future API work might); delete `makeUser` only if confirmed unused.

- [x] **Add structured JSON error responses to UI JSON endpoints**
  The UI JSON routes in `ui_routes/routes/user.py` currently return plain HTTP status codes on failure (400/403/404). Templates show generic `alert()` messages. Upgrade to return `{"error": "descriptive message"}` so the JS can surface meaningful errors to the user.
  - **Plan:** In `api/ui_routes/routes/user.py`, replace each `abort(400)` / `abort(403)` / `abort(404)` in JSON-returning handlers with:
    ```python
    return jsonify({"error": "descriptive message here"}), 400
    ```
    Add `from flask import jsonify` if not already imported. Then in the templates that call these endpoints, update the `.catch(...)` blocks to parse the response body as JSON and show `data.error` in the alert instead of a generic message.

- [x] **Remove `email` from `User.__init__`**
  `self.email` is stored but never read on any `User` instance. Drop the param and update both call sites: `api/api_routes/helpers.py:9` and `api/ui_routes/helpers.py:276`.
  - **Plan:** In `models/user.py` lines 10–13, delete the `email` parameter and the `self.email = email` line. Update the two call sites to drop `email=...`. Before doing so, grep the repo for `self.email` and `User(.*email=` to confirm nothing else reads it.

- [x] **`_refresh_access_token` should call `updateTokens` instead of writing inline**
  In `models/external.py` around line 91, the method writes to the DB directly. It should call `updateTokens` to consolidate token persistence into one place.
  - **Plan:** In `models/external.py` `_refresh_access_token` (~line 91), find the inline `db.table("externals").update({...}).eq("id", ...).execute()` call and replace it with `self.updateTokens(new_access_token, new_refresh_token)`. If `updateTokens`'s current signature does not accept those two args, adjust it minimally so it does.

- [x] **Refactor `External.__init__` to minimal params** *(do first — easy and unblocks tighter changes in items above)*
  Keep only `id`, `supabaseClient`, and `userId` as instance variables. Move `url`, `provider`, `accessToken`, and `refreshToken` into `save()` as parameters — `pullCalData`/`pushCalData`/`remove`/`updateTokens` already re-fetch them from the DB and never touch instance fields.
  - **Call sites (audited 2026-04-29):** 13 total
    - `api/ui_routes/routes/settings.py` lines 138, 145, 168, 186, 273, 280, 303, 321
    - `api/ui_routes/routes/user.py` line 344
    - `api/api_routes/routes/external.py` lines 42, 60, 83, 106 (these will be deleted by the API/UI separation item — refactor what's left after that lands, OR refactor first and accept the duplicated work)
  - **Plan:**
    1. **Update the model** in `models/external.py`:
       - Change `__init__(self, id, url, provider, supabaseClient, userId=None, accessToken=None, refreshToken=None)` to `__init__(self, id, supabaseClient, userId)`. Set those three on `self`.
       - Inline the `to_record()` body into `save()` and delete `to_record()` — only `save()` uses it.
       - Change `save(self)` to `save(self, url, provider, accessToken=None, refreshToken=None)`. Build the insert dict from those parameters plus `self.userId`.
    2. **Update the two `save()` call sites** (`settings.py` lines 138 & 145 for Google, 273 & 280 for Outlook):
       ```python
       External(id=..., supabaseClient=db, userId=uid).save(
           url=provider_url, provider="google",
           accessToken=..., refreshToken=...,
       )
       ```
       Note: lines 138 and 273 pass `id=existing["id"]`, which suggests upsert semantics. Verify whether `save()` is doing `insert()` (will fail on existing id) or upsert. If upsert is needed, expose it as a separate method rather than overloading `save()`.
    3. **Update the no-data call sites** (`settings.py` lines 168, 186, 303, 321 and `user.py:344`): these only construct an External to call `pullCalData()` / `pushCalData()` / `remove()`. Just drop the `url=""`, `provider=""` args:
       ```python
       ext = External(id=external_id, supabaseClient=db, userId=uid)
       ```
    4. **Verify:** `grep -rn "External(" api/ models/` — every call should match the new signature. Manually test connect / disconnect / pull / push from the settings page.
