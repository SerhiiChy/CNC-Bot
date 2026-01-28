import os
import telebot
from groq import Groq
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- ЦЕЙ БЛОК ДЛЯ RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
# --- КІНЕЦЬ БЛОКУ ДЛЯ RENDER ---

# Далі ваш звичайний код
token = os.environ.get('TELEGRAM_TOKEN')
groq_key = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(token)
client = Groq(api_key=groq_key)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Відповідай українською мовою."},
                {"role": "user", "content": message.text}
            ],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

print("Бот запущений...")
bot.infinity_polling()
