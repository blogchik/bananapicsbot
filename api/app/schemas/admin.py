"""Admin schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# ============ Auth ============


class TelegramLoginData(BaseModel):
    """Telegram Login Widget callback data."""

    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class AdminInfo(BaseModel):
    """Admin user info."""

    telegram_id: int
    username: Optional[str]
    first_name: str


class AdminLoginResponse(BaseModel):
    """Admin login response with JWT token."""

    access_token: str
    token_type: str = "bearer"
    admin: AdminInfo
    expires_at: datetime


# ============ Credits ============


class AdminCreditIn(BaseModel):
    """Admin credit adjustment input."""

    telegram_id: int
    amount: int = Field(..., description="Amount to add (positive) or subtract (negative)")
    reason: Optional[str] = Field(None, max_length=255)


class AdminCreditOut(BaseModel):
    """Admin credit adjustment output."""

    telegram_id: int
    amount: int
    old_balance: int
    new_balance: int
    reason: Optional[str]


# ============ Users ============


class UserSearchQuery(BaseModel):
    """User search query."""

    query: Optional[str] = None
    is_banned: Optional[bool] = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


class UserBanRequest(BaseModel):
    """User ban/unban request."""

    telegram_id: int
    ban: bool
    reason: Optional[str] = None


class AdminUserOut(BaseModel):
    """Admin user output."""

    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    photo_url: Optional[str] = None
    language_code: Optional[str]
    is_active: bool
    is_banned: bool
    ban_reason: Optional[str]
    trial_remaining: int
    balance: Decimal
    referrer_id: Optional[int]
    referral_code: Optional[str] = None
    referral_count: int
    generation_count: int
    total_spent: Optional[int] = 0
    total_deposits: Optional[int] = 0
    created_at: datetime
    last_active_at: Optional[datetime]


class UserListOut(BaseModel):
    """User list output."""

    users: List[AdminUserOut]
    total: int
    offset: int
    limit: int


# ============ Statistics ============


class DashboardStatsOut(BaseModel):
    """Dashboard statistics output."""

    # Users
    total_users: int
    active_users_7d: int
    active_users_30d: int
    new_users_today: int
    new_users_week: int
    new_users_month: int
    banned_users: int

    # Generations
    total_generations: int
    completed_generations: int
    failed_generations: int
    success_rate: float

    # Revenue
    total_deposits: float
    today_deposits: float
    week_deposits: float
    month_deposits: float
    total_refunded: float = 0.0
    total_spent: float
    net_revenue: float

    # Model statistics
    by_model: Dict[str, Dict[str, Any]] = {}

    # Payments
    total_payments: int
    completed_payments: int
    payment_success_rate: float


class DailyStatItem(BaseModel):
    """Daily stat item."""

    date: str
    count: int
    amount: Optional[float] = None


class DailyReportOut(BaseModel):
    """Daily report output."""

    user_stats: Dict[str, Any]
    generation_daily: List[Dict[str, Any]]
    revenue_daily: List[Dict[str, Any]]
    payment_daily: List[Dict[str, Any]]


# ============ Generations ============


class GenerationSearchQuery(BaseModel):
    """Generation search query."""

    telegram_id: Optional[int] = None
    model_slug: Optional[str] = None
    status: Optional[str] = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


class AdminGenerationOut(BaseModel):
    """Admin generation output."""

    id: UUID
    public_id: str
    telegram_id: int
    model_id: int
    prompt: str
    status: str
    credits_charged: Decimal
    created_at: datetime
    completed_at: Optional[datetime]


class RefundRequest(BaseModel):
    """Refund request."""

    generation_id: UUID
    reason: Optional[str] = None


class RefundOut(BaseModel):
    """Refund output."""

    generation_id: UUID
    telegram_id: int
    amount: Decimal
    success: bool


# ============ Broadcast ============


class BroadcastFilterType(str):
    """Broadcast filter types."""

    ALL = "all"
    ACTIVE_7D = "active_7d"
    ACTIVE_30D = "active_30d"
    WITH_BALANCE = "with_balance"
    PAID_USERS = "paid_users"
    NEW_USERS = "new_users"


class BroadcastCreateRequest(BaseModel):
    """Broadcast create request."""

    content_type: str = Field(..., pattern="^(text|photo|video|audio|sticker)$")
    text: Optional[str] = None
    media_file_id: Optional[str] = None
    inline_button_text: Optional[str] = Field(None, max_length=100)
    inline_button_url: Optional[str] = Field(None, max_length=500)
    filter_type: str = Field(default="all")
    filter_params: Optional[Dict[str, Any]] = None


class BroadcastOut(BaseModel):
    """Broadcast output."""

    id: int
    public_id: str
    admin_id: int
    content_type: str
    text: Optional[str]
    media_file_id: Optional[str]
    inline_button_text: Optional[str]
    inline_button_url: Optional[str]
    filter_type: str
    status: str
    total_users: int
    sent_count: int
    failed_count: int
    blocked_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class BroadcastStatusOut(BaseModel):
    """Broadcast status output."""

    public_id: str
    status: str
    total_users: int
    sent_count: int
    failed_count: int
    blocked_count: int
    progress_percent: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class BroadcastListOut(BaseModel):
    """Broadcast list output."""

    broadcasts: List[BroadcastOut]
    total: int
    offset: int = 0
    limit: int = 20


# ============ Revenue ============


class RevenueStatsOut(BaseModel):
    """Revenue statistics output."""

    period_days: int
    total_deposits: float
    total_spent: float
    admin_adjustments: float
    referral_bonuses: float
    refunds: float
    net_revenue: float


class PaymentStatsOut(BaseModel):
    """Payment statistics output."""

    period_days: int
    total_payments: int
    completed_payments: int
    success_rate: float
    total_amount: float
    total_credits: float
    by_provider: Dict[str, Dict[str, Any]]
