import os
import telebot
from groq import Groq
from flask import Flask, request

# -------------------------
# Переменные окружения
# -------------------------
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8080))

# -------------------------
# ID пользователей, на которых бот реагирует всегда
# -------------------------
SPAMMER_IDS = {}  # <-- твой ID

# -------------------------
# Инициализация
# -------------------------
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
client = Groq(api_key=GROQ_KEY)
app = Flask(__name__)

# -------------------------
# Обработчик сообщений
# -------------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.is_bot:
        return

    user_id = message.from_user.id
    text = getattr(message, "text", None)

    # реагируем ТОЛЬКО на нужных пользователей
    if user_id not in SPAMMER_IDS:
        return

    if not text:
        bot.send_message(message.chat.id, "🤖 Я текст люблю. Картинки — ні 🙂")
        return

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ти чат-бот про ЧПУ, верстати та виробництво. "
                        "Відповідай КОРОТКО (1–3 речення), але завершено. "
                        "Без списків і без води. "
                        "Додавай легкий технічний гумор або іронію, якщо доречно."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=120,
            temperature=0.8
        )

        choice = completion.choices[0] if completion.choices else None
        content = getattr(choice.message, "content", None) if choice else None

        if content:
            bot.send_message(message.chat.id, content)
            print(f"✅ Ответ отправлен пользователю {user_id}")
        else:
            bot.send_message(message.chat.id, "⚠️ Мозок ЧПУ завис, спробуй ще раз 😅")

    except Exception as e:
        print("Ошибка Groq:", e)
        bot.send_message(message.chat.id, "⚠️ Щось пішло не так. Навіть верстат так не лагає.")

# -------------------------
# Webhook endpoint
# -------------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200

# -------------------------
# Health check
# -------------------------
@app.route("/", methods=["GET", "HEAD"])
def health():
    return "OK", 200

# -------------------------
# Запуск
# -------------------------
if __name__ == "__main__":
    bot.delete_webhook(drop_pending_updates=True)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook установлен")
    app.run(host="0.0.0.0", port=PORT)

