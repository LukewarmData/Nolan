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
    return "البوت يعمل بنجاح 24/7!"

# 2. جلب المفاتيح من بيئة الاستضافة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 3. إعداد الاتصال
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# تخزين معرف البوت مرة واحدة لتسريع التحقق من الردود
BOT_ID = None

# --------------------------------------------------------
# إعدادات الستكر (اتركه فارغاً "" إذا لا تريد ستكر حالياً)
# أرسل أي ستكر للبوت في الخاص ليطبع لك رمزه
# --------------------------------------------------------
HELP_STICKER_ID = ""

# شخصية البوت
# --------------------------------------------------------
    # هنا تقوم بتعريف شخصية البوت (عدل هذا النص كما تحب)
    # --------------------------------------------------------
MY_SYSTEM_PROMPT = """
    أنت بوت ذكاء اصطناعي ذكي ومفيد اسمك "نولان". 
    تمت برمجتك وتطويرك بواسطة المبرمج ( حسين عدنان عبد الأمام ).
    تحدث دائماً بأسلوب ودود، محترم، وواثق. 
    إذا سألك شخص عن هويتك أو من صنعك، أخبره باسمك واسم مبرمجك باعتزاز. 
    وأجب دائما باللهجة العراقية واستخدم الايموجيات في ردودك, ولا تجب بالتفصيل دائما الا عندما يطلب منك ذالك
    """
    

# الكلمات التي تعتبر مناداة باسمه فقط
CALL_ONLY_PHRASES = {
    "نولان", "يا نولان", "يانولان",
    "nolan", "hey nolan", "hi nolan"
}

def get_bot_id():
    global BOT_ID
    if BOT_ID is None:
        BOT_ID = bot.get_me().id
    return BOT_ID

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا نولان، جاهز لمساعدتك.")

# استخراج رمز الستكر (في الخاص فقط)
@bot.message_handler(content_types=['sticker'])
def get_sticker_id(message):
    if message.chat.type == 'private':
        file_id = message.sticker.file_id
        bot.reply_to(
            message,
            f"هذا هو رمز الستكر (file_id):\n\n`{file_id}`\n\nانسخه وضعه في متغير HELP_STICKER_ID داخل الكود.",
            parse_mode="Markdown"
        )

@bot.message_handler(content_types=['text'])
def handle_message(message):
    try:
        text = message.text.strip()
        text_lower = text.lower()
        is_group = message.chat.type in ['group', 'supergroup']
        prompt_to_send = text

        if is_group:
            # 1) التحقق: هل الرسالة عبارة عن مناداة باسمه فقط؟
            if text_lower in CALL_ONLY_PHRASES:
                bot.reply_to(message, "نعم، أنا هنا! 👋 هل تحتاج إلى مساعدة في شيء ما؟")
                if HELP_STICKER_ID:
                    bot.send_sticker(message.chat.id, HELP_STICKER_ID)
                return

            # 2) التحقق: هل الرسالة رد (Reply) على رسالة سابقة للبوت؟
            replied_to_bot = (
                message.reply_to_message is not None
                and message.reply_to_message.from_user is not None
                and message.reply_to_message.from_user.id == get_bot_id()
            )

            # إذا لم تكن مناداة باسمه فقط ولم تكن رداً على رسالته -> يتجاهلها تماماً
            if not replied_to_bot:
                return

            # تمرير رسالة البوت السابقة كسياق ليفهم Gemini على ماذا يرد المستخدم
            previous_bot_text = message.reply_to_message.text or ""
            if previous_bot_text:
                prompt_to_send = f"رسالتك السابقة كانت: \"{previous_bot_text}\"\nرد المستخدم عليها الآن: {text}"

        # إرسال الرسالة إلى Gemini (في الخاص أو عند الرد على البوت في المجموعة)
        bot.send_chat_action(message.chat.id, 'typing')

        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt_to_send,
            config=types.GenerateContentConfig(
                system_instruction=MY_SYSTEM_PROMPT
            )
        )

        if response and response.text:
            reply_text = response.text
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

def run_bot():
    print("جاري تشغيل البوت...")
    while True:
        try:
            bot.remove_webhook()
            time.sleep(1)
            get_bot_id()
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