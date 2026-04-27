# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

---

## Bugs / Quick Fixes

- [ ] **Settings page — Pull/Push buttons should use UI routes**
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

## Architecture / Cleanup

- [ ] **Separate API and UI route responsibilities clearly**
  The website's JS currently reaches into API routes (Bearer token auth) for some actions and UI routes (session auth) for others. The rule should be: website buttons and forms use UI routes; API routes are for external consumers only (scripts, mobile apps, etc.).
