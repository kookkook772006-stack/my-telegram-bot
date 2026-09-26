import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

# قراءة التوكن من المتغيرات البيئية في Render
TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"مرحباً بك {html.bold(message.from_user.full_name)}! البوت يعمل الآن بنجاح من الاستضافة السحابية.")

async def main() -> None:
    if not TOKEN:
        logging.error("لم يتم العثور على توكن البوت!")
        return
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

