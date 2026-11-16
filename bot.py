import telebot
from google import genai
import os
import threading
from flask import Flask

# 1. إعداد الخادم الوهمي
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

# 2. جلب المفاتيح من الاستضافة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 3. إعداد Gemini (المكتبة الجديدة)
client = genai.Client(api_key=GEMINI_API_KEY)

# 4. إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا جاهز للعمل باستخدام أحدث وأقوى نموذج من Gemini.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # استخدام أقوى نموذج حالي (Gemini 2.5 Flash)
        response = client.models.generate_content(
            model='model=gemini-3.8-flash',
            contents=message.text
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        error_message = f"فشل الاتصال بـ Gemini ⚠️\n\nالسبب الدقيق:\n{str(e)}"
        bot.reply_to(message, error_message)

def run_bot():
    print("جاري تشغيل البوت...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)