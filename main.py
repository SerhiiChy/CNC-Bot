import os
import telebot
from groq import Groq
from flask import Flask, request, jsonify

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
# Обработчик сообщений Telegram
# -------------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Отправка текста пользователя в Groq
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
        )
        # Проверка ответа
        if completion.choices and completion.choices[0].message.content:
            bot.reply_to(message, completion.choices[0].message.content)
        else:
            bot.reply_to(message, "⚠️ Groq вернул пустой ответ")
        print("✅ Ответ отправлен")
    except Exception as e:
        # Логируем ошибку в Render
        print("Ошибка Groq:", e)
        bot.reply_to(message, "⚠️ Ошибка обработки сообщения")

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
    # Удаляем старый webhook Telegram
    bot.delete_webhook(drop_pending_updates=True)

    # Устанавливаем новый webhook
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook установлен")

    # Запуск Flask
    app.run(host="0.0.0.0", port=PORT)

