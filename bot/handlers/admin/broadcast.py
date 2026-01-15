"""Admin broadcast handlers."""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ContentType
from typing import Callable

from keyboards import AdminKeyboard
from keyboards.builders import AdminCallback
from locales import TranslationKey
from services import AdminService
from states import AdminStates
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="admin_broadcast")


@router.callback_query(F.data == AdminCallback.BROADCAST_NEW)
async def admin_broadcast_new(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start new broadcast."""
    await call.answer()
    await state.set_state(AdminStates.waiting_broadcast_message)
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_BROADCAST_ENTER_MESSAGE, None),
            reply_markup=AdminKeyboard.cancel_action(_),
        )


@router.message(AdminStates.waiting_broadcast_message)
async def admin_broadcast_message(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle broadcast message input."""
    # Store message content for broadcast
    content_type = message.content_type
    
    broadcast_data = {
        "content_type": content_type,
        "text": message.text or message.caption,
    }
    
    if message.photo:
        broadcast_data["photo"] = message.photo[-1].file_id
    elif message.video:
        broadcast_data["video"] = message.video.file_id
    elif message.document:
        broadcast_data["document"] = message.document.file_id
    elif message.animation:
        broadcast_data["animation"] = message.animation.file_id
    
    await state.update_data(broadcast_data=broadcast_data)
    await state.set_state(AdminStates.waiting_broadcast_confirm)
    
    # Show preview
    await message.answer(
        _(TranslationKey.ADMIN_BROADCAST_PREVIEW, None),
        reply_to_message_id=message.message_id,
    )
    
    # Forward message as preview
    await message.copy_to(message.chat.id)
    
    await message.answer(
        _(TranslationKey.ADMIN_BROADCAST_CONFIRM_PROMPT, None),
        reply_markup=AdminKeyboard.broadcast_confirm(_),
    )


@router.callback_query(
    AdminStates.waiting_broadcast_confirm,
    F.data == AdminCallback.BROADCAST_CONFIRM,
)
async def admin_broadcast_confirm(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Confirm and start broadcast."""
    await call.answer()
    
    data = await state.get_data()
    broadcast_data = data.get("broadcast_data")
    
    if not broadcast_data:
        await state.clear()
        if call.message:
            await call.message.edit_text(
                _(TranslationKey.ERROR_GENERIC, None),
                reply_markup=AdminKeyboard.back_to_main(_),
            )
        return
    
    # Start broadcast
    try:
        result = await AdminService.start_broadcast(broadcast_data)
        broadcast_id = result.get("broadcast_id")
    except Exception as e:
        logger.error("Failed to start broadcast", error=str(e))
        if call.message:
            await call.message.edit_text(
                _(TranslationKey.ERROR_CONNECTION, None),
                reply_markup=AdminKeyboard.back_to_main(_),
            )
        return
    
    await state.clear()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_BROADCAST_STARTED, {"broadcast_id": broadcast_id}),
            reply_markup=AdminKeyboard.broadcast_status(broadcast_id, _),
        )


@router.callback_query(F.data == AdminCallback.BROADCAST_CANCEL)
async def admin_broadcast_cancel(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Cancel broadcast."""
    await call.answer()
    await state.clear()
    
    if call.message:
        await call.message.edit_text(
            _(TranslationKey.ADMIN_BROADCAST_CANCELLED, None),
            reply_markup=AdminKeyboard.back_to_main(_),
        )


@router.callback_query(F.data == AdminCallback.BROADCAST_HISTORY)
async def admin_broadcast_history(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show broadcast history."""
    await call.answer()
    
    try:
        broadcasts = await AdminService.get_broadcasts(limit=10)
    except Exception as e:
        logger.warning("Failed to get broadcasts", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    if not broadcasts:
        if call.message:
            await call.message.edit_text(
                _(TranslationKey.ADMIN_BROADCAST_EMPTY, None),
                reply_markup=AdminKeyboard.back_to_broadcast(_),
            )
        return
    
    lines = [_(TranslationKey.ADMIN_BROADCAST_HISTORY_TITLE, None), ""]
    
    for bc in broadcasts:
        status = bc.get("status", "unknown")
        sent = bc.get("sent_count", 0)
        failed = bc.get("failed_count", 0)
        created = bc.get("created_at", "-")
        
        lines.append(f"📢 {bc.get('id', '-')[:8]} | {status}")
        lines.append(f"   ✅ {sent} | ❌ {failed} | 📅 {created}")
        lines.append("")
    
    if call.message:
        await call.message.edit_text(
            "\n".join(lines),
            reply_markup=AdminKeyboard.back_to_broadcast(_),
        )


@router.callback_query(F.data.startswith("admin:broadcast:status:"))
async def admin_broadcast_status(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Check broadcast status."""
    await call.answer()
    
    try:
        broadcast_id = call.data.split(":", 3)[3]
    except IndexError:
        return
    
    try:
        status = await AdminService.get_broadcast_status(broadcast_id)
    except Exception as e:
        logger.warning("Failed to get broadcast status", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    lines = [
        _(TranslationKey.ADMIN_BROADCAST_STATUS_TITLE, None),
        "",
        _(TranslationKey.ADMIN_BROADCAST_ID, {"id": broadcast_id[:8]}),
        _(TranslationKey.ADMIN_BROADCAST_STATUS, {"status": status.get("status", "unknown")}),
        "",
        _(TranslationKey.ADMIN_BROADCAST_SENT, {"count": status.get("sent_count", 0)}),
        _(TranslationKey.ADMIN_BROADCAST_FAILED, {"count": status.get("failed_count", 0)}),
        _(TranslationKey.ADMIN_BROADCAST_PENDING, {"count": status.get("pending_count", 0)}),
    ]
    
    if call.message:
        await call.message.edit_text(
            "\n".join(lines),
            reply_markup=AdminKeyboard.back_to_broadcast(_),
        )
