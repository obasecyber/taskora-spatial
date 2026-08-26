from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.api.v1 import health
from backend.app.db.session import get_db
from backend.app.main import app


class FakeSession:
    def execute(self, statement):
        assert str(statement) == "SELECT 1"


def fake_db():
    yield FakeSession()


def test_health_reports_database_connection():
    app.dependency_overrides[get_db] = fake_db
    response = TestClient(app).get("/api/v1/health")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}