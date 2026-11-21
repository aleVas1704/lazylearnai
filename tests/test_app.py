from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "abstracthon-base"}


def test_home_renders_html_and_css() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Una base sencilla" in response.text
    assert "/static/css/tokens.css" in response.text
