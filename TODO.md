# TODO

Known tasks and improvements for the Calendar project. Update this file when you pick something up or finish it.

## Suspected Dead Code — needs review

- [models/admin.py, `view_system_logs`] method is defined but never called anywhere in the codebase
- [models/admin.py, `unlink_all_external_calendars`] method is defined but never called anywhere in the codebase

## Suspected Dead Code - needs review

- [models/calendar.py, `remove_member`] method is defined but never called anywhere in the codebase
- [utils/logger.py, `log_event`] `result` is assigned from the log insert but is only used by a commented debug print
