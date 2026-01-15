from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User

from api_client import ApiClient
from config import load_settings
from keyboards import referral_menu

router = Router()


async def get_bot_username(message: Message) -> str:
    me = await message.bot.get_me()
    return me.username or ""


def format_referral_text(
    link: str,
    referrals_count: int,
    bonus_total: int,
    bonus_percent: int,
) -> str:
    return (
        "🤝 Referral\n"
        f"Do'stlaringizni taklif qiling va ularning to'lovlaridan {bonus_percent}% bonus oling.\n"
        "Referral faqat yangi userlar uchun ishlaydi.\n\n"
        f"Link: {link}\n\n"
        f"Referallar: {referrals_count}\n"
        f"Yig'ilgan bonus: {bonus_total} credit"
    )


async def send_referral_menu(message: Message, user: User) -> None:
    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        await client.sync_user(user.id)
        info = await client.get_referral_info(user.id)
    except Exception:
        await message.answer("Server bilan ulanishda xatolik. Keyinroq urinib ko'ring.")
        return
    try:
        username = await get_bot_username(message)
    except Exception:
        username = ""
    code = str(info.get("referral_code", ""))
    link = f"https://t.me/{username}?start=r_{code}" if username and code else "-"
    text = format_referral_text(
        link,
        int(info.get("referrals_count", 0)),
        int(info.get("referral_credits_total", 0)),
        int(info.get("bonus_percent", 10)),
    )
    await message.answer(text, reply_markup=referral_menu())




@router.message(Command("referral"))
async def referral_command(message: Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("User topilmadi.")
        return
    await send_referral_menu(message, user)


@router.callback_query(lambda call: call.data == "menu:referral")
async def referral_callback(call: CallbackQuery) -> None:
    await call.answer()
    if call.message:
        await call.message.delete()
        await send_referral_menu(call.message, call.from_user)

