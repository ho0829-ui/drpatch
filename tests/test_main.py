"""FastAPI 앱 뼈대: 앱이 뜨고 /health가 응답하는지."""

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
