"""Stars payment handlers."""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from typing import Callable

from keyboards import PaymentKeyboard
from keyboards.builders import TopupCallback, MenuCallback
from locales import TranslationKey
from services import PaymentService
from states import PaymentStates
from core.container import get_container
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="stars_payment")


@router.callback_query(F.data == MenuCallback.TOPUP)
async def open_topup_menu(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Open top-up menu."""
    await call.answer()
    
    if call.message:
        await call.message.delete()
    
    try:
        options = await PaymentService.get_stars_options()
    except Exception as e:
        logger.warning("Failed to get stars options", error=str(e))
        await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    if not options.get("enabled"):
        await call.message.answer(_(TranslationKey.TOPUP_DISABLED, None))
        return
    
    presets = options.get("preset_stars") or []
    numerator = int(options.get("exchange_numerator", 1))
    denominator = int(options.get("exchange_denominator", 1))
    
    preset_pairs = PaymentService.build_preset_pairs(presets, numerator, denominator)
    try:
        avg_price = await PaymentService.get_average_generation_price()
    except Exception as e:
        logger.warning("Failed to get average generation price", error=str(e))
        avg_price = None
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
    await call.message.answer(
        text,
        reply_markup=PaymentKeyboard.topup_menu(preset_pairs, avg_price, _),
    )


@router.callback_query(F.data.startswith("topup:stars:"))
async def handle_topup_preset(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle preset amount selection."""
    await call.answer()
    
    try:
        stars_amount = int(call.data.split(":", 2)[2])
    except (IndexError, ValueError):
        return
    
    data = await state.get_data()
    options = data.get("stars_options")
    
    if not options:
        try:
            options = await PaymentService.get_stars_options()
        except Exception:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
            return
    
    min_stars = int(options.get("min_stars", 0))
    if stars_amount < min_stars:
        await call.message.answer(_(TranslationKey.TOPUP_MIN_AMOUNT, {"min": min_stars}))
        return
    
    numerator = int(options.get("exchange_numerator", 1))
    denominator = int(options.get("exchange_denominator", 1))
    currency = str(options.get("currency", "XTR"))
    
    container = get_container()
    
    await PaymentService.send_stars_invoice(
        call.message.bot,
        call.message.chat.id,
        call.message.message_id,
        stars_amount,
        numerator,
        denominator,
        currency,
        container.settings.payment_provider_token,
        _,
    )


@router.callback_query(F.data == TopupCallback.CUSTOM)
async def handle_topup_custom(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle custom amount request."""
    await call.answer()
    
    data = await state.get_data()
    options = data.get("stars_options") or {}
    min_stars = int(options.get("min_stars", 70))
    
    await state.set_state(PaymentStates.waiting_stars_amount)
    await call.message.answer(
        _(TranslationKey.TOPUP_ENTER_AMOUNT, {"min": min_stars}),
        reply_to_message_id=call.message.message_id,
    )


@router.message(PaymentStates.waiting_stars_amount)
async def handle_custom_stars(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle custom stars amount input."""
    amount = PaymentService.parse_stars_amount(message.text or "")
    
    if amount is None:
        await message.answer(
            _(TranslationKey.TOPUP_INVALID_AMOUNT, None),
            reply_to_message_id=message.message_id,
        )
        return
    
    data = await state.get_data()
    options = data.get("stars_options")
    
    if not options:
        try:
            options = await PaymentService.get_stars_options()
        except Exception:
            await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
            return
    
    min_stars = int(options.get("min_stars", 0))
    if amount < min_stars:
        await message.answer(
            _(TranslationKey.TOPUP_MIN_AMOUNT, {"min": min_stars}),
            reply_to_message_id=message.message_id,
        )
        return
    
    numerator = int(options.get("exchange_numerator", 1))
    denominator = int(options.get("exchange_denominator", 1))
    credits = PaymentService.calculate_credits(amount, numerator, denominator)
    
    await message.answer(
        _(TranslationKey.TOPUP_CONFIRMATION, {"stars": amount, "credits": credits}),
        reply_to_message_id=message.message_id,
    )
    
    await state.clear()
    
    container = get_container()
    
    await PaymentService.send_stars_invoice(
        message.bot,
        message.chat.id,
        message.message_id,
        amount,
        numerator,
        denominator,
        str(options.get("currency", "XTR")),
        container.settings.payment_provider_token,
        _,
    )


@router.pre_checkout_query()
async def handle_pre_checkout(query: PreCheckoutQuery) -> None:
    """Handle pre-checkout query."""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(
    message: Message,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle successful payment."""
    payment = message.successful_payment
    if not payment:
        return
    
    try:
        result = await PaymentService.confirm_payment(
            telegram_id=message.from_user.id,
            stars_amount=payment.total_amount,
            currency=payment.currency,
            telegram_charge_id=payment.telegram_payment_charge_id,
            provider_charge_id=payment.provider_payment_charge_id,
            invoice_payload=payment.invoice_payload,
        )
        
        credits_added = int(result.get("credits_added", 0))
        # API returns "balance", not "new_balance"
        new_balance = int(result.get("balance", 0))
        
        await message.answer(
            _(TranslationKey.TOPUP_SUCCESS, {
                "credits": credits_added,
                "balance": new_balance,
            })
        )
    
    except Exception as e:
        logger.error("Payment confirmation failed", error=str(e))
        await message.answer(_(TranslationKey.ERROR_GENERIC, None))
