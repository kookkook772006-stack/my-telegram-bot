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

processed_updates = set()
last_update_id = 0

print("Direct Forward Student Bot started...")

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{URL}/sendMessage", data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

def forward_message(chat_id, message_id):
    # استخدام forwardMessage لإعادة توجيه الرسالة بكل محتواها (ملف، صوت، صورة...) مع حفظ اسم المرسل الأصلي في التيليجرام
    payload = {
        "chat_id": CHANNEL_ID,
        "from_chat_id": chat_id,
        "message_id": message_id
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{URL}/forwardMessage", data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error forwarding message: {e}")

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
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        
                        # استقبال الرسائل من المحادثات الخاصة فقط
                        if msg["chat"]["type"] != "private":
                            continue
                            
                        text = msg.get("text", "")
                        
                        # أمر البدء
                        if text == "/start":
                            send_message(chat_id, "حياك الله! 📚\nأهلاً بك في بوت استقبال مشاركات الطلبة.\n\nأرسل أي ملف، صوت، صورة، أو نص، وسأقوم بإعادة توجيهه إلى القناة مباشرة وفوراً دون أي خطوات معقدة:")
                            continue
                        
                        # إعادة توجيه أي شي يرسله المستخدم (ملف، ميديا، نص) بحذافيره إلى القناة
                        forward_message(chat_id, msg["message_id"])
                        
                        # تأكيد وصول للمستخدم
                        send_message(chat_id, "✅ جزاك الله خيراً! تم إرسال مشاركتك إلى القناة بنجاح.")
                            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)
