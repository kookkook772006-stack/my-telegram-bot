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
CHANNEL_ID = "@m388393"

user_states = {}
last_update_id = 0

print("Bot is running perfectly...")

def send_message(chat_id, text):
    data = json.dumps({"chat_id": chat_id, "text": text}).encode('utf-8')
    req = urllib.request.Request(f"{URL}/sendMessage", data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

def copy_message(chat_id, message_id, caption):
    data = json.dumps({
        "chat_id": CHANNEL_ID,
        "from_chat_id": chat_id,
        "message_id": message_id,
        "caption": caption
    }).encode('utf-8')
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
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        
                        # المحادثات الخاصة فقط
                        if msg["chat"]["type"] != "private":
                            continue
                            
                        user = msg.get("from", {})
                        username = f"@{user.get('username')}" if user.get("username") else "بدون معرف"
                        text = msg.get("text")
                        
                        # أمر البدء
                        if text == "/start":
                            user_states[chat_id] = {"step": "module"}
                            send_message(chat_id, "حياك الله! 📚\nأهلاً بك. أرسل اسم المقياس (المادة) مباشرة:")
                            continue
                            
                        if chat_id not in user_states:
                            user_states[chat_id] = {"step": "none"}
                            
                        step = user_states[chat_id]["step"]
                        
                        # الخطوة 1: استقبال اسم المقياس (أي كلمة يكتبها الطالب تُعتبر هي المادة فوراً)
                        if step == "module":
                            user_states[chat_id]["module"] = text or "مشاركة"
                            user_states[chat_id]["step"] = "professor"
                            send_message(chat_id, "تم تسجيل المقياس بنجاح.\nالآن، أرسل اسم الأستاذ:")
                            
                        # الخطوة 2: استقبال اسم الأستاذ
                        elif step == "professor":
                            user_states[chat_id]["professor"] = text or "غير محدد"
                            user_states[chat_id]["step"] = "doc_type"
                            send_message(chat_id, "ممتاز. ما هو نوع المستند؟ (مثال: ملخص، محاضرة، امتحان...):")
                            
                        # الخطوة 3: استقبال نوع المستند
                        elif step == "doc_type":
                            user_states[chat_id]["doc_type"] = text or "غير محدد"
                            user_states[chat_id]["step"] = "file"
                            send_message(chat_id, "رائع جداً.\nالآن أرسل الملف أو المحتوى مباشرة:")
                            
                        # الخطوة 4: استقبال الملف ونشره
                        elif step == "file":
                            mod = user_states[chat_id].get("module", "-")
                            prof = user_states[chat_id].get("professor", "-")
                            dtype = user_states[chat_id].get("doc_type", "-")
                            
                            caption = (
                                f"📄 مشاركة جديدة:\n\n"
                                f"▪️ المقياس: {mod}\n"
                                f"▪️ الأستاذ: {prof}\n"
                                f"▪️ النوع: {dtype}\n\n"
                                f"👤 مرسل من: (مجهول) | المعرف: {username}"
                            )
                            
                            copy_message(chat_id, msg["message_id"], caption)
                            send_message(chat_id, "تم استلام مشاركتك ونشرها عند المشرفين بنجاح. جزاك الله خيراً! لرفع مشاركة أخرى أرسل /start")
                            user_states[chat_id] = {"step": "none"}
                            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
