# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

---

## Bugs / Quick Fixes

- [ ] **Settings page — Pull/Push buttons should use UI routes**
  The Pull and Push buttons currently call the API routes (`/externals/<id>/pull`, `/externals/<id>/push`), which require a Bearer token. The website should use the existing UI routes (`/settings/external/google/<id>/sync` and `/settings/external/google/<id>/push`) instead, since those use the session and are simpler. The API routes are meant for external callers, not the website itself.

---

## Incomplete Features

- [ ] **Outlook sync (pull)**
  `External.pullCalData()` in `models/external.py` returns an error for the `outlook` provider. Needs implementation once we have Outlook OAuth set up.

- [ ] **Outlook sync (push)**
  Same as above — `External.pushCalData()` has a stub for Outlook that returns an error.

- [ ] **Admin — Unlink External Calendars page uses placeholder data**
  `/admin/unlink` in `ui_routes/routes/admin.py` passes a hardcoded `placeholder_externals` list to the template instead of fetching real provider data from the database.

- [ ] **Public calendar/event views use placeholder data**
  The `/calendars` and `/events` routes in `ui_routes/routes/home.py` render placeholder data instead of real records. These pages need to be wired up to the actual database.

---

## Architecture / Cleanup

- [ ] **Separate API and UI route responsibilities clearly**
  The website's JS currently reaches into API routes (Bearer token auth) for some actions and UI routes (session auth) for others. The rule should be: website buttons and forms use UI routes; API routes are for external consumers only (scripts, mobile apps, etc.).
