import telebot
from google import genai
from google.genai import types
import os
import threading
import time
from flask import Flask

# 1. إعداد الخادم الوهمي لمنصة Render
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت يعمل بشخصيته الجديدة بنجاح 24/7!"

# 2. جلب المفاتيح من بيئة الاستضافة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 3. إعداد الاتصال
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --------------------------------------------------------
# شخصية البوت (عدل هذا النص كما تحب)
# --------------------------------------------------------
# --------------------------------------------------------
    # هنا تقوم بتعريف شخصية البوت (عدل هذا النص كما تحب)
    # --------------------------------------------------------
MY_SYSTEM_PROMPT = """
    أنت بوت ذكاء اصطناعي واسمك "نولان". 
    تمت برمجتك بواسطة المبرمج ( حسين عدنان عبد الأمام ).
    إذا سألك من صنعك، أخبره باسم مبرمجك . 
    وأجب باللهجة دائما العراقية, واستخدم الايموجيات في الردود عند الحاجة, ولا تجب بالتفصيل الا عندما يطلب منك ذالك
    """
    

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا نولان، جاهز لمساعدتك.")

@bot.message_handler(content_types=['text'])
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=message.text,
            config=types.GenerateContentConfig(
                system_instruction=MY_SYSTEM_PROMPT
            )
        )
        
        if response and response.text:
            reply_text = response.text
            # تقسيم الرسالة تلقائياً إذا تجاوزت حد تليجرام (4096 حرف)
            for i in range(0, len(reply_text), 4000):
                bot.reply_to(message, reply_text[i:i+4000])
        else:
            bot.reply_to(message, "لم أتمكن من توليد رد لهذه الرسالة، جرب صياغتها بطريقة أخرى.")
            
    except Exception as e:
        try:
            error_message = f"تعذر الرد حالياً ⚠️\n\nالسبب:\n{str(e)[:1000]}"
            bot.reply_to(message, error_message)
        except Exception as send_err:
            print(f"فشل إرسال رسالة الخطأ: {send_err}")

# تشغيل البوت مع إعادة تشغيل تلقائية في حال انقطاع الاتصال
def run_bot():
    print("جاري تشغيل البوت...")
    while True:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.infinity_polling(
                skip_pending=True,
                timeout=20,
                long_polling_timeout=20
            )
        except Exception as e:
            print(f"توقف البوت بسبب خطأ، سيتم إعادة التشغيل بعد 5 ثوانٍ: {e}")
            time.sleep(5)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)