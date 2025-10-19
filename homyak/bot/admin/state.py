from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from pathlib import Path
from ..database.admins import is_admin
from ..database.rarity import get_rarity, RARITY_NAMES, RARITY_POINTS
import os

router = Router()

class HomyakState(StatesGroup):
    waiting_for_name = State()
    renaming_homyak = State()
    viewing_homyak = State()
    changing_rarity = State()

HOMYAK_FILES_DIR = Path(__file__).parent.parent / "files"

@router.message(F.text == "/state")
async def cmd_state(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти", callback_data="state_find")]
    ])
    await message.answer("🛠️ <b>Управление хомяками</b>\nНажмите Найти, чтобы начать.", 
                        reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "state_find")
async def find_homyak(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("✏️ Введите название хомяка:")
    await state.set_state(HomyakState.waiting_for_name)
    await callback_query.answer()

@router.message(HomyakState.waiting_for_name)
async def process_homyak_name(message: Message, state: FSMContext, bot: Bot):
    query = message.text.strip()
    if query.startswith("/") or not query:
        await state.clear()
        await message.answer("❌ Отменено")
        return

    all_files = [
        f.name for f in HOMYAK_FILES_DIR.glob("*.png")
        if f.name.lower() != "welcome.mp4"
    ]

    matches = []
    query_lower = query.lower()
    for filename in all_files:
        name_without_ext = filename[:-4]
        if query_lower in name_without_ext.lower():
            matches.append(filename)

    attempts = await state.get_data()
    failed_attempts = attempts.get("failed_attempts", 0)

    if not matches:
        failed_attempts += 1
        await state.update_data(failed_attempts=failed_attempts)

        if failed_attempts >= 3:
            await state.clear()
            await message.answer("❌ Три неудачные попытки. Пожалуйста, начните поиск заново.")
            return

        await message.answer("❌ Хомяки не найдены. Попробуйте другое название.")
        return

    await state.update_data(failed_attempts=0)

    if len(matches) == 1:
        await show_homyak_details(message, matches[0], state)
    else:
        buttons = []
        for filename in matches[:10]:
            name = filename[:-4]
            buttons.append([InlineKeyboardButton(text=name, callback_data=f"state_select_{filename}")])
        
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="state_find")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("🔍 Найдено несколько хомяков:", reply_markup=keyboard)

async def show_homyak_details(message: Message, filename: str, state: FSMContext):
    file_path = HOMYAK_FILES_DIR / filename
    homyak_name = filename[:-4]

    rarity_id = await get_rarity(filename)
    points = RARITY_POINTS[rarity_id]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"state_delete_{filename}")],
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"state_rename_{filename}")],
        [InlineKeyboardButton(text="🌟 Изменить редкость", callback_data=f"state_change_rarity_{filename}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="state_find")]
    ])

    caption = (
        f"🪄 <b>{homyak_name}</b>\n\n"
        f"💎 Редкость: {RARITY_NAMES[rarity_id]}\n"
        f"✨ Очки: {points}\n"
    )

    await message.answer_photo(
        photo=FSInputFile(file_path),
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.update_data(current_filename=filename)
    await state.set_state(HomyakState.viewing_homyak)

@router.callback_query(F.data.startswith("state_delete_"))
async def delete_homyak(callback_query: CallbackQuery, state: FSMContext):
    try:
        import re
        match = re.search(r"state_delete_(.*)", callback_query.data)
        if match:
            filename = match.group(1)
        else:
            await callback_query.answer("Не удалось извлечь имя файла.")
            return

        file_path = Path(HOMYAK_FILES_DIR) / filename
        print(f"Путь к файлу для удаления: {file_path}")

        if file_path.exists():
            file_path.unlink()
            print(f"Файл {filename} удалён.")
        else:
            await callback_query.message.edit_caption(caption="❌ Файл уже удалён.")
            await state.clear()
            await callback_query.answer()
            return

        from ..database.rarity import remove_rarity
        await remove_rarity(filename)

        from ..database.cards import remove_homyak_from_all_users
        await remove_homyak_from_all_users(filename)

        await callback_query.message.edit_caption(caption="✅ Хомяк полностью удалён!")
    except Exception as e:
        await callback_query.message.edit_caption(caption=f"❌ Ошибка удаления: {e}")

    await state.clear()
    await callback_query.answer()

@router.callback_query(F.data.startswith("state_rename_"))
async def rename_homyak_start(callback_query: CallbackQuery, state: FSMContext):
    filename = callback_query.data[14:]
    await callback_query.message.answer("✏️ Введите новое название:")
    await state.update_data(rename_filename=filename)
    await state.set_state(HomyakState.renaming_homyak)
    await callback_query.answer()

@router.message(HomyakState.renaming_homyak)
async def rename_homyak_process(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if new_name.startswith("/") or not new_name:
        await state.clear()
        await message.answer("❌ Отменено")
        return

    data = await state.get_data()
    old_filename = data.get("rename_filename")
    if not old_filename:
        await state.clear()
        await message.answer("❌ Ошибка: файл не найден.")
        return

    new_filename = f"{new_name}.png"
    old_path = HOMYAK_FILES_DIR / old_filename
    new_path = HOMYAK_FILES_DIR / new_filename

    if new_path.exists():
        await message.answer("❌ Хомяк с таким названием уже существует.")
        return
 
    if not old_path.exists():
        await message.answer("❌ Оригинальный файл не найден.")
        return

    old_path.rename(new_path)

    from ..database.rarity import get_rarity, set_rarity
    rarity = await get_rarity(old_filename)
    await set_rarity(new_filename, rarity)

    from ..database.rarity import remove_rarity
    await remove_rarity(old_filename)

    from ..database.cards import rename_homyak_in_cards
    await rename_homyak_in_cards(old_filename, new_filename)

    await message.answer(f"✅ Название изменено на «{new_name}».")
    await state.clear()

@router.callback_query(F.data.startswith("state_change_rarity_"))
async def change_rarity_start(callback_query: CallbackQuery, state: FSMContext):
    filename = callback_query.data[22:]
    await state.update_data(change_rarity_filename=filename)
    
    rarity_buttons = [
        [InlineKeyboardButton(text="1 — Обычная", callback_data="rarity_1")],
        [InlineKeyboardButton(text="2 — Редкая", callback_data="rarity_2")],
        [InlineKeyboardButton(text="3 — Мифическая", callback_data="rarity_3")],
        [InlineKeyboardButton(text="4 — Легендарная", callback_data="rarity_4")],
        [InlineKeyboardButton(text="5 — Секретный", callback_data="rarity_5")],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="state_cancel_rarity")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=rarity_buttons)
    await callback_query.message.answer("Выберите новую редкость:", reply_markup=keyboard)
    await state.set_state(HomyakState.changing_rarity)
    await callback_query.answer()

@router.callback_query(F.data.startswith("rarity_"))
async def set_new_rarity(callback_query: CallbackQuery, state: FSMContext):
    try:
        rarity_str = callback_query.data[8:]
        if not rarity_str:
            raise ValueError("empty")
        
        rarity = int(rarity_str)
        if rarity not in [1, 2, 3, 4, 5]:
            raise ValueError("fuck rarity")
        
        data = await state.get_data()
        filename = data["change_rarity_filename"]
        
        from ..database.rarity import set_rarity
        await set_rarity(filename, rarity)
        
        rarity_names = {1: "Обычная", 2: "Редкая", 3: "Мифическая", 4: "Легендарная", 5: "Секретный"}
        await callback_query.message.edit_text(f"✅ Редкость изменена на «{rarity_names[rarity]}»!")
        await show_homyak_details(callback_query.message, filename, state)
        
    except Exception as e:
        await callback_query.message.edit_text(f"invalid type rarity")
    finally:
        await state.clear()

@router.callback_query(F.data == "state_cancel_rarity")
async def cancel_rarity_change(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filename = data.get("change_rarity_filename", "")
    if filename:
        await show_homyak_details(callback_query.message, filename, state)
    else:
        await callback_query.message.edit_text("❌ Отменено.")
    await state.clear()
    await callback_query.answer()