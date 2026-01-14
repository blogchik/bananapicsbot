from datetime import datetime

from pydantic import BaseModel


class LedgerEntryOut(BaseModel):
    id: int
    amount: int
    entry_type: str
    reference_id: str | None = None
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
