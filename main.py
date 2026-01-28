import os
import telebot
from groq import Groq
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ЦЕЙ БЛОК ОБМАНЮЄ RENDER, ЩОБ ВІН НЕ ВИМИКАВСЯ
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_server():
    # Беремо порт, який вимагає Render
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheck)
    httpd.serve_forever()

# Запускаємо сервер-обманку у фоні
threading.Thread(target=run_server, daemon=True).start()

# ТУТ ТВІЙ БОТ
bot = telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN'))
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

@bot.message_handler(func=lambda m: True)
def chat(message):
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama3-8b-8192"
        )
        bot.reply_to(message, res.choices[0].message.content)
    except Exception:
        pass

print("Бот готовий!")
bot.infinity_polling()
