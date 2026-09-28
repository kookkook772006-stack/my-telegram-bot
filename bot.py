import os
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# إعداد سيرفر وهمي للحفاظ على البوت مستيقظاً على Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Educational Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

t = threading.Thread(target=run_web_server)
t.daemon = True
t.start()

TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL_ID = "@m388393"  # قناة النشر

# ذاكرة مؤقتة لحفظ حالة المستخدم
user_states = {}
processed_updates = set()
last_update_id = 0

print("Edu Bot Started Successfully...")

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
                    
                    # 1. التفاعل مع الأزرار (Inline Keyboards)
                    if "callback_query" in update:
                        cq = update["callback_query"]
                        chat_id = cq["message"]["chat"]["id"]
                        data_val = cq["data"]
                        
                        if data_val == "btn_share":
                            user_states[chat_id] = {"step": "waiting_file"}
                            send_message(chat_id, "📥 أرسل الآن الملف، الصورة، أو المستند الذي تريد مشاركته:")
                        
                        elif data_val == "btn_get":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "📚 السنة الأولى ليسونس", "callback_data": "year_1"}],
                                    [{"text": "📖 السنة الثانية ليسونس", "callback_data": "year_2"}],
                                    [{"text": "🔙 القائمة الرئيسية", "callback_data": "main_menu"}]
                                ]
                            }
                            send_message(chat_id, "اختر السنة الدراسية للبحث والتصفح:", reply_markup=keyboard)
                            
                        elif data_val == "year_1":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": " السداسي الأول", "callback_data": "s1"}],
                                    [{"text": " السداسي الثاني", "callback_data": "s2"}],
                                    [{"text": "🔙 رجوع", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "اختر السداسي:", reply_markup=keyboard)
                            
                        elif data_val in ["s1", "s2"]:
                            send_message(chat_id, "📁 ستجد جميع ملفات هذا القسم منشورة ومرتبة في قناتنا الرسمية: " + CHANNEL_ID)
                            
                        elif data_val == "main_menu":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "➕ أود مشاركة ملف", "callback_data": "btn_share"}],
                                    [{"text": "📂 أود الحصول على ملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "أهلاً بك في القائمة الرئيسية:", reply_markup=keyboard)
                            
                        continue

                    # 2. التفاعل مع الرسائل والملفات
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
                            
                        current_step = user_states.get(chat_id, {}).get("step", "menu")
                        
                        if current_step == "waiting_file":
                            has_media = any(k in msg for k in ["document", "photo", "audio", "voice", "video"])
                            if has_media:
                                user_states[chat_id]["file_msg_id"] = msg["message_id"]
                                user_states[chat_id]["step"] = "waiting_subject"
                                send_message(chat_id, "ممتاز! 📄\nالآن اكتب اسم المقياس أو المادة الخاصة بهذا الملف:")
                            else:
                                send_message(chat_id, "⚠️ الرجاء إرسال ملف أو مستند صالح للمشاركة.")
                            continue
                            
                        elif current_step == "waiting_subject":
                            subject_name = text
                            file_msg_id = user_states[chat_id].get("file_msg_id")
                            
                            caption = f"📚 مقياس: {subject_name}\n👤 المرسل: {username}"
                            copy_message(chat_id, file_msg_id, caption)
                            
                            user_states[chat_id]["step"] = "menu"
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🔄 مشاركة ملف آخر", "callback_data": "btn_share"}],
                                    [{"text": "📂 تصفح الملفات", "callback_data": "btn_get"}]
                                ]
                            }
                            send_message(chat_id, "✅ جزاك الله خيراً! تم نشر الملف وتصنيفه في القناة بنجاح.", reply_markup=keyboard)
                            continue

    except Exception as e:
        print(f"Error: {e}")
        import time
        time.sleep(3)
