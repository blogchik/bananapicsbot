"""add more system settings

Revision ID: 0020_add_more_settings
Revises: 0019_add_system_settings
Create Date: 2026-02-13 14:00:00.000000
"""

from alembic import op

revision = "0020_add_more_settings"
down_revision = "0019_add_system_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use INSERT ... ON CONFLICT DO NOTHING to avoid duplicate key errors
    op.execute(
        """
        INSERT INTO system_settings (key, value, value_type, description, created_at)
        VALUES 
            ('stars_min_amount', '70', 'int', 'Minimum stars amount for purchases', NOW()),
            ('generation_poll_interval_seconds', '3', 'int', 'Interval between generation status checks (seconds)', NOW()),
            ('generation_poll_max_duration_seconds', '300', 'int', 'Maximum time to wait for generation completion (seconds)', NOW()),
            ('rate_limit_rps', '5', 'int', 'API rate limit - requests per second', NOW()),
            ('rate_limit_burst', '10', 'int', 'API rate limit - burst size', NOW()),
            ('wavespeed_timeout_seconds', '180', 'int', 'Wavespeed API request timeout (seconds)', NOW()),
            ('wavespeed_min_balance', '1.0', 'float', 'Minimum Wavespeed balance before alert', NOW()),
            ('wavespeed_balance_cache_ttl_seconds', '60', 'int', 'Cache TTL for Wavespeed balance (seconds)', NOW()),
            ('redis_cache_ttl_seconds', '300', 'int', 'Default Redis cache TTL (seconds)', NOW()),
            ('redis_active_generation_ttl_seconds', '900', 'int', 'Active generation data TTL in Redis (seconds)', NOW())
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
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
