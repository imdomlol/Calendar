from unittest.mock import MagicMock, patch

from tests.conftest import AUTH_HEADER, FAKE_USER, auth_mock, supabase_mock


class TestAuthBoundary:
    def test_no_token_returns_401(self, client):
        resp = client.get("/calendars")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        from urllib.error import URLError
        # require_auth catches URLError and converts it to 401
        with patch("utils.auth.urlopen", side_effect=URLError("network error")):
            resp = client.get("/calendars", headers=AUTH_HEADER)
        assert resp.status_code == 401

    def test_me_returns_user_fields(self, client):
        with patch("utils.auth.urlopen", auth_mock()):
            resp = client.get("/me", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json["id"] == FAKE_USER["id"]
        assert resp.json["email"] == FAKE_USER["email"]
        # success is implied by 200, these keys should not be present
        assert "success" not in resp.json
        assert "session" not in resp.json


class TestCalendars:
    def test_list_returns_200_with_calendars_key(self, client):
        sb = supabase_mock(calendars=[{"id": "cal-1", "name": "Work"}])
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.get("/calendars", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert "calendars" in resp.json

    def test_create_missing_name_returns_400(self, client):
        with patch("utils.auth.urlopen", auth_mock()):
            resp = client.post("/calendars", json={}, headers=AUTH_HEADER)
        assert resp.status_code == 400
        assert "name" in resp.json["error"]

    def test_create_no_body_returns_400(self, client):
        with patch("utils.auth.urlopen", auth_mock()):
            resp = client.post("/calendars", headers=AUTH_HEADER)
        assert resp.status_code == 400

    def test_create_success_returns_201(self, client):
        new_cal = {"id": "cal-1", "name": "Work", "owner_id": FAKE_USER["id"]}
        mock_result = MagicMock()
        mock_result.data = [new_cal]
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("models.calendar.Calendar.save", return_value=mock_result):
            resp = client.post("/calendars", json={"name": "Work"}, headers=AUTH_HEADER)
        assert resp.status_code == 201
        assert resp.json["name"] == "Work"

    def test_delete_not_owned_returns_404(self, client):
        sb = supabase_mock(calendars=[])  # ownership check returns nothing
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.delete("/calendars/unknown-id", headers=AUTH_HEADER)
        assert resp.status_code == 404


class TestEvents:
    def test_list_no_calendars_returns_empty(self, client):
        sb = supabase_mock(calendars=[])
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.get("/events", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json["events"] == []

    def test_list_returns_events_key(self, client):
        sb = supabase_mock(
            calendars=[{"id": "cal-1"}],
            events=[{"id": "evt-1", "title": "Standup"}],
        )
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.get("/events", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert "events" in resp.json

    def test_create_missing_title_returns_400(self, client):
        with patch("utils.auth.urlopen", auth_mock()):
            resp = client.post("/events", json={"calendar_ids": ["cal-1"]}, headers=AUTH_HEADER)
        assert resp.status_code == 400
        assert "title" in resp.json["error"]

    def test_create_missing_calendar_ids_returns_400(self, client):
        with patch("utils.auth.urlopen", auth_mock()):
            resp = client.post("/events", json={"title": "My Event"}, headers=AUTH_HEADER)
        assert resp.status_code == 400

    def test_create_unowned_calendar_returns_403(self, client):
        sb = supabase_mock(calendars=[])  # user owns no calendars
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.post("/events", json={
                "title": "My Event", "calendar_ids": ["not-my-cal"]
            }, headers=AUTH_HEADER)
        assert resp.status_code == 403

    def test_edit_no_valid_fields_returns_400(self, client):
        sb = supabase_mock(
            calendars=[{"id": "cal-1"}],
            events=[{"id": "evt-1", "calendar_ids": ["cal-1"]}],
        )
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.put("/events/evt-1", json={"bad_field": "x"}, headers=AUTH_HEADER)
        assert resp.status_code == 400
        assert "allowed" in resp.json["error"]

    def test_delete_not_found_returns_404(self, client):
        sb = supabase_mock(events=[])
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.delete("/events/nonexistent", headers=AUTH_HEADER)
        assert resp.status_code == 404


class TestExternals:
    def test_list_returns_externals_key(self, client):
        sb = supabase_mock(externals=[])
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.get("/externals", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert "externals" in resp.json

    def test_create_missing_url_returns_400(self, client):
        with patch("utils.auth.urlopen", auth_mock()):
            resp = client.post("/externals", json={"provider": "google"}, headers=AUTH_HEADER)
        assert resp.status_code == 400
        assert "url" in resp.json["error"]

    def test_create_missing_provider_returns_400(self, client):
        with patch("utils.auth.urlopen", auth_mock()):
            resp = client.post("/externals", json={"url": "https://example.com"}, headers=AUTH_HEADER)
        assert resp.status_code == 400
        assert "provider" in resp.json["error"]

    def test_delete_not_owned_returns_404(self, client):
        sb = supabase_mock(externals=[])
        with patch("utils.auth.urlopen", auth_mock()), \
             patch("api.index.get_supabase_client", return_value=sb):
            resp = client.delete("/externals/unknown-id", headers=AUTH_HEADER)
        assert resp.status_code == 404
