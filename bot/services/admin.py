"""Admin service."""

import aiohttp

from core.container import get_container
from core.exceptions import APIError, APIConnectionError
from core.logging import get_logger

logger = get_logger(__name__)


class AdminService:
    """Admin-related business logic."""
    
    @staticmethod
    async def add_credits(
        telegram_id: int,
        credits: int,
        description: str | None = None,
    ) -> dict:
        """Add credits to user."""
        container = get_container()
        return await container.api_client.add_admin_credits(
            telegram_id=telegram_id,
            credits=credits,
            description=description,
        )
    
    @staticmethod
    async def get_stats() -> dict:
        """Get admin statistics."""
        container = get_container()
        return await container.api_client.get_admin_stats()
    
    @staticmethod
    async def get_users_list(
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get users list."""
        container = get_container()
        return await container.api_client.get_users_list(limit=limit, offset=offset)
    
    @staticmethod
    async def fetch_star_transactions(
        bot_token: str,
        offset: int,
        limit: int,
    ) -> list[dict]:
        """Fetch star transactions from Telegram API."""
        url = f"https://api.telegram.org/bot{bot_token}/getStarTransactions"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"offset": offset, "limit": limit}) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("description", "Telegram API error"))
                result = data.get("result") or {}
                return list(result.get("transactions") or [])
    
    @staticmethod
    async def refund_star_payment(
        bot_token: str,
        user_id: int,
        charge_id: str,
    ) -> tuple[bool, str | None]:
        """Refund star payment."""
        url = f"https://api.telegram.org/bot{bot_token}/refundStarPayment"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data={"user_id": user_id, "telegram_payment_charge_id": charge_id},
            ) as resp:
                payload = await resp.json()
                if payload.get("ok"):
                    return True, None
                return False, str(payload.get("description"))
    
    @staticmethod
    async def process_refund(
        bot_token: str,
        user_id: int,
        stars_amount: int,
    ) -> tuple[int, int, list[str]]:
        """
        Process refund for user.
        
        Returns:
            Tuple of (refunded_total, refunded_count, errors)
        """
        refunded_total = 0
        refunded_count = 0
        errors: list[str] = []
        offset = 0
        limit = 100
        
        while refunded_total < stars_amount:
            transactions = await AdminService.fetch_star_transactions(bot_token, offset, limit)
            if not transactions:
                break
            
            for tx in reversed(transactions):
                source = tx.get("source") or {}
                if source.get("type") != "user":
                    continue
                if source.get("transaction_type") != "invoice_payment":
                    continue
                
                user = source.get("user") or {}
                if int(user.get("id", 0)) != user_id:
                    continue
                
                amount = int(tx.get("amount") or 0)
                if amount <= 0:
                    continue
                
                charge_id = tx.get("id")
                if not charge_id:
                    continue
                
                ok, error = await AdminService.refund_star_payment(
                    bot_token, user_id, charge_id
                )
                
                if ok:
                    refunded_total += amount
                    refunded_count += 1
                    if refunded_total >= stars_amount:
                        break
                elif error:
                    errors.append(error)
            
            offset += limit
        
        return refunded_total, refunded_count, errors
    
    # === New methods for admin panel ===
    
    @staticmethod
    async def get_overview_stats() -> dict:
        """Get overview statistics for admin panel."""
        container = get_container()
        try:
            return await container.api_client.get_admin_overview_stats()
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get overview stats", error=str(e))
            return {"error": True}
    
    @staticmethod
    async def get_user_stats() -> dict:
        """Get user statistics."""
        container = get_container()
        try:
            return await container.api_client.get_admin_user_stats()
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get user stats", error=str(e))
            return {"error": True}
    
    @staticmethod
    async def get_generation_stats() -> dict:
        """Get generation statistics."""
        container = get_container()
        try:
            return await container.api_client.get_admin_generation_stats()
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get generation stats", error=str(e))
            return {"error": True}
    
    @staticmethod
    async def get_revenue_stats() -> dict:
        """Get revenue statistics."""
        container = get_container()
        try:
            return await container.api_client.get_admin_revenue_stats()
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get revenue stats", error=str(e))
            return {"error": True}
    
    @staticmethod
    async def search_users(query: str) -> list[dict]:
        """Search users by ID or username."""
        container = get_container()
        try:
            return await container.api_client.search_users(query)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to search users", error=str(e))
            # If search endpoint not available, try to get user directly by ID
            if query.isdigit():
                try:
                    user = await container.api_client.get_user_by_telegram_id(int(query))
                    if user:
                        return [user]
                except Exception:
                    pass
            return []
    
    @staticmethod
    async def get_user(telegram_id: int) -> dict | None:
        """Get user by telegram ID."""
        container = get_container()
        try:
            return await container.api_client.get_user_by_telegram_id(telegram_id)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get user", error=str(e))
            return None
    
    @staticmethod
    async def get_users_page(page: int = 0, per_page: int = 20) -> dict:
        """Get paginated users list."""
        container = get_container()
        try:
            return await container.api_client.get_users_page(page=page, per_page=per_page)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get users page", error=str(e))
            return {"users": [], "total": 0, "error": True}
    
    @staticmethod
    async def toggle_ban(telegram_id: int) -> dict:
        """Toggle user ban status."""
        container = get_container()
        try:
            return await container.api_client.toggle_user_ban(telegram_id)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to toggle ban", error=str(e))
            return {"error": True, "message": str(e)}
    
    @staticmethod
    async def adjust_credits(
        telegram_id: int,
        amount: int,
        reason: str = "Admin adjustment",
    ) -> dict:
        """Adjust user credits (add or remove)."""
        container = get_container()
        try:
            # Use existing add_credits endpoint with positive/negative amount
            if amount >= 0:
                return await container.api_client.add_admin_credits(
                    telegram_id=telegram_id,
                    credits=amount,
                    description=reason,
                )
            else:
                # For negative adjustments, try adjust endpoint or return error
                return await container.api_client.adjust_user_credits(
                    telegram_id=telegram_id,
                    amount=amount,
                    reason=reason,
                )
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to adjust credits", error=str(e))
            return {"error": True, "message": str(e)}
    
    @staticmethod
    async def get_user_generations(
        telegram_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """Get user's recent generations."""
        container = get_container()
        try:
            return await container.api_client.get_user_generations(
                telegram_id=telegram_id,
                limit=limit,
            )
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get user generations", error=str(e))
            return []
    
    @staticmethod
    async def refund_generation(telegram_id: int, generation_id: str) -> dict:
        """Refund a specific generation."""
        container = get_container()
        try:
            return await container.api_client.refund_generation(
                telegram_id=telegram_id,
                generation_id=generation_id,
            )
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to refund generation", error=str(e))
            return {"error": True, "message": str(e)}
    
    @staticmethod
    async def start_broadcast(broadcast_data: dict) -> dict:
        """Start a new broadcast."""
        container = get_container()
        try:
            return await container.api_client.start_broadcast(broadcast_data)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to start broadcast", error=str(e))
            # Return mock broadcast_id for now since API endpoint not implemented
            return {"broadcast_id": "not_implemented", "error": True}
    
    @staticmethod
    async def get_broadcasts(limit: int = 10) -> list[dict]:
        """Get broadcast history."""
        container = get_container()
        try:
            return await container.api_client.get_broadcasts(limit=limit)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get broadcasts", error=str(e))
            return []
    
    @staticmethod
    async def get_broadcast_status(broadcast_id: str) -> dict:
        """Get broadcast status."""
        container = get_container()
        try:
            return await container.api_client.get_broadcast_status(broadcast_id)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get broadcast status", error=str(e))
            return {"error": True, "status": "unknown"}
