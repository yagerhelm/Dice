from telegram import Update
from telegram.ext import ContextTypes
from scripts.utils import get_user_profile, get_user_by_uid

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if context.args:
        user_name = context.args[0]
        
        mentioned_user = update.message.entities[0] if update.message.entities else None
        if mentioned_user and mentioned_user.type == 'mention':
            user_name = update.message.text[mentioned_user.offset:mentioned_user.offset + mentioned_user.length]
            user_name = user_name.replace('@', '')
        
        user_data = await get_user_profile(user_name)

        if user_data:
            uid, name, level, score = user_data

            user_info = (
                f" <b>Профиль пользователя</b> \n\n"
                f" <b>Имя:</b> <code>{name}</code>\n"
                f" <b>Уровень доступа:</b> <code>{level}</code>\n"
                f" <b>Score:</b> <code>{score}</code>\n"
            )

            await update.message.reply_text(user_info, parse_mode='HTML')
        else:
            await update.message.reply_text("❗️ Профиль не найден.")
    else:
        user_data = await get_user_by_uid(user_id)

        if user_data:
            uid, name, level, score = user_data

            user_info = (
                f" <b>Ваш профиль</b> \n\n"
                f" <b>Имя:</b> <code>{name}</code>\n"
                f" <b>Уровень доступа:</b> <code>{level}</code>\n"
                f" <b>Score:</b> <code>{score}</code>\n"
            )

            await update.message.reply_text(user_info, parse_mode='HTML')
        else:
            await update.message.reply_text("❗️ Ваш профиль не найден.")
