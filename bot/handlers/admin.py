from __future__ import annotations

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from api_client import ApiClient
from config import load_settings

router = Router()

ADMIN_USER_ID = 686980246


def is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id == ADMIN_USER_ID)


def parse_two_ints(text: str | None) -> tuple[int, int] | None:
    if not text:
        return None
    parts = text.strip().split()
    if len(parts) < 3:
        return None
    try:
        first = int(parts[1])
        second = int(parts[2])
    except ValueError:
        return None
    return first, second


async def fetch_star_transactions(bot_token: str, offset: int, limit: int) -> list[dict]:
    url = f"https://api.telegram.org/bot{bot_token}/getStarTransactions"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params={"offset": offset, "limit": limit}) as resp:
            data = await resp.json()
            if not data.get("ok"):
                raise RuntimeError(data.get("description", "Telegram API error"))
            result = data.get("result") or {}
            return list(result.get("transactions") or [])


async def refund_star_payment(bot_token: str, user_id: int, charge_id: str) -> tuple[bool, str | None]:
    url = f"https://api.telegram.org/bot{bot_token}/refundStarPayment"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            data={"user_id": user_id, "telegram_payment_charge_id": charge_id},
        ) as resp:
            payload = await resp.json()
            if payload.get("ok"):
                return True, None
            return False, str(payload.get("description"))


@router.message(Command("refund"))
async def refund_command(message: Message) -> None:
    if not is_admin(message):
        return
    parsed = parse_two_ints(message.text)
    if not parsed:
        await message.answer("Foydalanish: /refund USER_ID STARS")
        return
    user_id, stars_amount = parsed
    if stars_amount <= 0:
        await message.answer("STARS musbat bo'lishi kerak.")
        return
    settings = load_settings()
    refunded_total = 0
    refunded_count = 0
    errors: list[str] = []
    offset = 0
    limit = 100
    while refunded_total < stars_amount:
        transactions = await fetch_star_transactions(settings.bot_token, offset, limit)
        if not transactions:
            break
        for tx in reversed(transactions):
            source = tx.get("source") or {}
            if source.get("type") != "user":
                continue
            if source.get("transaction_type") != "invoice_payment":
                continue
            user = source.get("user") or {}
            if int(user.get("id", 0)) != user_id:
                continue
            amount = int(tx.get("amount") or 0)
            if amount <= 0:
                continue
            charge_id = tx.get("id")
            if not charge_id:
                continue
            ok, error = await refund_star_payment(settings.bot_token, user_id, str(charge_id))
            if ok:
                refunded_total += amount
                refunded_count += 1
            else:
                if error and "CHARGE_ALREADY_REFUNDED" in error:
                    continue
                errors.append(error or "unknown error")
            if refunded_total >= stars_amount:
                break
        offset += len(transactions)
    if refunded_total <= 0:
        await message.answer("Refund uchun mos to'lov topilmadi.")
        return
    response = f"Refund yakunlandi. Qaytarildi: {refunded_total} ⭐ ({refunded_count} ta to'lov)."
    if refunded_total < stars_amount:
        response += " To'liq summa topilmadi."
    if errors:
        response += f" Xatolar: {len(errors)}"
    await message.answer(response)


@router.message(Command("pay"))
async def pay_command(message: Message) -> None:
    if not is_admin(message):
        return
    parsed = parse_two_ints(message.text)
    if not parsed:
        await message.answer("Foydalanish: /pay USER_ID CREDITS")
        return
    user_id, credits = parsed
    if credits <= 0:
        await message.answer("CREDITS musbat bo'lishi kerak.")
        return
    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        result = await client.add_admin_credits(
            telegram_id=user_id,
            credits=credits,
            description=f"Admin pay {credits}",
        )
    except Exception:
        await message.answer("Server bilan ulanishda xatolik. Keyinroq urinib ko'ring.")
        return
    await message.answer(
        f"✅ Balans to'ldirildi.\n"
        f"Qo'shildi: {result.get('credits_added')} credit\n"
        f"Yangi balans: {result.get('balance')}"
    )
