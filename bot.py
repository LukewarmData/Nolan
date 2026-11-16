import telebot
from google import genai
import os
import threading
import time
from flask import Flask

# 1. إعداد الخادم الوهمي لمنصة Render
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت يعمل بنجاح 24/7!"

# 2. جلب المفاتيح من بيئة الاستضافة وتنظيفها من المسافات
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 3. إعداد الاتصال باستخدام المكتبة والنموذج الحديث
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! البوت يعمل الآن بنموذج Gemini 3.5 Flash-Lite.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=message.text
        )
        if response and response.text:
            bot.reply_to(message, response.text)
    except Exception as e:
        error_message = f"فشل الاتصال بـ Gemini ⚠️\n\nالسبب الدقيق:\n{str(e)}"
        bot.reply_to(message, error_message)

def run_bot():
    print("جاري تشغيل البوت...")
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)