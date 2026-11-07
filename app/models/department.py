from sqlmodel import Field, SQLModel


class Department(SQLModel, table=True):
    """Single-row department budget (id is always 1)."""

    __tablename__ = "department"

    id: int = Field(default=1, primary_key=True)
    budget_hours_remaining: int
