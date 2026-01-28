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
# Обработчик команды /ask
# -------------------------
@bot.message_handler(commands=['ask'])
def handle_ask(message):
    # Игнорируем свои сообщения
    if message.from_user.is_bot:
        return

    # Берем текст после команды /ask
    text = message.text.replace('/ask', '').strip()
    if not text:
        bot.send_message(message.chat.id, "⚠️ Напиши вопрос после /ask")
        return

    try:
        # Отправка текста пользователя в Groq
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": text}],
            model="groq/compound",  # рабочая модель
        )

        # Безопасная проверка ответа
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
    # Удаляем старый webhook Telegram
    bot.delete_webhook(drop_pending_updates=True)

    # Устанавливаем новый webhook
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook установлен")

    # Запуск Flask
    app.run(host="0.0.0.0", port=PORT)
