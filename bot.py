import os
import time
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# خادم الويب الوهمي لإبقاء البوت قيد التشغيل على Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

t = threading.Thread(target=run_web_server)
t.daemon = True
t.start()

TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"

# معرف قناة المشرفين المحددة
CHANNEL_ID = "@m388393"

# قاموس لتخزين حالة المحادثة لكل طالب
user_states = {}

print("Advanced student submissions bot started...")

last_update_id = 0

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    req = urllib.request.Request(
        f"{URL}/sendMessage",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Send message error: {e}")

def forward_or_copy_message(from_chat_id, message_id, caption_text):
    payload = {
        "chat_id": CHANNEL_ID,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "caption": caption_text
    }
    req = urllib.request.Request(
        f"{URL}/copyMessage",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Copy message error: {e}")

while True:
    try:
        req = urllib.request.Request(f"{URL}/getUpdates?offset={last_update_id + 1}&timeout=30")
        with urllib.request.urlopen(req, timeout=40) as response:
            data = json.loads(response.read().decode())
            
            if "result" in data:
                for update in data["result"]:
                    last_update_id = update["update_id"]
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        
                        # استقبال في المحادثات الخاصة حصراً
                        if message["chat"]["type"] != "private":
                            continue
                            
                        user = message.get("from", {})
                        user_username = f"@{user.get('username')}" if user.get("username") else "بدون معرف"
                        text = message.get("text")
                        
                        # أمر البداية /start أو إعادة الضبط
                        if text == "/start":
                            user_states[chat_id] = {"step": "waiting_module"}
                            send_message(chat_id, "حياك الله! 📚\nأهلاً بك في بوت استقبال مشاركات الطلبة.\nالرجاء كتابة اسم المقياس (المادة) أولاً:")
                            continue
                            
                        if chat_id not in user_states:
                            user_states[chat_id] = {"step": "none"}
                            
                        current_state = user_states[chat_id]["step"]
                        
                        if current_state == "waiting_module":
                            user_states[chat_id]["module"] = text
                            user_states[chat_id]["step"] = "waiting_professor"
                            send_message(chat_id, "حسناً، تم تسجيل المقياس.\nالآن، يرجى كتابة اسم الأستاذ المسؤول عن المادة:")
                            
                        elif current_state == "waiting_professor":
                            user_states[chat_id]["professor"] = text
                            user_states[chat_id]["step"] = "waiting_doc_type"
                            send_message(chat_id, "ممتاز. ما هو نوع المستند أو المطبوعة؟ (مثال: ملخص، محاضرة، امتحان، تسجيل صوتي... الخ):")
                            
                        elif current_state == "waiting_doc_type":
                            user_states[chat_id]["doc_type"] = text
                            user_states[chat_id]["step"] = "waiting_file"
                            send_message(chat_id, "رائع جداً.\nالآن أرسل الملف، المستند، الصورة، أو التسجيل الصوتي الخاص بالمشاركة:")
                            
                        elif current_state == "waiting_file":
                            module = user_states[chat_id].get("module", "غير محدد")
                            professor = user_states[chat_id].get("professor", "غير محدد")
                            doc_type = user_states[chat_id].get("doc_type", "غير محدد")
                            
                            # تنسيق الرسالة لتكون مجهولة مع إظهار المعرف للاحتياط
                            caption = (
                                f"📄 مشاركة جديدة:\n\n"
                                f"▪️ المقياس: {module}\n"
                                f"▪️ الأستاذ: {professor}\n"
                                f"▪️ النوع: {doc_type}\n\n"
                                f"👤 مرسل من: (مجهول) | المعرف: {user_username}"
                            )
                            
                            forward_or_copy_message(chat_id, message["message_id"], caption)
                            
                            send_message(chat_id, "تم استلام مشاركتك وإرسالها إلى قناة المشرفين بنجاح. جزاك الله خيراً! لرفع مشاركة أخرى أرسل /start")
                            user_states[chat_id] = {"step": "none"}
                            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
