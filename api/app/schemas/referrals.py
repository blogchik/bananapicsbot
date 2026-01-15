from pydantic import BaseModel


class ReferralInfoOut(BaseModel):
    user_id: int
    referral_code: str
    referrals_count: int
    referral_credits_total: int
    bonus_percent: int
