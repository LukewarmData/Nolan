import telebot
import google.generativeai as genai
import os
import threading
from flask import Flask

# 1. إعداد Flask (الخادم الوهمي لـ Render)
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

# 2. جلب المفاتيح من بيئة الاستضافة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 3. إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 4. إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا بوت ذكاء اصطناعي مدعوم بـ Gemini.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "عذراً، حدث خطأ.")

# 5. دالة لتشغيل البوت في خيط (Thread) منفصل
def run_bot():
    print("البوت يعمل الآن...")
    bot.infinity_polling()

# 6. تشغيل الخادم والبوت معاً
if __name__ == "__main__":
    # تشغيل البوت في الخلفية
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # تشغيل خادم Flask (المنفذ يحدده Render تلقائياً)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)