from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User

from api_client import ApiClient
from config import load_settings
from keyboards import referral_menu
from locales.base import TranslationKey

router = Router()


async def get_bot_username(message: Message) -> str:
    me = await message.bot.get_me()
    return me.username or ""


async def send_referral_menu(message: Message, user: User, _) -> None:
    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        await client.sync_user(user.id)
        info = await client.get_referral_info(user.id)
    except Exception:
        await message.answer(_(TranslationKey.ERROR_CONNECTION))
        return
    try:
        username = await get_bot_username(message)
    except Exception:
        username = ""
    code = str(info.get("referral_code", ""))
    link = f"https://t.me/{username}?start=r_{code}" if username and code else "-"
    
    bonus_percent = int(info.get("bonus_percent", 10))
    text = (
        f"{_(TranslationKey.REFERRAL_TITLE)}\n"
        f"{_(TranslationKey.REFERRAL_INFO).format(percent=bonus_percent)}\n\n"
        f"{_(TranslationKey.REFERRAL_LINK).format(link=link)}\n\n"
        f"{_(TranslationKey.REFERRAL_COUNT).format(count=info.get('referrals_count', 0))}\n"
        f"{_(TranslationKey.REFERRAL_BONUS).format(total=info.get('referral_credits_total', 0))}"
    )
    await message.answer(text, reply_markup=referral_menu())




@router.message(Command("referral"))
async def referral_command(message: Message, _) -> None:
    user = message.from_user
    if not user:
        await message.answer(_(TranslationKey.ERROR_USER_NOT_FOUND))
        return
    await send_referral_menu(message, user, _)


@router.callback_query(lambda call: call.data == "menu:referral")
async def referral_callback(call: CallbackQuery, _) -> None:
    await call.answer()
    if call.message:
        await call.message.delete()
        await send_referral_menu(call.message, call.from_user, _)

