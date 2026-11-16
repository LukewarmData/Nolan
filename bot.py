import telebot
import google.generativeai as genai
import os
import threading
from flask import Flask

# 1. إعداد الخادم الوهمي
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

# 2. جلب المفاتيح مع تنظيفها من المسافات المخفية (strip)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 3. إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 4. إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا جاهز للعمل.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # إظهار حالة "يكتب..." للمستخدم
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        # إرسال الخطأ الحقيقي للمستخدم بدلاً من رسالة عامة
        error_message = f"فشل الاتصال بـ Gemini ⚠️\n\nالسبب الدقيق:\n{str(e)}"
        bot.reply_to(message, error_message)

# 5. تشغيل البوت وتجاهل الرسائل القديمة العالقة
def run_bot():
    print("جاري تشغيل البوت...")
    bot.infinity_polling(skip_pending=True)

# 6. التشغيل المزدوج (الخادم والبوت)
if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)