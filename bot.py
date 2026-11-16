import telebot
from google import genai
import os
import threading
from flask import Flask

# إعداد الخادم الوهمي لمنصة Render
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

# جلب المفاتيح من بيئة الاستضافة مع تنظيفها من المسافات المخفية
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# إعداد اتصال Gemini باستخدام المكتبة الجديدة
client = genai.Client(api_key=GEMINI_API_KEY)

# إعداد اتصال البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# الرد على رسالة البدء /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا جاهز للعمل باستخدام أحدث وأقوى نموذج من Gemini.")

# معالجة الرسائل النصية
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # إظهار حالة "يكتب..." للمستخدم
        bot.send_chat_action(message.chat.id, 'typing')
        
        # استخدام الإصدار الأحدث بالصيغة الصحيحة
        response = client.models.generate_content(
            model='models/gemini-3.8-flash',
            contents=message.text
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        error_message = f"فشل الاتصال بـ Gemini ⚠️\n\nالسبب الدقيق:\n{str(e)}"
        bot.reply_to(message, error_message)

# تشغيل البوت وتجاهل الرسائل القديمة العالقة
def run_bot():
    print("جاري تشغيل البوت...")
    bot.infinity_polling(skip_pending=True)

# التشغيل المزدوج (الخادم والبوت معاً)
if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)