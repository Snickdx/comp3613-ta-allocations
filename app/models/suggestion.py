from typing import Optional

from sqlmodel import Field, SQLModel


class Suggestion(SQLModel, table=True):
    __tablename__ = "suggestions"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int
    weekly_hours: int
    mode: str
    ranked_ta_ids: str
    created_at: str
    confirmed_ta_id: Optional[int] = None
    override: bool = False
    confirmed_at: Optional[str] = None

    def ranked_ids(self):
        return [int(x) for x in self.ranked_ta_ids.split(",")]
