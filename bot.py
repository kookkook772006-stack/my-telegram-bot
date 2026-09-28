import os
import json
from flask import Flask, request
import telebot

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP = "-1004332853451"  # معرف مجموعة الإدارة الخاصة بك
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

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

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Forwarding Bot to Admin Group is running smoothly!"

# 1. أمر البداية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if message.chat.type != "private":
        return
    user_states[chat_id] = {}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("➕ أود مشاركة ملف", callback_data="btn_share"),
        telebot.types.InlineKeyboardButton("📂 أود الحصول على ملفات", callback_data="btn_get")
    )
    bot.send_message(chat_id, "حياك الله في بوت خدمات الطلبة 📚\nيمكنك إرسال أي ملف لمشاركته مع الإدارة:", reply_markup=markup)

# 2. استقبال الملفات وتحويلها فوراً للمجموعة
@bot.message_handler(content_types=['document', 'audio', 'voice', 'photo', 'video'])
def handle_files(message):
    chat_id = message.chat.id
    if message.chat.type != "private":
        return
        
    user = message.from_user
    username = f"@{user.username}" if user.username else user.first_name
    
    # تحويل الملف رسيماً إلى مجموعة الإدارة مع أزرار الإشراف
    caption = (
        f"📥 **ملف جديد مُرسل للمراجعة:**\n"
        f"👤 الطالب: {username} (ID: `{chat_id}`)\n"
        f"📎 تم استلام الملف وبانتظار مراجعته ونشره."
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ قبول ونشر", callback_data=f"admin_accept_{chat_id}"),
        telebot.types.InlineKeyboardButton("❌ رفض وحذف", callback_data="admin_reject")
    )
    
    try:
        # إعادة توجيه الرسالة لمجموعة الإدارة
        bot.forward_message(chat_id=ADMIN_GROUP, from_chat_id=chat_id, message_id=message.message_id)
        # إرسال أزرار الإشراف تحت الرسالة في المجموعة
        bot.send_message(ADMIN_GROUP, caption, reply_markup=markup, parse_mode="Markdown")
        
        # إشعار الطالب بأن ملفه وصل للإدارة
        bot.send_message(chat_id, "✅ **تم استلام ملفك وتحويله إلى مجموعة الإدارة بنجاح!**\nسيتم مراجعته ونشره قريباً.", reply_markup={
            "inline_keyboard": [
                [{"text": "➕ إرسال ملف آخر", "callback_data": "btn_share"}],
                [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}]
            ]
        })
    except Exception as e:
        print(f"Error forwarding message: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ أثناء إرسال الملف للإدارة. يجيب التأكد من أن البوت مشرف في مجموعة الإدارة.")

# 3. معالجة الأزرار التفاعلية
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "btn_share":
        bot.send_message(chat_id, "📥 **أرسل الآن الملف** في المحادثة هنا، وسيقوم البوت بتحويله للمجموعة تلقائياً:")
        
    elif data == "btn_get":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📚 السنة الأولى ليسونس", callback_data="get_s1"),
            telebot.types.InlineKeyboardButton("📖 السنة الثانية ليسونس", callback_data="get_s2"),
            telebot.types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, "اختر السنة الدراسية للتصفح من القناة الرسمية:", reply_markup=markup)
        
    elif data in ["get_s1", "get_s2"]:
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for subj in SUBJECTS:
            markup.add(telebot.types.InlineKeyboardButton(f"📁 {subj}", callback_data=f"browse_{subj}"))
        markup.add(telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, "اختر المقياس:", reply_markup=markup)
        
    elif data.startswith("browse_"):
        subj_name = data.replace("browse_", "")
        bot.send_message(chat_id, f"📂 يتم الآن مراجعة ملفات مقياس ({subj_name}) ونشرها في القناة المخصصة.")
        
    elif data.startswith("admin_accept_"):
        bot.answer_callback_query(call.id, "تم قبول ونشر الملف بنجاح ✅")
        bot.send_message(chat_id, "✅ **تم قبول هذا الملف ونشره.**")
        
    elif data == "admin_reject":
        bot.answer_callback_query(call.id, "تم رفض الملف ❌")
        bot.send_message(chat_id, "❌ **تم رفض وحذف هذا الملف.**")
        
    elif data == "main_menu":
        user_states[chat_id] = {}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ أود مشاركة ملف", callback_data="btn_share"),
            telebot.types.InlineKeyboardButton("📂 أود الحصول على ملفات", callback_data="btn_get")
        )
        bot.send_message(chat_id, "أهلاً بك في القائمة الرئيسية:", reply_markup=markup)

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
