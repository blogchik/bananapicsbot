"""add generation indexes

Revision ID: 0016
Revises: 0015
Create Date: 2026-01-17

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016_add_generation_indexes"
down_revision: Union[str, None] = "0015_create_broadcasts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_generation_requests_user_status_created_at "
        "ON generation_requests (user_id, status, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_generation_requests_status_created_at "
        "ON generation_requests (status, created_at)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_generation_results_request_id ON generation_results (request_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_generation_jobs_request_id ON generation_jobs (request_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_generation_jobs_request_id")
    op.execute("DROP INDEX IF EXISTS ix_generation_results_request_id")
    op.execute("DROP INDEX IF EXISTS ix_generation_requests_status_created_at")
    op.execute("DROP INDEX IF EXISTS ix_generation_requests_user_status_created_at")
