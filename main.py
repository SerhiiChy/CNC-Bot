import os
import telebot
from groq import Groq
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8080))

TRIGGERS = ["шпиндель", "cnc", "gcode", "g-код", "чпу"]

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
client = Groq(api_key=GROQ_KEY)
app = Flask(__name__)

def reply_groq(message, text):
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ти чат-бот про ЧПУ та верстати. "
                    "Відповідай коротко (1–3 речення), по суті. "
                    "Додавай легкий технічний гумор."
                )
            },
            {"role": "user", "content": text}
        ],
        max_tokens=120,
        temperature=0.8
    )

    content = completion.choices[0].message.content
    bot.send_message(message.chat.id, content)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.is_bot:
        return

    text = message.text
    if not text:
        return

    chat_type = message.chat.type
    text_l = text.lower()

    # приват — завжди відповідаємо
    if chat_type == "private":
        reply_groq(message, text)
        return

    # група — тільки / або тригери
    if chat_type in ("group", "supergroup"):
        if text.startswith("/") or any(t in text_l for t in TRIGGERS):
            reply_groq(message, text)
        return

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET", "HEAD"])
def health():
    return "OK", 200

if __name__ == "__main__":
    bot.delete_webhook(drop_pending_updates=True)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
