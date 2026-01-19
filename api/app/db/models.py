import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    referral_code: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, nullable=False
    )
    referred_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    referrer: Mapped["User | None"] = relationship(
        "User",
        remote_side="User.id",
        back_populates="referrals",
        foreign_keys=[referred_by_id],
    )
    referrals: Mapped[list["User"]] = relationship(
        "User",
        back_populates="referrer",
        foreign_keys=[referred_by_id],
    )
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(
        "LedgerEntry", back_populates="user"
    )
    generation_requests: Mapped[list["GenerationRequest"]] = relationship(
        "GenerationRequest", back_populates="user"
    )
    trial_uses: Mapped[list["TrialUse"]] = relationship(
        "TrialUse", back_populates="user"
    )


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    entry_type: Mapped[str] = mapped_column(String(50))
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    user: Mapped[User] = relationship("User", back_populates="ledger_entries")


class GenerationStatus(str, Enum):
    pending = "pending"
    configuring = "configuring"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ModelCatalog(Base):
    __tablename__ = "model_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(100))
    supports_text_to_image: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_image_to_image: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_aspect_ratio: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_style: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    prices: Mapped[list["ModelPrice"]] = relationship(
        "ModelPrice", back_populates="model"
    )
    generation_requests: Mapped[list["GenerationRequest"]] = relationship(
        "GenerationRequest", back_populates="model"
    )


class ModelPrice(Base):
    __tablename__ = "model_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("model_catalog.id"), index=True)
    currency: Mapped[str] = mapped_column(String(20), default="credit")
    unit_price: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    model: Mapped[ModelCatalog] = relationship("ModelCatalog", back_populates="prices")


class GenerationRequest(Base):
    __tablename__ = "generation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("model_catalog.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[GenerationStatus] = mapped_column(
        SqlEnum(GenerationStatus, name="generation_status"),
        default=GenerationStatus.pending,
    )
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    aspect_ratio: Mapped[str | None] = mapped_column(String(50), nullable=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    references_count: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship("User", back_populates="generation_requests")
    model: Mapped[ModelCatalog] = relationship("ModelCatalog", back_populates="generation_requests")
    references: Mapped[list["GenerationReference"]] = relationship(
        "GenerationReference", back_populates="request"
    )
    results: Mapped[list["GenerationResult"]] = relationship(
        "GenerationResult", back_populates="request"
    )
    jobs: Mapped[list["GenerationJob"]] = relationship(
        "GenerationJob", back_populates="request"
    )


class GenerationReference(Base):
    __tablename__ = "generation_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"), index=True
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    request: Mapped[GenerationRequest] = relationship(
        "GenerationRequest", back_populates="references"
    )


class GenerationResult(Base):
    __tablename__ = "generation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"), index=True
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    request: Mapped[GenerationRequest] = relationship(
        "GenerationRequest", back_populates="results"
    )


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"), index=True
    )
    provider: Mapped[str] = mapped_column(String(100))
    status: Mapped[JobStatus] = mapped_column(
        SqlEnum(JobStatus, name="job_status"), default=JobStatus.queued
    )
    provider_job_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    request: Mapped[GenerationRequest] = relationship(
        "GenerationRequest", back_populates="jobs"
    )


class TrialUse(Base):
    __tablename__ = "trial_uses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("generation_requests.id"), nullable=True
    )
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    user: Mapped[User] = relationship("User", back_populates="trial_uses")


class PaymentLedger(Base):
    __tablename__ = "payment_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10))
    stars_amount: Mapped[int] = mapped_column(Integer)
    credits_amount: Mapped[int] = mapped_column(Integer)
    telegram_charge_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    provider_charge_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    invoice_payload: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    user: Mapped[User] = relationship("User")


class BroadcastStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    admin_id: Mapped[int] = mapped_column(BigInteger, index=True)
    content_type: Mapped[str] = mapped_column(String(50))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    inline_button_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    inline_button_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filter_type: Mapped[str] = mapped_column(String(50), default="all")
    filter_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[BroadcastStatus] = mapped_column(
        SqlEnum(BroadcastStatus, name="broadcast_status"),
        default=BroadcastStatus.pending,
    )
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    blocked_count: Mapped[int] = mapped_column(Integer, default=0)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    recipients: Mapped[list["BroadcastRecipient"]] = relationship(
        "BroadcastRecipient", back_populates="broadcast", cascade="all, delete-orphan"
    )


class BroadcastRecipient(Base):
    __tablename__ = "broadcast_recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    broadcast_id: Mapped[int] = mapped_column(
        ForeignKey("broadcasts.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    broadcast: Mapped[Broadcast] = relationship("Broadcast", back_populates="recipients")
