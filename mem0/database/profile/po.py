from datetime import datetime

from sqlalchemy import func
from sqlmodel import SQLModel, Field


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profile"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    profile: str | None = Field(default=None)
    created_time: datetime | None = Field(
        default=func.now()
    ) 
    updated_time: datetime | None = Field(
        default=func.now()
    )  # pylint:disable=not-callable
