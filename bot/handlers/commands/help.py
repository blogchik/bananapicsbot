"""Help command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from typing import Callable

from keyboards import HomeKeyboard
from locales import TranslationKey
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="help")


HELP_TEXT_UZ = """
🤖 <b>Bananapics Bot</b>

<b>Qanday ishlaydi?</b>
1. Prompt yuboring yoki rasm qo'shing
2. Model va parametrlarni tanlang
3. Generatsiyani boshlang
4. Natijani oling!

<b>Buyruqlar:</b>
/start - Botni boshlash
/profile - Profilingiz
/settings - Sozlamalar
/referral - Referral dasturi
/help - Yordam

<b>Savollar bo'lsa:</b>
@support_username
"""

HELP_TEXT_RU = """
🤖 <b>Bananapics Bot</b>

<b>Как работает?</b>
1. Отправьте промпт или добавьте изображение
2. Выберите модель и параметры
3. Запустите генерацию
4. Получите результат!

<b>Команды:</b>
/start - Запуск бота
/profile - Ваш профиль
/settings - Настройки
/referral - Реферальная программа
/help - Помощь

<b>Вопросы?</b>
@support_username
"""

HELP_TEXT_EN = """
🤖 <b>Bananapics Bot</b>

<b>How it works?</b>
1. Send a prompt or add an image
2. Select model and parameters
3. Start generation
4. Get your result!

<b>Commands:</b>
/start - Start the bot
/profile - Your profile
/settings - Settings
/referral - Referral program
/help - Help

<b>Questions?</b>
@support_username
"""

HELP_TEXTS = {
    "uz": HELP_TEXT_UZ,
    "ru": HELP_TEXT_RU,
    "en": HELP_TEXT_EN,
}


@router.message(Command("help"))
async def help_handler(
    message: Message,
    language: str,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle /help command."""
    help_text = HELP_TEXTS.get(language, HELP_TEXT_UZ)
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=HomeKeyboard.main(_),
    )
