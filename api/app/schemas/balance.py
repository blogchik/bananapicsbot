from pydantic import BaseModel


class BalanceOut(BaseModel):
    user_id: int
    balance: int
