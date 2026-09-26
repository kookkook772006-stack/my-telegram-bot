import os
import time
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

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
CHANNEL_ID = "@m388393"

user_states = {}
processed_updates = set()  # لتفادي تكرار معالجة نفس التحديث
last_update_id = 0

print("Anti-Duplicate Student Bot started...")

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

def copy_message(chat_id, message_id, caption=""):
    payload = {
        "chat_id": CHANNEL_ID,
        "from_chat_id": chat_id,
        "message_id": message_id
    }
    if caption:
        payload["caption"] = caption
        
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
                    
                    # تنظيف الذاكرة القديمة للمتغير للحفاظ على خفة البوت
                    if len(processed_updates) > 500:
                        processed_updates.clear()
                    
                    # التعامل مع الضغط على الأزرار
                    if "callback_query" in update:
                        cq = update["callback_query"]
                        chat_id = cq["message"]["chat"]["id"]
                        data_val = cq["data"]
                        
                        if data_val == "new_submission":
                            user_states[chat_id] = {"step": "waiting_file"}
                            send_message(chat_id, "حياك الله من جديد! 📚\nالرجاء إرسال الملفات أو الصور أو التسجيلات التي تريد مشاركتها مباشرة:")
                        continue

                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        
                        if msg["chat"]["type"] != "private":
                            continue
                            
                        user = msg.get("from", {})
                        username = f"@{user.get('username')}" if user.get("username") else "بدون معرف"
                        text = msg.get("text", "")
                        
                        if chat_id not in user_states:
                            user_states[chat_id] = {"step": "waiting_file"}
                            
                        step = user_states[chat_id]["step"]
                        
                        # أمر البدء أو إعادة التعيين
                        if text == "/start":
                            user_states[chat_id] = {"step": "waiting_file"}
                            send_message(chat_id, "حياك الله! 📚\nأهلاً بك في بوت استقبال مشاركات الطلبة.\n\nالرجاء إرسال ما تريد مشاركته (ملفات، صور، تسجيلات صوتية...) مباشرة:")
                            continue
                            
                        if step == "none" or step == "completed":
                            user_states[chat_id] = {"step": "waiting_file"}
                            step = "waiting_file"
                            
                        # الخطوة 1: استقبال الملف أولاً
                        if step == "waiting_file":
                            has_media = any(k in msg for k in ["document", "photo", "audio", "voice", "video", "video_note"])
                            
                            if has_media or (text and not text.startswith("/")):
                                caption = f"📄 مشاركة جديدة:\n👤 مرسل من: (مجهول) | المعرف: {username}"
                                copy_message(chat_id, msg["message_id"], caption)
                                
                                user_states[chat_id]["step"] = "waiting_details"
                                send_message(chat_id, "وصلنا، بارك الله فيك! 📥\nالآن اذكر لنا معلومات عن الملف (مثل: اسم المقياس، المحاضرة، الأستاذ، التاريخ، رقم الحصة، ونحوه):")
                                continue
                            
                        # الخطوة 2: استقبال التفاصيل لمرة واحدة فقط
                        elif step == "waiting_details":
                            user_states[chat_id]["step"] = "completed"  # تغيير الحالة فوراً لمنع أي تكرار
                            
                            details_text = f"📝 تفاصيل المشاركة:\n{text}\n\n👤 المرسل: {username}"
                            send_message(CHANNEL_ID, details_text)
                            
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🔄 إعادة المشاركة من جديد", "callback_data": "new_submission"}]
                                ]
                            }
                            
                            send_message(chat_id, "بوركت وجزاك الله خيراً! تم نشر تفاصيل الملف بنجاح. 🌸", reply_markup=keyboard)
                            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)
