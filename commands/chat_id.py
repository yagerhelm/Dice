import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

async def chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_user_id = update.effective_user.id
    
    user_level = await get_user_level(sender_user_id)
    if user_level < 4:
        await update.message.reply_text("⛔️ У вас недостаточно прав для выполнения этой команды.")
        return

    chat_id = update.effective_chat.id

    adjusted_chat_id = chat_id * -1
    
    await update.message.reply_text(f"🎲 Идентификатор чата: {adjusted_chat_id}")

async def get_user_level(user_id: int):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
