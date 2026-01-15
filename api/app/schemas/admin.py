from pydantic import BaseModel, Field


class AdminCreditIn(BaseModel):
    telegram_id: int
    credits: int = Field(gt=0)
    description: str | None = None


class AdminCreditOut(BaseModel):
    user_id: int
    credits_added: int
    balance: int
