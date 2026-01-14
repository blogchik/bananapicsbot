from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User

from api_client import ApiClient
from config import load_settings
from keyboards import profile_menu

router = Router()


def format_user_name(user: User) -> str:
    parts = [user.first_name or "", user.last_name or ""]
    name = " ".join(part for part in parts if part).strip()
    return name or (user.username or str(user.id))


async def send_profile(message: Message, user: User) -> None:

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    try:
        await client.sync_user(user.id)
        balance = await client.get_balance(user.id)
        trial = await client.get_trial(user.id)
    except Exception:
        await message.answer("Server bilan ulanishda xatolik. Keyinroq urinib ko'ring.")
        return

    username = f"@{user.username}" if user.username else "-"
    name = format_user_name(user)

    trial_status = "bor" if trial.trial_available else "yo'q"
    text = (
        "👤 Profil\n"
        "Mana sizning ma'lumotlaringiz:\n"
        f"Ism: {name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n\n"
        f"Balans: {balance}\n"
        f"Trial: {trial_status}"
    )

    if trial.used_count:
        text += f" (ishlatilgan: {trial.used_count})"

    await message.answer(text, reply_markup=profile_menu())


@router.message(Command("profile"))
async def profile_handler(message: Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("User topilmadi.")
        return
    await send_profile(message, user)


@router.callback_query(lambda call: call.data == "menu:profile")
async def profile_callback(call: CallbackQuery) -> None:
    await call.answer()
    if call.message:
        await call.message.delete()
        await send_profile(call.message, call.from_user)
