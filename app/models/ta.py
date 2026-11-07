from typing import Optional

from sqlmodel import Field, SQLModel


class Ta(SQLModel, table=True):
    __tablename__ = "tas"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
