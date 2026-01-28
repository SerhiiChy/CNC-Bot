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
SPAMMER_IDS = SPAMMER_IDS = {1630418047}

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
    text = getattr(message, "text", None)  # безопасно получаем текст

    # --- автоответ спамерам на любое сообщение ---
    if user_id in SPAMMER_IDS:
        try:
            # если есть текст, отправляем в Groq, иначе просто фиксированное сообщение
            content_to_send = ""
            if text:
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": text}],
                    model="llama-3.1-8b-instant",
                )
                choice = completion.choices[0] if completion.choices else None
                content_to_send = getattr(choice.message, "content", None) or "⚠️ Groq вернул пустой ответ"
            else:
                content_to_send = "🤖 Я вижу твоё сообщение!"

            bot.send_message(message.chat.id, content_to_send)
            print(f"✅ Ответ спамеру отправлен ({user_id})")
        except Exception as e:
            print("Ошибка Groq:", e)
            bot.send_message(message.chat.id, "⚠️ Ошибка обработки сообщения")
        return  # спамер обработан, дальше не идем

    # --- обычные команды через /
    if text and text.startswith("/"):
        bot.reply_to(message, "🤖 Команда принята")
        return

    # остальные пользователи — игнорируются
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
