"""Manual and auto TA course assignment."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, func, select

from app.database import engine
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.department import Department
from app.models.suggestion import Suggestion
from app.models.ta import Ta
from app.models.ta_experience import TaExperience
from app.services.allocation_auth import get_user
from app.services.capacity_guard import CapacityGuard
from app.services.constants import WEEKLY_HOUR_CAP
from app.services.ranking.candidate import Candidate
from app.services.ranking.experience_first import ExperienceFirstStrategy
from app.services.ranking.least_loaded import LeastLoadedStrategy
from app.services.ranking.registry import StrategyRegistry
from app.services.ranking.round_robin import RoundRobinStrategy

guard = CapacityGuard()

registry = StrategyRegistry()
registry.register(ExperienceFirstStrategy())
registry.register(LeastLoadedStrategy())
registry.register(RoundRobinStrategy())

MODES = tuple(registry.names())


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def list_tas() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(select(Ta).order_by(Ta.id)).all()
        return [r.model_dump() for r in rows]


def list_courses() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(select(Course).order_by(Course.id)).all()
        return [r.model_dump() for r in rows]


def list_assignments() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(select(Assignment).order_by(Assignment.id)).all()
        return [r.model_dump() for r in rows]


def _load_by_ta(session: Session) -> dict[int, int]:
    rows = session.exec(
        select(Assignment.ta_id, func.sum(Assignment.weekly_hours)).group_by(
            Assignment.ta_id
        )
    ).all()
    return {ta_id: int(total) for ta_id, total in rows}


def _experience_set(session: Session) -> set[tuple[int, int]]:
    rows = session.exec(select(TaExperience.ta_id, TaExperience.course_id)).all()
    return {(ta_id, course_id) for ta_id, course_id in rows}


def _budget_remaining(session: Session) -> int:
    dept = session.get(Department, 1)
    return int(dept.budget_hours_remaining)


def _candidate(session: Session, ta: Ta, course_id: int) -> Candidate:
    experienced = (ta.id, course_id) in _experience_set(session)
    used = _load_by_ta(session).get(ta.id, 0)
    return Candidate(ta, experienced, used)


def _all_candidates(session: Session, course_id: int) -> list[Candidate]:
    exp = _experience_set(session)
    load = _load_by_ta(session)
    result = []
    for ta in session.exec(select(Ta).order_by(Ta.id)).all():
        result.append(Candidate(ta, (ta.id, course_id) in exp, load.get(ta.id, 0)))
    return result


def _save_assignment(session: Session, ta_id: int, course_id: int, hours: int, dept: Department):
    row = Assignment(ta_id=ta_id, course_id=course_id, weekly_hours=hours, created_at=_now())
    session.add(row)
    dept.budget_hours_remaining -= hours
    session.add(dept)
    return row


def ta_remaining_hours(ta_id: int) -> int:
    with Session(engine) as session:
        used = _load_by_ta(session).get(ta_id, 0)
    return WEEKLY_HOUR_CAP - used


def highlight_candidates(course_id: int) -> list[dict[str, Any]]:
    """Soft preference view — experienced flagged for HOD."""
    with Session(engine) as session:
        course = session.get(Course, course_id)
        if course is None:
            return []
        exp = _experience_set(session)
        load = _load_by_ta(session)
        tas = [t.model_dump() for t in session.exec(select(Ta).order_by(Ta.id)).all()]
    out = []
    for t in tas:
        used = load.get(t["id"], 0)
        out.append(
            {
                **t,
                "prior_experience": (t["id"], course_id) in exp,
                "weekly_hours_used": used,
                "weekly_hours_remaining": WEEKLY_HOUR_CAP - used,
            }
        )
    return out


def assign_manual(
    hod_id: int, *, ta_id: int, course_id: int, weekly_hours: int
) -> dict[str, Any]:
    user = get_user(hod_id)
    if not user or user["role"] != "hod":
        return {"ok": False, "error": "hod only"}
    if weekly_hours <= 0:
        return {"ok": False, "error": "hours must be positive"}

    with Session(engine) as session:
        ta = session.get(Ta, ta_id)
        course = session.get(Course, course_id)
        if not ta or not course:
            return {"ok": False, "error": "ta or course not found"}

        dept = session.get(Department, 1)
        problem = guard.problem(
            _candidate(session, ta, course_id), weekly_hours, dept.budget_hours_remaining
        )
        if problem:
            return {"ok": False, "error": problem}

        row = _save_assignment(session, ta_id, course_id, weekly_hours, dept)
        session.commit()
        session.refresh(row)
        assignment = row.model_dump()

    return {"ok": True, "assignment": assignment}


def suggest(hod_id: int, *, course_id: int, weekly_hours: int, mode: str) -> dict[str, Any]:
    user = get_user(hod_id)
    if not user or user["role"] != "hod":
        return {"ok": False, "error": "hod only"}
    if weekly_hours <= 0:
        return {"ok": False, "error": "hours must be positive"}
    try:
        strategy = registry.get(mode)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    with Session(engine) as session:
        course = session.get(Course, course_id)
        if course is None:
            return {"ok": False, "error": "course not found"}

        budget = _budget_remaining(session)
        eligible = guard.filter(_all_candidates(session, course_id), weekly_hours, budget)
        ranked = strategy.rank(course, eligible)
        if len(ranked) == 0:
            return {"ok": False, "error": "no TA fits within the weekly cap and the budget"}

        row = Suggestion(
            course_id=course_id,
            weekly_hours=weekly_hours,
            mode=mode,
            ranked_ta_ids=",".join(str(c.ta_id) for c in ranked),
            created_at=_now(),
        )
        session.add(row)
        session.commit()
        session.refresh(row)

        return {
            "ok": True,
            "suggestion_id": row.id,
            "course_id": course_id,
            "weekly_hours": weekly_hours,
            "mode": mode,
            "ranked": [c.to_dict() for c in ranked],
        }


def confirm(hod_id: int, *, suggestion_id: int, ta_id: int) -> dict[str, Any]:
    user = get_user(hod_id)
    if not user or user["role"] != "hod":
        return {"ok": False, "error": "hod only"}

    with Session(engine) as session:
        sug = session.get(Suggestion, suggestion_id)
        if sug is None:
            return {"ok": False, "error": "suggestion not found"}
        if sug.confirmed_ta_id is not None:
            return {"ok": False, "error": "suggestion already confirmed"}

        ranked = sug.ranked_ids()
        if ta_id not in ranked:
            return {"ok": False, "error": "TA is not in this suggestion"}

        ta = session.get(Ta, ta_id)
        dept = session.get(Department, 1)

        # hours or budget may have changed since suggest, so check again
        problem = guard.problem(
            _candidate(session, ta, sug.course_id), sug.weekly_hours, dept.budget_hours_remaining
        )
        if problem:
            return {"ok": False, "error": "limits changed since suggest: " + problem}

        row = _save_assignment(session, ta_id, sug.course_id, sug.weekly_hours, dept)
        sug.confirmed_ta_id = ta_id
        sug.override = ta_id != ranked[0]
        sug.confirmed_at = _now()
        session.add(sug)
        session.commit()
        session.refresh(row)

        return {
            "ok": True,
            "assignment": row.model_dump(),
            "suggestion_id": sug.id,
            "override": sug.override,
        }


def get_suggestion(suggestion_id: int) -> dict[str, Any] | None:
    with Session(engine) as session:
        row = session.get(Suggestion, suggestion_id)
        if row is None:
            return None
        return row.model_dump()


def assign_auto(hod_id: int, *, course_id: int, weekly_hours: int, mode: str) -> dict[str, Any]:
    # one click version: suggest, then confirm the top TA
    sug = suggest(hod_id, course_id=course_id, weekly_hours=weekly_hours, mode=mode)
    if not sug["ok"]:
        return sug
    top_ta = sug["ranked"][0]["ta_id"]
    return confirm(hod_id, suggestion_id=sug["suggestion_id"], ta_id=top_ta)


def review_board() -> dict[str, Any]:
    with Session(engine) as session:
        courses = [c.model_dump() for c in session.exec(select(Course)).all()]
        assignments = [a.model_dump() for a in session.exec(select(Assignment)).all()]
        load = _load_by_ta(session)
        budget = _budget_remaining(session)
        tas = [t.model_dump() for t in session.exec(select(Ta)).all()]
    ta_view = [
        {
            **t,
            "weekly_hours_used": load.get(t["id"], 0),
            "weekly_hours_remaining": WEEKLY_HOUR_CAP - load.get(t["id"], 0),
        }
        for t in tas
    ]
    by_course = []
    for c in courses:
        rows = [a for a in assignments if a["course_id"] == c["id"]]
        by_course.append(
            {
                "course_id": c["id"],
                "code": c["code"],
                "title": c["title"],
                "hours_assigned": sum(a["weekly_hours"] for a in rows),
                "assignments": rows,
            }
        )
    return {
        "courses": courses,
        "assignments": assignments,
        "by_course": by_course,
        "tas": ta_view,
        "budget_hours_used": sum(a["weekly_hours"] for a in assignments),
        "budget_hours_remaining": budget,
        "weekly_hour_cap": WEEKLY_HOUR_CAP,
    }
