from pydantic import BaseModel


class TrialStatusOut(BaseModel):
    user_id: int
    trial_available: bool
    used_count: int
