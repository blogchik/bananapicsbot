import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from api_client import ApiClient
from config import load_settings
from keyboards import topup_menu

router = Router()


class TopUpStates(StatesGroup):
    waiting_for_stars = State()


def parse_stars_amount(value: str) -> int | None:
    value = value.strip().replace(" ", "")
    if not value.isdigit():
        return None
    amount = int(value)
    return amount if amount > 0 else None


async def get_stars_options(client: ApiClient) -> dict:
    return await client.get_stars_options()


def calculate_credits(stars_amount: int, numerator: int, denominator: int) -> int:
    if stars_amount <= 0 or denominator <= 0:
        return 0
    return int(round(stars_amount * numerator / denominator))


def format_exchange_rate(numerator: int, denominator: int) -> str:
    if numerator <= 0 or denominator <= 0:
        return ""
    return f"Kurs: {denominator} ⭐ = {numerator} credit"


async def send_stars_invoice(
    message: Message,
    stars_amount: int,
    numerator: int,
    denominator: int,
    currency: str,
) -> None:
    settings = load_settings()
    credits = calculate_credits(stars_amount, numerator, denominator)
    payload = f"stars:{stars_amount}:{uuid.uuid4().hex}"
    title = "Balans to'ldirish"
    description = f"{stars_amount} ⭐ → {credits} credit"
    prices = [LabeledPrice(label="Telegram Stars", amount=stars_amount)]
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=title,
        description=description,
        payload=payload,
        provider_token=settings.payment_provider_token,
        currency=currency,
        prices=prices,
        reply_to_message_id=message.message_id,
    )


@router.callback_query(F.data == "menu:topup")
async def open_topup_menu(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message:
        await call.message.delete()
    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        options = await get_stars_options(client)
    except Exception:
        await call.message.answer("Server bilan ulanishda xatolik. Keyinroq urinib ko'ring.")
        return
    if not options.get("enabled"):
        await call.message.answer("To'lovlar hozircha yopiq.")
        return
    presets = options.get("preset_stars") or []
    numerator = int(options.get("exchange_numerator", 1))
    denominator = int(options.get("exchange_denominator", 1))
    preset_pairs = [(amount, calculate_credits(amount, numerator, denominator)) for amount in presets]
    rate_line = format_exchange_rate(numerator, denominator)
    text = (
        "⭐ Balans to'ldirish\n"
        "Telegram Stars orqali to'lov qiling.\n"
        f"{rate_line}\n"
        "Summani tanlang yoki o'zingiz kiriting."
    )
    await state.update_data(stars_options=options)
    await call.message.answer(text, reply_markup=topup_menu(preset_pairs))


@router.callback_query(F.data.startswith("topup:stars:"))
async def handle_topup_preset(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    try:
        stars_amount = int(call.data.split(":", 2)[2])
    except (IndexError, ValueError):
        return
    data = await state.get_data()
    options = data.get("stars_options")
    if not options:
        settings = load_settings()
        client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
        options = await get_stars_options(client)
    min_stars = int(options.get("min_stars", 0))
    if stars_amount < min_stars:
        await call.message.answer("Minimal summa 70 ⭐.")
        return
    numerator = int(options.get("exchange_numerator", 1))
    denominator = int(options.get("exchange_denominator", 1))
    await send_stars_invoice(
        call.message,
        stars_amount,
        numerator,
        denominator,
        str(options.get("currency", "XTR")),
    )


@router.callback_query(F.data == "topup:custom")
async def handle_topup_custom(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.set_state(TopUpStates.waiting_for_stars)
    await call.message.answer(
        "Necha ⭐ to'lamoqchisiz? (minimum 70)",
        reply_to_message_id=call.message.message_id,
    )


@router.message(TopUpStates.waiting_for_stars)
async def handle_custom_stars(message: Message, state: FSMContext) -> None:
    amount = parse_stars_amount(message.text or "")
    if amount is None:
        await message.answer(
            "Raqam ko'rinishida yuboring. Masalan: 70",
            reply_to_message_id=message.message_id,
        )
        return
    data = await state.get_data()
    options = data.get("stars_options")
    if not options:
        settings = load_settings()
        client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
        options = await get_stars_options(client)
    min_stars = int(options.get("min_stars", 0))
    if amount < min_stars:
        await message.answer(
            f"Minimal summa {min_stars} ⭐.",
            reply_to_message_id=message.message_id,
        )
        return
    numerator = int(options.get("exchange_numerator", 1))
    denominator = int(options.get("exchange_denominator", 1))
    credits = calculate_credits(amount, numerator, denominator)
    await message.answer(
        f"Siz {amount} ⭐ uchun {credits} credit olasiz.",
        reply_to_message_id=message.message_id,
    )
    await state.clear()
    await send_stars_invoice(
        message,
        amount,
        numerator,
        denominator,
        str(options.get("currency", "XTR")),
    )


@router.pre_checkout_query()
async def handle_pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if not payment:
        return
    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        result = await client.confirm_stars_payment(
            telegram_id=message.from_user.id,
            stars_amount=payment.total_amount,
            currency=payment.currency,
            telegram_charge_id=payment.telegram_payment_charge_id,
            provider_charge_id=payment.provider_payment_charge_id,
            invoice_payload=payment.invoice_payload,
        )
    except Exception:
        await message.answer(
            "To'lovni tasdiqlashda muammo bo'ldi. Keyinroq urinib ko'ring.",
            reply_to_message_id=message.message_id,
        )
        return
    credits_added = result.get("credits_added")
    balance = result.get("balance")
    await message.answer(
        (f"✅ To'lov qabul qilindi.\n{payment.total_amount} ⭐ → {credits_added} credit\nBalans: {balance}"),
        reply_to_message_id=message.message_id,
    )
