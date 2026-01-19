"""Repository interfaces - data access contracts."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Optional, Sequence
from uuid import UUID

from ..entities.broadcast import Broadcast, BroadcastContentType, BroadcastStatus
from ..entities.generation import Generation, GenerationCreate, GenerationStatus
from ..entities.ledger import LedgerEntry, LedgerEntryType
from ..entities.model import Model
from ..entities.payment import Payment, PaymentProvider, PaymentStatus
from ..entities.user import User, UserCreate, UserUpdate


class IUserRepository(ABC):
    """User repository interface."""

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        pass

    @abstractmethod
    async def create(self, data: UserCreate) -> User:
        """Create new user."""
        pass

    @abstractmethod
    async def update(self, telegram_id: int, data: UserUpdate) -> Optional[User]:
        """Update user."""
        pass

    @abstractmethod
    async def search(
        self,
        query_str: Optional[str] = None,
        is_banned: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[User]:
        """Search users with filters."""
        pass

    @abstractmethod
    async def count_total(self) -> int:
        """Get total users count."""
        pass

    @abstractmethod
    async def count_referrals(self, telegram_id: int) -> int:
        """Count user's referrals."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        pass

    @abstractmethod
    async def ban_user(self, telegram_id: int, reason: Optional[str] = None) -> bool:
        """Ban user."""
        pass

    @abstractmethod
    async def unban_user(self, telegram_id: int) -> bool:
        """Unban user."""
        pass


class IGenerationRepository(ABC):
    """Generation repository interface."""

    @abstractmethod
    async def get_by_id(self, generation_id: UUID) -> Optional[Generation]:
        """Get generation by ID."""
        pass

    @abstractmethod
    async def create(self, data: GenerationCreate) -> Generation:
        """Create new generation."""
        pass

    @abstractmethod
    async def update_status(
        self,
        generation_id: UUID,
        status: GenerationStatus,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update generation status."""
        pass

    @abstractmethod
    async def get_user_generations(
        self,
        telegram_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Generation]:
        """Get user's generations."""
        pass

    @abstractmethod
    async def count_user_generations(
        self,
        telegram_id: int,
        status: Optional[GenerationStatus] = None,
    ) -> int:
        """Count user's generations."""
        pass

    @abstractmethod
    async def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get generation statistics."""
        pass


class IModelRepository(ABC):
    """Model repository interface."""

    @abstractmethod
    async def get_by_id(self, model_id: int) -> Optional[Model]:
        """Get model by ID."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Model]:
        """Get model by slug."""
        pass

    @abstractmethod
    async def get_active_models(self) -> Sequence[Model]:
        """Get all active models."""
        pass

    @abstractmethod
    async def get_price(
        self,
        model_id: int,
        generation_type: str,
    ) -> Optional[Decimal]:
        """Get current model price."""
        pass


class ILedgerRepository(ABC):
    """Ledger repository interface."""

    @abstractmethod
    async def create_entry(
        self,
        telegram_id: int,
        amount: Decimal,
        entry_type: LedgerEntryType,
        reason: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> LedgerEntry:
        """Create ledger entry."""
        pass

    @abstractmethod
    async def get_balance(self, telegram_id: int) -> Decimal:
        """Get user balance."""
        pass

    @abstractmethod
    async def get_user_entries(
        self,
        telegram_id: int,
        entry_type: Optional[LedgerEntryType] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[LedgerEntry]:
        """Get user's ledger entries."""
        pass

    @abstractmethod
    async def get_revenue_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue statistics."""
        pass


class IPaymentRepository(ABC):
    """Payment repository interface."""

    @abstractmethod
    async def create(
        self,
        telegram_id: int,
        provider: PaymentProvider,
        amount: Decimal,
        credits: Decimal,
        currency: str = "XTR",
    ) -> Payment:
        """Create payment record."""
        pass

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID."""
        pass

    @abstractmethod
    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        provider_payment_id: Optional[str] = None,
    ) -> bool:
        """Update payment status."""
        pass

    @abstractmethod
    async def get_user_payments(
        self,
        telegram_id: int,
        status: Optional[PaymentStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Payment]:
        """Get user's payments."""
        pass

    @abstractmethod
    async def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get payment statistics."""
        pass


class IBroadcastRepository(ABC):
    """Broadcast repository interface."""

    @abstractmethod
    async def create(
        self,
        admin_id: int,
        content_type: BroadcastContentType,
        content: str,
        media_file_id: Optional[str] = None,
        total_recipients: int = 0,
    ) -> Broadcast:
        """Create broadcast."""
        pass

    @abstractmethod
    async def get_by_id(self, broadcast_id: UUID) -> Optional[Broadcast]:
        """Get broadcast by ID."""
        pass

    @abstractmethod
    async def update_status(
        self,
        broadcast_id: UUID,
        status: BroadcastStatus,
    ) -> bool:
        """Update broadcast status."""
        pass

    @abstractmethod
    async def get_all(
        self,
        status: Optional[BroadcastStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Broadcast]:
        """Get broadcasts list."""
        pass

    @abstractmethod
    async def cancel(self, broadcast_id: UUID) -> bool:
        """Cancel broadcast."""
        pass
