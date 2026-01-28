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
# ID пользователей, на которых бот реагирует всегда
# -------------------------
SPAMMER_IDS = {
    1630418047,   # поменяй на нужные user_id
    987654321
}

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

    user_id = message.from_user.id
    text = message.text  # может быть None

    # Бот отвечает:
    # 1) любому через /
    # 2) любому сообщению от пользователей из SPAMMER_IDS
    if (text and text.startswith("/")) or (user_id in SPAMMER_IDS):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": text or ""}],
                model="llama-3.1-8b-instant",
            )

            choice = completion.choices[0] if completion.choices else None
            content = getattr(choice.message, "content", None) if choice else None
            reply = content or "⚠️ Groq вернул пустой ответ"

            bot.send_message(message.chat.id, reply)
            print(f"✅ Ответ отправлен пользователю {user_id}")

        except Exception as e:
            print("Ошибка Groq:", e)
            bot.send_message(message.chat.id, "⚠️ Ошибка обработки сообщения")

    else:
        # все остальные игнорируются
        return

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
