"""Admin Wavespeed provider status handler."""

from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery
from core.logging import get_logger
from keyboards import AdminKeyboard
from keyboards.builders import AdminCallback
from locales import TranslationKey
from services import AdminService

logger = get_logger(__name__)
router = Router(name="admin_wavespeed")


def _status_emoji(status: str) -> str:
    """Get emoji for provider status."""
    return {"online": "🟢", "degraded": "🟡", "offline": "🔴"}.get(status, "⚪")


def _format_wavespeed_text(
    data: dict,
    _: Callable[[TranslationKey, dict | None], str],
) -> str:
    """Format Wavespeed status data as text."""
    if data.get("error"):
        return _(TranslationKey.ADMIN_WAVESPEED_ERROR, None)

    balance = data.get("balance", {})
    status = data.get("provider_status", "unknown")
    stats_24h = data.get("generations_24h", {})
    stats_7d = data.get("generations_7d", {})
    queue = data.get("queue", {})
    models = data.get("models", [])

    lines = [
        _(TranslationKey.ADMIN_WAVESPEED_TITLE, None),
        "",
        # Provider status & balance
        f"{_status_emoji(status)} {_(TranslationKey.ADMIN_WAVESPEED_STATUS, {'status': status.upper()})}",
        _(
            TranslationKey.ADMIN_WAVESPEED_BALANCE,
            {"amount": f"{balance.get('amount', 0):.2f}", "currency": balance.get("currency", "USD")},
        ),
        "",
        # Queue
        _(
            TranslationKey.ADMIN_WAVESPEED_QUEUE,
            {"pending": queue.get("pending", 0), "running": queue.get("running", 0)},
        ),
        "",
        # 24h stats
        _(TranslationKey.ADMIN_WAVESPEED_STATS_24H, None),
        f"  📊 {stats_24h.get('total', 0)} jami | ✅ {stats_24h.get('completed', 0)} | ❌ {stats_24h.get('failed', 0)}",
        f"  📈 Success rate: {stats_24h.get('success_rate', 0)}%",
        "",
        # 7d stats
        _(TranslationKey.ADMIN_WAVESPEED_STATS_7D, None),
        f"  📊 {stats_7d.get('total', 0)} jami | ✅ {stats_7d.get('completed', 0)} | ❌ {stats_7d.get('failed', 0)}",
        f"  📈 Success rate: {stats_7d.get('success_rate', 0)}%",
    ]

    # Model breakdown (24h)
    if models:
        lines.append("")
        lines.append(_(TranslationKey.ADMIN_WAVESPEED_MODELS, None))
        for m in models[:8]:
            name = m.get("model_name", m.get("model_key", "?"))
            lines.append(f"  • {name}: {m.get('total', 0)} ({m.get('success_rate', 0)}% | {m.get('credits', 0)} cr)")

    return "\n".join(lines)


def _format_recent_text(
    data: dict,
    _: Callable[[TranslationKey, dict | None], str],
) -> str:
    """Format recent generations as text."""
    recent = data.get("recent_generations", [])

    if not recent:
        return _(TranslationKey.ADMIN_WAVESPEED_TITLE, None) + "\n\n📭 So'nggi generatsiyalar yo'q."

    status_emoji = {
        "completed": "✅",
        "failed": "❌",
        "running": "⏳",
        "pending": "🔄",
        "queued": "🔄",
        "configuring": "⚙️",
    }

    lines = [
        _(TranslationKey.ADMIN_WAVESPEED_RECENT, None),
        "",
    ]

    for gen in recent[:10]:
        emoji = status_emoji.get(gen.get("status", ""), "❓")
        model = gen.get("model_name", gen.get("model_key", "?"))
        cost = gen.get("cost", 0) or 0
        created = (gen.get("created_at") or "")[:16].replace("T", " ")
        prompt = gen.get("prompt", "")[:40]
        if prompt:
            prompt = f' "{prompt}"'

        lines.append(f"{emoji} {model} | {cost} cr | {created}")
        if prompt:
            lines.append(f"   {prompt}")

    return "\n".join(lines)


@router.callback_query(F.data == AdminCallback.WAVESPEED)
async def admin_wavespeed(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show Wavespeed provider status."""
    await call.answer()

    try:
        data = await AdminService.get_wavespeed_status()
    except Exception as e:
        logger.warning("Failed to get wavespeed status", error=str(e))
        if call.message:
            await call.message.edit_text(
                _(TranslationKey.ERROR_CONNECTION, None),
                reply_markup=AdminKeyboard.back_to_main(_),
            )
        return

    text = _format_wavespeed_text(data, _)

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=AdminKeyboard.wavespeed_menu(_),
        )


@router.callback_query(F.data == AdminCallback.WAVESPEED_REFRESH)
async def admin_wavespeed_refresh(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Refresh Wavespeed status data."""
    await call.answer("🔄")

    try:
        data = await AdminService.get_wavespeed_status()
    except Exception as e:
        logger.warning("Failed to refresh wavespeed status", error=str(e))
        if call.message:
            await call.message.edit_text(
                _(TranslationKey.ERROR_CONNECTION, None),
                reply_markup=AdminKeyboard.wavespeed_menu(_),
            )
        return

    text = _format_wavespeed_text(data, _)

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=AdminKeyboard.wavespeed_menu(_),
        )


@router.callback_query(F.data == AdminCallback.WAVESPEED_RECENT)
async def admin_wavespeed_recent(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show recent Wavespeed generations."""
    await call.answer()

    try:
        data = await AdminService.get_wavespeed_status()
    except Exception as e:
        logger.warning("Failed to get recent generations", error=str(e))
        if call.message:
            await call.message.edit_text(
                _(TranslationKey.ERROR_CONNECTION, None),
                reply_markup=AdminKeyboard.wavespeed_back(_),
            )
        return

    text = _format_recent_text(data, _)

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=AdminKeyboard.wavespeed_back(_),
        )
