"""Balance use cases."""
from typing import Optional, Sequence, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.entities.ledger import LedgerEntry, LedgerEntryType
from app.domain.entities.payment import Payment, PaymentStatus, PaymentProvider
from app.domain.interfaces.repositories import (
    ILedgerRepository,
    IPaymentRepository,
    IUserRepository,
)
from app.domain.interfaces.services import ICacheService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BalanceInfo:
    """User balance information."""
    balance: Decimal
    total_deposited: Decimal
    total_spent: Decimal
    referral_earnings: Decimal


class GetBalanceUseCase:
    """Get user balance and stats."""
    
    def __init__(
        self,
        ledger_repo: ILedgerRepository,
        cache: ICacheService,
    ):
        self._ledger_repo = ledger_repo
        self._cache = cache
    
    async def execute(self, telegram_id: int) -> BalanceInfo:
        """Execute use case."""
        # Try cache first
        cache_key = f"balance:{telegram_id}"
        cached = await self._cache.get(cache_key)
        if cached:
            return BalanceInfo(**cached)
        
        stats = await self._ledger_repo.get_user_stats(telegram_id)
        
        result = BalanceInfo(
            balance=Decimal(str(stats["balance"])),
            total_deposited=Decimal(str(stats["total_deposited"])),
            total_spent=Decimal(str(stats["total_spent"])),
            referral_earnings=Decimal(str(stats["referral_earnings"])),
        )
        
        # Cache for 1 minute
        await self._cache.set(
            cache_key,
            {
                "balance": str(result.balance),
                "total_deposited": str(result.total_deposited),
                "total_spent": str(result.total_spent),
                "referral_earnings": str(result.referral_earnings),
            },
            ttl=60,
        )
        
        return result


class AdjustBalanceUseCase:
    """Adjust user balance (admin action)."""
    
    def __init__(
        self,
        ledger_repo: ILedgerRepository,
        user_repo: IUserRepository,
        cache: ICacheService,
    ):
        self._ledger_repo = ledger_repo
        self._user_repo = user_repo
        self._cache = cache
    
    async def execute(
        self,
        telegram_id: int,
        amount: Decimal,
        reason: str,
        admin_id: int,
    ) -> LedgerEntry:
        """Execute use case."""
        # Verify user exists
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found")
        
        # Create ledger entry
        entry = await self._ledger_repo.create_entry(
            telegram_id=telegram_id,
            amount=amount,
            entry_type=LedgerEntryType.ADMIN_ADJUSTMENT,
            reason=f"Admin adjustment: {reason}",
            reference_id=f"admin:{admin_id}",
        )
        
        # Invalidate balance cache
        await self._cache.delete(f"balance:{telegram_id}")
        
        logger.info(
            "Balance adjusted by admin",
            telegram_id=telegram_id,
            amount=float(amount),
            reason=reason,
            admin_id=admin_id,
        )
        
        return entry


class ProcessPaymentUseCase:
    """Process payment completion."""
    
    def __init__(
        self,
        payment_repo: IPaymentRepository,
        ledger_repo: ILedgerRepository,
        user_repo: IUserRepository,
        cache: ICacheService,
        referral_bonus_percent: int = 10,
    ):
        self._payment_repo = payment_repo
        self._ledger_repo = ledger_repo
        self._user_repo = user_repo
        self._cache = cache
        self._referral_bonus_percent = referral_bonus_percent
    
    async def execute(
        self,
        payment_id: UUID,
        provider_payment_id: str,
    ) -> Payment:
        """Execute use case."""
        # Get payment
        payment = await self._payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status == PaymentStatus.COMPLETED:
            return payment  # Already processed
        
        # Update payment status
        await self._payment_repo.update_status(
            payment_id=payment_id,
            status=PaymentStatus.COMPLETED,
            provider_payment_id=provider_payment_id,
        )
        
        # Create ledger entry for deposit
        await self._ledger_repo.create_entry(
            telegram_id=payment.telegram_id,
            amount=payment.credits,
            entry_type=LedgerEntryType.DEPOSIT,
            reason=f"Payment: {payment.provider.value}",
            reference_id=str(payment_id),
        )
        
        # Invalidate balance cache
        await self._cache.delete(f"balance:{payment.telegram_id}")
        
        # Process referral bonus
        await self._process_referral_bonus(payment.telegram_id, payment.credits)
        
        logger.info(
            "Payment completed",
            payment_id=str(payment_id),
            telegram_id=payment.telegram_id,
            credits=float(payment.credits),
        )
        
        # Return updated payment
        return await self._payment_repo.get_by_id(payment_id)
    
    async def _process_referral_bonus(
        self,
        telegram_id: int,
        credits: Decimal,
    ) -> None:
        """Process referral bonus for referrer."""
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user or not user.referrer_id:
            return
        
        # Calculate bonus
        bonus = (credits * self._referral_bonus_percent) / 100
        if bonus <= 0:
            return
        
        # Credit referrer
        await self._ledger_repo.create_entry(
            telegram_id=user.referrer_id,
            amount=bonus,
            entry_type=LedgerEntryType.REFERRAL_BONUS,
            reason=f"Referral bonus from user {telegram_id}",
            reference_id=str(telegram_id),
        )
        
        # Invalidate referrer's balance cache
        await self._cache.delete(f"balance:{user.referrer_id}")
        
        logger.info(
            "Referral bonus credited",
            referrer_id=user.referrer_id,
            referred_id=telegram_id,
            bonus=float(bonus),
        )


class CreatePaymentUseCase:
    """Create new payment."""
    
    def __init__(
        self,
        payment_repo: IPaymentRepository,
        user_repo: IUserRepository,
        stars_exchange_rate: tuple[int, int] = (1000, 70),  # credits per stars
    ):
        self._payment_repo = payment_repo
        self._user_repo = user_repo
        self._stars_exchange_rate = stars_exchange_rate
    
    async def execute(
        self,
        telegram_id: int,
        provider: PaymentProvider,
        amount: Decimal,
        currency: str = "XTR",
    ) -> Payment:
        """Execute use case."""
        # Verify user exists
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found")
        
        if user.is_banned:
            raise ValueError("User is banned")
        
        # Calculate credits
        numerator, denominator = self._stars_exchange_rate
        credits = (amount * numerator) / denominator
        
        # Create payment
        payment = await self._payment_repo.create(
            telegram_id=telegram_id,
            provider=provider,
            amount=amount,
            credits=credits,
            currency=currency,
        )
        
        logger.info(
            "Payment created",
            payment_id=str(payment.id),
            telegram_id=telegram_id,
            amount=float(amount),
            credits=float(credits),
        )
        
        return payment
