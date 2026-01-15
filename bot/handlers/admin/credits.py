"""Admin credits management handlers."""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from typing import Callable

from keyboards import AdminKeyboard
from keyboards.builders import AdminCallback
from locales import TranslationKey
from services import AdminService
from states import AdminStates
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="admin_credits")


@router.callback_query(F.data.startswith("admin:user:credits:"))
async def admin_add_credits_start(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start add credits flow."""
    await call.answer()
    
    try:
        telegram_id = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return
    
    await state.update_data(credits_user_id=telegram_id)
    await state.set_state(AdminStates.waiting_credits_amount)
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_CREDITS_ENTER_AMOUNT, None),
            reply_markup=AdminKeyboard.cancel_action(_),
        )


@router.message(AdminStates.waiting_credits_amount)
async def admin_add_credits_amount(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle credits amount input."""
    text = (message.text or "").strip()
    
    try:
        amount = int(text)
    except ValueError:
        await message.answer(
            _(TranslationKey.ADMIN_CREDITS_INVALID_AMOUNT, None),
            reply_to_message_id=message.message_id,
        )
        return
    
    if amount == 0:
        await message.answer(
            _(TranslationKey.ADMIN_CREDITS_ZERO_AMOUNT, None),
            reply_to_message_id=message.message_id,
        )
        return
    
    await state.update_data(credits_amount=amount)
    await state.set_state(AdminStates.waiting_credits_reason)
    
    await message.answer(
        _(TranslationKey.ADMIN_CREDITS_ENTER_REASON, {"amount": amount}),
        reply_to_message_id=message.message_id,
    )


@router.message(AdminStates.waiting_credits_reason)
async def admin_add_credits_reason(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle credits reason and confirm."""
    reason = (message.text or "").strip() or "Admin adjustment"
    
    data = await state.get_data()
    telegram_id = data.get("credits_user_id")
    amount = data.get("credits_amount")
    
    if not telegram_id or amount is None:
        await state.clear()
        await message.answer(_(TranslationKey.ERROR_GENERIC, None))
        return
    
    try:
        result = await AdminService.adjust_credits(telegram_id, amount, reason)
        new_balance = result.get("new_balance", 0)
    except Exception as e:
        logger.warning("Failed to adjust credits", error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    await state.clear()
    
    if amount > 0:
        text = _(TranslationKey.ADMIN_CREDITS_ADDED, {
            "amount": amount,
            "user_id": telegram_id,
            "balance": new_balance,
        })
    else:
        text = _(TranslationKey.ADMIN_CREDITS_REMOVED, {
            "amount": abs(amount),
            "user_id": telegram_id,
            "balance": new_balance,
        })
    
    await message.answer(text, reply_markup=AdminKeyboard.back_to_main(_))


@router.callback_query(F.data == AdminCallback.CANCEL)
async def admin_cancel_action(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Cancel current admin action."""
    await call.answer()
    await state.clear()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_ACTION_CANCELLED, None),
            reply_markup=AdminKeyboard.back_to_main(_),
        )


@router.callback_query(F.data.startswith("admin:user:refund:"))
async def admin_refund_start(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start refund flow."""
    await call.answer()
    
    try:
        telegram_id = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return
    
    try:
        generations = await AdminService.get_user_generations(telegram_id, limit=10)
    except Exception as e:
        logger.warning("Failed to get generations", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    if not generations:
        if call.message:
            await call.message.answer(
                _(TranslationKey.ADMIN_REFUND_NO_GENERATIONS, None),
                reply_markup=AdminKeyboard.back_to_users(_),
            )
        return
    
    await state.update_data(refund_user_id=telegram_id)
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_REFUND_SELECT, None),
            reply_markup=AdminKeyboard.generation_list(generations, _),
        )


@router.callback_query(F.data.startswith("admin:refund:gen:"))
async def admin_refund_generation(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Refund specific generation."""
    await call.answer()
    
    try:
        gen_id = call.data.split(":", 3)[3]
    except IndexError:
        return
    
    data = await state.get_data()
    telegram_id = data.get("refund_user_id")
    
    if not telegram_id:
        await state.clear()
        await call.message.answer(_(TranslationKey.ERROR_GENERIC, None))
        return
    
    try:
        result = await AdminService.refund_generation(telegram_id, gen_id)
        refunded = result.get("credits_refunded", 0)
        new_balance = result.get("new_balance", 0)
    except Exception as e:
        logger.warning("Failed to refund generation", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    await state.clear()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_REFUND_SUCCESS, {
                "amount": refunded,
                "balance": new_balance,
            }),
            reply_markup=AdminKeyboard.back_to_users(_),
        )
