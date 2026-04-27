# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

---

## Bugs / Quick Fixes

- [x] **Settings page — Pull/Push buttons should use UI routes**
  The Pull and Push buttons currently call the API routes (`/externals/<id>/pull`, `/externals/<id>/push`), which require a Bearer token. The website should use the existing UI routes (`/settings/external/google/<id>/sync` and `/settings/external/google/<id>/push`) instead, since those use the session and are simpler. The API routes are meant for external callers, not the website itself.

---

## Incomplete Features

- [x] **Outlook sync (pull)**
  Implemented: OAuth redirect flow via `/ui/settings/external/azure/login` → `/ui/settings/external/azure/callback`, events fetched from Graph API with plain-text body, stored in "Outlook Calendar (Synced)".

- [x] **Outlook sync (push)**
  Implemented: local events (excluding the synced calendar) pushed to `POST /me/events` on the Graph API.

- [ ] **Deduplicate synced calendars**
  Both Google and Outlook sync currently append events on every pull. Re-syncing creates duplicates. The pull should clear existing events in the "(Synced)" calendar before inserting fresh ones.

- [ ] **Admin — Unlink External Calendars page uses placeholder data**
  `/admin/unlink` in `ui_routes/routes/admin.py` passes a hardcoded `placeholder_externals` list to the template instead of fetching real provider data from the database.

- [ ] **Public calendar/event views use placeholder data**
  The `/calendars` and `/events` routes in `ui_routes/routes/home.py` render placeholder data instead of real records. These pages need to be wired up to the actual database.

---

## Incomplete Features (continued)

- [ ] **Live syncing of external calendars**
  Currently sync is manual (user clicks Pull). Add background or webhook-based syncing so external calendar changes are reflected automatically without user action.

---

## Architecture / Cleanup

- [ ] **Separate API and UI route responsibilities clearly**
  Architecture direction: the website uses UI routes exclusively (session cookie auth, no Bearer token). The REST API is reserved for live syncing — webhook receivers from Google/Outlook that arrive with no user session.

- [x] **Convert internal AJAX calls from REST API to UI routes**
  The following pages use `fetch` with a Bearer token against the REST API, but should instead call JSON-returning UI routes (session cookie auth, no token needed). Each UI route calls the model directly, same as the REST route does today.
  - `home/calendar.html` — `POST /events`, `GET /events/<id>`, `DELETE /events/<id>`
  - `user/events.html` — `POST /events`, `DELETE /events/<id>`
  - `user/events_edit.html` — `PUT /events/<id>`
  - `user/calendars.html` — `POST /calendars`, `DELETE /calendars/<id>`, `POST/DELETE /calendars/<id>/guest-link`
  - `user/friends.html` — `POST /friends`, `DELETE /friends/<id>`
  - `user/remove_account.html` — `DELETE /me`
  - `settings/auth.html` — `DELETE /externals/<id>` (Disconnect button)
  New UI routes should live under `/ui/user/...`, accept JSON bodies where needed, and return JSON responses. JS callers drop the `getToken()` dance and use plain `fetch` with no `Authorization` header.

- [ ] **Add structured JSON error responses to UI JSON endpoints**
  The UI JSON routes in `ui_routes/routes/user.py` currently return plain HTTP status codes on failure (400/403/404). Templates show generic `alert()` messages. Upgrade to return `{"error": "descriptive message"}` so the JS can surface meaningful errors to the user.
