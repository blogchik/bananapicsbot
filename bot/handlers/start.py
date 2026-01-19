from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from api_client import ApiClient
from config import load_settings
from keyboards import home_menu

WELCOME_TEXT = "Assalomu alaykum! Bananapics botiga xush kelibsiz 😊\nPrompt yuboring yoki rasm qo'shib generatsiya boshlang."
REFERRAL_NOTICE_TEMPLATE = (
    "👤 Yangi referral qo'shildi.\nUning to'lovlaridan {bonus}% bonus olasiz."
)

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    user = message.from_user
    if user:
        referral_code = None
        if message.text:
            parts = message.text.split(maxsplit=1)
            if len(parts) > 1 and parts[1].startswith("r_"):
                referral_code = parts[1][2:].strip() or None
        settings = load_settings()
        client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
        try:
            result = await client.sync_user(user.id, referral_code=referral_code)
            if result.get("referral_applied") and result.get("referrer_telegram_id"):
                bonus_percent = int(result.get("bonus_percent", 10))
                await message.bot.send_message(
                    chat_id=int(result["referrer_telegram_id"]),
                    text=REFERRAL_NOTICE_TEMPLATE.format(bonus=bonus_percent),
                )
        except Exception:
            pass
    clearing = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await clearing.delete()
    await message.answer(WELCOME_TEXT, reply_markup=home_menu())


@router.callback_query(lambda call: call.data == "menu:home")
async def home_callback(call: CallbackQuery) -> None:
    await call.answer()
    if call.message:
        await call.message.delete()
    await call.message.answer(WELCOME_TEXT, reply_markup=home_menu())
