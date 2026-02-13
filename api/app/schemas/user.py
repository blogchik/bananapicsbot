from datetime import datetime

from pydantic import BaseModel


class UserBase(BaseModel):
    telegram_id: int


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserSyncIn(BaseModel):
    telegram_id: int
    referral_code: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None


class UserSyncOut(UserOut):
    referral_code: str
    referral_applied: bool = False
    referrer_telegram_id: int | None = None
    bonus_percent: int
