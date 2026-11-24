import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed

client = TestClient(app)
HOD = {"X-User-Id": "1"}


@pytest.fixture(autouse=True)
def fresh_db():
    seed(reset=True)


def course(board, code):
    for c in board["by_course"]:
        if c["code"] == code:
            return c
    return None


def test_review_board_groups_assignments_by_course():
    client.post(
        "/api/assignments/manual",
        headers=HOD,
        json={"ta_id": 2, "course_id": 2, "weekly_hours": 4},
    )
    board = client.get("/api/review").json()
    assert len(board["by_course"]) == 3
    assert course(board, "COMP3613")["hours_assigned"] == 18
    assert course(board, "COMP2602")["hours_assigned"] == 4
    assert course(board, "COMP2602")["assignments"][0]["ta_id"] == 2
    assert board["budget_hours_used"] == 22


def test_course_with_no_assignments_shows_zero_hours():
    board = client.get("/api/review").json()
    assert course(board, "COMP1601")["hours_assigned"] == 0
    assert course(board, "COMP1601")["assignments"] == []
