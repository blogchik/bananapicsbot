import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiClient, ApiError
from config import load_settings
from keyboards import (
    aspect_ratio_menu,
    generation_menu,
    model_menu,
    profile_menu,
    resolution_menu,
    size_menu,
)

router = Router()


def get_support_flags(
    supports_size: bool | None,
    supports_aspect_ratio: bool | None,
    supports_resolution: bool | None,
    size_options: list[str] | None,
    aspect_ratio_options: list[str] | None,
    resolution_options: list[str] | None,
) -> tuple[bool, bool, bool]:
    show_size = bool(supports_size and size_options)
    show_aspect = bool(supports_aspect_ratio and aspect_ratio_options)
    show_resolution = bool(supports_resolution and resolution_options)
    return show_size, show_aspect, show_resolution


def build_generation_text(
    prompt: str,
    model_name: str,
    size: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
    show_size: bool,
    show_aspect: bool,
    show_resolution: bool,
) -> str:
    size_label = size if size else "Default"
    aspect_label = aspect_ratio if aspect_ratio else "Default"
    resolution_label = resolution if resolution else "Default"

    lines = [
        "⚙️ Generatsiya sozlamalari",
        f"Prompt: {prompt}",
        f"Model: {model_name}",
    ]
    if show_size:
        lines.append(f"Size: {size_label}")
    if show_aspect:
        lines.append(f"Aspect ratio: {aspect_label}")
    if show_resolution:
        lines.append(f"Resolution: {resolution_label}")
    return "\n".join(lines)


def normalize_models(models: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for item in models:
        model = item.get("model") or {}
        model_id = model.get("id")
        if not model_id:
            continue
        prices = item.get("prices") or []
        price = int(prices[0].get("unit_price", 0)) if prices else 0
        options = model.get("options") or {}
        size_options = list(options.get("size_options") or [])
        aspect_ratio_options = list(options.get("aspect_ratio_options") or [])
        resolution_options = list(options.get("resolution_options") or [])
        supports_size = bool(options.get("supports_size")) or bool(size_options)
        supports_aspect_ratio = bool(options.get("supports_aspect_ratio")) or bool(
            aspect_ratio_options
        )
        supports_resolution = bool(options.get("supports_resolution")) or bool(
            resolution_options
        )
        normalized.append(
            {
                "id": int(model_id),
                "key": model.get("key"),
                "name": model.get("name") or model.get("key") or str(model_id),
                "price": price,
                "supports_size": supports_size,
                "supports_aspect_ratio": supports_aspect_ratio,
                "supports_resolution": supports_resolution,
                "size_options": size_options,
                "aspect_ratio_options": aspect_ratio_options,
                "resolution_options": resolution_options,
            }
        )
    return normalized


def find_model(models: list[dict], model_id: int) -> dict | None:
    for model in models:
        if int(model["id"]) == model_id:
            return model
    return None


async def fetch_models(client: ApiClient) -> list[dict]:
    return normalize_models(await client.get_models())


async def has_active_generation(client: ApiClient, telegram_id: int) -> bool:
    try:
        data = await client.get_active_generation(telegram_id)
    except Exception:
        return False
    return bool(data.get("has_active"))


async def get_models_from_state(state: FSMContext, client: ApiClient) -> list[dict]:
    data = await state.get_data()
    models = data.get("models")
    if models:
        return models
    models = normalize_models(await client.get_models())
    await state.update_data(models=models)
    return models


@router.message(F.photo)
async def handle_reference_photo(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    if await has_active_generation(client, user.id):
        await message.answer(
            "Sizda hozir aktiv generatsiya bor. Iltimos, tugashini kuting va keyinroq urinib ko'ring."
        )
        return

    data = await state.get_data()
    references = list(data.get("reference_urls", []))
    reference_file_ids = list(data.get("reference_file_ids", []))
    if len(references) >= 10:
        await message.answer("Maksimal 10 ta reference rasm yuborish mumkin.")
        return

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    content = file_bytes.read()
    filename = file.file_path.split("/")[-1]

    try:
        download_url = await client.upload_media(content, filename)
    except Exception:
        download_url = ""
    if not download_url:
        await message.answer("Rasm yuklashda xatolik. Keyinroq urinib ko'ring.")
        return

    references.append(download_url)
    reference_file_ids.append(photo.file_id)
    await state.update_data(reference_urls=references, reference_file_ids=reference_file_ids)

    if message.caption:
        await handle_prompt_message(message, state)
    else:
        await message.answer("Rasm qabul qilindi. Endi prompt yuboring.")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_message(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return

    prompt = message.caption or message.text or ""
    prompt = prompt.strip()
    if not prompt:
        await message.answer("Prompt bo'sh bo'lmasin.")
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    if await has_active_generation(client, user.id):
        await message.answer(
            "Sizda hozir aktiv generatsiya bor. Iltimos, tugashini kuting va keyinroq urinib ko'ring."
        )
        return

    try:
        models = await fetch_models(client)
    except Exception:
        await message.answer("Serverdan model ma'lumotini olishda xatolik.")
        return

    if not models:
        await message.answer("Hozircha model topilmadi.")
        return

    selected_model = models[0]

    data = await state.get_data()
    previous_menu_id = data.get("menu_message_id")
    if previous_menu_id:
        try:
            await message.bot.delete_message(message.chat.id, previous_menu_id)
        except TelegramBadRequest as exc:
            if "message to delete not found" not in str(exc):
                raise

    supports_size = selected_model.get("supports_size")
    supports_aspect_ratio = selected_model.get("supports_aspect_ratio")
    supports_resolution = selected_model.get("supports_resolution")
    size_options = selected_model.get("size_options") or []
    aspect_ratio_options = selected_model.get("aspect_ratio_options") or []
    resolution_options = selected_model.get("resolution_options") or []

    await state.update_data(
        prompt=prompt,
        model_id=selected_model["id"],
        model_name=selected_model["name"],
        model_key=selected_model.get("key"),
        price=selected_model["price"],
        size=None,
        aspect_ratio=None,
        resolution=None,
        supports_size=supports_size,
        supports_aspect_ratio=supports_aspect_ratio,
        supports_resolution=supports_resolution,
        size_options=size_options,
        aspect_ratio_options=aspect_ratio_options,
        resolution_options=resolution_options,
        models=models,
    )

    show_size, show_aspect, show_resolution = get_support_flags(
        supports_size,
        supports_aspect_ratio,
        supports_resolution,
        size_options,
        aspect_ratio_options,
        resolution_options,
    )
    menu_text = build_generation_text(
        prompt,
        selected_model["name"],
        None,
        None,
        None,
        show_size,
        show_aspect,
        show_resolution,
    )
    menu = generation_menu(
        selected_model["name"],
        None,
        None,
        None,
        selected_model["price"],
        show_size,
        show_aspect,
        show_resolution,
    )
    msg = await message.answer(menu_text, reply_markup=menu)
    await state.update_data(menu_message_id=msg.message_id)


@router.callback_query(F.data == "gen:model:menu")
async def open_model_menu(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        models = await get_models_from_state(state, client)
    except Exception:
        await call.message.answer("Model ma'lumotini olishda xatolik.")
        return

    model_id = int(data.get("model_id", 0)) if data.get("model_id") else None
    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(text, reply_markup=model_menu(models, model_id))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:model:set:"))
async def select_model(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    try:
        model_id = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        models = await get_models_from_state(state, client)
    except Exception:
        await call.message.answer("Model ma'lumotini olishda xatolik.")
        return

    selected = find_model(models, model_id)
    if not selected:
        await call.message.answer("Model topilmadi.")
        return

    supports_size = selected.get("supports_size")
    supports_aspect_ratio = selected.get("supports_aspect_ratio")
    supports_resolution = selected.get("supports_resolution")
    size_options = selected.get("size_options") or []
    aspect_ratio_options = selected.get("aspect_ratio_options") or []
    resolution_options = selected.get("resolution_options") or []

    show_size, show_aspect, show_resolution = get_support_flags(
        supports_size,
        supports_aspect_ratio,
        supports_resolution,
        size_options,
        aspect_ratio_options,
        resolution_options,
    )

    size = data.get("size") if show_size else None
    aspect_ratio = data.get("aspect_ratio") if show_aspect else None
    resolution = data.get("resolution") if show_resolution else None

    await state.update_data(
        model_id=selected["id"],
        model_name=selected["name"],
        model_key=selected.get("key"),
        price=selected["price"],
        size=size,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        supports_size=supports_size,
        supports_aspect_ratio=supports_aspect_ratio,
        supports_resolution=supports_resolution,
        size_options=size_options,
        aspect_ratio_options=aspect_ratio_options,
        resolution_options=resolution_options,
    )

    text = build_generation_text(
        prompt,
        selected["name"],
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                selected["name"],
                size,
                aspect_ratio,
                resolution,
                selected["price"],
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:size:menu")
async def open_size_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    supports_size = data.get("supports_size")
    size_options = data.get("size_options") or []
    show_size, show_aspect, show_resolution = get_support_flags(
        supports_size,
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        size_options,
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )
    if not show_size:
        await call.answer("Bu modelda size mavjud emas.", show_alert=True)
        return

    await call.answer()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(text, reply_markup=size_menu(size_options, size))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:size:set:"))
async def select_size(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    size_value = call.data.split(":", 3)[3]
    size = None if size_value == "default" else size_value

    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    await state.update_data(size=size)
    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:ratio:menu")
async def open_ratio_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    aspect_ratio_options = data.get("aspect_ratio_options") or []
    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        aspect_ratio_options,
        data.get("resolution_options"),
    )
    if not show_aspect:
        await call.answer("Bu modelda aspect ratio mavjud emas.", show_alert=True)
        return

    await call.answer()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=aspect_ratio_menu(aspect_ratio_options, aspect_ratio),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:ratio:set:"))
async def select_ratio(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    ratio_value = call.data.split(":", 3)[3]
    aspect_ratio = None if ratio_value == "default" else ratio_value

    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    size = data.get("size")
    resolution = data.get("resolution")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    await state.update_data(aspect_ratio=aspect_ratio)
    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:resolution:menu")
async def open_resolution_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    resolution_options = data.get("resolution_options") or []
    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        resolution_options,
    )
    if not show_resolution:
        await call.answer("Bu modelda resolution mavjud emas.", show_alert=True)
        return

    await call.answer()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=resolution_menu(resolution_options, resolution),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:resolution:set:"))
async def select_resolution(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    resolution_value = call.data.split(":", 3)[3]
    resolution = None if resolution_value == "default" else resolution_value

    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    await state.update_data(resolution=resolution)
    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:back")
async def back_to_generation(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")
    price = int(data.get("price", 0))

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


async def send_result_summary(bot, chat_id: int, prompt: str, model_name: str) -> None:
    text = "✅ Natija tayyor\n" f"Model: {model_name}\n" f"Prompt: {prompt}"
    await bot.send_message(chat_id, text)


async def send_outputs(bot, chat_id: int, outputs: list[str]) -> None:
    for url in outputs:
        sent_photo = False
        try:
            await bot.send_photo(chat_id, url)
            sent_photo = True
        except Exception:
            pass
        try:
            await bot.send_document(chat_id, url)
        except Exception:
            if not sent_photo:
                await bot.send_message(chat_id, url)


async def poll_generation_status(
    bot,
    client: ApiClient,
    chat_id: int,
    message_id: int,
    request_id: int,
    telegram_id: int,
    prompt: str,
    model_name: str,
) -> None:
    last_status = None
    for _ in range(20):
        await asyncio.sleep(3)
        try:
            result = await client.refresh_generation(request_id, telegram_id)
        except Exception:
            continue
        status = result.get("status")
        if status and status != last_status and status not in ("completed", "failed"):
            try:
                await bot.edit_message_text(
                    f"⏳ Jarayonda: {status}",
                    chat_id=chat_id,
                    message_id=message_id,
                )
            except TelegramBadRequest as exc:
                if "message is not modified" not in str(exc):
                    raise
            last_status = status
        if status == "completed":
            try:
                outputs = await client.get_generation_results(request_id, telegram_id)
            except Exception:
                outputs = []
            try:
                await bot.edit_message_text(
                    "✅ Tayyor bo'ldi", chat_id=chat_id, message_id=message_id
                )
            except TelegramBadRequest as exc:
                if "message is not modified" not in str(exc):
                    raise
            await send_result_summary(bot, chat_id, prompt, model_name)
            if outputs:
                await send_outputs(bot, chat_id, outputs)
            return
        if status == "failed":
            try:
                await bot.edit_message_text(
                    "❌ Generatsiya muvaffaqiyatsiz",
                    chat_id=chat_id,
                    message_id=message_id,
                )
            except TelegramBadRequest as exc:
                if "message is not modified" not in str(exc):
                    raise
            return


@router.callback_query(F.data == "gen:submit")
async def submit_generation(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    model_id = int(data.get("model_id", 0))
    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")
    references = list(data.get("reference_urls", []))
    reference_file_ids = list(data.get("reference_file_ids", []))

    if not prompt or not model_id:
        await call.message.answer("Prompt yoki model topilmadi.")
        return

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )
    if not show_size:
        size = None
    if not show_aspect:
        aspect_ratio = None
    if not show_resolution:
        resolution = None

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    try:
        await call.message.edit_text("⏳ Generatsiya qabul qilindi, ishlanmoqda...")
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise

    try:
        result = await client.submit_generation(
            telegram_id=call.from_user.id,
            model_id=model_id,
            prompt=prompt,
            size=size,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            reference_urls=references,
            reference_file_ids=reference_file_ids,
        )
    except ApiError as exc:
        if exc.status == 409:
            detail = exc.data.get("detail") if isinstance(exc.data, dict) else None
            active_id = None
            if isinstance(detail, dict):
                active_id = detail.get("active_request_id")
            suffix = f" (ID: {active_id})" if active_id else ""
            await call.message.edit_text(
                "Sizda boshqa generatsiya jarayoni ketmoqda. Iltimos, tugashini kuting."
                f"{suffix}"
            )
            return
        if exc.status == 402:
            await call.message.edit_text(
                "Sizda yetarli balans mavjud emas.", reply_markup=profile_menu()
            )
            return
        await call.message.edit_text(
            "Generatsiya boshlashda xatolik. Keyinroq urinib ko'ring."
        )
        return
    except Exception:
        await call.message.edit_text(
            "Generatsiya boshlashda xatolik. Keyinroq urinib ko'ring."
        )
        return

    request = result.get("request", {})
    request_id = request.get("id")
    public_id = request.get("public_id")
    request_status = request.get("status")
    trial_used = result.get("trial_used")

    note = "Trial ishlatildi" if trial_used else f"Narx: {price} cr"
    display_id = public_id or request_id
    text = f"Generatsiya boshlandi. ID: {display_id}\n{note}"
    try:
        await call.message.edit_text(text)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
    if not request_id:
        await call.message.answer("Job ID topilmadi. Keyinroq urinib ko'ring.")
        await state.clear()
        return
    if request_status == "completed":
        try:
            outputs = await client.get_generation_results(request_id, call.from_user.id)
        except Exception:
            outputs = []
        try:
            await call.message.edit_text("✅ Tayyor bo'ldi")
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc):
                raise
        await send_result_summary(call.message.bot, call.message.chat.id, prompt, model_name)
        if outputs:
            await send_outputs(call.message.bot, call.message.chat.id, outputs)
        await state.clear()
        return
    try:
        asyncio.create_task(
            poll_generation_status(
                call.message.bot,
                client,
                call.message.chat.id,
                call.message.message_id,
                request_id,
                call.from_user.id,
                prompt,
                model_name,
            )
        )
    except Exception:
        pass
    await state.clear()
