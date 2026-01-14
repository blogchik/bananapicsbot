"""add generation and catalog models

Revision ID: 0002_add_generation_models
Revises: 0001_create_users_ledger
Create Date: 2026-01-14 22:05:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_generation_models"
down_revision = "0001_create_users_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_catalog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("supports_reference", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supports_aspect_ratio", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supports_style", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_catalog_key", "model_catalog", ["key"], unique=True)

    op.create_table(
        "model_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=20), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["model_catalog.id"]),
    )
    op.create_index("ix_model_prices_model_id", "model_prices", ["model_id"], unique=False)

    generation_status = sa.Enum(
        "pending",
        "configuring",
        "queued",
        "running",
        "completed",
        "failed",
        "cancelled",
        name="generation_status",
    )
    job_status = sa.Enum(
        "queued",
        "running",
        "completed",
        "failed",
        name="job_status",
    )

    op.create_table(
        "generation_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", generation_status, nullable=False),
        sa.Column("aspect_ratio", sa.String(length=50), nullable=True),
        sa.Column("style", sa.String(length=100), nullable=True),
        sa.Column("references_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["model_id"], ["model_catalog.id"]),
    )
    op.create_index("ix_generation_requests_user_id", "generation_requests", ["user_id"], unique=False)
    op.create_index("ix_generation_requests_model_id", "generation_requests", ["model_id"], unique=False)

    op.create_table(
        "generation_references",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=200), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["generation_requests.id"]),
    )
    op.create_index("ix_generation_references_request_id", "generation_references", ["request_id"], unique=False)

    op.create_table(
        "generation_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=200), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["generation_requests.id"]),
    )
    op.create_index("ix_generation_results_request_id", "generation_results", ["request_id"], unique=False)

    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("provider_job_id", sa.String(length=200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["generation_requests.id"]),
    )
    op.create_index("ix_generation_jobs_request_id", "generation_jobs", ["request_id"], unique=False)

    op.create_table(
        "trial_uses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["request_id"], ["generation_requests.id"]),
    )
    op.create_index("ix_trial_uses_user_id", "trial_uses", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trial_uses_user_id", table_name="trial_uses")
    op.drop_table("trial_uses")

    op.drop_index("ix_generation_jobs_request_id", table_name="generation_jobs")
    op.drop_table("generation_jobs")

    op.drop_index("ix_generation_results_request_id", table_name="generation_results")
    op.drop_table("generation_results")

    op.drop_index("ix_generation_references_request_id", table_name="generation_references")
    op.drop_table("generation_references")

    op.drop_index("ix_generation_requests_model_id", table_name="generation_requests")
    op.drop_index("ix_generation_requests_user_id", table_name="generation_requests")
    op.drop_table("generation_requests")

    op.drop_index("ix_model_prices_model_id", table_name="model_prices")
    op.drop_table("model_prices")

    op.drop_index("ix_model_catalog_key", table_name="model_catalog")
    op.drop_table("model_catalog")

    op.execute("DROP TYPE IF EXISTS generation_status")
    op.execute("DROP TYPE IF EXISTS job_status")
