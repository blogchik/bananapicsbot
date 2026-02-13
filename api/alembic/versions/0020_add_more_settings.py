"""add more system settings

Revision ID: 0020_add_more_settings
Revises: 0019_add_system_settings
Create Date: 2026-02-13 14:00:00.000000
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "0020_add_more_settings"
down_revision = "0019_add_system_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    settings_table = sa.table(
        "system_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("value_type", sa.String),
        sa.column("description", sa.Text),
        sa.column("created_at", sa.DateTime),
    )

    now = datetime.utcnow()
    op.bulk_insert(
        settings_table,
        [
            {
                "key": "stars_min_amount",
                "value": "70",
                "value_type": "int",
                "description": "Minimum stars amount for purchases",
                "created_at": now,
            },
            {
                "key": "generation_poll_interval_seconds",
                "value": "3",
                "value_type": "int",
                "description": "Interval between generation status checks (seconds)",
                "created_at": now,
            },
            {
                "key": "generation_poll_max_duration_seconds",
                "value": "300",
                "value_type": "int",
                "description": "Maximum time to wait for generation completion (seconds)",
                "created_at": now,
            },
            {
                "key": "rate_limit_rps",
                "value": "5",
                "value_type": "int",
                "description": "API rate limit - requests per second",
                "created_at": now,
            },
            {
                "key": "rate_limit_burst",
                "value": "10",
                "value_type": "int",
                "description": "API rate limit - burst size",
                "created_at": now,
            },
            {
                "key": "wavespeed_timeout_seconds",
                "value": "180",
                "value_type": "int",
                "description": "Wavespeed API request timeout (seconds)",
                "created_at": now,
            },
            {
                "key": "wavespeed_min_balance",
                "value": "1.0",
                "value_type": "float",
                "description": "Minimum Wavespeed balance before alert",
                "created_at": now,
            },
            {
                "key": "wavespeed_balance_cache_ttl_seconds",
                "value": "60",
                "value_type": "int",
                "description": "Cache TTL for Wavespeed balance (seconds)",
                "created_at": now,
            },
            {
                "key": "redis_cache_ttl_seconds",
                "value": "300",
                "value_type": "int",
                "description": "Default Redis cache TTL (seconds)",
                "created_at": now,
            },
            {
                "key": "redis_active_generation_ttl_seconds",
                "value": "900",
                "value_type": "int",
                "description": "Active generation data TTL in Redis (seconds)",
                "created_at": now,
            },
        ],
    )


def downgrade() -> None:
    # Remove the added settings
    op.execute(
        """
        DELETE FROM system_settings 
        WHERE key IN (
            'stars_min_amount',
            'generation_poll_interval_seconds',
            'generation_poll_max_duration_seconds',
            'rate_limit_rps',
            'rate_limit_burst',
            'wavespeed_timeout_seconds',
            'wavespeed_min_balance',
            'wavespeed_balance_cache_ttl_seconds',
            'redis_cache_ttl_seconds',
            'redis_active_generation_ttl_seconds'
        )
        """
    )
