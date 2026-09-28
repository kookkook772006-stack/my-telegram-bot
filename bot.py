import os
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# سيرفر وهمي لإبقاء البوت مستيقظاً على Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Educational Bot is active and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

t = threading.Thread(target=run_web_server)
t.daemon = True
t.start()

TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL_ID = "@m388393"  # قناة التخزين العامة

user_states = {}
processed_updates = set()
last_update_id = 0

# قائمة المقاييس الأساسية بناءً على جدول الحصص
SUBJECTS = [
    "علوم القرآن",
    "مدخل لأصول الفقه",
    "العقيدة الإسلامية",
    "فقه عبادات",
    "أصول الفقه",
    "تاريخ إسلامي: السير",
    "منهج البحث",
    "مدخل لعلوم التربية",
    "تاريخ الجزائر",
    "لغة عربية",
    "ترتيل",
    "إنجليزية"
]

print("Advanced Student Bot Started Successfully...")

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{URL}/sendMessage", data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

def copy_message(chat_id, message_id, caption):
    payload = {
        "chat_id": CHANNEL_ID,
        "from_chat_id": chat_id,
        "message_id": message_id,
        "caption": caption
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{URL}/copyMessage", data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error copying message: {e}")

while True:
    try:
        req = urllib.request.Request(f"{URL}/getUpdates?offset={last_update_id + 1}&timeout=30")
        with urllib.request.urlopen(req, timeout=40) as response:
            data = json.loads(response.read().decode())
            if "result" in data:
                for update in data["result"]:
                    update_id = update["update_id"]
                    last_update_id = update_id
                    
                    if update_id in processed_updates:
                        continue
                    processed_updates.add(update_id)
                    if len(processed_updates) > 500:
                        processed_updates.clear()
                    
                    # 1. التعامل مع الأزرار التفاعلية
                    if "callback_query" in update:
                        cq = update["callback_query"]
                        chat_id = cq["message"]["chat"]["id"]
                        data_val = cq["data"]
                        
                        if data_val == "btn_share":
                            send_message(chat_id, "📥 أرسل الآن أي ملف، صورة، أو مستند تريد مشاركته، وسيتم استقباله وتصنيفه فوراً:")
                        
                        elif data_val == "btn_get":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "📚 السنة الأولى ليسونس", "callback_data": "get_year_1"}],
                                    [{"text": "📖 السنة الثانية ليسونس", "callback_data": "get_year_2"}],
                                    [{"text": "🔙 القائمة الرئيسية", "callback_data": "main_menu"}]
                                ]
                            }
                            send_message(chat_id, "اختر السنة الدراسية للتصفح:", reply_markup=keyboard)
                            
                        elif data_val in ["get_year_1", "get_year_2"]:
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": " السداسي الأول", "callback_data": "get_s1"}],
                                    [{"text": " السداسي الثاني", "callback_data": "get_s2"}],
                                    [{"text": "🔙 رجوع", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "اختر السداسي:", reply_markup=keyboard)
                            
                        elif data_val in ["get_s1", "get_s2"]:
                            keyboard_subjs = {"inline_keyboard": []}
                            row = []
                            for subj in SUBJECTS:
                                row.append({"text": f"📁 {subj}", "callback_data": f"browse_{subj}"})
                                if len(row) == 2:
                                    keyboard_subjs["inline_keyboard"].append(row)
                                    row = []
                            if row:
                                keyboard_subjs["inline_keyboard"].append(row)
                            keyboard_subjs["inline_keyboard"].append([
                                {"text": "🔙 رجوع", "callback_data": "get_year_1"},
                                {"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}
                            ])
                            send_message(chat_id, "اختر المقياس لعرض ملفاته:", reply_markup=keyboard_subjs)
                            
                        elif data_val.startswith("browse_"):
                            subj_name = data_val.replace("browse_", "")
                            keyboard_back = {
                                "inline_keyboard": [
                                    [{"text": "📂 تصفح مقياس آخر", "callback_data": "get_s1"}],
                                    [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}]
                                ]
                            }
                            send_message(chat_id, f"🔍 تصفحنا مقياس ({subj_name}).\n\n⚠️ **إن لم تجد ملفات مرفوعة حالياً، سيتم مشاركة ملفات أخرى قريباً. يمكنك المساهمة أنت في البوت بما لديك ليجدها الطلاب الآخرون!**", reply_markup=keyboard_back)
                            
                        elif data_val.startswith("cls_"):
                            # اختيار السنة مباشرة بعد إرسال الملف
                            chosen_year = data_val.replace("cls_", "")
                            user_states[chat_id]["temp_year"] = chosen_year
                            
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": " السداسي الأول", "callback_data": "cls_s1"}],
                                    [{"text": " السداسي الثاني", "callback_data": "cls_s2"}]
                                ]
                            }
                            send_message(chat_id, "اختر السداسي الخاص بهذا الملف:", reply_markup=keyboard)
                            
                        elif data_val in ["cls_s1", "cls_s2"]:
                            chosen_sem = "السداسي الأول" if data_val == "cls_s1" else "السداسي الثاني"
                            user_states[chat_id]["temp_sem"] = chosen_sem
                            
                            # الآن نعرض أزرار المقاييس ليختار المقياس النهائي
                            keyboard_subjects = {"inline_keyboard": []}
                            row = []
                            for subj in SUBJECTS:
                                row.append({"text": subj, "callback_data": f"final_subj_{subj}"})
                                if len(row) == 2:
                                    keyboard_subjects["inline_keyboard"].append(row)
                                    row = []
                            if row:
                                keyboard_subjects["inline_keyboard"].append(row)
                            
                            send_message(chat_id, "اختر المقياس النهائي للملف:", reply_markup=keyboard_subjects)
                            
                        elif data_val.startswith("final_subj_"):
                            subject_name = data_val.replace("final_subj_", "")
                            state = user_states.get(chat_id, {})
                            file_id = state.get("pending_file_id")
                            username = state.get("username", "مجهول")
                            year = state.get("temp_year", "السنة الأولى")
                            sem = state.get("temp_sem", "السداسي الأول")
                            
                            if file_id:
                                caption = f"📚 مقياس: {subject_name}\n🎓 السنة: {year} - {sem}\n👤 المرسل: {username}"
                                copy_message(chat_id, file_id, caption)
                            
                            user_states[chat_id] = {}
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "➕ مشاركة ملف آخر", "callback_data": "btn_share"}],
                                    [{"text": "📂 تصفح الملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, f"✅ جزاك الله خيراً! تم نشر وتصنيف الملف تحت مقياس ({subject_name}) بنجاح وإضافته لقسم الملفات.", reply_markup=keyboard)
                            
                        elif data_val == "main_menu":
                            user_states[chat_id] = {}
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "➕ أود مشاركة ملف", "callback_data": "btn_share"}],
                                    [{"text": "📂 أود الحصول على ملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "أهلاً بك في القائمة الرئيسية:", reply_markup=keyboard)
                            
                        continue

                    # 2. استقبال أي ملف أو رسالة فوراً ودون قيود
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        
                        if msg["chat"]["type"] != "private":
                            continue
                            
                        text = msg.get("text", "")
                        user = msg.get("from", {})
                        username = f"@{user.get('username')}" if user.get("username") else user.get("first_name", "مجهول")
                        
                        if text == "/start":
                            user_states[chat_id] = {}
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "➕ أود مشاركة ملف", "callback_data": "btn_share"}],
                                    [{"text": "📂 أود الحصول على ملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "حياك الله في بوت خدمات الطلبة 📚\nيمكنك إرسال أي ملف أو محاضرة في أي وقت، أو اختيار ما تحتاجه:", reply_markup=keyboard)
                            continue
                            
                        has_media = any(k in msg for k in ["document", "photo", "audio", "voice", "video", "video_note"])
                        if has_media:
                            # حفظ الملف مؤقتاً وبدء مسار التصنيف فوراً بالترتيب
                            user_states[chat_id] = {
                                "pending_file_id": msg["message_id"],
                                "username": username
                            }
                            
                            year_keyboard = {
                                "inline_keyboard": [
                                    [{"text": "📚 السنة الأولى ليسونس", "callback_data": "cls_السنة الأولى"}],
                                    [{"text": "📖 السنة الثانية ليسونس", "callback_data": "cls_السنة الثانية"}],
                                    [{"text": "❌ إلغاء", "callback_data": "main_menu"}]
                                ]
                            }
                            send_message(chat_id, "📥 تم استلام ملفك بنجاح!\nالآن حدد السنة الدراسية الخاصة به:", reply_markup=year_keyboard)
                        else:
                            # إذا أرسل نصاً عادياً
                            if text:
                                send_message(chat_id, " أهلاً بك. لاستخدام البوت، يمكنك الضغط على الأزرار أدناه أو إرسال ملف مباشرة لتصنيفه.", reply_markup={
                                    "inline_keyboard": [
                                        [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}]
                                    ]
                                })
                        continue

    except Exception as e:
        print(f"Error: {e}")
        import time
        time.sleep(3)
