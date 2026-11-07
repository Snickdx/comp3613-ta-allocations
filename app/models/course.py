from typing import Optional

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    __tablename__ = "courses"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    title: str
    budgeted_hours: int
