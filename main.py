from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN
from bot.handlers import register_handlers

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
register_handlers(dp)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)