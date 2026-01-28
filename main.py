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
# Тригер-имя бота
# -------------------------
TRIGGER_NAME = "Шпиндель:"

# -------------------------
# Обработчик сообщений с триггером
# -------------------------
@bot.message_handler(func=lambda message: message.text and message.text.startswith(TRIGGER_NAME))
def handle_trigger(message):
    if message.from_user.is_bot:
        return  # игнорируем сообщения от других ботов

    # убираем триггер из текста
    text = message.text[len(TRIGGER_NAME):].strip()
    if not text:
        bot.send_message(message.chat.id, f"⚠️ Напиши питання після '{TRIGGER_NAME}'")
        return

    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": text}],
            model="llama-3.1-8b-instant",
        )

        choice = completion.choices[0] if completion.choices else None
        content = getattr(choice.message, "content", None) if choice else None

        if content:
            bot.send_message(message.chat.id, content)
        else:
            bot.send_message(message.chat.id, "⚠️ Groq вернув пусту відповідь")

        print("✅ Ответ отправлен")

    except Exception as e:
        print("Помилка Groq:", e)
        bot.send_message(message.chat.id, "⚠️ Сталася помилка при обробці повідомлення")

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
