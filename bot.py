import os
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

t = threading.Thread(target=run_web_server)
t.daemon = True
t.start()

TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"

DB_FILE = "database.json"

# دالة لتحميل البيانات من الملف الدائم
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

# دالة لحفظ البيانات في الملف الدائم
def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

user_states = {}
processed_updates = set()
last_update_id = 0

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

FILE_TYPES = [
    "🎧 محاضرة صوتية",
    "📝 محاضرة مكتوبة",
    "📁 ملخص محاضرة",
    "📑 مطبوعة",
    "📚 كتاب",
    "✍️ تمارين",
    "📋 مواضيع امتحانات"
]

print("Persistent Database Bot Started Successfully...")

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{URL}/sendMessage", data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

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
                    
                    if "callback_query" in update:
                        cq = update["callback_query"]
                        chat_id = cq["message"]["chat"]["id"]
                        data_val = cq["data"]
                        
                        if data_val == "btn_share":
                            send_message(chat_id, "📥 **أرسل الآن الملف (مستند، صوت، صورة...)** هنا، وسيلتقطه البوت تلقائياً:")
                        
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
                            database_files = load_db()
                            matched_files = [f for f in database_files if f["subject"] == subj_name]
                            
                            if matched_files:
                                send_message(chat_id, f"📂 **إليك الملفات المتاحة لمقياس ({subj_name}):**")
                                for file_item in matched_files:
                                    f_type = file_item["type"]
                                    f_id = file_item["file_id"]
                                    caption = f"📚 المقياس: {subj_name}\n🏷️ النوع: {f_type}"
                                    
                                    payload = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
                                    if file_item["media_type"] == "document":
                                        payload["document"] = f_id
                                        endpoint = "sendDocument"
                                    elif file_item["media_type"] == "audio":
                                        payload["audio"] = f_id
                                        endpoint = "sendAudio"
                                    elif file_item["media_type"] == "voice":
                                        payload["voice"] = f_id
                                        endpoint = "sendVoice"
                                    else:
                                        payload["photo"] = f_id
                                        endpoint = "sendPhoto"
                                        
                                    req_send = urllib.request.Request(f"{URL}/{endpoint}", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                                    try:
                                        urllib.request.urlopen(req_send)
                                    except Exception as ex:
                                        print(f"Error sending file: {ex}")
                            else:
                                send_message(chat_id, f"⚠️ **لا توجد ملفات مرفوعة حالياً لمقياس ({subj_name}).**", reply_markup={
                                    "inline_keyboard": [
                                        [{"text": "📂 تصفح مقياس آخر", "callback_data": "get_s1"}],
                                        [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}]
                                    ]
                                })
                            
                        elif data_val.startswith("autosave_type_"):
                            chosen_type = data_val.replace("autosave_type_", "")
                            user_states[chat_id]["temp_type"] = chosen_type
                            
                            keyboard_subjects = {"inline_keyboard": []}
                            row = []
                            for subj in SUBJECTS:
                                row.append({"text": subj, "callback_data": f"autosave_subj_{subj}"})
                                if len(row) == 2:
                                    keyboard_subjects["inline_keyboard"].append(row)
                                    row = []
                            if row:
                                keyboard_subjects["inline_keyboard"].append(row)
                                
                            send_message(chat_id, "اختر المقياس لربط هذا الملف به وتخزينه:", reply_markup=keyboard_subjects)
                            
                        elif data_val.startswith("autosave_subj_"):
                            subject_name = data_val.replace("autosave_subj_", "")
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
                                
                            send_message(chat_id, f"✅ **تم تخزين الملف بنجاح في قاعدة البيانات تحت مقياس ({subject_name})!**\nأصبح متاحاً للطلاب فوراً.", reply_markup={
                                "inline_keyboard": [
                                    [{"text": "➕ إرسال ملف آخر", "callback_data": "btn_share"}],
                                    [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}]
                                ]
                            })
                            user_states[chat_id] = {}
                            
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
                            send_message(chat_id, "حياك الله في بوت خدمات الطلبة 📚", reply_markup=keyboard)
                            continue
                            
                        media_type = None
                        file_id = None
                        if "document" in msg:
                            media_type = "document"
                            file_id = msg["document"]["file_id"]
                        elif "audio" in msg:
                            media_type = "audio"
                            file_id = msg["audio"]["file_id"]
                        elif "voice" in msg:
                            media_type = "voice"
                            file_id = msg["voice"]["file_id"]
                        elif "photo" in msg:
                            media_type = "photo"
                            file_id = msg["photo"][-1]["file_id"]
                            
                        if file_id:
                            user_states[chat_id] = {
                                "file_id": file_id,
                                "media_type": media_type,
                                "username": username
                            }
                            
                            keyboard_types = {"inline_keyboard": []}
                            row = []
                            for f_type in FILE_TYPES:
                                row.append({"text": f_type, "callback_data": f"autosave_type_{f_type}"})
                                if len(row) == 2:
                                    keyboard_types["inline_keyboard"].append(row)
                                    row = []
                            if row:
                                keyboard_types["inline_keyboard"].append(row)
                                
                            send_message(chat_id, "📥 **تم التقاط الملف بنجاح!**\nاختر نوع الملف:", reply_markup=keyboard_types)
                        else:
                            if text:
                                send_message(chat_id, "أهلاً بك. اختر ما تحتاجه من القائمة:", reply_markup={
                                    "inline_keyboard": [
                                        [{"text": "🏠 القائمة الرئيسية", "callback_data": "main_menu"}]
                                    ]
                                })
                        continue

    except Exception as e:
        print(f"Error: {e}")
        import time
        time.sleep(3)
