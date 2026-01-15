"""Generation use cases."""
from typing import Optional, Sequence, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.entities.generation import Generation, GenerationCreate, GenerationStatus
from app.domain.entities.ledger import LedgerEntryType
from app.domain.interfaces.repositories import (
    IGenerationRepository,
    IModelRepository,
    ILedgerRepository,
    IUserRepository,
)
from app.domain.interfaces.services import ICacheService, IWavespeedService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationResult:
    """Generation result DTO."""
    generation: Generation
    result_urls: Sequence[str]


class CreateGenerationUseCase:
    """Create new image generation."""
    
    def __init__(
        self,
        generation_repo: IGenerationRepository,
        model_repo: IModelRepository,
        ledger_repo: ILedgerRepository,
        user_repo: IUserRepository,
        cache: ICacheService,
    ):
        self._generation_repo = generation_repo
        self._model_repo = model_repo
        self._ledger_repo = ledger_repo
        self._user_repo = user_repo
        self._cache = cache
    
    async def execute(
        self,
        telegram_id: int,
        model_slug: str,
        prompt: str,
        generation_type: str = "t2i",  # t2i or i2i
        negative_prompt: Optional[str] = None,
        input_image_url: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        input_params: Optional[Dict[str, Any]] = None,
    ) -> Generation:
        """Execute use case."""
        # Get user
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found")
        
        if user.is_banned:
            raise ValueError("User is banned")
        
        # Get model
        model = await self._model_repo.get_by_slug(model_slug)
        if not model:
            raise ValueError(f"Model not found: {model_slug}")
        
        if not model.is_active:
            raise ValueError(f"Model is not active: {model_slug}")
        
        # Check model supports generation type
        if generation_type == "t2i" and not model.supports_t2i:
            raise ValueError(f"Model doesn't support text-to-image: {model_slug}")
        if generation_type == "i2i" and not model.supports_i2i:
            raise ValueError(f"Model doesn't support image-to-image: {model_slug}")
        
        # Get price
        price = await self._model_repo.get_price(model.id, generation_type)
        if price is None:
            raise ValueError(f"No price configured for model: {model_slug}")
        
        # Check balance or trial
        balance = await self._ledger_repo.get_balance(telegram_id)
        use_trial = False
        
        if balance < price:
            # Check trial
            if user.trial_remaining > 0:
                use_trial = True
            else:
                raise ValueError("Insufficient balance")
        
        # Create generation record
        generation_data = GenerationCreate(
            telegram_id=telegram_id,
            model_id=model.id,
            prompt=prompt,
            negative_prompt=negative_prompt,
            input_image_url=input_image_url,
            input_params=input_params or {},
            width=width,
            height=height,
            credits_charged=Decimal("0") if use_trial else price,
        )
        
        generation = await self._generation_repo.create(generation_data)
        
        # Charge credits or use trial
        if use_trial:
            # Decrease trial
            from app.domain.entities.user import UserUpdate
            await self._user_repo.update(
                telegram_id,
                UserUpdate(trial_remaining=user.trial_remaining - 1),
            )
            await self._cache.delete(f"user:{telegram_id}")
            
            logger.info(
                "Trial generation started",
                telegram_id=telegram_id,
                generation_id=str(generation.id),
                remaining=user.trial_remaining - 1,
            )
        else:
            # Charge credits
            await self._ledger_repo.create_entry(
                telegram_id=telegram_id,
                amount=-price,
                entry_type=LedgerEntryType.GENERATION,
                reason=f"Generation: {model_slug}",
                reference_id=str(generation.id),
            )
            
            logger.info(
                "Generation started",
                telegram_id=telegram_id,
                generation_id=str(generation.id),
                credits_charged=float(price),
            )
        
        # Store in active generations cache
        await self._cache.set(
            f"active_gen:{telegram_id}",
            str(generation.id),
            ttl=900,  # 15 minutes
        )
        
        return generation


class GetGenerationStatusUseCase:
    """Get generation status and results."""
    
    def __init__(
        self,
        generation_repo: IGenerationRepository,
        cache: ICacheService,
    ):
        self._generation_repo = generation_repo
        self._cache = cache
    
    async def execute(
        self,
        generation_id: UUID,
        telegram_id: Optional[int] = None,
    ) -> Optional[GenerationResult]:
        """Execute use case."""
        generation = await self._generation_repo.get_by_id(generation_id)
        
        if not generation:
            return None
        
        # Security check
        if telegram_id and generation.telegram_id != telegram_id:
            return None
        
        # Get result URLs if completed
        result_urls = []
        if generation.status == GenerationStatus.COMPLETED:
            result_urls = await self._generation_repo.get_result_urls(generation_id)
        
        return GenerationResult(
            generation=generation,
            result_urls=result_urls,
        )


class GetUserGenerationsUseCase:
    """Get user's generation history."""
    
    def __init__(
        self,
        generation_repo: IGenerationRepository,
    ):
        self._generation_repo = generation_repo
    
    async def execute(
        self,
        telegram_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Generation]:
        """Execute use case."""
        return await self._generation_repo.get_user_generations(
            telegram_id=telegram_id,
            offset=offset,
            limit=limit,
        )


class RefundGenerationUseCase:
    """Refund a failed generation."""
    
    def __init__(
        self,
        generation_repo: IGenerationRepository,
        ledger_repo: ILedgerRepository,
        cache: ICacheService,
    ):
        self._generation_repo = generation_repo
        self._ledger_repo = ledger_repo
        self._cache = cache
    
    async def execute(
        self,
        generation_id: UUID,
        admin_id: int,
        reason: Optional[str] = None,
    ) -> bool:
        """Execute use case."""
        generation = await self._generation_repo.get_by_id(generation_id)
        
        if not generation:
            return False
        
        # Only refund if credits were charged
        if generation.credits_charged <= 0:
            return False
        
        # Create refund entry
        await self._ledger_repo.create_entry(
            telegram_id=generation.telegram_id,
            amount=generation.credits_charged,
            entry_type=LedgerEntryType.REFUND,
            reason=reason or f"Refund for generation {generation_id}",
            reference_id=str(generation_id),
        )
        
        logger.info(
            "Generation refunded",
            generation_id=str(generation_id),
            telegram_id=generation.telegram_id,
            amount=float(generation.credits_charged),
            admin_id=admin_id,
        )
        
        return True
