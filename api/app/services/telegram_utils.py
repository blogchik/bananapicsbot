"""Shared Telegram utility functions for message sending and formatting.

This module provides common utilities for interacting with the Telegram Bot API,
used by both the API layer (endpoints) and the Celery task layer (workers).
"""

import httpx

from app.core.config import get_settings


def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram parse_mode='HTML'.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text safe for Telegram messages
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_telegram_api_url(bot_token: str, method: str) -> str:
    """Build Telegram Bot API URL for a given method.

    Args:
        bot_token: Bot token from BotFather
        method: API method name (e.g., 'sendMessage', 'sendPhoto')

    Returns:
        Full URL for the API endpoint
    """
    settings = get_settings()
    return f"{settings.telegram_api_base_url}/bot{bot_token}/{method}"


def build_inline_keyboard(button_text: str, button_url: str) -> dict:
    """Build inline keyboard markup with a single button.

    Args:
        button_text: Text to display on the button
        button_url: URL to open when button is clicked

    Returns:
        Inline keyboard markup dict for Telegram API
    """
    return {"inline_keyboard": [[{"text": button_text, "url": button_url}]]}


def send_telegram_message(
    bot_token: str,
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: dict | None = None,
    timeout: float = 10.0,
) -> dict:
    """Send a text message via Telegram Bot API (synchronous).

    Args:
        bot_token: Bot token from BotFather
        chat_id: Target chat ID
        text: Message text
        parse_mode: Message formatting mode (default: HTML)
        reply_markup: Optional keyboard markup
        timeout: HTTP request timeout in seconds

    Returns:
        Telegram API response dict

    Raises:
        Exception: If Telegram API returns an error
    """
    url = build_telegram_api_url(bot_token, "sendMessage")
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
        return data


async def send_telegram_message_async(
    bot_token: str,
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: dict | None = None,
    timeout: float = 10.0,
) -> dict:
    """Send a text message via Telegram Bot API (asynchronous).

    Args:
        bot_token: Bot token from BotFather
        chat_id: Target chat ID
        text: Message text
        parse_mode: Message formatting mode (default: HTML)
        reply_markup: Optional keyboard markup
        timeout: HTTP request timeout in seconds

    Returns:
        Telegram API response dict

    Raises:
        Exception: If Telegram API returns an error
    """
    url = build_telegram_api_url(bot_token, "sendMessage")
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
        return data


def format_model_hashtag(model_name: str) -> str:
    """Format model name as a hashtag for Telegram messages.

    Args:
        model_name: Model name (e.g., "nano-banana-pro")

    Returns:
        Hashtag formatted model name (e.g., "#NanoBananaPro")
    """
    clean = "".join(c for c in model_name if c.isalnum())
    if not clean:
        return "#Model"
    return f"#{clean.title()}"
