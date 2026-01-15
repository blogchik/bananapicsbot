from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User

from api_client import ApiClient
from config import load_settings
from keyboards import profile_menu
from locales.base import TranslationKey

router = Router()


def format_user_name(user: User) -> str:
    parts = [user.first_name or "", user.last_name or ""]
    name = " ".join(part for part in parts if part).strip()
    return name or (user.username or str(user.id))


async def send_profile(message: Message, user: User, _) -> None:

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    try:
        await client.sync_user(user.id)
        balance = await client.get_balance(user.id)
        trial = await client.get_trial(user.id)
    except Exception:
        await message.answer(_(TranslationKey.ERROR_CONNECTION))
        return

    username = f"@{user.username}" if user.username else "-"
    name = format_user_name(user)

    if trial.trial_available:
        trial_status = _(TranslationKey.PROFILE_TRIAL)
    elif trial.used_count:
        trial_status = _(TranslationKey.PROFILE_TRIAL_USED).format(count=trial.used_count)
    else:
        trial_status = "yo'q"
    
    text = f"{_(TranslationKey.PROFILE_TITLE)}\n" + _(TranslationKey.PROFILE_INFO).format(
        name=name,
        username=username,
        user_id=user.id,
        balance=balance,
        trial=trial_status
    )

    await message.answer(text, reply_markup=profile_menu())


@router.message(Command("profile"))
async def profile_handler(message: Message, _) -> None:
    user = message.from_user
    if not user:
        await message.answer(_(TranslationKey.ERROR_USER_NOT_FOUND))
        return
    await send_profile(message, user, _)


@router.callback_query(lambda call: call.data == "menu:profile")
async def profile_callback(call: CallbackQuery, _) -> None:
    await call.answer()
    if call.message:
        await call.message.delete()
        await send_profile(call.message, call.from_user, _)
