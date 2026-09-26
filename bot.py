import os
import time
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# تشغيل خادم ويب وهمي لتلبية شروط منصة Render وإبقاء البوت قيد التشغيل
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# بدء خادم الويب في خلفية الكود
t = threading.Thread(target=run_web_server)
t.daemon = True
t.start()

# كود بوت تيليجرام
TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"

print("Telegram bot polling started...")

last_update_id = 0

while True:
    try:
        req = urllib.request.Request(f"{URL}/getUpdates?offset={last_update_id + 1}&timeout=30")
        with urllib.request.urlopen(req, timeout=40) as response:
            data = json.loads(response.read().decode())
            
            if "result" in data:
                for update in data["result"]:
                    last_update_id = update["update_id"]
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        user_name = update["message"]["from"].get("first_name", "مستخدم")
                        
                        if text == "/start":
                            reply_text = f"مرحباً بك {user_name}! يعمل البوت الآن بنجاح تام من الاستضافة السحابية."
                        else:
                            reply_text = "أهلاً بك، لقد تلقيت رسالتك بنجاح!"
                            
                        payload = json.dumps({
                            "chat_id": chat_id,
                            "text": reply_text
                        }).encode('utf-8')
                        
                        send_req = urllib.request.Request(
                            f"{URL}/sendMessage",
                            data=payload,
                            headers={'Content-Type': 'application/json'}
                        )
                        urllib.request.urlopen(send_req)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
