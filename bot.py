import telebot
from google import genai
from google.genai import types # استدعاء مكتبة الإعدادات لإضافة الشخصية
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا جاهز لمساعدتك.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    # --------------------------------------------------------
    # هنا تقوم بتعريف شخصية البوت (عدل هذا النص كما تحب)
    # --------------------------------------------------------
    my_system_prompt = """
    أنت بوت ذكاء اصطناعي ذكي ومفيد اسمك "نولان". 
    تمت برمجتك وتطويرك بواسطة المبرمج ( حسين عدنان عبد الأمام ).
    تحدث دائماً بأسلوب ودود، محترم، وواثق. 
    إذا سألك شخص عن هويتك أو من صنعك، أخبره باسمك واسم مبرمجك باعتزاز. 
    وأجب دائما باللهجة العراقية واستخدم الايموجيات في ردودك, ولا تجب بالتفصيل دائما الا عندما يطلب منك ذالك
    """
    
    try:
        # إرسال الرسالة مع دمج شخصية البوت (System Instruction)
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=message.text,
            config=types.GenerateContentConfig(
                system_instruction=my_system_prompt
            )
        )
        if response and response.text:
            bot.reply_to(message, response.text)
    except Exception as e:
        error_message = f"تعذر الرد حالياً ⚠️\n\nالسبب:\n{str(e)}"
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