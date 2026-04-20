from unittest.mock import MagicMock, patch


class TestRegister:
    def test_missing_email_returns_400(self, client):
        resp = client.post("/api/auth/register", json={"password": "secret123"})
        assert resp.status_code == 400
        assert "email" in resp.json["error"]

    def test_missing_password_returns_400(self, client):
        resp = client.post("/api/auth/register", json={"email": "a@b.com"})
        assert resp.status_code == 400

    def test_no_body_returns_400(self, client):
        resp = client.post("/api/auth/register")
        assert resp.status_code == 400

    def test_success_returns_201(self, client):
        mock_result = MagicMock()
        mock_result.session = {"access_token": "tok"}
        mock_result.user = {"id": "user-123", "email": "a@b.com"}
        with patch("api.auth_routes.supabase") as mock_sb:
            mock_sb.auth.sign_up.return_value = mock_result
            resp = client.post("/api/auth/register", json={
                "email": "a@b.com",
                "password": "password123",
            })
        assert resp.status_code == 201
        assert resp.json["message"] == "User created"

    def test_optional_name_forwarded(self, client):
        mock_result = MagicMock()
        mock_result.session = None
        mock_result.user = {"id": "user-123"}
        with patch("api.auth_routes.supabase") as mock_sb:
            mock_sb.auth.sign_up.return_value = mock_result
            client.post("/api/auth/register", json={
                "email": "a@b.com", "password": "pass123", "name": "Alice"
            })
            call_payload = mock_sb.auth.sign_up.call_args[0][0]
        assert call_payload["options"]["data"]["name"] == "Alice"


class TestLogin:
    def test_missing_email_returns_400(self, client):
        resp = client.post("/api/auth/login", json={"password": "secret"})
        assert resp.status_code == 400

    def test_missing_password_returns_400(self, client):
        resp = client.post("/api/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 400

    def test_no_body_returns_400(self, client):
        resp = client.post("/api/auth/login")
        assert resp.status_code == 400

    def test_bad_credentials_returns_401(self, client):
        with patch("api.auth_routes.supabase") as mock_sb:
            mock_sb.auth.sign_in_with_password.side_effect = Exception("bad creds")
            resp = client.post("/api/auth/login", json={
                "email": "a@b.com", "password": "wrong"
            })
        assert resp.status_code == 401
        assert resp.json["error"] == "Invalid credentials"

    def test_success_returns_200(self, client):
        mock_result = MagicMock()
        mock_result.session = {"access_token": "tok"}
        mock_result.user = {"id": "user-123"}
        with patch("api.auth_routes.supabase") as mock_sb:
            mock_sb.auth.sign_in_with_password.return_value = mock_result
            resp = client.post("/api/auth/login", json={
                "email": "a@b.com", "password": "password123"
            })
        assert resp.status_code == 200
        assert resp.json["message"] == "Login successful"
