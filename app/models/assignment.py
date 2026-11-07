from typing import Optional

from sqlmodel import Field, SQLModel


class Assignment(SQLModel, table=True):
    __tablename__ = "assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    ta_id: int = Field(index=True)
    course_id: int = Field(index=True)
    weekly_hours: int
    created_at: str
