import os
import json
from flask import Flask, request
import telebot

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP = "-1004332853451"  # مجموعة الإدارة
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

DB_FILE = "database.json"

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

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Advanced Bot is running perfectly!"

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
            telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, "📌 **خطوة 1 من 4:** حدد السنة الدراسية للملف الذي تريد مشاركته:", reply_markup=markup)
        
    elif data.startswith("cls_year_"):
        chosen_year = data.replace("cls_year_", "")
        user_states[chat_id] = user_states.get(chat_id, {})
        user_states[chat_id]["temp_year"] = chosen_year
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(" السداسي الأول", callback_data="cls_sem_الأول"),
            telebot.types.InlineKeyboardButton(" السداسي الثاني", callback_data="cls_sem_الثاني"),
            telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, "📌 **خطوة 2 من 4:** اختر السداسي:", reply_markup=markup)
        
    elif data.startswith("cls_sem_"):
        chosen_sem = data.replace("cls_sem_", "")
        user_states[chat_id]["temp_sem"] = chosen_sem
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for f_type in FILE_TYPES:
            markup.add(telebot.types.InlineKeyboardButton(f_type, callback_data=f"cls_type_{f_type}"))
        markup.add(telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, "📌 **خطوة 3 من 4:** اختر نوع الملف:", reply_markup=markup)
        
    elif data.startswith("cls_type_"):
        chosen_type = data.replace("cls_type_", "")
        user_states[chat_id]["temp_type"] = chosen_type
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for subj in SUBJECTS:
            markup.add(telebot.types.InlineKeyboardButton(subj, callback_data=f"cls_subj_{subj}"))
        markup.add(telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, "📌 **خطوة 4 من 4:** اختر المقياس النهائي للملف:", reply_markup=markup)
        
    elif data.startswith("cls_subj_"):
        chosen_subj = data.replace("cls_subj_", "")
        user_states[chat_id]["temp_subj"] = chosen_subj
        user_states[chat_id]["step"] = "waiting_for_file"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, f"✅ **تم ضبط التصنيف بنجاح:**\n📚 المقياس: {chosen_subj}\n\n📥 **الآن أرسل ملفاتك تباعاً (مستند، صوت، فيديو...) وسيتم إرسالها للإدارة بنفس التصنيف. عندما تنتهي اضغط (تم، إنهاء)!**", reply_markup=markup)
        
    elif data == "more_files":
        user_states[chat_id]["step"] = "waiting_for_file"
        subj = user_states[chat_id].get("temp_subj", "المقياس")
        bot.send_message(chat_id, f"📥 أرسل الملف التالي لنفس المقياس ({subj}):")
        
    elif data == "finish_files":
        user_states[chat_id] = {}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ مشاركة ملفات جديدة", callback_data="btn_share"),
            telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, "✅ **تم إنهاء عملية رفع الملفات بنجاح. شكراً لمساهمتك العطرة!**", reply_markup=markup)
        
    elif data == "btn_get":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📚 السنة الأولى ليسونس", callback_data="get_s1"),
            telebot.types.InlineKeyboardButton("📖 السنة الثانية ليسونس", callback_data="get_s2"),
            telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
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
        db = load_db()
        matched_files = [f for f in db if f.get("subject") == subj_name and f.get("status") == "approved"]
        
        if matched_files:
            bot.send_message(chat_id, f"📂 **إليك الملفات المتاحة لمقياس ({subj_name}):**")
            for item in matched_files:
                caption = f"📚 المقياس: {subj_name}\n🏷️ النوع: {item['type']}"
                try:
                    if item["media_type"] == "document":
                        bot.send_document(chat_id, item["file_id"], caption=caption)
                    elif item["media_type"] == "audio":
                        bot.send_audio(chat_id, item["file_id"], caption=caption)
                    elif item["media_type"] == "voice":
                        bot.send_voice(chat_id, item["file_id"], caption=caption)
                    elif item["media_type"] == "photo":
                        bot.send_photo(chat_id, item["file_id"], caption=caption)
                    elif item["media_type"] == "video":
                        bot.send_video(chat_id, item["file_id"], caption=caption)
                except Exception as ex:
                    print(f"Error sending file: {ex}")
        else:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
            bot.send_message(chat_id, f"⚠️ **لا توجد ملفات مقبولة حالياً لمقياس ({subj_name}).**", reply_markup=markup)
            
    elif data.startswith("accept_"):
        file_id_key = data.replace("accept_", "")
        db = load_db()
        for item in db:
            if str(item.get("unique_key")) == file_id_key:
                item["status"] = "approved"
                try:
                    bot.send_message(item["student_chat_id"], f"🎉 **مبروك! تم قبول ونشر ملفك الخاص بمقياس ({item['subject']}) في البوت بنجاح.**")
                except:
                    pass
                break
        save_db(db)
        bot.answer_callback_query(call.id, "تم قبول ونشر الملف بنجاح ✅")
        bot.edit_message_text(call.message.text + "\n\n✅ **[تم قبول ونشر الملف]**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        
    elif data.startswith("ask_reject_"):
        file_id_key = data.replace("ask_reject_", "")
        user_states[f"reject_reason_{chat_id}"] = file_id_key
        bot.answer_callback_query(call.id, "اكتب سبب الرفض في رسالة الآن")
        bot.send_message(chat_id, "✍️ **أرسل الآن رسالة نصية تحتوي على سبب الرفض ليتم إرسالها للطالب:**")
        
    elif data.startswith("chg_subj_"):
        file_id_key = data.replace("chg_subj_", "")
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for subj in SUBJECTS:
            markup.add(telebot.types.InlineKeyboardButton(subj, callback_data=f"set_new_subj_{file_id_key}_{subj}"))
        bot.send_message(chat_id, "🔄 اختر المقياس الصحيح الجديد للملف:", reply_markup=markup)
        
    elif data.startswith("set_new_subj_"):
        parts = data.replace("set_new_subj_", "").split("_", 1)
        file_id_key = parts[0]
        new_subj = parts[1]
        db = load_db()
        for item in db:
            if str(item.get("unique_key")) == file_id_key:
                item["subject"] = new_subj
                break
        save_db(db)
        bot.answer_callback_query(call.id, f"تم تعديل المقياس إلى: {new_subj} ✅")
        bot.send_message(chat_id, f"✅ **تم تحديث مقياس الملف بنجاح إلى: ({new_subj})**")
        
    elif data == "main_menu":
        user_states[chat_id] = {}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ أود مشاركة ملف", callback_data="btn_share"),
            telebot.types.InlineKeyboardButton("📂 أود الحصول على ملفات", callback_data="btn_get")
        )
        bot.send_message(chat_id, "أهلاً بك في القائمة الرئيسية:", reply_markup=markup)

@bot.message_handler(func=lambda message: f"reject_reason_{message.chat.id}" in user_states)
def handle_reject_reason(message):
    chat_id = message.chat.id
    file_id_key = user_states.pop(f"reject_reason_{chat_id}")
    reason = message.text
    
    db = load_db()
    target_item = None
    new_db = []
    for item in db:
        if str(item.get("unique_key")) == file_id_key:
            target_item = item
        else:
            new_db.append(item)
    save_db(new_db)
    
    if target_item:
        try:
            bot.send_message(target_item["student_chat_id"], f"❌ **عذراً، تم رفض ملفك الخاص بمقياس ({target_item['subject']}).**\n📝 **السبب:** {reason}")
        except:
            pass
    bot.send_message(chat_id, "✅ **تم رفض الملف وحذفه وإرسال سبب الرفض للطالب بنجاح.**")

@bot.message_handler(content_types=['document', 'audio', 'voice', 'photo', 'video'])
def handle_files(message):
    chat_id = message.chat.id
    if message.chat.type != "private":
        return
        
    state = user_states.get(chat_id, {})
    
    if state.get("step") != "waiting_for_file":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ اضغط هنا لبدء تصنيف الملف", callback_data="btn_share"),
            telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, "⚠️ **عذراً، يرجى اختيار (أود مشاركة ملف) وتحديد التصنيف أولاً!**", reply_markup=markup)
        return
        
    user = message.from_user
    username = f"@{user.username}" if user.username else user.first_name
    
    year = state.get("temp_year", "غير محدد")
    sem = state.get("temp_sem", "غير محدد")
    f_type = state.get("temp_type", "ملف")
    subj = state.get("temp_subj", "غير محدد")
    
    media_type = "document"
    file_id = message.document.file_id if message.document else ""
    if message.audio:
        media_type = "audio"
        file_id = message.audio.file_id
    elif message.voice:
        media_type = "voice"
        file_id = message.voice.file_id
    elif message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        file_id = message.video.file_id
        
    unique_key = str(message.message_id)
    
    db = load_db()
    new_item = {
        "unique_key": unique_key,
        "subject": subj,
        "file_id": file_id,
        "media_type": media_type,
        "type": f_type,
        "sender": username,
        "student_chat_id": chat_id,
        "status": "pending"
    }
    db.append(new_item)
    save_db(db)
    
    caption = (
        f"📥 **طلب مشاركة جديد للمراجعة:**\n\n"
        f"📚 المقياس: {subj}\n"
        f"🎓 السنة: {year} - السداسي {sem}\n"
        f"🏷️ النوع: {f_type}\n"
        f"👤 الطالب: {username} (ID: `{chat_id}`)"
    )
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ قبول ونشر", callback_data=f"accept_{unique_key}"),
        telebot.types.InlineKeyboardButton("❌ رفض مع سبب", callback_data=f"ask_reject_{unique_key}"),
        telebot.types.InlineKeyboardButton("🔄 تعديل التصنيف", callback_data=f"chg_subj_{unique_key}")
    )
    
    try:
        bot.forward_message(chat_id=ADMIN_GROUP, from_chat_id=chat_id, message_id=message.message_id)
        bot.send_message(ADMIN_GROUP, caption, reply_markup=markup, parse_mode="Markdown")
        
        markup_student = telebot.types.InlineKeyboardMarkup()
        markup_student.add(
            telebot.types.InlineKeyboardButton("➕ إضافة ملف آخر لنفس التصنيف", callback_data="more_files"),
            telebot.types.InlineKeyboardButton("✅ تم، إنهاء", callback_data="finish_files"),
            telebot.types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(chat_id, f"✅ **تم استلام الملف وإرساله للإدارة تحت مقياس ({subj}).**\nهل تريد إضافة ملف آخر بنفس التصنيف أم تنتهي؟", reply_markup=markup_student)
    except Exception as e:
        print(f"Error forwarding: {e}")
        bot.send_message(chat_id, "✅ **تم إرسال الملف للمجموعة بنجاح.**")

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
