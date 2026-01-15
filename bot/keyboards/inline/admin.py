"""Admin panel keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Callable

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
            rows.append([
                InlineKeyboardButton(
                    text=f"👤 {name} ({balance} cr)",
                    callback_data=AdminCallback.user_detail(user_id),
                )
            ])
        
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
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=AdminCallback.PANEL,
            )
        ])
        
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
            rows.append([
                InlineKeyboardButton(
                    text=f"👤 {name}",
                    callback_data=f"admin:user:view:{user_id}",
                )
            ])
        
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=AdminCallback.USERS,
            )
        ])
        
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
            rows.append([
                InlineKeyboardButton(
                    text=f"👤 {name} | {balance} cr",
                    callback_data=f"admin:user:view:{user_id}",
                )
            ])
        
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
        
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=AdminCallback.USERS,
            )
        ])
        
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
            
            rows.append([
                InlineKeyboardButton(
                    text=f"🎨 {model} | {credits} cr | {created}",
                    callback_data=f"admin:refund:gen:{gen_id}",
                )
            ])
        
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=AdminCallback.USERS,
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)
    
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
        broadcast_id: str,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build broadcast status button."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Refresh",
                        callback_data=f"admin:broadcast:status:{broadcast_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=AdminCallback.BROADCAST,
                    )
                ],
            ]
        )
    
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
