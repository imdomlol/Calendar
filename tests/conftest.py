import json
import os
from unittest.mock import MagicMock

import pytest

# Must be set before importing the app, index.py reads these at module load time
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret")

from api.index import app as flask_app  # noqa: E402

FAKE_USER = {
    "id": "user-123",
    "email": "test@example.com",
    "role": "authenticated",
    "sub": "user-123",
    "last_sign_in_at": "2026-01-01T00:00:00Z",
}

AUTH_HEADER = {"Authorization": "Bearer test-token"}


@pytest.fixture(scope="session")
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    yield flask_app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


def auth_mock():
    """Returns a urlopen mock that makes require_auth succeed with FAKE_USER."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(FAKE_USER).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=mock_resp)


def supabase_mock(**table_data):
    """
    Returns a MagicMock Supabase client where any method chain ends in
    execute().data returning the rows supplied for that table name.

    Usage:
        sb = supabase_mock(calendars=[{"id": "1", "name": "Work"}], events=[])
    """
    sb = MagicMock()

    def _make_chain(rows):
        chain = MagicMock()
        result = MagicMock()
        result.data = rows
        # Wire every method that appears in the query chains to return the same chain
        for method in ("select", "insert", "update", "delete", "eq", "neq",
                        "contains", "overlaps", "order", "limit", "single"):
            getattr(chain, method).return_value = chain
        chain.execute.return_value = result
        return chain

    def _table(name):
        return _make_chain(table_data.get(name, []))

    sb.table.side_effect = _table
    return sb
