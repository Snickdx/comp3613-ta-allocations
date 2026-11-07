"""Shallow scenario smoke tests — intentionally weak."""

from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed


def setup_module() -> None:
    seed(reset=True)


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["scenario"] == "ta-allocations"


def test_login_hod():
    r = client.post(
        "/api/auth/login",
        json={"email": "hod@example.com", "password": "hod-dev"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "hod"
    assert "password" not in r.json()["user"]
    assert "password_hash" not in r.json()["user"]


def test_review_board():
    r = client.get("/api/review")
    assert r.status_code == 200
    assert "tas" in r.json()
    assert "assignments" in r.json()
