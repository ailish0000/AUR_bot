from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentTypes

from bot import dp, bot, user_started, ADMIN_ID
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Состояния ---
class BroadcastStates(StatesGroup):
    waiting_for_content = State()  # Поддержка текста, фото, видео и т.д.

class ReplyStates(StatesGroup):
    waiting_for_message = State()


# --- Проверка администратора ---
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# --- Уведомление админу о новом пользователе ---
async def notify_admin_new_user(user: types.User):
    try:
        username = f"@{user.username}" if user.username else user.full_name
        await bot.send_message(
            ADMIN_ID,
            f"✅ Новый пользователь: {username} (ID: {user.id})\n"
            f"Имя: {user.full_name}\n"
            f"Запустил бота: /start"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")


# --- Команда /admin — панель управления ---
@dp.message_handler(commands=['admin'])
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📤 Создать рассылку", callback_data="admin_broadcast"),
        InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users"),
        InlineKeyboardButton("ℹ️ Инфо", callback_data="admin_info")
    )
    await message.answer("🔐 <b>Админ-панель</b>", reply_markup=markup, parse_mode="HTML")


# --- Обработка кнопок админ-панели ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_") and c.message.chat.id == ADMIN_ID)
async def process_admin_panel(callback_query: types.CallbackQuery):
    action = callback_query.data

    if action == "admin_stats":
        count = len(user_started)
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"📊 <b>Статистика</b>\n\n"
                 f"👥 Всего пользователей: <b>{count}</b>\n"
                 f"🕒 Онлайн: <b>{count}</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
            )
        )

    elif action == "admin_broadcast":
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="✉️ Введите сообщение для рассылки.\n"
                 "Можно отправить текст, фото, видео, файл или голосовое.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("◀️ Отмена", callback_data="admin_back")
            )
        )
        await BroadcastStates.waiting_for_content.set()

    elif action == "admin_users":
        if not user_started:
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text="👥 Нет активных пользователей.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
                )
            )
            return

        markup = InlineKeyboardMarkup(row_width=1)
        for uid in user_started:
            user_info = f"Пользователь {uid}"
            markup.add(InlineKeyboardButton(user_info, callback_data=f"reply_{uid}"))
        markup.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))

        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Выберите пользователя для ответа:",
            reply_markup=markup
        )

    elif action == "admin_info":
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="ℹ️ <b>Админ-панель</b>\n\n"
                 "Доступные функции:\n"
                 "• Рассылка всем пользователям\n"
                 "• Ответ пользователю\n"
                 "• Просмотр статистики\n\n"
                 "Разработано для поддержки бота Аврора.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
            )
        )

    elif action == "admin_back":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton("📤 Создать рассылку", callback_data="admin_broadcast"),
            InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users"),
            InlineKeyboardButton("ℹ️ Инфо", callback_data="admin_info")
        )
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="🔐 <b>Админ-панель</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )

    await bot.answer_callback_query(callback_query.id)


# --- Рассылка: ожидание контента (текст, фото и т.д.) ---
@dp.message_handler(state=BroadcastStates.waiting_for_content, content_types=ContentTypes.ANY)
async def process_broadcast_content(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.finish()
        return

    # Сохраняем тип и содержимое
    await state.update_data(broadcast_message=message)
    user_count = len(user_started)

    confirm_markup = InlineKeyboardMarkup(row_width=2)
    confirm_markup.add(
        InlineKeyboardButton("✅ Да, отправить", callback_data="confirm_broadcast"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")
    )

    await message.reply(
        f"📬 Вы собираетесь отправить это сообщение {user_count} пользователям.\n\n"
        "Подтвердите отправку:",
        reply_markup=confirm_markup
    )
    await state.set_state(BroadcastStates.waiting_for_content)


# --- Подтверждение рассылки ---
@dp.callback_query_handler(lambda c: c.data in ["confirm_broadcast", "cancel_broadcast"], state=BroadcastStates.waiting_for_content)
async def confirm_broadcast(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "cancel_broadcast":
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="❌ Рассылка отменена."
        )
        await state.finish()
        return

    data = await state.get_data()
    msg: types.Message = data.get("broadcast_message")
    sent_count = 0
    failed_count = 0

    progress_msg = await bot.send_message(ADMIN_ID, "📤 Рассылка начата... (0 из 10)")

    for i, user_id in enumerate(user_started):
        if i % 10 == 0:
            await progress_msg.edit_text(f"📤 Рассылка... ({i} из {len(user_started)})")

        try:
            # Копируем сообщение с сохранением форматирования
            await msg.send_copy(chat_id=user_id)
            sent_count += 1
        except Exception as e:
            logger.error(f"Ошибка при отправке пользователю {user_id}: {e}")
            failed_count += 1

    await progress_msg.edit_text(
        f"✅ Рассылка завершена!\n"
        f"📬 Отправлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}"
    )
    await state.finish()


# --- Обработка "Ответить" (из /users или из сообщения) ---
@dp.callback_query_handler(lambda c: c.data.startswith("reply_"), user_id=ADMIN_ID)
async def enter_reply_mode(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split("_")[-1])
    if user_id not in user_started:
        await bot.answer_callback_query(callback_query.id, "❌ Пользователь не найден.", show_alert=True)
        return

    await state.update_data(reply_user_id=user_id)
    await ReplyStates.waiting_for_message.set()

    await bot.send_message(
        ADMIN_ID,
        f"✉️ Введите сообщение для пользователя {user_id}.\n"
        "Можно отправить текст, фото, видео и т.д."
    )
    await bot.answer_callback_query(callback_query.id)


# --- Отправка ответа пользователю ---
@dp.message_handler(state=ReplyStates.waiting_for_message, content_types=ContentTypes.ANY)
async def process_reply_message(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.finish()
        return

    data = await state.get_data()
    user_id = data.get('reply_user_id')

    if not user_id:
        await message.reply("⚠️ Не указан получатель.")
        await state.finish()
        return

    try:
        # Копируем любое сообщение от админа
        await message.send_copy(chat_id=user_id)
        await message.reply(f"✅ Сообщение отправлено пользователю {user_id}.")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа пользователю {user_id}: {e}")
        await message.reply(f"❌ Не удалось отправить сообщение: {str(e)}")

    await state.finish()


# --- Экспорт функции уведомления ---
__all__ = ["notify_admin_new_user"]