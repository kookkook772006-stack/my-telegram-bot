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

# تخزين مؤقت لحالات ومقاييس المستخدمين
user_states = {}
processed_updates = set()
last_update_id = 0

# قائمة المقاييس الأساسية بناءً على جدول الحصص (محاضرات وأعمال موجهة)
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

print("Professional Educational Bot Started Successfully...")

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
                    
                    # 1. التعامل مع الأزرار التفاعلية (Inline Keyboards)
                    if "callback_query" in update:
                        cq = update["callback_query"]
                        chat_id = cq["message"]["chat"]["id"]
                        data_val = cq["data"]
                        
                        if data_val == "btn_share":
                            user_states[chat_id] = {"step": "collecting_files", "files": []}
                            send_message(chat_id, "📥 أرسل الآن الملفات (مستندات، صور، صوتيات).\nيمكنك إرسال ملف واحد أو عدة ملفات، ثم اضغط على زر 'تم الانتهاء وإرسال المقياس' أسفل الرسائل.")
                        
                        elif data_val == "finish_files":
                            if not user_states.get(chat_id, {}).get("files"):
                                send_message(chat_id, "⚠️ لم تقم بإرسال أي ملف بعد! أرسل الملفات أولاً.")
                                continue
                            
                            # إظهار أزرار المقاييس ليختار منها مباشرة
                            keyboard_subjects = {"inline_keyboard": []}
                            row = []
                            for subj in SUBJECTS:
                                row.append({"text": subj, "callback_data": f"subj_{subj}"})
                                if len(row) == 2:
                                    keyboard_subjects["inline_keyboard"].append(row)
                                    row = []
                            if row:
                                keyboard_subjects["inline_keyboard"].append(row)
                            keyboard_subjects["inline_keyboard"].append([{"text": "🔙 إلغاء", "callback_data": "main_menu"}])
                            
                            user_states[chat_id]["step"] = "selecting_subject"
                            send_message(chat_id, "اختر المقياس المناسب لهذه الملفات:", reply_markup=keyboard_subjects)
                        
                        elif data_val.startswith("subj_"):
                            subject_name = data_val.replace("subj_", "")
                            state = user_states.get(chat_id, {})
                            files = state.get("files", [])
                            username = state.get("username", "مجهول")
                            
                            # نشر الملفات المعلقة إلى القناة مع التصنيف واسم المرسل
                            for file_id in files:
                                caption = f"📚 مقياس: {subject_name}\n👤 المرسل: {username}"
                                copy_message(chat_id, file_id, caption)
                            
                            user_states[chat_id] = {"step": "menu"}
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🔄 مشاركة ملف آخر", "callback_data": "btn_share"}],
                                    [{"text": "📂 تصفح الملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, f"✅ جزاك الله خيراً! تم نشر وتصنيف الملفات تحت مقياس ({subject_name}) بنجاح.", reply_markup=keyboard)
                        
                        elif data_val == "btn_get":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "📚 السنة الأولى ليسونس", "callback_data": "get_year_1"}],
                                    [{"text": "📖 السنة الثانية ليسونس", "callback_data": "get_year_2"}],
                                    [{"text": "🔙 القائمة الرئيسية", "callback_data": "main_menu"}]
                                ]
                            }
                            send_message(chat_id, "اختر السنة الدراسية للتصفح:", reply_markup=keyboard)
                            
                        elif data_val == "get_year_1":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": " السداسي الأول", "callback_data": "get_s1"}],
                                    [{"text": " السداسي الثاني", "callback_data": "get_s2"}],
                                    [{"text": "🔙 رجوع", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "اختر السداسي:", reply_markup=keyboard)
                            
                        elif data_val in ["get_s1", "get_s2"]:
                            # عرض المقاييس للتصفح المباشر
                            keyboard_subjs = {"inline_keyboard": []}
                            row = []
                            for subj in SUBJECTS:
                                row.append({"text": f"📁 {subj}", "callback_data": f"browse_{subj}"})
                                if len(row) == 2:
                                    keyboard_subjs["inline_keyboard"].append(row)
                                    row = []
                            if row:
                                keyboard_subjs["inline_keyboard"].append(row)
                            keyboard_subjs["inline_keyboard"].append([{"text": "🔙 رجوع", "callback_data": "get_year_1"}])
                            
                            send_message(chat_id, "اختر المقياس لعرض ملفاته:", reply_markup=keyboard_subjs)
                            
                        elif data_val.startswith("browse_"):
                            subj_name = data_val.replace("browse_", "")
                            send_message(chat_id, f"🔍 ستجد كافة محاضرات وتمارين مقياس ({subj_name}) مرفوعة ومرتبة في قناتنا الرسمية المخصصة: {CHANNEL_ID}\n(يمكنك البحث داخل القناة باسم المقياس مباشرة للوصول الفوري).")
                            
                        elif data_val == "main_menu":
                            user_states[chat_id] = {"step": "menu"}
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "➕ أود مشاركة ملف", "callback_data": "btn_share"}],
                                    [{"text": "📂 أود الحصول على ملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "أهلاً بك في القائمة الرئيسية:", reply_markup=keyboard)
                            
                        continue

                    # 2. التعامل مع الملفات والرسائل الواردة
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        
                        if msg["chat"]["type"] != "private":
                            continue
                            
                        text = msg.get("text", "")
                        user = msg.get("from", {})
                        username = f"@{user.get('username')}" if user.get("username") else user.get("first_name", "مجهول")
                        
                        if text == "/start":
                            user_states[chat_id] = {"step": "menu"}
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "➕ أود مشاركة ملف", "callback_data": "btn_share"}],
                                    [{"text": "📂 أود الحصول على ملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "حياك الله في بوت خدمات الطلبة 📚\nاختر ما تحتاجه:", reply_markup=keyboard)
                            continue
                            
                        current_state = user_states.get(chat_id, {"step": "menu"})
                        current_step = current_state.get("step")
                        
                        if current_step == "collecting_files":
                            has_media = any(k in msg for k in ["document", "photo", "audio", "voice", "video"])
                            if has_media:
                                # حفظ معرف الرسالة والملف في قائمة مؤقتة
                                if "files" not in current_state:
                                    current_state["files"] = []
                                current_state["files"].append(msg["message_id"])
                                current_state["username"] = username
                                user_states[chat_id] = current_state
                                
                                # زر الانتهاء وتحديد المقياس
                                finish_keyboard = {
                                    "inline_keyboard": [
                                        [{"text": "✅ تم الانتهاء (حدد المقياس الآن)", "callback_data": "finish_files"}],
                                        [{"text": "❌ إلغاء", "callback_data": "main_menu"}]
                                    ]
                                }
                                send_message(chat_id, f"📥 تم استلام الملف بنجاح (عدد الملفات المجهزة: {len(current_state['files'])}).\nأرسل ملفاً آخر إذا أردت، أو اضغط على الزر أدناه لاختيار المقياس:", reply_markup=finish_keyboard)
                            else:
                                send_message(chat_id, "⚠️ الرجاء إرسال ملف، صورة، أو مستند صالح.")
                            continue

    except Exception as e:
        print(f"Error: {e}")
        import time
        time.sleep(3)
