# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

---

## Bugs / Quick Fixes

_(none — all clear)_

---

## Incomplete Features

- [ ] **Deduplicate synced calendars**
  Both Google and Outlook sync currently append events on every pull. Re-syncing creates duplicates. The pull should clear existing events in the "(Synced)" calendar before inserting fresh ones.

- [ ] **Admin — Unlink External Calendars page uses placeholder data**
  `/admin/unlink` in `ui_routes/routes/admin.py` passes a hardcoded `placeholder_externals` list to the template instead of fetching real provider data from the database.

---

## Incomplete Features (continued)

- [ ] **Live syncing of external calendars**
  Currently sync is manual (user clicks Pull). Add background or webhook-based syncing so external calendar changes are reflected automatically without user action.

---

## Architecture / Cleanup

- [ ] **Separate API and UI route responsibilities clearly**
  Architecture direction: the website uses UI routes exclusively (session cookie auth, no Bearer token). The REST API is reserved for live syncing — webhook receivers from Google/Outlook that arrive with no user session.

- [ ] **Add structured JSON error responses to UI JSON endpoints**
  The UI JSON routes in `ui_routes/routes/user.py` currently return plain HTTP status codes on failure (400/403/404). Templates show generic `alert()` messages. Upgrade to return `{"error": "descriptive message"}` so the JS can surface meaningful errors to the user.
