"""Admin panel main handler."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from typing import Callable

from keyboards import AdminKeyboard
from keyboards.builders import AdminCallback
from locales import TranslationKey
from services import AdminService
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="admin_panel")


@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show admin panel."""
    await state.clear()
    
    await message.answer(
        _(TranslationKey.ADMIN_PANEL_TITLE, None),
        reply_markup=AdminKeyboard.main(_),
    )


@router.callback_query(F.data == AdminCallback.MAIN)
async def admin_main(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Return to admin main menu."""
    await call.answer()
    await state.clear()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_PANEL_TITLE, None),
            reply_markup=AdminKeyboard.main(_),
        )


@router.callback_query(F.data == AdminCallback.STATS)
async def admin_stats_menu(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show stats menu."""
    await call.answer()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_STATS_TITLE, None),
            reply_markup=AdminKeyboard.stats_menu(_),
        )


@router.callback_query(F.data == AdminCallback.USERS)
async def admin_users_menu(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show users management menu."""
    await call.answer()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_USERS_TITLE, None),
            reply_markup=AdminKeyboard.users_menu(_),
        )


@router.callback_query(F.data == AdminCallback.BROADCAST)
async def admin_broadcast_menu(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show broadcast menu."""
    await call.answer()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_BROADCAST_TITLE, None),
            reply_markup=AdminKeyboard.broadcast_menu(_),
        )
