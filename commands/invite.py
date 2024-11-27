from telegram import Update
from telegram.ext import ContextTypes
from scripts.utils import get_user_profile, create_user
import aiosqlite

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.message.reply_text("❗️ Пожалуйста, укажите пользователя: /invite @user")
        return

    username = context.args[0]
    uid = update.message.from_user.id

    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT * FROM users WHERE uid = ?", (uid,)) as cursor:
            existing_user = await cursor.fetchone()
            if existing_user:
                await update.message.reply_text("⛔️ Вы уже создали профиль!")
                return

    await create_user(uid, username)
    await update.message.reply_text(f"✅ Профиль для {username} успешно создан.")
