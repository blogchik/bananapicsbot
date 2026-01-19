"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class GenerationStatusEnum(str, PyEnum):
    """Generation status enum."""

    pending = "pending"
    configuring = "configuring"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class JobStatusEnum(str, PyEnum):
    """Job status enum."""

    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class PaymentStatusEnum(str, PyEnum):
    """Payment status enum."""

    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"
    cancelled = "cancelled"


class BroadcastStatusEnum(str, PyEnum):
    """Broadcast status enum."""

    pending = "pending"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class UserModel(Base):
    """User ORM model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    referral_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="uz")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    referrer: Mapped[Optional["UserModel"]] = relationship(
        "UserModel", remote_side=[id], back_populates="referrals"
    )
    referrals: Mapped[list["UserModel"]] = relationship(
        "UserModel", back_populates="referrer"
    )
    ledger_entries: Mapped[list["LedgerEntryModel"]] = relationship(
        "LedgerEntryModel", back_populates="user"
    )
    generations: Mapped[list["GenerationModel"]] = relationship(
        "GenerationModel", back_populates="user"
    )
    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel", back_populates="user"
    )
    trial_uses: Mapped[list["TrialUseModel"]] = relationship(
        "TrialUseModel", back_populates="user"
    )


class LedgerEntryModel(Base):
    """Ledger entry ORM model."""

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    entry_type: Mapped[str] = mapped_column(String(50))
    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[UserModel] = relationship("UserModel", back_populates="ledger_entries")

    __table_args__ = (
        Index("ix_ledger_user_created", "user_id", "created_at"),
    )


class ModelCatalogModel(Base):
    """Model catalog ORM model."""

    __tablename__ = "model_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supports_text_to_image: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_image_to_image: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_aspect_ratio: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_style: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    prices: Mapped[list["ModelPriceModel"]] = relationship(
        "ModelPriceModel", back_populates="model"
    )
    generations: Mapped[list["GenerationModel"]] = relationship(
        "GenerationModel", back_populates="model"
    )


class ModelPriceModel(Base):
    """Model price ORM model."""

    __tablename__ = "model_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("model_catalog.id"), index=True)
    currency: Mapped[str] = mapped_column(String(20), default="credit")
    unit_price: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    model: Mapped[ModelCatalogModel] = relationship(
        "ModelCatalogModel", back_populates="prices"
    )


class GenerationModel(Base):
    """Generation ORM model."""

    __tablename__ = "generation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("model_catalog.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[GenerationStatusEnum] = mapped_column(
        Enum(GenerationStatusEnum), default=GenerationStatusEnum.pending
    )
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    aspect_ratio: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    input_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    references_count: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    wavespeed_request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[UserModel] = relationship("UserModel", back_populates="generations")
    model: Mapped[ModelCatalogModel] = relationship(
        "ModelCatalogModel", back_populates="generations"
    )
    references: Mapped[list["GenerationReferenceModel"]] = relationship(
        "GenerationReferenceModel", back_populates="generation"
    )
    results: Mapped[list["GenerationResultModel"]] = relationship(
        "GenerationResultModel", back_populates="generation"
    )
    jobs: Mapped[list["GenerationJobModel"]] = relationship(
        "GenerationJobModel", back_populates="generation"
    )

    __table_args__ = (
        Index("ix_generation_user_status", "user_id", "status"),
        Index("ix_generation_created", "created_at"),
    )


class GenerationReferenceModel(Base):
    """Generation reference ORM model."""

    __tablename__ = "generation_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"), index=True
    )
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    generation: Mapped[GenerationModel] = relationship(
        "GenerationModel", back_populates="references"
    )


class GenerationResultModel(Base):
    """Generation result ORM model."""

    __tablename__ = "generation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"), index=True
    )
    url: Mapped[str] = mapped_column(String(500))
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    generation: Mapped[GenerationModel] = relationship(
        "GenerationModel", back_populates="results"
    )


class GenerationJobModel(Base):
    """Generation job ORM model."""

    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"), index=True
    )
    wavespeed_request_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[JobStatusEnum] = mapped_column(
        Enum(JobStatusEnum), default=JobStatusEnum.queued
    )
    output_urls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    generation: Mapped[GenerationModel] = relationship(
        "GenerationModel", back_populates="jobs"
    )


class TrialUseModel(Base):
    """Trial use ORM model."""

    __tablename__ = "trial_uses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    generation_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[UserModel] = relationship("UserModel", back_populates="trial_uses")


class PaymentModel(Base):
    """Payment ORM model."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)  # Stars amount
    credits: Mapped[int] = mapped_column(Integer)  # Credits to add
    provider: Mapped[str] = mapped_column(String(50))
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending
    )
    currency: Mapped[str] = mapped_column(String(10), default="XTR")
    telegram_charge_id: Mapped[Optional[str]] = mapped_column(
        String(200), unique=True, nullable=True
    )
    provider_charge_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    invoice_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[UserModel] = relationship("UserModel", back_populates="payments")

    __table_args__ = (
        Index("ix_payment_user_status", "user_id", "status"),
        Index("ix_payment_created", "created_at"),
    )


class BroadcastModel(Base):
    """Broadcast ORM model."""

    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_by: Mapped[int] = mapped_column(Integer, index=True)
    content_type: Mapped[str] = mapped_column(String(20))
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[BroadcastStatusEnum] = mapped_column(
        Enum(BroadcastStatusEnum), default=BroadcastStatusEnum.pending
    )
    target_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
