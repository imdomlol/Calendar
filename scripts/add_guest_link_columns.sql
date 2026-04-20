alter table calendars
  add column if not exists guest_link_token text,
  add column if not exists guest_link_role text,
  add column if not exists guest_link_active boolean not null default false;

-- speeds up the token lookup on every guest page load
create index if not exists idx_calendars_guest_link_token
  on calendars (guest_link_token);
