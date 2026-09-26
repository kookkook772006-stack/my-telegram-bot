import logging
import os
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("مرحباً بك! البوت يعمل الآن بنجاح على الاستضافة السحابية.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
