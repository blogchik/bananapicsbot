from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def home_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Profile", callback_data="menu:profile")],
        ]
    )


def profile_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Balans to'ldirish", callback_data="menu:topup")],
            [InlineKeyboardButton(text="🤝 Referral", callback_data="menu:referral")],
            [InlineKeyboardButton(text="🏠 Home", callback_data="menu:home")],
        ]
    )


def topup_menu(presets: list[tuple[int, int]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(presets), 2):
        row = []
        for amount, credits in presets[i : i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=f"{amount} ⭐ → {credits} cr",
                    callback_data=f"topup:stars:{amount}",
                )
            )
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="✍️ Boshqa summa", callback_data="topup:custom")]
    )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:profile")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def referral_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:profile")],
        ]
    )


def generation_menu(
    model_name: str,
    size: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
    price: int,
    show_size: bool,
    show_aspect_ratio: bool,
    show_resolution: bool,
) -> InlineKeyboardMarkup:
    size_label = size if size else "Default"
    aspect_label = aspect_ratio if aspect_ratio else "Default"
    resolution_label = resolution if resolution else "Default"
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"🧠 Model: {model_name}",
                callback_data="gen:model:menu",
            )
        ]
    ]
    if show_size:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📐 Size: {size_label}",
                    callback_data="gen:size:menu",
                )
            ]
        )
    if show_aspect_ratio:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📏 Aspect ratio: {aspect_label}",
                    callback_data="gen:ratio:menu",
                )
            ]
        )
    if show_resolution:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🖼️ Resolution: {resolution_label}",
                    callback_data="gen:resolution:menu",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"🚀 Generatsiyani boshlash ({price} cr)",
                callback_data="gen:submit",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def model_menu(models: list[dict], selected_id: int | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for model in models:
        model_id = int(model["id"])
        name = str(model["name"])
        label = f"✅ {name}" if selected_id == model_id else name
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"gen:model:set:{model_id}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="gen:back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def size_menu(
    sizes: list[str],
    selected_size: str | None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    default_label = "✅ Default" if not selected_size else "Default"
    rows.append(
        [InlineKeyboardButton(text=default_label, callback_data="gen:size:set:default")]
    )
    for i in range(0, len(sizes), 2):
        row = []
        for size in sizes[i : i + 2]:
            label = f"✅ {size}" if size == selected_size else size
            row.append(
                InlineKeyboardButton(text=label, callback_data=f"gen:size:set:{size}")
            )
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="gen:back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def aspect_ratio_menu(
    ratios: list[str],
    selected_ratio: str | None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    default_label = "✅ Default" if not selected_ratio else "Default"
    rows.append(
        [
            InlineKeyboardButton(
                text=default_label,
                callback_data="gen:ratio:set:default",
            )
        ]
    )
    for i in range(0, len(ratios), 2):
        row = []
        for ratio in ratios[i : i + 2]:
            label = f"✅ {ratio}" if ratio == selected_ratio else ratio
            row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"gen:ratio:set:{ratio}",
                )
            )
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="gen:back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def resolution_menu(
    resolutions: list[str],
    selected_resolution: str | None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    default_label = "✅ Default" if not selected_resolution else "Default"
    rows.append(
        [
            InlineKeyboardButton(
                text=default_label,
                callback_data="gen:resolution:set:default",
            )
        ]
    )
    for i in range(0, len(resolutions), 2):
        row = []
        for resolution in resolutions[i : i + 2]:
            label = (
                f"✅ {resolution}"
                if resolution == selected_resolution
                else resolution
            )
            row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"gen:resolution:set:{resolution}",
                )
            )
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="gen:back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
