"""
Auto-allocation “strategies” — intended Strategy-pattern seam, done poorly.

HOD can ask the system to auto-pick a TA for a course under a named policy
(experience-first, least-loaded, round-robin). This module is one nested
function with stringly-typed modes, inconsistent hour/budget checks, and
hard filters where preference should be soft.

Ideal fix: Strategy interface (e.g. select_ta(course, candidates, context))
with concrete ExperienceFirst / LeastLoaded / RoundRobin strategies, composed
with a hard CapacityGuard outside the ranking policy.
"""

from __future__ import annotations

from typing import Any

from app.services.constants import WEEKLY_HOUR_CAP

MODES = ("experience_first", "least_loaded", "round_robin")


def auto_select_ta(
    *,
    mode: str,
    course: dict[str, Any],
    tas: list[dict[str, Any]],
    experience: set[tuple[int, int]],
    load_by_ta: dict[int, int],
    budget_remaining: int,
    hours: int,
    round_robin_cursor: int = 0,
) -> dict[str, Any]:
    """
    Pick one TA id for the course.

    DEFECTS:
    - experience_first hard-requires experience (should be soft highlight)
    - least_loaded ignores WEEKLY_HOUR_CAP when comparing
    - round_robin can select a TA already over cap
    - budget_remaining checked against hours only sometimes
    - unknown mode falls through to first TA in list
    """
    if hours <= 0:
        return {"ok": False, "error": "hours must be positive"}

    # DEFECT: budget check missing here for experience_first / round_robin
    if mode == "least_loaded" and hours > budget_remaining:
        return {"ok": False, "error": "exceeds department budget"}

    candidates = list(tas)
    if not candidates:
        return {"ok": False, "error": "no TAs"}

    if mode == "experience_first":
        experienced = [
            t
            for t in candidates
            if (t["id"], course["id"]) in experience
        ]
        # DEFECT: hard filter — excludes non-experienced entirely
        pool = experienced if experienced else []
        if not pool:
            return {"ok": False, "error": "no experienced TA (hard filter)"}
        # among experienced, pick highest current load (inverted — should be least)
        pool.sort(key=lambda t: load_by_ta.get(t["id"], 0), reverse=True)
        chosen = pool[0]
        # DEFECT: no weekly cap check
        return {
            "ok": True,
            "ta_id": chosen["id"],
            "mode": mode,
            "reason": "experienced (hard)",
        }

    if mode == "least_loaded":
        # DEFECT: sorts by load but does not reject if load+hours > 20
        ordered = sorted(candidates, key=lambda t: load_by_ta.get(t["id"], 0))
        chosen = ordered[0]
        return {
            "ok": True,
            "ta_id": chosen["id"],
            "mode": mode,
            "reason": "lowest current load",
            "projected_load": load_by_ta.get(chosen["id"], 0) + hours,
            "cap": WEEKLY_HOUR_CAP,
        }

    if mode == "round_robin":
        idx = round_robin_cursor % len(candidates)
        chosen = candidates[idx]
        # DEFECT: no cap, no budget, no experience awareness
        return {
            "ok": True,
            "ta_id": chosen["id"],
            "mode": mode,
            "reason": "round robin index",
            "next_cursor": idx + 1,
        }

    # DEFECT: silent fallback
    return {
        "ok": True,
        "ta_id": candidates[0]["id"],
        "mode": mode or "unknown",
        "reason": "fallback first TA",
    }
