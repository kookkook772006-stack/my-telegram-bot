import os
import json
from flask import Flask, request
import telebot

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

DB_FILE = "database.json"

# دوال إدارة قاعدة البيانات المحلية الدائمة
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

SUBJECTS = [
    "علوم القرآن", "مدخل لأصول الفقه", "العقيدة الإسلامية",
    "فقه عبادات", "أصول الفقه", "تاريخ إسلامي: السير",
    "منهج البحث", "مدخل لعلوم التربية", "تاريخ الجزائر",
    "لغة عربية", "ترتيل", "إنجليزية"
]

FILE_TYPES = [
    "🎧 محاضرة صوتية", "📝 محاضرة مكتوبة", "📁 ملخص محاضرة",
    "📑 مطبوعة", "📚 كتاب", "✍️ تمارين", "📋 مواضيع امتحانات"
]

user_states = {}

# نقطة استقبال التحديثات من تيليجرام (Webhook)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Webhook Bot is running smoothly!"

# 1. أمر البداية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_states[chat_id] = {}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("➕ أود مشاركة ملف", callback_data="btn_share"),
        telebot.types.InlineKeyboardButton("📂 أود الحصول على ملفات", callback_data="btn_get")
    )
    bot.send_message(chat_id, "حياك الله في بوت خدمات الطلبة 📚\nاختر ما تحتاجه:", reply_markup=markup)

# 2. استقبال الملفات التقاطاً فورياً
@bot.message_handler(content_types=['document', 'audio', 'voice', 'photo'])
def handle_files(message):
    chat_id = message.chat.id
    if message.chat.type != "private":
        return
        
    media_type = None
    file_id = None
    if message.document:
        media_type = "document"
        file_id = message.document.file_id
    elif message.audio:
        media_type = "audio"
        file_id = message.audio.file_id
    elif message.voice:
        media_type = "voice"
        file_id = message.voice.file_id
    elif message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
        
    if file_id:
        user_states[chat_id] = {
            "file_id": file_id,
            "media_type": media_type,
            "username": message.from_user.first_name
        }
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for f_type in FILE_TYPES:
            markup.add(telebot.types.InlineKeyboardButton(f_type, callback_data=f"autosave_type_{f_type}"))
            
        bot.send_message(chat_id, "📥 **تم التقاط الملف بنجاح!**\nما هو نوع هذا الملف؟", reply_markup=markup)

# 3. معالجة الأزرار التفاعلية
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "btn_share":
        bot.send_message(chat_id, "📥 **أرسل الآن الملف** في المحادثة هنا، وسيلتقطه البوت تلقائياً لربطه بالقسم.")
        
    elif data == "btn_get":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📚 السنة الأولى ليسونس", callback_data="get_s1"),
            telebot.types.InlineKeyboardButton("📖 السنة الثانية ليسونس", callback_data="get_s2"),
            telebot.types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, "اختر السنة الدراسية للتصفح:", reply_markup=markup)
        
    elif data in ["get_s1", "get_s2"]:
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for subj in SUBJECTS:
            markup.add(telebot.types.InlineKeyboardButton(f"📁 {subj}", callback_data=f"browse_{subj}"))
        markup.add(telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, "اختر المقياس لعرض ملفاته:", reply_markup=markup)
        
    elif data.startswith("browse_"):
        subj_name = data.replace("browse_", "")
        db = load_db()
        matched_files = [f for f in db if f["subject"] == subj_name]
        
        if matched_files:
            bot.send_message(chat_id, f"📂 **إليك الملفات المتاحة لمقياس ({subj_name}):**")
            for item in matched_files:
                caption = f"📚 المقياس: {subj_name}\n🏷️ النوع: {item['type']}"
                if item["media_type"] == "document":
                    bot.send_document(chat_id, item["file_id"], caption=caption)
                elif item["media_type"] == "audio":
                    bot.send_audio(chat_id, item["file_id"], caption=caption)
                elif item["media_type"] == "voice":
                    bot.send_voice(chat_id, item["file_id"], caption=caption)
                elif item["media_type"] == "photo":
                    bot.send_photo(chat_id, item["file_id"], caption=caption)
        else:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
            bot.send_message(chat_id, f"⚠️ **لا توجد ملفات مرفوعة حالياً لمقياس ({subj_name}).**", reply_markup=markup)
            
    elif data.startswith("autosave_type_"):
        chosen_type = data.replace("autosave_type_", "")
        if chat_id not in user_states:
            user_states[chat_id] = {}
        user_states[chat_id]["temp_type"] = chosen_type
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for subj in SUBJECTS:
            markup.add(telebot.types.InlineKeyboardButton(subj, callback_data=f"autosave_subj_{subj}"))
        bot.send_message(chat_id, "اختر المقياس أو القسم لربط هذا الملف به:", reply_markup=markup)
        
    elif data.startswith("autosave_subj_"):
        subject_name = data.replace("autosave_subj_", "")
        state = user_states.get(chat_id, {})
        
        if "file_id" in state:
            db = load_db()
            db.append({
                "subject": subject_name,
                "file_id": state["file_id"],
                "media_type": state["media_type"],
                "type": state.get("temp_type", "ملف عام"),
                "sender": state.get("username", "مجهول")
            })
            save_db(db)
            
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ إرسال ملف آخر", callback_data="btn_share"),
            telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, f"✅ **تم تخزين الملف بنجاح تحت مقياس ({subject_name})!**\nأصبح متاحاً للطلاب فوراً.", reply_markup=markup)
        user_states[chat_id] = {}
        
    elif data == "main_menu":
        user_states[chat_id] = {}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ أود مشاركة ملف", callback_data="btn_share"),
            telebot.types.InlineKeyboardButton("📂 أود الحصول على ملفات", callback_data="btn_get")
        )
        bot.send_message(chat_id, "أهلاً بك في القائمة الرئيسية:", reply_markup=markup)

if __name__ == "__main__":
    # ضبط الـ Webhook تلقائياً عند تشغيل السيرفر
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") # رابط استضافتك على رندر مثلاً
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
