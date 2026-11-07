from typing import Optional

from sqlmodel import Field, SQLModel


class TaExperience(SQLModel, table=True):
    """A TA has prior experience on a course (soft preference only)."""

    __tablename__ = "ta_experience"

    id: Optional[int] = Field(default=None, primary_key=True)
    ta_id: int = Field(index=True)
    course_id: int = Field(index=True)
