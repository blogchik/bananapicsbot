from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

WELCOME_TEXT = "Assalomu alaykum! Bananapicsbotga xush kelibsiz."

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(WELCOME_TEXT)
