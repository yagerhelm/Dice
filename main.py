import asyncio
import tracemalloc
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from my_token import TOKEN
from scripts.database import check_database

from commands.profile import router as profile_router
from commands.activate import router as activate_router
from commands.deactivate import router as deactivate_router
from commands.chat_id import router as chat_id_router
from commands.show_logs import router as logs_router
from commands.show_active_chats import router as active_chats_router
from commands.invite import router as invite_router
from commands.dice_game import router as dice_router

async def main():
    # Check and initialize database if needed
    await check_database()
    
    # Initialize Bot instance with a default parse mode using DefaultBotProperties
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # Create Dispatcher instance
    dp = Dispatcher()

    # Include routers
    dp.include_router(profile_router)
    dp.include_router(activate_router)
    dp.include_router(deactivate_router)
    dp.include_router(chat_id_router)
    dp.include_router(logs_router)
    dp.include_router(active_chats_router)
    dp.include_router(invite_router)
    dp.include_router(dice_router)

    # Start bot
    await dp.start_polling(bot)

if __name__ == '__main__':
    tracemalloc.start()
    asyncio.run(main())