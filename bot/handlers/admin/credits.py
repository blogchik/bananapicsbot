"""Admin credits management handlers."""

from typing import Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from core.logging import get_logger
from keyboards import AdminKeyboard
from keyboards.builders import AdminCallback
from locales import TranslationKey
from services import AdminService
from states import AdminStates

logger = get_logger(__name__)
router = Router(name="admin_credits")


@router.callback_query(F.data == AdminCallback.ADD_CREDITS)
async def admin_credits_menu(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show add credits prompt - ask for user ID."""
    await call.answer()
    await state.set_state(AdminStates.waiting_credits_user_id)

    if call.message:
        await call.message.edit_text(
            "👤 Foydalanuvchi Telegram ID sini kiriting:",
            reply_markup=AdminKeyboard.cancel_action(_),
        )


@router.message(AdminStates.waiting_credits_user_id)
async def admin_credits_user_id(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle user ID input for credits."""
    text = (message.text or "").strip()

    try:
        telegram_id = int(text)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format. Telegram ID raqam bo'lishi kerak.",
            reply_to_message_id=message.message_id,
        )
        return

    # Verify user exists
    try:
        user = await AdminService.get_user(telegram_id)
    except Exception as e:
        logger.warning("Failed to get user", error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    if not user:
        await message.answer(
            _(TranslationKey.ADMIN_USER_NOT_FOUND, None),
            reply_to_message_id=message.message_id,
        )
        return

    await state.update_data(credits_user_id=telegram_id)
    await state.set_state(AdminStates.waiting_credits_amount)

    await message.answer(
        _(TranslationKey.ADMIN_CREDITS_ENTER_AMOUNT, None),
        reply_to_message_id=message.message_id,
    )


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
        text = _(
            TranslationKey.ADMIN_CREDITS_ADDED,
            {
                "amount": amount,
                "user_id": telegram_id,
                "balance": new_balance,
            },
        )
    else:
        text = _(
            TranslationKey.ADMIN_CREDITS_REMOVED,
            {
                "amount": abs(amount),
                "user_id": telegram_id,
                "balance": new_balance,
            },
        )

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


@router.callback_query(F.data == AdminCallback.REFUND)
async def admin_refund_menu(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show refund type selection menu."""
    await call.answer()
    await state.clear()

    if call.message:
        await call.message.edit_text(
            "🔙 **Refund turi tanlang:**\n\n"
            "🎨 **Credit Refund** - Generatsiya uchun sarflangan kreditlarni qaytarish\n"
            "⭐ **Stars Refund** - Telegram Stars to'lovini qaytarish",
            parse_mode="Markdown",
            reply_markup=AdminKeyboard.refund_menu(_),
        )


@router.callback_query(F.data == AdminCallback.REFUND_CREDITS)
async def admin_credit_refund_start(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start credit refund flow - ask for user ID."""
    await call.answer()
    await state.set_state(AdminStates.waiting_refund_user_id)

    if call.message:
        await call.message.edit_text(
            "🎨 **Credit Refund**\n\n👤 Foydalanuvchi Telegram ID sini kiriting:",
            parse_mode="Markdown",
            reply_markup=AdminKeyboard.cancel_action(_),
        )


@router.message(AdminStates.waiting_refund_user_id)
async def admin_refund_user_id(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle user ID input for refund."""
    text = (message.text or "").strip()

    try:
        telegram_id = int(text)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format. Telegram ID raqam bo'lishi kerak.",
            reply_to_message_id=message.message_id,
        )
        return

    # Get user generations
    try:
        generations = await AdminService.get_user_generations(telegram_id, limit=10)
    except Exception as e:
        logger.warning("Failed to get user generations", error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    if not generations:
        await message.answer(
            _(TranslationKey.ADMIN_REFUND_NO_GENERATIONS, None),
            reply_markup=AdminKeyboard.back_to_main(_),
        )
        await state.clear()
        return

    await state.update_data(refund_user_id=telegram_id)

    await message.answer(
        _(TranslationKey.ADMIN_REFUND_SELECT, None),
        reply_markup=AdminKeyboard.generation_list(generations, _),
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
            _(
                TranslationKey.ADMIN_REFUND_SUCCESS,
                {
                    "amount": refunded,
                    "balance": new_balance,
                },
            ),
            reply_markup=AdminKeyboard.back_to_users(_),
        )


# ============ Stars Refund Handlers ============


@router.callback_query(F.data == AdminCallback.REFUND_STARS)
async def admin_stars_refund_start(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start stars refund flow - ask for user ID."""
    await call.answer()
    await state.set_state(AdminStates.waiting_stars_refund_user_id)

    if call.message:
        await call.message.edit_text(
            "⭐ **Stars Refund**\n\n👤 Foydalanuvchi Telegram ID sini kiriting:",
            parse_mode="Markdown",
            reply_markup=AdminKeyboard.cancel_action(_),
        )


@router.message(AdminStates.waiting_stars_refund_user_id)
async def admin_stars_refund_user_id(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle user ID input for stars refund - show unrefunded transactions."""
    text = (message.text or "").strip()

    try:
        telegram_id = int(text)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format. Telegram ID raqam bo'lishi kerak.",
            reply_to_message_id=message.message_id,
        )
        return

    # Get user info
    try:
        user = await AdminService.get_user(telegram_id)
    except Exception as e:
        logger.warning("Failed to get user", error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    if not user:
        await message.answer(
            _(TranslationKey.ADMIN_USER_NOT_FOUND, None),
            reply_to_message_id=message.message_id,
        )
        return

    balance = user.get("balance", 0)

    # Show loading message
    loading_msg = await message.answer(
        "⏳ Telegram API orqali tranzaksiyalar yuklanmoqda...",
        reply_to_message_id=message.message_id,
    )

    # Get bot token and fetch unrefunded transactions
    from core.container import get_container

    container = get_container()
    bot_token = container.settings.bot_token.get_secret_value()

    try:
        transactions = await AdminService.get_user_unrefunded_transactions(
            bot_token=bot_token,
            user_id=telegram_id,
        )
    except Exception as e:
        logger.error("Failed to fetch transactions", error=str(e))
        await loading_msg.edit_text(
            f"❌ Tranzaksiyalarni olishda xatolik: {str(e)}",
        )
        return

    await state.clear()

    if not transactions:
        await loading_msg.edit_text(
            f"❌ **To'lovlar topilmadi**\n\n"
            f"👤 User: `{telegram_id}`\n"
            f"💰 Balans: **{balance}** credits\n\n"
            f"Bu foydalanuvchi Stars bilan to'lov qilmagan.",
            parse_mode="Markdown",
            reply_markup=AdminKeyboard.back_to_main(_),
        )
        return

    # Store data for later use - use list to preserve order for index-based lookup
    await state.update_data(
        stars_refund_user_id=telegram_id,
        stars_refund_balance=balance,
        stars_refund_transactions=transactions,
    )

    total_stars = sum(tx["amount"] for tx in transactions)

    await loading_msg.edit_text(
        f"⭐ **Stars Refund**\n\n"
        f"👤 User: `{telegram_id}`\n"
        f"💰 Balans: **{balance}** credits\n\n"
        f"📋 **Stars to'lovlar ({len(transactions)} ta):**\n"
        f"Jami: **{total_stars}** ⭐\n\n"
        f"Qaytarmoqchi bo'lgan to'lovni tanlang:",
        parse_mode="Markdown",
        reply_markup=AdminKeyboard.stars_refund_transactions(transactions, _),
    )


@router.callback_query(F.data.startswith("admin:refund:stars:tx:"))
async def admin_stars_refund_single(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Refund a single transaction."""
    await call.answer()

    # Extract transaction index from callback data
    try:
        tx_index = int(call.data.replace("admin:refund:stars:tx:", ""))
    except ValueError:
        await state.clear()
        if call.message:
            await call.message.edit_text(
                "❌ **Xatolik**\n\nNoto'g'ri callback data.",
                parse_mode="Markdown",
                reply_markup=AdminKeyboard.back_to_main(_),
            )
        return

    data = await state.get_data()
    telegram_id = data.get("stars_refund_user_id")
    balance = data.get("stars_refund_balance", 0)
    transactions = data.get("stars_refund_transactions", [])

    if not telegram_id or tx_index >= len(transactions):
        await state.clear()
        if call.message:
            await call.message.edit_text(
                "❌ **Xatolik**\n\nMa'lumotlar topilmadi. Qaytadan boshlang.",
                parse_mode="Markdown",
                reply_markup=AdminKeyboard.back_to_main(_),
            )
        return

    tx = transactions[tx_index]
    tx_id = tx["id"]
    stars_amount = tx["amount"]

    if call.message:
        await call.message.edit_text(
            f"⏳ Stars refund jarayoni...\n\n👤 User: `{telegram_id}`\n⭐ {stars_amount} Stars qaytarilmoqda...",
            parse_mode="Markdown",
        )

    # Get bot token
    from core.container import get_container

    container = get_container()
    bot_token = container.settings.bot_token.get_secret_value()

    try:
        ok, error = await AdminService.refund_star_payment(
            bot_token=bot_token,
            user_id=telegram_id,
            charge_id=tx_id,
        )

        if ok:
            # Get exchange rate and deduct credits
            try:
                settings = await AdminService.get_stars_settings()
                numerator = settings.get("exchange_numerator", 1)
                denominator = settings.get("exchange_denominator", 1)
            except Exception:
                numerator = 1
                denominator = 1

            credits_to_deduct = (stars_amount * numerator) // denominator

            try:
                await AdminService.adjust_credits(
                    telegram_id=telegram_id,
                    amount=-credits_to_deduct,
                    reason=f"Stars refund: {stars_amount}⭐",
                )
                new_balance = balance - credits_to_deduct

                # Mark payment as refunded in database
                try:
                    await container.api_client.mark_payment_refunded(tx_id)
                except Exception as e:
                    logger.warning("Failed to mark payment as refunded", error=str(e))

                await state.clear()
                if call.message:
                    await call.message.edit_text(
                        f"✅ **Stars Refund muvaffaqiyatli!**\n\n"
                        f"👤 User: `{telegram_id}`\n"
                        f"⭐ Qaytarildi: **{stars_amount}** Stars\n"
                        f"💰 Ayirildi: **{credits_to_deduct}** credits\n"
                        f"📊 Yangi balans: **{new_balance}** credits",
                        parse_mode="Markdown",
                        reply_markup=AdminKeyboard.back_to_main(_),
                    )
            except Exception as e:
                logger.warning("Failed to deduct credits", error=str(e))
                await state.clear()
                if call.message:
                    await call.message.edit_text(
                        f"⚠️ **Stars qaytarildi, lekin credits ayirilmadi!**\n\n"
                        f"👤 User: `{telegram_id}`\n"
                        f"⭐ Qaytarildi: **{stars_amount}** Stars\n\n"
                        f"❌ Qo'lda **{credits_to_deduct}** credits ayiring!",
                        parse_mode="Markdown",
                        reply_markup=AdminKeyboard.back_to_main(_),
                    )
        else:
            # Handle specific error cases
            if error and "CHARGE_ALREADY_REFUNDED" in error:
                # Transaction already refunded - remove from list and refresh
                transactions.pop(tx_index)
                await state.update_data(stars_refund_transactions=transactions)

                if not transactions:
                    await state.clear()
                    if call.message:
                        await call.message.edit_text(
                            f"ℹ️ **Barcha to'lovlar qaytarilgan**\n\n"
                            f"👤 User: `{telegram_id}`\n\n"
                            f"Bu foydalanuvchining qaytariladigan to'lovlari qolmagan.",
                            parse_mode="Markdown",
                            reply_markup=AdminKeyboard.back_to_main(_),
                        )
                else:
                    total_stars = sum(tx["amount"] for tx in transactions)
                    if call.message:
                        await call.message.edit_text(
                            f"⚠️ **Bu to'lov allaqachon qaytarilgan**\n\n"
                            f"👤 User: `{telegram_id}`\n"
                            f"💰 Balans: **{balance}** credits\n\n"
                            f"📋 **Qolgan to'lovlar ({len(transactions)} ta):**\n"
                            f"Jami: **{total_stars}** ⭐\n\n"
                            f"Boshqa tranzaksiyani tanlang:",
                            parse_mode="Markdown",
                            reply_markup=AdminKeyboard.stars_refund_transactions(transactions, _),
                        )
            else:
                await state.clear()
                error_text = error or "Nomalum xato"
                if call.message:
                    await call.message.edit_text(
                        f"❌ **Stars refund muvaffaqiyatsiz**\n\n"
                        f"👤 User: `{telegram_id}`\n"
                        f"⭐ {stars_amount} Stars\n\n"
                        f"**Xato:** {error_text}",
                        parse_mode="Markdown",
                        reply_markup=AdminKeyboard.back_to_main(_),
                    )

    except Exception as e:
        logger.error("Stars refund failed", error=str(e))
        await state.clear()
        if call.message:
            await call.message.edit_text(
                f"❌ **Xatolik yuz berdi**\n\n{str(e)}",
                parse_mode="Markdown",
                reply_markup=AdminKeyboard.back_to_main(_),
            )


@router.callback_query(F.data == AdminCallback.REFUND_STARS_ALL)
async def admin_stars_refund_all(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Refund all transactions."""
    await call.answer()

    data = await state.get_data()
    telegram_id = data.get("stars_refund_user_id")
    balance = data.get("stars_refund_balance", 0)
    transactions = data.get("stars_refund_transactions", [])

    if not telegram_id or not transactions:
        await state.clear()
        if call.message:
            await call.message.edit_text(
                "❌ **Xatolik**\n\nMa'lumotlar topilmadi. Qaytadan boshlang.",
                parse_mode="Markdown",
                reply_markup=AdminKeyboard.back_to_main(_),
            )
        return

    total_stars = sum(tx["amount"] for tx in transactions)

    if call.message:
        await call.message.edit_text(
            f"⏳ Barcha tranzaksiyalar qaytarilmoqda...\n\n"
            f"👤 User: `{telegram_id}`\n"
            f"⭐ Jami: {total_stars} Stars ({len(transactions)} ta)",
            parse_mode="Markdown",
        )

    # Get bot token
    from core.container import get_container

    container = get_container()
    bot_token = container.settings.bot_token.get_secret_value()

    refunded_total = 0
    refunded_count = 0
    errors: list[str] = []

    for tx in transactions:
        tx_id = tx["id"]
        try:
            ok, error = await AdminService.refund_star_payment(
                bot_token=bot_token,
                user_id=telegram_id,
                charge_id=tx_id,
            )

            if ok:
                refunded_total += tx["amount"]
                refunded_count += 1
                # Mark payment as refunded in database
                try:
                    await container.api_client.mark_payment_refunded(tx_id)
                except Exception as e:
                    logger.warning("Failed to mark payment as refunded", error=str(e))
            elif error:
                if "CHARGE_ALREADY_REFUNDED" in error:
                    errors.append(f"{tx['amount']}⭐: allaqachon qaytarilgan")
                else:
                    errors.append(f"{tx['amount']}⭐: {error}")
        except Exception as e:
            errors.append(f"{tx['amount']}⭐: {str(e)}")

    if refunded_total > 0:
        # Deduct credits
        try:
            settings = await AdminService.get_stars_settings()
            numerator = settings.get("exchange_numerator", 1)
            denominator = settings.get("exchange_denominator", 1)
        except Exception:
            numerator = 1
            denominator = 1

        credits_to_deduct = (refunded_total * numerator) // denominator

        try:
            await AdminService.adjust_credits(
                telegram_id=telegram_id,
                amount=-credits_to_deduct,
                reason=f"Stars refund: {refunded_total}⭐",
            )
            new_balance = balance - credits_to_deduct

            await state.clear()

            error_text = ""
            if errors:
                error_text = "\n\n⚠️ **Ba'zi xatolar:**\n" + "\n".join(f"• {e}" for e in errors[:3])

            if call.message:
                await call.message.edit_text(
                    f"✅ **Stars Refund muvaffaqiyatli!**\n\n"
                    f"👤 User: `{telegram_id}`\n"
                    f"⭐ Qaytarildi: **{refunded_total}** Stars\n"
                    f"📊 Tranzaksiyalar: **{refunded_count}** ta\n"
                    f"💰 Ayirildi: **{credits_to_deduct}** credits\n"
                    f"📊 Yangi balans: **{new_balance}** credits"
                    f"{error_text}",
                    parse_mode="Markdown",
                    reply_markup=AdminKeyboard.back_to_main(_),
                )
        except Exception as e:
            logger.warning("Failed to deduct credits", error=str(e))
            await state.clear()
            if call.message:
                await call.message.edit_text(
                    f"⚠️ **Stars qaytarildi, lekin credits ayirilmadi!**\n\n"
                    f"👤 User: `{telegram_id}`\n"
                    f"⭐ Qaytarildi: **{refunded_total}** Stars\n\n"
                    f"❌ Qo'lda **{credits_to_deduct}** credits ayiring!",
                    parse_mode="Markdown",
                    reply_markup=AdminKeyboard.back_to_main(_),
                )
    else:
        await state.clear()
        error_text = "\n".join(f"• {e}" for e in errors[:5])
        if call.message:
            await call.message.edit_text(
                f"❌ **Hech qanday tranzaksiya qaytarilmadi**\n\n"
                f"👤 User: `{telegram_id}`\n\n"
                f"**Xatolar:**\n{error_text}",
                parse_mode="Markdown",
                reply_markup=AdminKeyboard.back_to_main(_),
            )


@router.callback_query(F.data == AdminCallback.REFUND_STARS_CANCEL)
async def admin_stars_refund_cancel(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Cancel stars refund."""
    await call.answer()
    await state.clear()

    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_ACTION_CANCELLED, None),
            reply_markup=AdminKeyboard.back_to_main(_),
        )
