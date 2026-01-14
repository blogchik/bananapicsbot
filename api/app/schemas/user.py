from datetime import datetime

from pydantic import BaseModel


class UserBase(BaseModel):
    telegram_id: int


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
