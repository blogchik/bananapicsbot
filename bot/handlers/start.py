from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from keyboards import home_menu

WELCOME_TEXT = "Assalomu alaykum! Bananapicsbotga xush kelibsiz 😊"

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    clearing = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await clearing.delete()
    await message.answer(WELCOME_TEXT, reply_markup=home_menu())


@router.callback_query(lambda call: call.data == "menu:home")
async def home_callback(call: CallbackQuery) -> None:
    await call.answer()
    if call.message:
        await call.message.delete()
    await call.message.answer(WELCOME_TEXT, reply_markup=home_menu())
