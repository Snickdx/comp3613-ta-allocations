"""TA allocations scenario JSON API (OpenAPI /docs)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services import allocation_auth as auth
from app.services import allocations
from app.services.strategies import MODES

router = APIRouter(tags=["ta-allocations"])


class LoginBody(BaseModel):
    email: str
    password: str


class ManualAssignBody(BaseModel):
    ta_id: int
    course_id: int
    weekly_hours: int


class AutoAssignBody(BaseModel):
    course_id: int
    weekly_hours: int
    mode: str = Field(description=" | ".join(MODES))


def _actor_id(x_user_id: str | None) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    try:
        return int(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-User-Id must be int") from exc


@router.post("/auth/login")
def login(body: LoginBody) -> dict[str, Any]:
    user = auth.login(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"user": user}


@router.get("/tas")
def tas() -> dict[str, Any]:
    return {"tas": allocations.list_tas()}


@router.get("/courses")
def courses() -> dict[str, Any]:
    return {"courses": allocations.list_courses()}


@router.get("/courses/{course_id}/candidates")
def candidates(course_id: int) -> dict[str, Any]:
    return {"candidates": allocations.highlight_candidates(course_id)}


@router.get("/assignments")
def assignments() -> dict[str, Any]:
    return {"assignments": allocations.list_assignments()}


@router.get("/review")
def review() -> dict[str, Any]:
    return allocations.review_board()


@router.post("/assignments/manual")
def manual(
    body: ManualAssignBody, x_user_id: str | None = Header(default=None)
) -> dict[str, Any]:
    result = allocations.assign_manual(
        _actor_id(x_user_id),
        ta_id=body.ta_id,
        course_id=body.course_id,
        weekly_hours=body.weekly_hours,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/assignments/auto")
def auto(
    body: AutoAssignBody, x_user_id: str | None = Header(default=None)
) -> dict[str, Any]:
    result = allocations.assign_auto(
        _actor_id(x_user_id),
        course_id=body.course_id,
        weekly_hours=body.weekly_hours,
        mode=body.mode,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
