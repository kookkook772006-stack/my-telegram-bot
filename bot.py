import os
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State,StatesGroup
from aiogram.fsm.context import FSMContext

# إعداد خادم الويب الوهمي لتلبية شروط منصة Render وإبقاء البوت قيد التشغيل
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# تشغيل خادم الويب في خلفية النظام
web_thread = threading.Thread(target=run_web_server)
web_thread.daemon = True
web_thread.start()

# إعدادات البوت
TOKEN = os.getenv("BOT_TOKEN", "8602792772:AAEg8qIlzMd1kBuuTjlPdmvdaV3AlBmjVa4")
LOG_GROUP_ID = -1004448279953

bot = Bot(token=TOKEN)
dp = Dispatcher()

class SubmissionForm(StatesGroup):
    waiting_for_module = State()
    waiting_for_professor = State()
    waiting_for_doc_type = State()
    waiting_for_file = State()

def get_restart_keyboard():
    button = InlineKeyboardButton(text="🔄 إرسال مشاركة أخرى", callback_data="restart_submission")
    return InlineKeyboardMarkup(inline_keyboard=[[button]])

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    welcome_text = (
        "حياك الله يا أخي الكريم!\n\n"
        "مرحباً بك في بوت استقبال المشاركات والملفات الدراسية.\n"
        "للبدء في إرسال مشاركتك، يرجى كتابة **اسم المقياس (المادة)** أولاً:"
    )
    await message.answer(welcome_text)
    await state.set_state(SubmissionForm.waiting_for_module)

@dp.callback_query(F.data == "restart_submission")
async def restart_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🔄 حسناً، نبدأ مشاركة جديدة.\n\nيرجى كتابة **اسم المقياس (المادة)** أولاً:")
    await state.set_state(SubmissionForm.waiting_for_module)
    await callback.answer()

@dp.message(SubmissionForm.waiting_for_module)
async def process_module(message: Message, state: FSMContext):
    await state.update_data(module=message.text)
    await message.answer("تمام. الآن، من هو **أستاذ المقياس**؟")
    await state.set_state(SubmissionForm.waiting_for_professor)

@dp.message(SubmissionForm.waiting_for_professor)
async def process_professor(message: Message, state: FSMContext):
    await state.update_data(professor=message.text)
    await message.answer("ممتاز. ما هو **نوع المطبوعة أو المحاضرة**؟ (مثلاً: محاضرة رقم 1، ملخص، تمرين...)")
    await state.set_state(SubmissionForm.waiting_for_doc_type)

@dp.message(SubmissionForm.waiting_for_doc_type)
async def process_doc_type(message: Message, state: FSMContext):
    await state.update_data(doc_type=message.text)
    await message.answer("بارك الله فيك. الآن **أرسل الملف أو المستند أو الصور أو التسجيل الصوتي** الخاص بمشاركتك:")
    await state.set_state(SubmissionForm.waiting_for_file)

@dp.message(SubmissionForm.waiting_for_file, F.chat.type == "private")
async def process_file_and_finish(message: Message, state: FSMContext):
    user_data = await state.get_data()
    module = user_data.get("module")
    professor = user_data.get("professor")
    doc_type = user_data.get("doc_type")

    student_name = message.from_user.full_name
    student_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"

    # صياغة الرسالة التي ستصل إلى مجموعة الإدارة أو المشرفين
    caption = (
        "📥 **مشاركة جديدة من طالب:**\n\n"
        f"📚 **المقياس:** {module}\n"
        f"👨‍🏫 **الأستاذ:** {professor}\n"
        f"📄 **نوع المطبوعة:** {doc_type}\n\n"
        f"👤 **الطالب:** {student_name}\n"
        f"🆔 **المعرف:** `{student_id}` ({username})"
    )

    try:
        # إعادة توجيه الملف أو الرسالة إلى مجموعة الإدارة
        if LOG_GROUP_ID:
            await message.forward(chat_id=LOG_GROUP_ID)
            await bot.send_message(chat_id=LOG_GROUP_ID, text=caption, parse_mode="Markdown")

        # إعلام الطالب بنجاح الإرسال
        await message.answer(
            "✅ جزاك الله خيراً! تم إرسال مشاركتك إلى الإدارة بنجاح.",
            reply_markup=get_restart_keyboard()
        )
    except Exception as e:
        logging.error(f"Error forwarding message: {e}")
        await message.answer("⚠️ حدث خطأ أثناء إرسال المشاركة، يرجى المحاولة لاحقاً.")
    
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    print("✨ Bot is starting with aiogram...")
    # حذف أي Webhook قديم والبدء في استقبال التحديثات عبر Polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
