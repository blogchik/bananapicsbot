"""Topup command handler."""

from typing import Callable

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from core.logging import get_logger
from keyboards import PaymentKeyboard
from locales import TranslationKey
from services import PaymentService

logger = get_logger(__name__)
router = Router(name="topup")


@router.message(Command("topup"))
async def topup_handler(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle /topup command."""
    try:
        options = await PaymentService.get_stars_options()
    except Exception as e:
        logger.warning("Failed to get stars options", error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    if not options.get("enabled"):
        await message.answer(_(TranslationKey.TOPUP_DISABLED, None))
        return

    presets = options.get("preset_stars") or []
    numerator = int(options.get("exchange_numerator", 1))
    denominator = int(options.get("exchange_denominator", 1))

    preset_pairs = PaymentService.build_preset_pairs(presets, numerator, denominator)
    try:
        min_price = await PaymentService.get_min_generation_price()
    except Exception as e:
        logger.warning("Failed to get minimum generation price", error=str(e))
        min_price = None
    rate_line = _(TranslationKey.TOPUP_EXCHANGE_RATE, {
        "numerator": numerator,
        "denominator": denominator,
    })
    lines = [
        _(TranslationKey.TOPUP_TITLE, None),
        _(TranslationKey.TOPUP_DESCRIPTION, None),
        rate_line,
    ]
    lines.append(_(TranslationKey.TOPUP_SELECT_AMOUNT, None))
    text = "\n".join(lines)

    await state.update_data(stars_options=options)
    await message.answer(
        text,
        reply_markup=PaymentKeyboard.topup_menu(preset_pairs, min_price, _),
    )
