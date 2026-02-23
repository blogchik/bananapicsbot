"""Tests for search_users - verifies that total count uses the same filters as the result query."""

from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest


class TestSearchUsersCount:
    """Test that search_users returns the correct total count when filtering."""

    def _make_session(self, users_result, count_result):
        """Create a mock AsyncSession that returns given users and count."""
        session = MagicMock()

        execute_users = MagicMock()
        execute_users.scalars.return_value.all.return_value = users_result

        execute_count = MagicMock()
        execute_count.scalar.return_value = count_result

        # First call → count query, second call → data query
        session.execute = AsyncMock(side_effect=[execute_count, execute_users])
        return session

    @pytest.mark.asyncio
    async def test_no_filter_returns_all_users_count(self):
        """Without a query filter the total should equal count of all users."""
        from app.services.admin_service import AdminService

        mock_users = [MagicMock(), MagicMock()]
        session = self._make_session(users_result=mock_users, count_result=2)

        service = AdminService(session)
        users, total = await service.search_users(query=None)

        assert total == 2
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_filter_by_telegram_id_returns_filtered_count(self):
        """When filtering by telegram_id, total must reflect only matching users."""
        from app.services.admin_service import AdminService

        mock_user = MagicMock()
        # DB has 100 users but only 1 matches the telegram_id filter
        session = self._make_session(users_result=[mock_user], count_result=1)

        service = AdminService(session)
        users, total = await service.search_users(query="123456789")

        # total must be 1 (filtered), not 100 (all users)
        assert total == 1
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_filter_by_referral_code_returns_filtered_count(self):
        """When filtering by referral_code, total must reflect only matching users."""
        from app.services.admin_service import AdminService

        # DB has 50 users but only 3 match the referral_code filter
        session = self._make_session(users_result=[MagicMock(), MagicMock(), MagicMock()], count_result=3)

        service = AdminService(session)
        users, total = await service.search_users(query="ABC")

        assert total == 3
        assert len(users) == 3

    @pytest.mark.asyncio
    async def test_filter_with_no_matches_returns_zero_count(self):
        """When no users match the filter, total must be 0."""
        from app.services.admin_service import AdminService

        session = self._make_session(users_result=[], count_result=0)

        service = AdminService(session)
        users, total = await service.search_users(query="nonexistent_code")

        assert total == 0
        assert users == []

    @pytest.mark.asyncio
    async def test_count_query_applies_same_filter_as_data_query(self):
        """
        Regression test for bug #63: the count query must carry the same WHERE
        clause as the data query so the returned total matches the actual filter.
        """
        from app.db.models import User
        from app.services.admin_service import AdminService

        captured_queries = []

        async def capture_execute(stmt, *args, **kwargs):
            captured_queries.append(stmt)
            result = MagicMock()
            if len(captured_queries) == 1:
                # Count query
                result.scalar.return_value = 1
            else:
                # Data query
                result.scalars.return_value.all.return_value = [MagicMock()]
            return result

        session = MagicMock()
        session.execute = capture_execute

        service = AdminService(session)
        await service.search_users(query="99999")

        assert len(captured_queries) == 2

        count_query_str = str(captured_queries[0])
        data_query_str = str(captured_queries[1])

        # Both queries must contain the telegram_id filter
        assert "telegram_id" in count_query_str, (
            "Count query is missing the telegram_id filter — bug #63 regression"
        )
        assert "telegram_id" in data_query_str
