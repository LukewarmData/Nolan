import telebot
from google import genai
import os
import threading
import time
from flask import Flask

# إعداد الخادم الوهمي
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

# جلب المفاتيح من بيئة الاستضافة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# إعداد اتصال Gemini 
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا جاهز للعمل باستخدام أحدث نموذج.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    max_retries = 6 # عدد محاولات الاتصال
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='models/gemini-3.8-flash',
                contents=message.text
            )
            bot.reply_to(message, response.text)
            break # إذا نجح الاتصال، يكسر الحلقة ويوقف المحاولات
            
        except Exception as e:
            # إذا فشل، يتحقق هل هذه آخر محاولة؟
            if attempt < max_retries - 1:
                time.sleep(2) # ينتظر ثانيتين ثم يحاول بصمت مرة أخرى
            else:
                # إذا استنفد الـ 3 محاولات وفشل، يرسل الخطأ لك
                error_message = f"الخوادم عليها ضغط شديد حالياً ⚠️\nيرجى المحاولة بعد قليل."
                bot.reply_to(message, error_message)

def run_bot():
    print("جاري تشغيل البوت...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)