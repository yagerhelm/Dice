from telegram import Update
from telegram.ext import ContextTypes
import aiosqlite

async def get_user_level(user_id):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    return result[0] if result else None

async def show_active_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_level = await get_user_level(user_id)

    if user_level is None:
        await update.message.reply_text("⛔️ У вас нет доступа к этой команде.")
        return
    elif user_level < 5:
        await update.message.reply_text("⛔️ У вас недостаточно прав для выполнения этой команды.")
        return

    try:
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute("SELECT chat_id, chat_title FROM active_chats") as cursor:
                chat_entries = await cursor.fetchall()
        if chat_entries:
            response = "🗣 Список активных бесед:\n\n"
            for chat_id, chat_title in chat_entries:
                response += f"ID: {chat_id}, Название: {chat_title}\n"
                
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("📭 Нет активных бесед.")
    
    except Exception as e:
        await update.message.reply_text(f"⛔️ Произошла ошибка: {e}")
