"""Admin panel keyboards."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.builders import AdminCallback, MenuCallback
from locales import TranslationKey


class AdminKeyboard:
    """Admin panel keyboard builder."""

    @staticmethod
    def main(_: Callable[[TranslationKey, dict | None], str]) -> InlineKeyboardMarkup:
        """Build main admin panel menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.ADMIN_STATS, None),
                        callback_data=AdminCallback.STATS,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.ADMIN_USERS, None),
                        callback_data=AdminCallback.USERS,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.ADMIN_ADD_CREDITS, None),
                        callback_data=AdminCallback.ADD_CREDITS,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.ADMIN_BROADCAST, None),
                        callback_data=AdminCallback.BROADCAST,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.ADMIN_REFUND, None),
                        callback_data=AdminCallback.REFUND,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.HOME, None),
                        callback_data=MenuCallback.HOME,
                    )
                ],
            ]
        )

    @staticmethod
    def users_list(
        users: list[dict],
        page: int,
        total_pages: int,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build users list with pagination."""
        rows: list[list[InlineKeyboardButton]] = []

        # User buttons
        for user in users:
            user_id = user.get("telegram_id", 0)
            name = user.get("name", str(user_id))
            balance = user.get("balance", 0)
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"👤 {name} ({balance} cr)",
                        callback_data=AdminCallback.user_detail(user_id),
                    )
                ]
            )

        # Pagination
        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=AdminCallback.user_page(page - 1),
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="noop",
            )
        )

        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=AdminCallback.user_page(page + 1),
                )
            )

        if nav_row:
            rows.append(nav_row)

        # Back button
        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=AdminCallback.PANEL,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def user_detail(
        user_id: int,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build user detail menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.ADMIN_ADD_CREDITS, None),
                        callback_data=f"admin:user:credits:{user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.USERS,
                    )
                ],
            ]
        )

    @staticmethod
    def back_to_panel(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build back to panel button."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.PANEL,
                    )
                ]
            ]
        )

    @staticmethod
    def stats_menu(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build stats submenu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 Overview",
                        callback_data=AdminCallback.STATS_OVERVIEW,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Users Stats",
                        callback_data=AdminCallback.STATS_USERS,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎨 Generations Stats",
                        callback_data=AdminCallback.STATS_GENERATIONS,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💰 Revenue Stats",
                        callback_data=AdminCallback.STATS_REVENUE,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.MAIN,
                    )
                ],
            ]
        )

    @staticmethod
    def stats_back(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build back button for stats."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.STATS,
                    )
                ]
            ]
        )

    @staticmethod
    def users_menu(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build users management menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔍 Search User",
                        callback_data=AdminCallback.USERS_SEARCH,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Users List",
                        callback_data=AdminCallback.USERS_LIST,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.MAIN,
                    )
                ],
            ]
        )

    @staticmethod
    def back_to_users(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build back button to users menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.USERS,
                    )
                ]
            ]
        )

    @staticmethod
    def user_list(
        users: list[dict],
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build simple user list."""
        rows: list[list[InlineKeyboardButton]] = []

        for user in users:
            user_id = user.get("telegram_id", 0)
            name = user.get("full_name") or user.get("username") or str(user_id)
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"👤 {name}",
                        callback_data=f"admin:user:view:{user_id}",
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=AdminCallback.USERS,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def user_list_paginated(
        users: list[dict],
        page: int,
        has_more: bool,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build paginated user list."""
        rows: list[list[InlineKeyboardButton]] = []

        for user in users:
            user_id = user.get("telegram_id", 0)
            name = user.get("full_name") or user.get("username") or str(user_id)
            balance = user.get("balance", 0)
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"👤 {name} | {balance} cr",
                        callback_data=f"admin:user:view:{user_id}",
                    )
                ]
            )

        # Pagination
        nav_row = []
        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"admin:users:page:{page - 1}",
                )
            )

        if has_more:
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"admin:users:page:{page + 1}",
                )
            )

        if nav_row:
            rows.append(nav_row)

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=AdminCallback.USERS,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def user_actions(
        user_id: int,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build user actions menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💰 Add Credits",
                        callback_data=f"admin:user:credits:{user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Refund",
                        callback_data=f"admin:user:refund:{user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🚫 Ban/Unban",
                        callback_data=f"admin:user:ban:{user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.USERS,
                    )
                ],
            ]
        )

    @staticmethod
    def refund_menu(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build refund type selection menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎨 Credit Refund (Generatsiya)",
                        callback_data=AdminCallback.REFUND_CREDITS,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐ Stars Refund (To'lov)",
                        callback_data=AdminCallback.REFUND_STARS,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.MAIN,
                    )
                ],
            ]
        )

    @staticmethod
    def stars_refund_confirm(
        user_id: int,
        stars_amount: int,
        credits_to_deduct: int,
        current_balance: int,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build stars refund confirmation."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅ Tasdiqlash ({stars_amount}⭐ = {credits_to_deduct} cr)",
                        callback_data=AdminCallback.REFUND_STARS_CONFIRM,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish",
                        callback_data=AdminCallback.REFUND_STARS_CANCEL,
                    )
                ],
            ]
        )

    @staticmethod
    def stars_refund_transactions(
        transactions: list[dict],
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build transaction selection for stars refund."""
        from datetime import datetime

        buttons: list[list[InlineKeyboardButton]] = []

        for idx, tx in enumerate(transactions[:10]):  # Limit to 10 transactions
            amount = tx["amount"]
            tx_date = tx.get("date", 0)

            # Format date with time
            if tx_date:
                dt = datetime.fromtimestamp(tx_date)
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            else:
                date_str = "???"

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"⭐ {amount} Stars - {date_str}",
                        callback_data=AdminCallback.refund_stars_tx(idx),
                    )
                ]
            )

        # Add "Refund All" button if multiple transactions
        if len(transactions) > 1:
            total = sum(tx["amount"] for tx in transactions)
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"🔄 Barchasini qaytarish ({total}⭐)",
                        callback_data=AdminCallback.REFUND_STARS_ALL,
                    )
                ]
            )

        # Back button
        buttons.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=AdminCallback.REFUND,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def cancel_action(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build cancel action button."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data=AdminCallback.CANCEL,
                    )
                ]
            ]
        )

    @staticmethod
    def back_to_main(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build back to main admin panel button."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.MAIN,
                    )
                ]
            ]
        )

    @staticmethod
    def generation_list(
        generations: list[dict],
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build generation list for refund."""
        rows: list[list[InlineKeyboardButton]] = []

        for gen in generations:
            gen_id = gen.get("id", "")
            model = gen.get("model", "Unknown")
            credits = gen.get("credits", 0)
            created = gen.get("created_at", "")[:10]

            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"🎨 {model} | {credits} cr | {created}",
                        callback_data=f"admin:refund:gen:{gen_id}",
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=AdminCallback.USERS,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)

    # ============ Broadcast ============

    @staticmethod
    def broadcast_menu(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build broadcast menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📤 New Broadcast",
                        callback_data=AdminCallback.BROADCAST_NEW,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📜 History",
                        callback_data=AdminCallback.BROADCAST_HISTORY,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.MAIN,
                    )
                ],
            ]
        )

    @staticmethod
    def broadcast_filter_select(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build broadcast filter selection."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👥 All Users",
                        callback_data="admin:broadcast:filter:all",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔥 Active (7 days)",
                        callback_data="admin:broadcast:filter:active_7d",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Active (30 days)",
                        callback_data="admin:broadcast:filter:active_30d",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💰 With Balance",
                        callback_data="admin:broadcast:filter:with_balance",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💳 Paid Users",
                        callback_data="admin:broadcast:filter:paid_users",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆕 New Users (7 days)",
                        callback_data="admin:broadcast:filter:new_users",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data=AdminCallback.BROADCAST_CANCEL,
                    )
                ],
            ]
        )

    @staticmethod
    def broadcast_button_options(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build inline button options for broadcast."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔘 Add Button",
                        callback_data="admin:broadcast:add_button",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⏭ Skip (No Button)",
                        callback_data="admin:broadcast:skip_button",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data=AdminCallback.BROADCAST_CANCEL,
                    )
                ],
            ]
        )

    @staticmethod
    def broadcast_preview(
        users_count: int,
        filter_type: str,
        has_button: bool,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build broadcast preview/confirmation."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"📤 Send to {users_count} users",
                        callback_data=AdminCallback.BROADCAST_CONFIRM,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data=AdminCallback.BROADCAST_CANCEL,
                    )
                ],
            ]
        )

    @staticmethod
    def broadcast_confirm(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build broadcast confirmation buttons."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Confirm",
                        callback_data=AdminCallback.BROADCAST_CONFIRM,
                    ),
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data=AdminCallback.BROADCAST_CANCEL,
                    ),
                ]
            ]
        )

    @staticmethod
    def broadcast_status(
        public_id: str,
        status: str,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build broadcast status button."""
        rows = [
            [
                InlineKeyboardButton(
                    text="🔄 Refresh",
                    callback_data=f"admin:broadcast:status:{public_id}",
                )
            ]
        ]

        # Add cancel button if still running
        if status in ("pending", "running"):
            rows.append(
                [
                    InlineKeyboardButton(
                        text="⛔ Cancel Broadcast",
                        callback_data=f"admin:broadcast:cancel:{public_id}",
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=AdminCallback.BROADCAST,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def back_to_broadcast(
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build back to broadcast menu button."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.BROADCAST,
                    )
                ]
            ]
        )
