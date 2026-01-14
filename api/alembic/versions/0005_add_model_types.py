"""add model type flags

Revision ID: 0005_add_model_types
Revises: 0004_update_provider
Create Date: 2026-01-14 22:28:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_add_model_types"
down_revision = "0004_update_provider"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "model_catalog",
        sa.Column(
            "supports_text_to_image",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "model_catalog",
        sa.Column(
            "supports_image_to_image",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.execute(
        "UPDATE model_catalog SET supports_text_to_image = true, "
        "supports_image_to_image = true, supports_reference = true "
        "WHERE key = 'seedream-v4'"
    )


def downgrade() -> None:
    op.drop_column("model_catalog", "supports_image_to_image")
    op.drop_column("model_catalog", "supports_text_to_image")
