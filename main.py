import os
import telebot
from groq import Groq

# Отримуємо ключі з секретів системи
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Бот відповідає на команди або згадування (оскільки Privacy Mode увімкнено)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ти — корисний асистент на базі Llama 3. Відповідай українською мовою."},
                {"role": "user", "content": message.text}
            ],
            model="llama3-8b-8192",
        )
        response = chat_completion.choices[0].message.content
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Бот запущений...")
    bot.infinity_polling()
