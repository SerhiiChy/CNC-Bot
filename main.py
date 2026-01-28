import os
import telebot
from groq import Groq
from flask import Flask, request

# -------------------------
# Переменные окружения
# -------------------------
TOKEN = os.environ.get("TELEGRAM_TOKEN")       # Telegram токен
GROQ_KEY = os.environ.get("GROQ_API_KEY")      # Groq ключ
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Публичный URL Render
PORT = int(os.environ.get("PORT", 8080))       # Порт Render

# -------------------------
# Инициализация
# -------------------------
bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_KEY)
app = Flask(__name__)

# -------------------------
# Обработчик всех сообщений Telegram
# -------------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.is_bot:
        return  # игнорируем сообщения от ботов

    try:
        # Отправка текста пользователя в Groq
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",  # модель
        )

        # Получаем ответ
        choice = completion.choices[0] if completion.choices else None
        content = getattr(choice.message, "content", None) if choice else None

        if content:
            bot.send_message(message.chat.id, content)
        else:
            bot.send_message(message.chat.id, "⚠️ Groq вернул пустой ответ")

        print("✅ Ответ отправлен")

    except Exception as e:
        print("Ошибка Groq:", e)
        bot.send_message(message.chat.id, "⚠️ Ошибка обработки сообщения")

# -------------------------
# Webhook endpoint
# -------------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# -------------------------
# Health check (для Render)
# -------------------------
@app.route("/", methods=["GET", "HEAD"])
def health():
    return "OK", 200

# -------------------------
# Запуск сервиса
# -------------------------
if __name__ == "__main__":
    bot.delete_webhook(drop_pending_updates=True)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook установлен")
    app.run(host="0.0.0.0", port=PORT)
