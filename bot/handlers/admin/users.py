"""Admin users management handlers."""

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
router = Router(name="admin_users")


@router.callback_query(F.data == AdminCallback.USERS_SEARCH)
async def admin_users_search(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start user search."""
    await call.answer()
    await state.set_state(AdminStates.waiting_user_search)
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_USER_SEARCH_PROMPT, None),
            reply_markup=AdminKeyboard.back_to_users(_),
        )


@router.message(AdminStates.waiting_user_search)
async def admin_search_user(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle user search query."""
    query = (message.text or "").strip()
    
    if not query:
        await message.answer(_(TranslationKey.ADMIN_USER_SEARCH_EMPTY, None))
        return
    
    try:
        users = await AdminService.search_users(query)
    except Exception as e:
        logger.warning("Failed to search users", error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    if not users:
        await message.answer(
            _(TranslationKey.ADMIN_USER_NOT_FOUND, None),
            reply_markup=AdminKeyboard.back_to_users(_),
        )
        return
    
    await state.clear()
    
    if len(users) == 1:
        # Show single user
        user = users[0]
        await state.update_data(selected_user_id=user.get("telegram_id"))
        text = format_user_profile(user, _)
        await message.answer(
            text,
            reply_markup=AdminKeyboard.user_actions(user.get("telegram_id"), _),
        )
    else:
        # Show list
        await message.answer(
            _(TranslationKey.ADMIN_USER_SELECT, None),
            reply_markup=AdminKeyboard.user_list(users, _),
        )


def format_user_profile(user: dict, _: Callable[[TranslationKey, dict | None], str]) -> str:
    """Format user profile for admin view."""
    lines = [
        _(TranslationKey.ADMIN_USER_PROFILE_TITLE, None),
        "",
        _(TranslationKey.ADMIN_USER_ID, {"id": user.get("telegram_id", "")}),
        _(TranslationKey.ADMIN_USER_USERNAME, {"username": user.get("username") or "-"}),
        _(TranslationKey.ADMIN_USER_NAME, {"name": user.get("full_name", "")}),
        "",
        _(TranslationKey.ADMIN_USER_BALANCE, {"balance": user.get("balance", 0)}),
        _(TranslationKey.ADMIN_USER_TRIAL, {"trial": user.get("trial_credits", 0)}),
        _(TranslationKey.ADMIN_USER_GENERATIONS, {"count": user.get("total_generations", 0)}),
        "",
        _(TranslationKey.ADMIN_USER_CREATED, {"date": user.get("created_at", "-")}),
        _(TranslationKey.ADMIN_USER_LAST_ACTIVE, {"date": user.get("last_active", "-")}),
    ]
    
    if user.get("is_banned"):
        lines.append("")
        lines.append(_(TranslationKey.ADMIN_USER_BANNED, None))
    
    return "\n".join(lines)


@router.callback_query(F.data.startswith("admin:user:view:"))
async def admin_view_user(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """View user profile."""
    await call.answer()
    
    try:
        telegram_id = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return
    
    try:
        user = await AdminService.get_user(telegram_id)
    except Exception as e:
        logger.warning("Failed to get user", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    if not user:
        if call.message:
            await call.message.answer(_(TranslationKey.ADMIN_USER_NOT_FOUND, None))
        return
    
    await state.update_data(selected_user_id=telegram_id)
    
    text = format_user_profile(user, _)
    
    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=AdminKeyboard.user_actions(telegram_id, _),
        )


@router.callback_query(F.data == AdminCallback.USERS_LIST)
async def admin_users_list(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show users list with pagination."""
    await call.answer()
    
    data = await state.get_data()
    page = data.get("users_page", 0)
    
    try:
        result = await AdminService.get_users_page(page)
    except Exception as e:
        logger.warning("Failed to get users list", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    users = result.get("users", [])
    total = result.get("total", 0)
    has_more = result.get("has_more", False)
    
    if not users:
        if call.message:
            await call.message.edit_text(
                _(TranslationKey.ADMIN_USERS_EMPTY, None),
                reply_markup=AdminKeyboard.back_to_users(_),
            )
        return
    
    text = _(TranslationKey.ADMIN_USERS_LIST_TITLE, {"total": total, "page": page + 1})
    
    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=AdminKeyboard.user_list_paginated(users, page, has_more, _),
        )


@router.callback_query(F.data.startswith("admin:users:page:"))
async def admin_users_page(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle users list pagination."""
    await call.answer()
    
    try:
        page = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return
    
    await state.update_data(users_page=page)
    
    try:
        result = await AdminService.get_users_page(page)
    except Exception as e:
        logger.warning("Failed to get users page", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    users = result.get("users", [])
    total = result.get("total", 0)
    has_more = result.get("has_more", False)
    
    text = _(TranslationKey.ADMIN_USERS_LIST_TITLE, {"total": total, "page": page + 1})
    
    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=AdminKeyboard.user_list_paginated(users, page, has_more, _),
        )


@router.callback_query(F.data.startswith("admin:user:ban:"))
async def admin_ban_user(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Ban/unban user."""
    await call.answer()
    
    try:
        telegram_id = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return
    
    try:
        result = await AdminService.toggle_ban(telegram_id)
        is_banned = result.get("is_banned", False)
    except Exception as e:
        logger.warning("Failed to toggle ban", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    if is_banned:
        msg = _(TranslationKey.ADMIN_USER_BANNED_SUCCESS, None)
    else:
        msg = _(TranslationKey.ADMIN_USER_UNBANNED_SUCCESS, None)
    
    if call.message:
        await call.message.answer(msg)
    
    # Refresh user view
    await admin_view_user.__wrapped__(call, FSMContext, _)
