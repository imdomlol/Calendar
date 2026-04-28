# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

---

## Bugs / Quick Fixes

- [ ] **Fix manage calendars — event count always shows 0**
  Calendar cards always display "0 event(s) linked" regardless of actual event count. Wire the count up to the real `events` array length from the DB row.

- [ ] **Default event create form times to now / now+1hr**
  On the manage events page, default start datetime to now and end datetime to 1 hour from now when the create form opens.

---

## UI / UX

- [ ] **Format timestamps in local timezone across all user pages**
  Event start/end times are displayed as raw UTC timestamp strings in several places (e.g. manage events). Replace with human-readable local-timezone formatting throughout all user-facing UI.

- [ ] **Add "Copy Link" button for guest/shareable calendar links**
  Add a clipboard copy button next to the shareable URL on each calendar card so users don't have to manually select and copy it.

- [ ] **Consolidate guest link controls onto one line**
  Move the "Rotate", "Revoke", and Viewer/Editor dropdown onto a single line at the bottom of the calendar card. Drop the word "Link" from both button labels.

- [ ] **Add member from existing calendar card**
  Add an "Add Member" input directly on existing calendar cards in the manage calendars page so members can be added without leaving the card.

- [ ] **Add members by email or userId everywhere**
  Members should be addable by email or userId on both the "Create a new calendar" form and existing calendar cards.

- [ ] **Add friend by email, display name, or userId**
  Update the friends feature so users can search/add friends by any of: email, display name, or userId — not just one identifier type.

---

## Incomplete Features

- [ ] **Deduplicate synced calendars**
  Both Google and Outlook sync currently append events on every pull. Re-syncing creates duplicates. The pull should clear existing events in the "(Synced)" calendar before inserting fresh ones.

- [ ] **Admin — Unlink External Calendars page uses placeholder data**
  `/admin/unlink` in `ui_routes/routes/admin.py` passes a hardcoded `placeholder_externals` list to the template instead of fetching real provider data from the database.

- [ ] **Live syncing of external calendars**
  Currently sync is manual (user clicks Pull). Add background or webhook-based syncing so external calendar changes are reflected automatically without user action.

---

## Architecture / Cleanup

- [ ] **Refactor admin role to `is_admin` column on `users` table**
  Replace the current manual `app_metadata` edit in Supabase with a dedicated `is_admin` boolean column. Update `@ui_admin_required` and the session user dict (set at login in `auth.py`) to read from this column. Add an admin UI action to promote/demote users so it no longer requires direct DB access.

- [ ] **Separate API and UI route responsibilities clearly**
  Architecture direction: the website uses UI routes exclusively (session cookie auth, no Bearer token). The REST API is reserved for live syncing — webhook receivers from Google/Outlook that arrive with no user session.

- [ ] **Add structured JSON error responses to UI JSON endpoints**
  The UI JSON routes in `ui_routes/routes/user.py` currently return plain HTTP status codes on failure (400/403/404). Templates show generic `alert()` messages. Upgrade to return `{"error": "descriptive message"}` so the JS can surface meaningful errors to the user.

- [ ] **Remove `email` from `User.__init__`**
  `self.email` is stored but never read on any `User` instance. Drop the param and update both call sites: `api/api_routes/helpers.py:9` and `api/ui_routes/helpers.py:276`.

- [ ] **Add `Event.find(eventId)` static method to `models/event.py`**
  Should query the `events` table by id and return the row dict or `None`. Then replace `u.viewEvent(event_id)` in `api/ui_routes/routes/user.py:100` with `Event.find(event_id)`.

- [ ] **Delete `models/guest.py` and the `Guest` class**
  All four methods are unused once `Event.find()` is in place. Remove the `from models.guest import Guest` import and `(Guest)` base class from `models/user.py`.

- [ ] **`_refresh_access_token` should call `updateTokens` instead of writing inline**
  In `models/external.py` around line 91, the method writes to the DB directly. It should call `updateTokens` to consolidate token persistence into one place.

- [ ] **Refactor `External.__init__` to minimal params**
  Keep only `id`, `supabaseClient`, and `userId` as instance variables. Move `url`, `provider`, `accessToken`, and `refreshToken` into `save()` as parameters — `pullCalData`/`pushCalData` already re-fetch them from the DB and never touch instance fields.
