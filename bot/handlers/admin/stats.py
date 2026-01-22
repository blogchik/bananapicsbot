"""Admin statistics handlers."""

from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery
from core.logging import get_logger
from keyboards import AdminKeyboard
from keyboards.builders import AdminCallback
from locales import TranslationKey
from services import AdminService

logger = get_logger(__name__)
router = Router(name="admin_stats")


def format_stats_text(
    stats: dict,
    _: Callable[[TranslationKey, dict | None], str],
) -> str:
    """Format statistics data as text."""
    lines = [
        _(TranslationKey.ADMIN_STATS_TITLE, None),
        "",
    ]

    users = stats.get("users", {})
    lines.append(_(TranslationKey.ADMIN_STATS_USERS_TOTAL, {"count": users.get("total", 0)}))
    lines.append(_(TranslationKey.ADMIN_STATS_USERS_TODAY, {"count": users.get("today", 0)}))
    lines.append(_(TranslationKey.ADMIN_STATS_USERS_WEEK, {"count": users.get("week", 0)}))
    lines.append(_(TranslationKey.ADMIN_STATS_USERS_MONTH, {"count": users.get("month", 0)}))
    lines.append("")

    generations = stats.get("generations", {})
    lines.append(_(TranslationKey.ADMIN_STATS_GENS_TOTAL, {"count": generations.get("total", 0)}))
    lines.append(_(TranslationKey.ADMIN_STATS_GENS_TODAY, {"count": generations.get("today", 0)}))
    lines.append(_(TranslationKey.ADMIN_STATS_GENS_WEEK, {"count": generations.get("week", 0)}))
    lines.append("")

    revenue = stats.get("revenue", {})
    lines.append(_(TranslationKey.ADMIN_STATS_REVENUE_TOTAL, {"amount": revenue.get("total_stars", 0)}))
    lines.append(_(TranslationKey.ADMIN_STATS_REVENUE_TODAY, {"amount": revenue.get("today_stars", 0)}))
    lines.append(_(TranslationKey.ADMIN_STATS_REVENUE_WEEK, {"amount": revenue.get("week_stars", 0)}))

    return "\n".join(lines)


@router.callback_query(F.data == AdminCallback.STATS_OVERVIEW)
async def admin_stats_overview(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show stats overview."""
    await call.answer()

    try:
        stats = await AdminService.get_overview_stats()
    except Exception as e:
        logger.warning("Failed to get stats", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    text = format_stats_text(stats, _)

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=AdminKeyboard.stats_back(_),
        )


@router.callback_query(F.data == AdminCallback.STATS_USERS)
async def admin_stats_users(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show user statistics."""
    await call.answer()

    try:
        stats = await AdminService.get_user_stats()
    except Exception as e:
        logger.warning("Failed to get user stats", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    lines = [
        _(TranslationKey.ADMIN_USER_STATS_TITLE, None),
        "",
        _(TranslationKey.ADMIN_STATS_USERS_TOTAL, {"count": stats.get("total", 0)}),
        _(TranslationKey.ADMIN_STATS_USERS_ACTIVE, {"count": stats.get("active", 0)}),
        _(TranslationKey.ADMIN_STATS_USERS_PAYING, {"count": stats.get("paying", 0)}),
        "",
        _(TranslationKey.ADMIN_STATS_AVG_BALANCE, {"amount": round(stats.get("avg_balance", 0), 2)}),
        _(TranslationKey.ADMIN_STATS_TOTAL_BALANCE, {"amount": stats.get("total_balance", 0)}),
    ]

    if call.message:
        await call.message.edit_text(
            "\n".join(lines),
            reply_markup=AdminKeyboard.stats_back(_),
        )


@router.callback_query(F.data == AdminCallback.STATS_GENERATIONS)
async def admin_stats_generations(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show generation statistics."""
    await call.answer()

    try:
        stats = await AdminService.get_generation_stats()
    except Exception as e:
        logger.warning("Failed to get generation stats", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    lines = [
        _(TranslationKey.ADMIN_GEN_STATS_TITLE, None),
        "",
        _(TranslationKey.ADMIN_STATS_GENS_TOTAL, {"count": stats.get("total", 0)}),
        _(TranslationKey.ADMIN_STATS_GENS_COMPLETED, {"count": stats.get("completed", 0)}),
        _(TranslationKey.ADMIN_STATS_GENS_FAILED, {"count": stats.get("failed", 0)}),
        "",
        _(TranslationKey.ADMIN_STATS_CREDITS_SPENT, {"amount": stats.get("credits_spent", 0)}),
    ]

    by_model = stats.get("by_model", {})
    if by_model:
        lines.append("")
        lines.append(_(TranslationKey.ADMIN_STATS_BY_MODEL, None))
        # Handle both dict format (with credits) and int format (legacy)
        sorted_models = sorted(
            by_model.items(), key=lambda x: x[1].get("count", x[1]) if isinstance(x[1], dict) else x[1], reverse=True
        )[:10]
        for model, data in sorted_models:
            if isinstance(data, dict):
                count = data.get("count", 0)
                credits = data.get("credits", 0)
                lines.append(f"  • {model}: {count} ({credits} credits)")
            else:
                lines.append(f"  • {model}: {data}")

    if call.message:
        await call.message.edit_text(
            "\n".join(lines),
            reply_markup=AdminKeyboard.stats_back(_),
        )


@router.callback_query(F.data == AdminCallback.STATS_REVENUE)
async def admin_stats_revenue(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show revenue statistics."""
    await call.answer()

    try:
        stats = await AdminService.get_revenue_stats()
    except Exception as e:
        logger.warning("Failed to get revenue stats", error=str(e))
        if call.message:
            await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    lines = [
        _(TranslationKey.ADMIN_REVENUE_STATS_TITLE, None),
        "",
        _(TranslationKey.ADMIN_STATS_REVENUE_TOTAL, {"amount": stats.get("total_stars", 0)}),
        _(TranslationKey.ADMIN_STATS_REVENUE_TODAY, {"amount": stats.get("today_stars", 0)}),
        _(TranslationKey.ADMIN_STATS_REVENUE_WEEK, {"amount": stats.get("week_stars", 0)}),
        _(TranslationKey.ADMIN_STATS_REVENUE_MONTH, {"amount": stats.get("month_stars", 0)}),
        "",
        _(TranslationKey.ADMIN_STATS_PAYMENTS_COUNT, {"count": stats.get("payments_count", 0)}),
        _(TranslationKey.ADMIN_STATS_AVG_PAYMENT, {"amount": round(stats.get("avg_payment", 0), 2)}),
    ]

    if call.message:
        await call.message.edit_text(
            "\n".join(lines),
            reply_markup=AdminKeyboard.stats_back(_),
        )
