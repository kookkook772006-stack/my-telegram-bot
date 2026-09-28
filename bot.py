import os
import json
from flask import Flask, request
import telebot

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP = "-1004332853451"  # مجموعة الإدارة
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
    return "Smart Classification Bot is running smoothly!"

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
    bot.send_message(chat_id, "حياك الله في بوت خدمات الطلبة 📚\nاختر ما تحتاجه:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "btn_share":
        user_states[chat_id] = {"step": "choose_year"}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📚 السنة الأولى ليسونس", callback_data="cls_year_السنة الأولى"),
            telebot.types.InlineKeyboardButton("📖 السنة الثانية ليسونس", callback_data="cls_year_السنة الثانية"),
            telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data="main_menu")
        )
        bot.send_message(chat_id, "📌 **خطوة 1 من 4:** حدد السنة الدراسية للملف الذي تريد مشاركته:", reply_markup=markup)
        
    elif data.startswith("cls_year_"):
        chosen_year = data.replace("cls_year_", "")
        user_states[chat_id] = user_states.get(chat_id, {})
        user_states[chat_id]["temp_year"] = chosen_year
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(" السداسي الأول", callback_data="cls_sem_الأول"),
            telebot.types.InlineKeyboardButton(" السداسي الثاني", callback_data="cls_sem_الثاني")
        )
        bot.send_message(chat_id, "📌 **خطوة 2 من 4:** اختر السداسي:", reply_markup=markup)
        
    elif data.startswith("cls_sem_"):
        chosen_sem = data.replace("cls_sem_", "")
        user_states[chat_id]["temp_sem"] = chosen_sem
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for f_type in FILE_TYPES:
            markup.add(telebot.types.InlineKeyboardButton(f_type, callback_data=f"cls_type_{f_type}"))
        bot.send_message(chat_id, "📌 **خطوة 3 من 4:** اختر نوع الملف:", reply_markup=markup)
        
    elif data.startswith("cls_type_"):
        chosen_type = data.replace("cls_type_", "")
        user_states[chat_id]["temp_type"] = chosen_type
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for subj in SUBJECTS:
            markup.add(telebot.types.InlineKeyboardButton(subj, callback_data=f"cls_subj_{subj}"))
        bot.send_message(chat_id, "📌 **خطوة 4 من 4:** اختر المقياس النهائي للملف:", reply_markup=markup)
        
    elif data.startswith("cls_subj_"):
        chosen_subj = data.replace("cls_subj_", "")
        user_states[chat_id]["temp_subj"] = chosen_subj
        user_states[chat_id]["step"] = "waiting_for_file"
        
        bot.send_message(chat_id, f"✅ **تم ضبط التصنيف بنجاح:**\n📚 المقياس: {chosen_subj}\n\n📥 **الآن أرسل الملف المطلوب (مستند، صوت، فيديو، صورة...) في المحادثة هنا، وسيتم رفعه فوراً للإدارة مع تصنيفه!**")
        
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
        bot.send_message(chat_id, "اختر المقياس:", reply_markup=markup)
        
    elif data.startswith("browse_"):
        subj_name = data.replace("browse_", "")
        bot.send_message(chat_id, f"📂 يتم تصفح ملفات مقياس ({subj_name}).")
        
    elif data.startswith("admin_accept_"):
        bot.answer_callback_query(call.id, "تم قبول ونشر الملف بنجاح ✅")
        bot.send_message(chat_id, "✅ **تم قبول هذا الملف ونشره بنجاح.**")
        
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

# استقبال الملفات بعد تحديد التصنيف
@bot.message_handler(content_types=['document', 'audio', 'voice', 'photo', 'video'])
def handle_files(message):
    chat_id = message.chat.id
    if message.chat.type != "private":
        return
        
    state = user_states.get(chat_id, {})
    
    # إذا أرسل الطالب الملف مباشرة دون اختيار التصنيف أولاً
    if state.get("step") != "waiting_for_file":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("➕ اضغط هنا لبدء تصنيف الملف", callback_data="btn_share"))
        bot.send_message(chat_id, "⚠️ **عذراً، يرجى اختيار (أود مشاركة ملف) وتحديد التصنيف والسنة أولاً قبل إرسال الملف، لكي يتم ربطه بشكل صحيح!**", reply_markup=markup)
        return
        
    user = message.from_user
    username = f"@{user.username}" if user.username else user.first_name
    
    year = state.get("temp_year", "غير محدد")
    sem = state.get("temp_sem", "غير محدد")
    f_type = state.get("temp_type", "ملف")
    subj = state.get("temp_subj", "غير محدد")
    
    caption = (
        f"📥 **طلب مشاركة جديد للمراجعة:**\n\n"
        f"📚 المقياس: {subj}\n"
        f"🎓 السنة: {year} - السداسي {sem}\n"
        f"🏷️ النوع: {f_type}\n"
        f"👤 الطالب: {username} (ID: `{chat_id}`)"
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ قبول ونشر", callback_data=f"admin_accept_{chat_id}"),
        telebot.types.InlineKeyboardButton("❌ رفض وحذف", callback_data="admin_reject")
    )
    
    try:
        bot.forward_message(chat_id=ADMIN_GROUP, from_chat_id=chat_id, message_id=message.message_id)
        bot.send_message(ADMIN_GROUP, caption, reply_markup=markup, parse_mode="Markdown")
        
        bot.send_message(chat_id, f"✅ **تم إرسال الملف وتصنيفه تحت مقياس ({subj}) إلى مجموعة الإدارة بنجاح!**\nسيتم مراجعته ونشره قريباً.", reply_markup={
            "inline_keyboard": [
                [{"text": "➕ إرسال ملف آخر", "callback_data": "btn_share"}],
                [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}]
            ]
        })
        user_states[chat_id] = {}
    except Exception as e:
        print(f"Error forwarding: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ أثناء إرسال الملف للإدارة. تأكد أن البوت مشرف في مجموعة الإدارة.")

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
