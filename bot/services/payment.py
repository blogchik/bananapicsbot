"""Payment service."""

import uuid
from typing import Callable

from aiogram import Bot
from aiogram.types import LabeledPrice, Message

from core.container import get_container
from core.logging import get_logger
from locales import TranslationKey

logger = get_logger(__name__)


class PaymentService:
    """Payment-related business logic."""
    
    @staticmethod
    async def get_stars_options() -> dict:
        """Get stars payment options."""
        container = get_container()
        return await container.api_client.get_stars_options()

    @staticmethod
    async def get_average_generation_price() -> int | None:
        """Get average model generation price."""
        container = get_container()
        models = await container.api_client.get_models()
        prices: list[int] = []
        for item in models:
            model = item.get("model") or {}
            if not model.get("id"):
                continue
            model_prices = item.get("prices") or []
            if not model_prices:
                continue
            try:
                unit_price = int(model_prices[0].get("unit_price", 0))
            except (TypeError, ValueError):
                unit_price = 0
            if unit_price > 0:
                prices.append(unit_price)
        if not prices:
            return None
        return int(round(sum(prices) / len(prices)))
    
    @staticmethod
    def calculate_credits(
        stars_amount: int,
        numerator: int,
        denominator: int,
    ) -> int:
        """Calculate credits from stars amount."""
        if stars_amount <= 0 or denominator <= 0:
            return 0
        return int(round(stars_amount * numerator / denominator))
    
    @staticmethod
    def format_exchange_rate(numerator: int, denominator: int) -> str:
        """Format exchange rate for display."""
        if numerator <= 0 or denominator <= 0:
            return ""
        return f"Kurs: {denominator} ⭐ = {numerator} credit"
    
    @staticmethod
    def parse_stars_amount(value: str) -> int | None:
        """Parse stars amount from user input."""
        value = value.strip().replace(" ", "")
        if not value.isdigit():
            return None
        amount = int(value)
        return amount if amount > 0 else None
    
    @staticmethod
    async def send_stars_invoice(
        bot: Bot,
        chat_id: int,
        message_id: int,
        stars_amount: int,
        numerator: int,
        denominator: int,
        currency: str,
        provider_token: str,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> None:
        """Send stars payment invoice."""
        credits = PaymentService.calculate_credits(stars_amount, numerator, denominator)
        payload = f"stars:{stars_amount}:{uuid.uuid4().hex}"
        title = _(TranslationKey.TOPUP_TITLE, None)
        description = _(TranslationKey.TOPUP_INVOICE_DESCRIPTION, {
            "stars": stars_amount,
            "credits": credits,
        })
        label = _(TranslationKey.TOPUP_INVOICE_LABEL, None)
        prices = [LabeledPrice(label=label, amount=stars_amount)]
        
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            reply_to_message_id=message_id,
        )
    
    @staticmethod
    async def confirm_payment(
        telegram_id: int,
        stars_amount: int,
        currency: str,
        telegram_charge_id: str,
        provider_charge_id: str | None,
        invoice_payload: str | None,
    ) -> dict:
        """Confirm stars payment."""
        container = get_container()
        return await container.api_client.confirm_stars_payment(
            telegram_id=telegram_id,
            stars_amount=stars_amount,
            currency=currency,
            telegram_charge_id=telegram_charge_id,
            provider_charge_id=provider_charge_id,
            invoice_payload=invoice_payload,
        )
    
    @staticmethod
    def build_preset_pairs(
        presets: list[int],
        numerator: int,
        denominator: int,
    ) -> list[tuple[int, int]]:
        """Build preset amount pairs (stars, credits)."""
        return [
            (amount, PaymentService.calculate_credits(amount, numerator, denominator))
            for amount in presets
        ]
