import os
import telebot
from groq import Groq
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render даёт автоматически

bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_KEY)

app = Flask(__name__)

# --- Telegram handler ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка обробки повідомлення")
        print(e)

# --- Webhook endpoint ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# --- Health check ---
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook встановлено")
    app.run(host="0.0.0.0", port=PORT)

