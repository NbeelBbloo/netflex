import telebot
from telebot import types
from playwright.sync_api import sync_playwright
import os

# جلب التوكن والبروكسي من متغيرات البيئة في Railway بدلاً من كتابتها هنا
TOKEN = os.getenv('BOT_TOKEN')
PROXY_URL = os.getenv('PROXY_URL')

# التأكد من أن التوكن موجود لتجنب توقف الكود
if not TOKEN:
    raise ValueError("❌ لم يتم العثور على التوكن! يرجى إضافته في متغيرات Railway تحت اسم BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# تفعيل البروكسي افتراضياً فقط إذا قمت بإضافته في Railway
USE_PROXY = True if PROXY_URL else False

def get_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # تحديد النص المعروض حسب وجود البروكسي
    if PROXY_URL:
        proxy_status_text = "🟢 مفعّل (عراقي)" if USE_PROXY else "🔴 معطّل (IP السيرفر)"
    else:
        proxy_status_text = "⚠️ لا يوجد بروكسي (يجب إضافته في Railway)"
        
    btn_fetch = types.InlineKeyboardButton("🔄 جلب البيانات من نتفليكس", callback_data="fetch_netflix")
    btn_toggle = types.InlineKeyboardButton(f"🌐 حالة البروكسي: {proxy_status_text}", callback_data="toggle_proxy")
    btn_check_ip = types.InlineKeyboardButton("🔍 فحص الـ IP الحالي للمتصفح", callback_data="check_ip")
    keyboard.add(btn_fetch, btn_toggle, btn_check_ip)
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "🇮🇶 **مرحباً بك في بوت نتفليكس (نسخة المتغيرات الآمنة)!**\n\nيمكنك التحكم بالبروكسي وجلب البيانات عبر الأزرار أدناه."
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global USE_PROXY
    if call.data == "toggle_proxy":
        if not PROXY_URL:
            bot.answer_callback_query(call.id, "❌ لا يمكن التفعيل: لم تقم بإضافة متغير PROXY_URL في Railway", show_alert=True)
            return
            
        USE_PROXY = not USE_PROXY
        bot.answer_callback_query(call.id, f"تم التغيير إلى: {'مفعّل 🟢' if USE_PROXY else 'معطّل 🔴'}")
        try:
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_keyboard())
        except: pass
            
    elif call.data == "fetch_netflix":
        bot.answer_callback_query(call.id, "جاري فتح المتصفح...")
        msg = bot.send_message(call.message.chat.id, "⏳ جاري الاتصال بموقع نتفليكس...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                if USE_PROXY and PROXY_URL:
                    context = browser.new_context(proxy={"server": PROXY_URL}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                else:
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    
                page = context.new_page()
                page.goto('https://www.netflix.com/clearcookies', timeout=40000)
                page.wait_for_load_state('networkidle')
                text_result = page.inner_text('body')
                
                if not text_result.strip(): text_result = "⚠️ الصفحة فارغة من النص المرئي."
                final_text = f"📋 **النتيجة:**\n\n{text_result[:3800]}"
                bot.edit_message_text(final_text, chat_id=call.message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
                browser.close()
        except Exception as e:
            bot.edit_message_text(f"❌ **خطأ:**\n`{e}`", chat_id=call.message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
            
    elif call.data == "check_ip":
        bot.answer_callback_query(call.id, "جاري فحص الـ IP...")
        msg = bot.send_message(call.message.chat.id, "🔎 جاري فحص الـ IP...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(proxy={"server": PROXY_URL}) if (USE_PROXY and PROXY_URL) else browser.new_context()
                page = context.new_page()
                page.goto('https://ipapi.co/json/', timeout=20000)
                ip_info = page.inner_text('body')
                bot.edit_message_text(f"🌐 **معلومات الـ IP:**\n```json\n{ip_info}\n```", chat_id=call.message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
                browser.close()
        except Exception as e:
            bot.edit_message_text(f"❌ **فشل الفحص:**\n`{e}`", chat_id=call.message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

bot.polling(none_stop=True)
