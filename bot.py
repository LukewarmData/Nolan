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
    return "البوت يعمل بشخصيته الجديدة وذاكرة المحادثات والصور والملفات بنجاح 24/7!"

# 2. جلب المفاتيح من بيئة الاستضافة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 3. إعداد الاتصال
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# متغير لتخزين معرّف البوت مرة واحدة لتسريع التحقق في المجموعات
BOT_ID = None

def get_bot_id():
    global BOT_ID
    if BOT_ID is None:
        BOT_ID = bot.get_me().id
    return BOT_ID

def should_reply(message):
    """التحقق مما إذا كان يجب على البوت الرد على هذه الرسالة"""
    # في الخاص: يرد على كل شيء طبيعي
    if message.chat.type == 'private':
        return True
    
    # في المجموعات: يرد فقط إذا كانت الرسالة رداً (Reply) على رسالة للبوت
    if message.chat.type in ['group', 'supergroup']:
        return (
            message.reply_to_message is not None
            and message.reply_to_message.from_user is not None
            and message.reply_to_message.from_user.id == get_bot_id()
        )
    
    return False

# --------------------------------------------------------
# شخصية البوت
# --------------------------------------------------------
MY_SYSTEM_PROMPT = """
أنت بوت ذكاء اصطناعي واسمك "نولان". 
تمت برمجتك بواسطة المبرمج ( حسين عدنان عبد الأمام ).
إذا سألك من صنعك، أخبره باسم مبرمجك . 
وأجب باللهجة العراقية, واستخدم الايموجيات في الردود عند الحاجة, ولا تجب بالتفصيل الا عندما يطلب منك ذالك
"""

# قاموس لحفظ جلسة المحادثة لكل مستخدم حسب الـ ID الخاص به
user_chats = {}

def get_user_chat(user_id):
    """جلب محادثة المستخدم الحالية أو إنشاء محادثة جديدة له"""
    if user_id not in user_chats:
        user_chats[user_id] = client.chats.create(
            model='gemini-3.5-flash-lite',
            config=types.GenerateContentConfig(
                system_instruction=MY_SYSTEM_PROMPT
            )
        )
    return user_chats[user_id]

def send_long_reply(message, reply_text):
    """تقسيم الرسالة تلقائياً إذا تجاوزت حد تليجرام (4096 حرف)"""
    for i in range(0, len(reply_text), 4000):
        bot.reply_to(message, reply_text[i:i+4000])

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "مرحباً! أنا نولان، جاهز لمساعدتك. 👋\n"
        "يمكنك إرسال نصوص، صور، أو ملفات (مثل PDF وملفات نصية) للنقاش حولها.\n"
        "(أرسل /reset إذا أردت مسح الذاكرة والبدء بمحادثة جديدة)"
    )

@bot.message_handler(commands=['reset'])
def reset_chat(message):
    user_id = message.from_user.id
    if user_id in user_chats:
        del user_chats[user_id]
    bot.reply_to(message, "تم مسح ذاكرة محادثتنا بنجاح! نبدأ من جديد 🔄")

# --------------------------------------------------------
# أمر المناداة /nolan (يعمل في المجموعات بدون صلاحية قراءة الرسائل)
# --------------------------------------------------------
@bot.message_handler(commands=['nolan'])
def handle_nolan_command(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        user_id = message.from_user.id
        chat = get_user_chat(user_id)
        
        # التحقق هل كتب المستخدم نصاً بعد /nolan أم ناداه فقط
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            prompt = parts[1].strip()
        else:
            prompt = "شخص ما ناداك باسمك فقط الآن، رد عليه برد عشوائي قصير وعفوي حسب شخصيتك واسأله شلون تكدر تساعده."
        
        response = chat.send_message(prompt)
        
        if response and response.text:
            send_long_reply(message, response.text)
        else:
            bot.reply_to(message, "ها عيني، موجود! شلون أگدر أساعدك؟ 👋")
            
    except Exception as e:
        try:
            error_message = f"تعذر الرد حالياً ⚠️\n\nالسبب:\n{str(e)[:1000]}"
            bot.reply_to(message, error_message)
        except Exception as send_err:
            print(f"فشل إرسال رسالة الخطأ: {send_err}")

# --------------------------------------------------------
# 1. معالجة الرسائل النصية
# --------------------------------------------------------
@bot.message_handler(content_types=['text'])
def handle_message(message):
    if not should_reply(message):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        user_id = message.from_user.id
        chat = get_user_chat(user_id)
        
        response = chat.send_message(message.text)
        
        if response and response.text:
            send_long_reply(message, response.text)
        else:
            bot.reply_to(message, "لم أتمكن من توليد رد لهذه الرسالة، جرب صياغتها بطريقة أخرى.")
            
    except Exception as e:
        try:
            error_message = f"تعذر الرد حالياً ⚠️\n\nالسبب:\n{str(e)[:1000]}"
            bot.reply_to(message, error_message)
        except Exception as send_err:
            print(f"فشل إرسال رسالة الخطأ: {send_err}")

# --------------------------------------------------------
# 2. معالجة الصور
# --------------------------------------------------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if not should_reply(message):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        user_id = message.from_user.id
        chat = get_user_chat(user_id)
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        prompt = message.caption if message.caption else "شنو موجود بهذه الصورة؟ اشرحلي باختصار."
        
        image_part = types.Part.from_bytes(
            data=downloaded_file,
            mime_type="image/jpeg"
        )
        
        response = chat.send_message([image_part, prompt])
        
        if response and response.text:
            send_long_reply(message, response.text)
        else:
            bot.reply_to(message, "ما گدرت أقرأ الصورة بشكل واضح، جرب ترسلها مرة ثانية.")
            
    except Exception as e:
        try:
            error_message = f"تعذر معالجة الصورة حالياً ⚠️\n\nالسبب:\n{str(e)[:1000]}"
            bot.reply_to(message, error_message)
        except Exception as send_err:
            print(f"فشل إرسال رسالة الخطأ: {send_err}")

# --------------------------------------------------------
# 3. معالجة الملفات (PDF, TXT, CSV, أكواد برمجية، إلخ)
# --------------------------------------------------------
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not should_reply(message):
        return

    try:
        doc = message.document
        
        if doc.file_size and doc.file_size > 20 * 1024 * 1024:
            bot.reply_to(message, "حجم الملف أكبر من 20 ميجابايت، تليجرام ما يسمح للبوت بتحميل ملفات بهذا الحجم ⚠️")
            return

        bot.send_chat_action(message.chat.id, 'typing')
        
        user_id = message.from_user.id
        chat = get_user_chat(user_id)
        
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        mime_type = doc.mime_type or "text/plain"
        file_name = doc.file_name or "ملف"
        
        prompt = message.caption if message.caption else f"اقرأ هذا الملف ({file_name}) ولخصلي محتواه باختصار."
        
        file_part = types.Part.from_bytes(
            data=downloaded_file,
            mime_type=mime_type
        )
        
        response = chat.send_message([file_part, prompt])
        
        if response and response.text:
            send_long_reply(message, response.text)
        else:
            bot.reply_to(message, "ما گدرت أقرأ محتوى هذا الملف، تأكد إنه بصيغة مدعومة مثل PDF أو ملف نصي.")
            
    except Exception as e:
        try:
            error_message = f"تعذر قراءة الملف حالياً ⚠️\n(تأكد إن الصيغة مدعومة مثل PDF أو TXT أو صور)\n\nالسبب:\n{str(e)[:1000]}"
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