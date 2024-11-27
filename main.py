import tracemalloc

tracemalloc.start()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from my_token import TOKEN

from commands.profile import profile
from commands.activate import activate
from commands.deactivate import deactivate
from commands.chat_id import chat_id
from commands.show_logs import logs
from commands.show_active_chats import show_active_chats
from commands.invite import invite
from commands.dice_game import setup_handlers as setup_dice_handlers

from scripts.logger import log_command
from scripts.active_check import is_bot_active

def command_wrapper(command_func):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)

        if not await is_bot_active(chat_id):
            await update.message.reply_text("❗️ Бот не активирован в этом чате.")
            return

        message = update.message.text.strip()
        command, *args = message.split()
        command_text = f"{command} {' '.join(args)}"
        await command_func(update, context)
        await log_command(update, command_text)
    return wrapped

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("profile", command_wrapper(profile)))
    app.add_handler(CommandHandler("id", command_wrapper(chat_id)))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", command_wrapper(deactivate)))
    app.add_handler(CommandHandler("active", command_wrapper(show_active_chats)))
    app.add_handler(CommandHandler("logs", command_wrapper(logs)))
    app.add_handler(CommandHandler("invite", command_wrapper(invite)))
    setup_dice_handlers(app)

    app.run_polling()