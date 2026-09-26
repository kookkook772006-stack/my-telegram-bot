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
last_update_id = 0

print("Reversed flow student bot started...")

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
                    last_update_id = update["update_id"]
                    
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
                            user_states[chat_id] = {"step": "none"}
                            
                        step = user_states[chat_id]["step"]
                        
                        # أمر البدء
                        if text == "/start" or step == "none":
                            user_states[chat_id] = {"step": "waiting_file"}
                            send_message(chat_id, "حياك الله! 📚\nأهلاً بك في بوت استقبال مشاركات الطلبة.\n\nالرجاء إرسال ما تريد مشاركته (ملفات، صور، تسجيلات صوتية...) مباشرة:")
                            continue
                            
                        # الخطوة 1: استقبال الملفات مباشرة أولاً
                        if step == "waiting_file":
                            # حفظ معرف رسالة الملف مؤقتاً أو نسخه فوراً للقناة مع تذييل المجهول
                            caption = f"📄 مشاركة جديدة:\n👤 مرسل من: (مجهول) | المعرف: {username}"
                            copy_message(chat_id, msg["message_id"], caption)
                            
                            user_states[chat_id]["step"] = "waiting_details"
                            send_message(chat_id, "وصلنا، بارك الله فيك! 📥\nالآن اذكر لنا معلومات عن الملف (مثل: اسم المقياس، المحاضرة، الأستاذ، التاريخ، رقم الحصة، ونحوه):")
                            
                        # الخطوة 2: استقبال تفاصيل الملف ومعلوماته كخطوة أخيرة
                        elif step == "waiting_details":
                            # إرسال تفاصيل الملف للقناة أيضاً
                            details_text = f"📝 تفاصيل المشاركة:\n{text}\n\n👤 المرسل: {username}"
                            send_message(CHANNEL_ID, details_text)
                            
                            # زر إعادة المشاركة
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🔄 إعادة المشاركة من جديد", "callback_data": "new_submission"}]
                                ]
                            }
                            
                            send_message(chat_id, "بوركت وجزاك الله خيراً! تم نشر تفاصيل الملف بنجاح. 🌸", reply_markup=keyboard)
                            user_states[chat_id]["step"] = "completed"
                            
                        elif step == "completed":
                            send_message(chat_id, "لقد أكملت مشاركتك السابقة. يرجى الضغط على زر (إعادة المشاركة من جديد) في الرسالة السابقة لرفع ملف جديد.")
                            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)
