"""Admin service."""

import aiohttp
from core.container import get_container
from core.exceptions import APIConnectionError, APIError
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
    async def get_user_unrefunded_transactions(
        bot_token: str,
        user_id: int,
    ) -> list[dict]:
        """
        Get user's star payment transactions.
        
        Returns list of payment transactions for the user.
        Each transaction has: id, amount, date
        
        Note: Telegram API doesn't provide a way to check if a payment was
        already refunded without actually refunding it. So we return all
        payments and handle CHARGE_ALREADY_REFUNDED in the UI when user
        tries to refund.
        """
        payments: list[dict] = []
        offset = 0
        limit = 100
        pages_checked = 0
        max_pages = 10

        while pages_checked < max_pages:
            try:
                transactions = await AdminService.fetch_star_transactions(bot_token, offset, limit)
            except RuntimeError as e:
                logger.warning("Failed to fetch transactions", error=str(e))
                break

            if not transactions:
                break

            pages_checked += 1

            for tx in transactions:
                tx_id = tx.get("id")
                if not tx_id:
                    continue

                source = tx.get("source") or {}
                tx_type = source.get("type")
                tx_transaction_type = source.get("transaction_type")
                tx_user = source.get("user") or {}
                tx_user_id = tx_user.get("id")

                # Only user payments (not refunds which have "receiver" field)
                if tx_type != "user":
                    continue

                # Only invoice payments
                if tx_transaction_type and tx_transaction_type != "invoice_payment":
                    continue

                # Only this user
                if tx_user_id is None or int(tx_user_id) != user_id:
                    continue

                amount = int(tx.get("amount") or 0)
                if amount <= 0:
                    continue

                # Get date from transaction
                tx_date = tx.get("date", 0)

                payments.append({
                    "id": tx_id,
                    "amount": amount,
                    "date": tx_date,
                })

            offset += limit

        # Sort by date descending (newest first)
        payments.sort(key=lambda x: x.get("date", 0), reverse=True)

        return payments



    @staticmethod
    async def refund_single_transaction(
        bot_token: str,
        user_id: int,
        tx_id: str,
    ) -> tuple[bool, int, str | None]:
        """
        Refund a single transaction.
        
        Returns: (success, amount, error_message)
        """
        # First, get the transaction to find amount
        transactions = await AdminService.get_user_unrefunded_transactions(bot_token, user_id)

        tx_amount = 0
        for tx in transactions:
            if tx["id"] == tx_id:
                tx_amount = tx["amount"]
                break

        if tx_amount == 0:
            return False, 0, "Tranzaksiya topilmadi yoki allaqachon qaytarilgan"

        ok, error = await AdminService.refund_star_payment(bot_token, user_id, tx_id)

        if ok:
            return True, tx_amount, None

        # Parse error
        if error and "CHARGE_ALREADY_REFUNDED" in error:
            return False, 0, "Tranzaksiya allaqachon qaytarilgan"
        elif error and "USER_BOT_INVALID" in error:
            return False, 0, "Foydalanuvchi bot bilan aloqa o'chirilgan"
        elif error and "CHARGE_NOT_FOUND" in error:
            return False, 0, "Tranzaksiya topilmadi (eskirgan)"

        return False, 0, error

    @staticmethod
    async def process_refund(
        bot_token: str,
        user_id: int,
        stars_amount: int,
    ) -> tuple[int, int, list[str], bool]:
        """
        Process refund for user.
        
        Returns:
            Tuple of (refunded_total, refunded_count, errors, user_has_payments)
        """
        refunded_total = 0
        refunded_count = 0
        errors: list[str] = []
        user_has_payments = False
        offset = 0
        limit = 100
        pages_checked = 0
        max_pages = 10  # Limit to avoid infinite loop

        while refunded_total < stars_amount and pages_checked < max_pages:
            try:
                transactions = await AdminService.fetch_star_transactions(bot_token, offset, limit)
            except RuntimeError as e:
                errors.append(f"API xatosi: {str(e)}")
                break

            if not transactions:
                logger.info("No more transactions found", offset=offset)
                break

            pages_checked += 1
            logger.info(
                "Processing transactions page",
                page=pages_checked,
                count=len(transactions),
                user_id=user_id,
            )

            for tx in transactions:
                source = tx.get("source") or {}
                tx_type = source.get("type")
                tx_transaction_type = source.get("transaction_type")
                tx_user = source.get("user") or {}
                tx_user_id = tx_user.get("id")

                logger.info(
                    "Checking transaction",
                    tx_id=tx.get("id"),
                    source_type=tx_type,
                    transaction_type=tx_transaction_type,
                    tx_user_id=tx_user_id,
                    target_user_id=user_id,
                    amount=tx.get("amount"),
                )

                if tx_type != "user":
                    continue

                # Check if this is a payment (not a refund which has negative amount)
                # transaction_type might be "invoice_payment" or might not exist
                if tx_transaction_type and tx_transaction_type != "invoice_payment":
                    continue

                if tx_user_id is None or int(tx_user_id) != user_id:
                    continue

                # User has made payments to this bot
                user_has_payments = True

                amount = int(tx.get("amount") or 0)
                if amount <= 0:
                    # Negative amount means it was already refunded
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
                    logger.info(
                        "Star payment refunded",
                        user_id=user_id,
                        charge_id=charge_id,
                        amount=amount,
                    )
                    if refunded_total >= stars_amount:
                        break
                elif error:
                    # Parse Telegram API error
                    if "CHARGE_ALREADY_REFUNDED" in error:
                        errors.append("Tranzaksiya allaqachon qaytarilgan")
                    elif "USER_BOT_INVALID" in error:
                        errors.append("Foydalanuvchi bot bilan aloqa o'chirilgan")
                    elif "CHARGE_NOT_FOUND" in error:
                        errors.append("Tranzaksiya topilmadi (eskirgan)")
                    else:
                        errors.append(error)

            offset += limit

        return refunded_total, refunded_count, errors, user_has_payments

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
            # Both positive and negative use same endpoint
            result = await container.api_client.add_admin_credits(
                telegram_id=telegram_id,
                credits=amount,
                description=reason,
            )
            # Transform response to expected format
            return {
                "new_balance": result.get("new_balance", 0),
                "old_balance": result.get("old_balance", 0),
                "amount": result.get("amount", amount),
            }
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

    # ============ Broadcast ============

    @staticmethod
    async def create_broadcast(
        admin_id: int,
        content_type: str,
        text: str | None = None,
        media_file_id: str | None = None,
        inline_button_text: str | None = None,
        inline_button_url: str | None = None,
        filter_type: str = "all",
    ) -> dict:
        """Create a new broadcast."""
        container = get_container()
        try:
            return await container.api_client.create_broadcast(
                admin_id=admin_id,
                content_type=content_type,
                text=text,
                media_file_id=media_file_id,
                inline_button_text=inline_button_text,
                inline_button_url=inline_button_url,
                filter_type=filter_type,
            )
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to create broadcast", error=str(e))
            raise

    @staticmethod
    async def start_broadcast(public_id: str) -> dict:
        """Start sending a broadcast."""
        container = get_container()
        try:
            return await container.api_client.start_broadcast(public_id)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to start broadcast", error=str(e))
            raise

    @staticmethod
    async def cancel_broadcast(public_id: str) -> dict:
        """Cancel a broadcast."""
        container = get_container()
        try:
            return await container.api_client.cancel_broadcast(public_id)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to cancel broadcast", error=str(e))
            raise

    @staticmethod
    async def get_broadcasts(limit: int = 10) -> list[dict]:
        """Get broadcast history."""
        container = get_container()
        try:
            result = await container.api_client.get_broadcasts(limit=limit)
            return result.get("broadcasts", [])
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get broadcasts", error=str(e))
            return []

    @staticmethod
    async def get_broadcast_status(public_id: str) -> dict:
        """Get broadcast status."""
        container = get_container()
        try:
            return await container.api_client.get_broadcast_status(public_id)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get broadcast status", error=str(e))
            return {"error": True, "status": "unknown"}

    @staticmethod
    async def get_users_count(filter_type: str = "all") -> int:
        """Get users count by filter."""
        container = get_container()
        try:
            result = await container.api_client.get_users_count(filter_type)
            return result.get("count", 0)
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get users count", error=str(e))
            return 0

    @staticmethod
    async def get_user_payments(
        telegram_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """Get user's payment history."""
        container = get_container()
        try:
            return await container.api_client.get_user_payments(
                telegram_id=telegram_id,
                limit=limit,
            )
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get user payments", error=str(e))
            return []

    @staticmethod
    async def get_stars_settings() -> dict:
        """Get stars payment settings."""
        container = get_container()
        try:
            return await container.api_client.get_stars_options()
        except (APIError, APIConnectionError) as e:
            logger.warning("Failed to get stars settings", error=str(e))
            return {
                "exchange_numerator": 1,
                "exchange_denominator": 1,
            }

