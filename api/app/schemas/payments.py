from pydantic import BaseModel, Field


class StarsPaymentOptionsOut(BaseModel):
    enabled: bool
    min_stars: int
    preset_stars: list[int] = Field(default_factory=list)
    exchange_numerator: int
    exchange_denominator: int
    currency: str


class StarsPaymentConfirmIn(BaseModel):
    telegram_id: int
    stars_amount: int
    currency: str
    telegram_charge_id: str
    provider_charge_id: str | None = None
    invoice_payload: str | None = None


class StarsPaymentConfirmOut(BaseModel):
    credits_added: int
    balance: int
