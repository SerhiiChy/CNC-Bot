import os
import telebot
from groq import Groq
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Цей блок необхідний Render для перевірки працездатності порту
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Запуск сервера перевірки у фоновому потоці
threading.Thread(target=run_health_check_server, daemon=True).start()

# Основний код бота
bot = telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN'))
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

print("Бот запущений!")
bot.infinity_polling()
