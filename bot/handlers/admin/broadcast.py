"""Admin broadcast handlers.

Full broadcast flow:
1. Admin selects "New Broadcast"
2. Admin sends message (text/photo/video/audio/sticker)
3. Admin selects user filter (all, active_7d, etc.)
4. Admin optionally adds inline button
5. Preview shown with user count
6. Admin confirms - broadcast created and started via Celery
7. Admin can check status and cancel if needed
"""

from datetime import datetime
from typing import Callable

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from core.logging import get_logger
from keyboards import AdminKeyboard
from keyboards.builders import AdminCallback
from locales import TranslationKey
from services import AdminService
from states import AdminStates

logger = get_logger(__name__)
router = Router(name="admin_broadcast")


# Filter type labels
FILTER_LABELS = {
    "all": "👥 All Users",
    "active_7d": "🔥 Active (7 days)",
    "active_30d": "📊 Active (30 days)",
    "with_balance": "💰 With Balance",
    "paid_users": "💳 Paid Users",
    "new_users": "🆕 New Users (7 days)",
}


# ============ Start Broadcast Flow ============


@router.callback_query(F.data == AdminCallback.BROADCAST_NEW)
async def admin_broadcast_new(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start new broadcast - ask for message."""
    await call.answer()
    await state.set_state(AdminStates.waiting_broadcast_message)

    if call.message:
        await call.message.edit_text(
            "📤 <b>New Broadcast</b>\n\n"
            "Send me the message you want to broadcast.\n\n"
            "Supported types:\n"
            "• Text\n"
            "• Photo (with caption)\n"
            "• Video (with caption)\n"
            "• Audio (with caption)\n"
            "• Sticker",
            reply_markup=AdminKeyboard.cancel_action(_),
        )


# ============ Receive Broadcast Message ============


@router.message(AdminStates.waiting_broadcast_message)
async def admin_broadcast_message(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle broadcast message input."""
    # Determine content type
    content_type = "text"
    media_file_id = None
    text = message.text or message.caption

    if message.photo:
        content_type = "photo"
        media_file_id = message.photo[-1].file_id
    elif message.video:
        content_type = "video"
        media_file_id = message.video.file_id
    elif message.audio:
        content_type = "audio"
        media_file_id = message.audio.file_id
    elif message.sticker:
        content_type = "sticker"
        media_file_id = message.sticker.file_id
        text = None  # Stickers don't have captions

    # Store broadcast data
    await state.update_data(
        broadcast_content_type=content_type,
        broadcast_text=text,
        broadcast_media_file_id=media_file_id,
    )

    # Move to filter selection
    await state.set_state(AdminStates.waiting_broadcast_filter)

    # Show preview
    await message.answer("✅ Message received! Here's a preview:")

    # Forward message as preview
    await message.copy_to(message.chat.id)

    # Ask for filter
    await message.answer(
        "📊 <b>Select Target Audience</b>\n\nChoose which users should receive this broadcast:",
        reply_markup=AdminKeyboard.broadcast_filter_select(_),
    )


# ============ Select Filter ============


@router.callback_query(
    AdminStates.waiting_broadcast_filter,
    F.data.startswith("admin:broadcast:filter:"),
)
async def admin_broadcast_filter_selected(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle filter selection."""
    await call.answer()

    filter_type = call.data.split(":")[-1]
    await state.update_data(broadcast_filter_type=filter_type)

    # Get user count for this filter
    try:
        users_count = await AdminService.get_users_count(filter_type)
    except Exception as e:
        logger.error("Failed to get users count", error=str(e))
        users_count = 0

    await state.update_data(broadcast_users_count=users_count)

    filter_label = FILTER_LABELS.get(filter_type, filter_type)

    if call.message:
        await call.message.edit_text(
            f"📊 Filter: <b>{filter_label}</b>\n"
            f"👥 Users: <b>{users_count}</b>\n\n"
            "🔘 <b>Add Inline Button?</b>\n\n"
            "You can add a button with a URL to your broadcast message.",
            reply_markup=AdminKeyboard.broadcast_button_options(_),
        )


# ============ Add Inline Button ============


@router.callback_query(F.data == "admin:broadcast:add_button")
async def admin_broadcast_add_button(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Start adding inline button - ask for text."""
    await call.answer()
    await state.set_state(AdminStates.waiting_broadcast_button_text)

    if call.message:
        await call.message.edit_text(
            "🔘 <b>Add Button</b>\n\n"
            "Send the button text (what users will see on the button).\n\n"
            "Example: <code>Learn More</code>",
            reply_markup=AdminKeyboard.cancel_action(_),
        )


@router.message(AdminStates.waiting_broadcast_button_text)
async def admin_broadcast_button_text(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle button text input."""
    if not message.text:
        await message.answer("Please send text for the button.")
        return

    if len(message.text) > 100:
        await message.answer("Button text is too long (max 100 characters).")
        return

    await state.update_data(broadcast_button_text=message.text)
    await state.set_state(AdminStates.waiting_broadcast_button_url)

    await message.answer(
        "🔗 <b>Button URL</b>\n\n"
        "Now send the URL that the button will open.\n\n"
        "Example: <code>https://example.com</code>",
    )


@router.message(AdminStates.waiting_broadcast_button_url)
async def admin_broadcast_button_url(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle button URL input."""
    if not message.text:
        await message.answer("Please send a URL.")
        return

    url = message.text.strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        await message.answer("Please send a valid URL starting with http:// or https://")
        return

    await state.update_data(broadcast_button_url=url)

    # Show preview with button
    await _show_broadcast_preview(message, state, _)


@router.callback_query(F.data == "admin:broadcast:skip_button")
async def admin_broadcast_skip_button(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Skip adding button - go to preview."""
    await call.answer()

    await state.update_data(broadcast_button_text=None, broadcast_button_url=None)

    # Show preview
    await _show_broadcast_preview(call.message, state, _)


# ============ Preview and Confirm ============


async def _show_broadcast_preview(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show broadcast preview and confirmation."""
    data = await state.get_data()

    content_type = data.get("broadcast_content_type", "text")
    filter_type = data.get("broadcast_filter_type", "all")
    users_count = data.get("broadcast_users_count", 0)
    button_text = data.get("broadcast_button_text")
    _button_url = data.get("broadcast_button_url")  # Reserved for future use

    filter_label = FILTER_LABELS.get(filter_type, filter_type)

    lines = [
        "📤 <b>Broadcast Preview</b>",
        "",
        f"📝 Type: <b>{content_type.title()}</b>",
        f"📊 Filter: <b>{filter_label}</b>",
        f"👥 Recipients: <b>{users_count}</b>",
    ]

    if button_text:
        lines.append(f"🔘 Button: <b>{button_text}</b>")

    lines.extend(
        [
            "",
            "⚠️ <b>Are you sure you want to send this broadcast?</b>",
            "",
            f"This will send to <b>{users_count}</b> users.",
        ]
    )

    await state.set_state(AdminStates.waiting_broadcast_confirm)

    await message.answer(
        "\n".join(lines),
        reply_markup=AdminKeyboard.broadcast_preview(users_count, filter_type, button_text is not None, _),
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
    await call.answer("Starting broadcast...")

    data = await state.get_data()

    content_type = data.get("broadcast_content_type", "text")
    text = data.get("broadcast_text")
    media_file_id = data.get("broadcast_media_file_id")
    filter_type = data.get("broadcast_filter_type", "all")
    button_text = data.get("broadcast_button_text")
    button_url = data.get("broadcast_button_url")

    admin_id = call.from_user.id if call.from_user else 0

    try:
        # Create broadcast in API
        result = await AdminService.create_broadcast(
            admin_id=admin_id,
            content_type=content_type,
            text=text,
            media_file_id=media_file_id,
            inline_button_text=button_text,
            inline_button_url=button_url,
            filter_type=filter_type,
        )

        public_id = result.get("public_id", "")
        total_users = result.get("total_users", 0)

        # Start broadcast
        await AdminService.start_broadcast(public_id)

        await state.clear()

        if call.message:
            await call.message.edit_text(
                f"✅ <b>Broadcast Started!</b>\n\n"
                f"📋 ID: <code>{public_id}</code>\n"
                f"👥 Recipients: <b>{total_users}</b>\n"
                f"📊 Status: <b>Running</b>\n\n"
                "Use the refresh button to check progress.",
                reply_markup=AdminKeyboard.broadcast_status(public_id, "running", _),
            )

    except Exception as e:
        logger.exception("Failed to start broadcast", error=str(e))
        await state.clear()

        if call.message:
            await call.message.edit_text(
                f"❌ <b>Failed to start broadcast</b>\n\nError: {str(e)}",
                reply_markup=AdminKeyboard.back_to_broadcast(_),
            )


# ============ Cancel ============


@router.callback_query(F.data == AdminCallback.BROADCAST_CANCEL)
async def admin_broadcast_cancel(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Cancel broadcast creation."""
    await call.answer()
    await state.clear()

    if call.message:
        await call.message.edit_text(
            "❌ Broadcast cancelled.",
            reply_markup=AdminKeyboard.back_to_broadcast(_),
        )


# ============ History ============


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
            await call.message.answer("❌ Failed to load broadcast history.")
        return

    if not broadcasts:
        if call.message:
            await call.message.edit_text(
                "📜 <b>Broadcast History</b>\n\nNo broadcasts yet.",
                reply_markup=AdminKeyboard.back_to_broadcast(_),
            )
        return

    lines = ["📜 <b>Broadcast History</b>", ""]

    for bc in broadcasts:
        status = bc.get("status", "unknown")
        status_emoji = {
            "pending": "⏳",
            "running": "🚀",
            "completed": "✅",
            "cancelled": "⛔",
            "failed": "❌",
        }.get(status, "❓")

        public_id = bc.get("public_id", "-")[:8]
        sent = bc.get("sent_count", 0)
        total = bc.get("total_users", 0)
        blocked = bc.get("blocked_count", 0)

        lines.append(f"{status_emoji} <code>{public_id}</code> | {status}")
        lines.append(f"   ✅ {sent}/{total} | 🚫 {blocked} blocked")
        lines.append("")

    if call.message:
        await call.message.edit_text(
            "\n".join(lines),
            reply_markup=AdminKeyboard.back_to_broadcast(_),
        )


# ============ Status ============


@router.callback_query(F.data.startswith("admin:broadcast:status:"))
async def admin_broadcast_status(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Check broadcast status."""
    await call.answer("Refreshing...")

    try:
        public_id = call.data.split(":")[-1]
    except IndexError:
        return

    try:
        status = await AdminService.get_broadcast_status(public_id)
    except Exception as e:
        logger.warning("Failed to get broadcast status", error=str(e))
        if call.message:
            await call.message.answer("❌ Failed to get broadcast status.")
        return

    if status.get("error"):
        if call.message:
            await call.message.edit_text(
                "❌ Broadcast not found.",
                reply_markup=AdminKeyboard.back_to_broadcast(_),
            )
        return

    bc_status = status.get("status", "unknown")
    status_emoji = {
        "pending": "⏳",
        "running": "🚀",
        "completed": "✅",
        "cancelled": "⛔",
        "failed": "❌",
    }.get(bc_status, "❓")

    total = status.get("total_users", 0)
    sent = status.get("sent_count", 0)
    failed = status.get("failed_count", 0)
    blocked = status.get("blocked_count", 0)
    progress = status.get("progress_percent", 0)

    # Progress bar
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)

    # Add timestamp to make message unique
    timestamp = datetime.now().strftime("%H:%M:%S")

    lines = [
        "📊 <b>Broadcast Status</b>",
        "",
        f"📋 ID: <code>{public_id}</code>",
        f"{status_emoji} Status: <b>{bc_status.title()}</b>",
        "",
        f"[{bar}] {progress:.1f}%",
        "",
        f"📤 Sent: <b>{sent}</b>",
        f"❌ Failed: <b>{failed}</b>",
        f"🚫 Blocked: <b>{blocked}</b>",
        f"👥 Total: <b>{total}</b>",
        "",
        f"🕐 Updated: {timestamp}",
    ]

    if call.message:
        try:
            await call.message.edit_text(
                "\n".join(lines),
                reply_markup=AdminKeyboard.broadcast_status(public_id, bc_status, _),
            )
        except TelegramBadRequest:
            # Message not modified - ignore
            pass


# ============ Cancel Running Broadcast ============


@router.callback_query(F.data.startswith("admin:broadcast:cancel:"))
async def admin_broadcast_cancel_running(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Cancel a running broadcast."""
    await call.answer("Cancelling...")

    try:
        public_id = call.data.split(":")[-1]
    except IndexError:
        return

    try:
        await AdminService.cancel_broadcast(public_id)

        if call.message:
            await call.message.edit_text(
                f"⛔ <b>Broadcast Cancelled</b>\n\n"
                f"📋 ID: <code>{public_id}</code>\n\n"
                "The broadcast has been cancelled. "
                "Messages already sent will not be recalled.",
                reply_markup=AdminKeyboard.back_to_broadcast(_),
            )
    except Exception as e:
        logger.warning("Failed to cancel broadcast", error=str(e))
        if call.message:
            await call.message.answer("❌ Failed to cancel broadcast.")
