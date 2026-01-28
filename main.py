import os
import telebot
from groq import Groq
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# 1. СУВОРО ДЛЯ RENDER: ЦЕЙ БЛОК ВІДКРИВАЄ ПОРТ
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_check():
    # Render автоматично підставляє PORT, ми його просто беремо
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Сервер перевірки запущено на порту {port}")
    httpd.serve_forever()

# Запускаємо сервер у фоні, щоб він не заважав боту
threading.Thread(target=run_health_check, daemon=True).start()

# 2. ВАШ БОТ
token = os.environ.get('TELEGRAM_TOKEN')
groq_key = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(token)
client = Groq(api_key=groq_key)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Помилка: {e}")

print("Бот офіційно запущений!")
bot.infinity_polling()
