"""Seed HOD, TAs, courses, experience, and department budget."""

from __future__ import annotations

from sqlmodel import Session, select

from app.database import drop_all, ensure_db_and_tables, engine
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.department import Department
from app.models.ta import Ta
from app.models.ta_experience import TaExperience
from app.models.user import User
from app.utilities.security import encrypt_password


def seed(*, reset: bool = False) -> None:
    import app.models  # noqa: F401

    if reset:
        try:
            drop_all()
        except Exception:
            pass
    ensure_db_and_tables()

    with Session(engine) as session:
        if session.exec(select(User)).first() is not None:
            return

        session.add(
            User(
                username="hod",
                email="hod@example.com",
                password=encrypt_password("hod-dev"),
                role="hod",
            )
        )

        for name, email in [
            ("Alex TA", "alex@example.com"),
            ("Blair TA", "blair@example.com"),
            ("Casey TA", "casey@example.com"),
        ]:
            session.add(Ta(name=name, email=email))

        for code, title, hours in [
            ("COMP3613", "Software Engineering II", 30),
            ("COMP2602", "Databases", 20),
            ("COMP1601", "Intro Programming", 15),
        ]:
            session.add(Course(code=code, title=title, budgeted_hours=hours))
        session.commit()

        # Alex experienced on COMP3613; Blair on COMP2602
        alex = session.exec(select(Ta).where(Ta.email == "alex@example.com")).one()
        blair = session.exec(select(Ta).where(Ta.email == "blair@example.com")).one()
        c3613 = session.exec(select(Course).where(Course.code == "COMP3613")).one()
        c2602 = session.exec(select(Course).where(Course.code == "COMP2602")).one()
        session.add(TaExperience(ta_id=alex.id, course_id=c3613.id))
        session.add(TaExperience(ta_id=blair.id, course_id=c2602.id))

        # Seed one assignment so Alex already has 18h (near cap); 80 - 18 = 62 left
        session.add(Department(id=1, budget_hours_remaining=62))
        session.add(
            Assignment(
                ta_id=alex.id,
                course_id=c3613.id,
                weekly_hours=18,
                created_at="2099-01-01T10:00:00+00:00",
            )
        )
        session.commit()
