import os
import logging
import subprocess
import random
import importlib
import sys
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ---------------------------------------------------------
# المرحلة الأولى: إعداد البيئة وتثبيت الملحقات (FFmpeg)
# ---------------------------------------------------------
import importlib
import sys

try:
    ffmpeg_pkg = importlib.import_module("static_ffmpeg")
    ffmpeg_add_paths = getattr(ffmpeg_pkg, "add_paths", None)
    if callable(ffmpeg_add_paths):
        ffmpeg_add_paths()
    else:
        raise ImportError("static_ffmpeg does not provide add_paths")
except Exception:
    # Use the same Python interpreter to install the package, then import again.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "static-ffmpeg"])
    ffmpeg_pkg = importlib.import_module("static_ffmpeg")
    ffmpeg_add_paths = getattr(ffmpeg_pkg, "add_paths", None)
    if callable(ffmpeg_add_paths):
        ffmpeg_add_paths()

# تكوين ثوابت: احصل عليها من المتغيرات البيئية لتجنب أخطاء NameError
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID") or 0)
BOT_NAME = os.getenv("BOT_NAME", "لولي")

USER_FILE = "users.txt"
DOWNLOADS_DIR = "downloads"

# إعداد السجلات (Logging) لمراقبة أداء "لولي"
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("LolyBot")
# القيمة True تعني أن الترفيه يعمل، و False تعني أنه معطل
entertainment_enabled = True

def ensure_downloads():
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
def untrack(update, context):
    # حماية المطور: التأكد أنك أنت من يرسل الأمر 🔐
        if update.effective_user.id != DEVELOPER_ID:
            return # هذه الكلمة يجب أن تكون مزاحة بمسافتين (2 Tabs) عن بداية السطر

    try:
        # تحويل النص المكتوب بعد الأمر إلى رقم (ID) 🆔
        target_id = int(context.args[0])
        
        if target_id in tracked_users:
            tracked_users.remove(target_id)
            update.message.reply_text(f"✅ تم إلغاء مراقبة الحساب: {target_id}")
        else:
            update.message.reply_text("⚠️ هذا الحساب غير موجود في قائمة المراقبة.")
            
    except (IndexError, ValueError):
        update.message.reply_text("❌ يرجى كتابة الآيدي بشكل صحيح بعد الأمر.\nمثال: /untrack 123456 ")

def give_nickname(update, context):
    # 1. التأكد أن المستخدم قام بالرد على رسالة شخص آخر
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        giver_user = update.effective_user
        
        # 2. اختيار لقب عشوائي من القائمة التي جهزناها سابقاً
        random_nickname = random.choice(nicknames_list)
        
        # 3. صياغة الرسالة
        response = (
            f"🎁 قام {giver_user.first_name} بإهداء لقب لـ {target_user.first_name}\n"
            f"✨ اللقب هو: {random_nickname}"
        )
        
        update.message.reply_text(response, parse_mode='Markdown')
    else:
        update.message.reply_text("الرجاء الرد على رسالة الشخص الذي تريد إهداءه لقباً! 🎯")
        def button_callback(update, context):
    query = update.callback_query
    data = query.data
    
    # إشعار التليجرام بأن الضغطة تمت بنجاح
    query.answer()

    if data == 'admin_list':
        # عرض أوامر الإشراف مع زر للعودة
        admin_text = (
            "👮 قائمة أوامر الإشراف:\n\n"
            "• /pin : تثبيت رسالة (بالرد عليها) 📌\n"
            "• /muteall : كتم العضو تماماً 🤐\n"
            "• /unmute : فك كتم العضو 🔓\n"
            "• /kick : طرد العضو من المجموعة 👞\n"
            "• /clean : تنظيف الملفات المؤقتة 🧹"
        )
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة", callback_data='main_menu')]]
        query.edit_message_text(text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data == 'fun_list':
        # عرض أوامر الترفيه بناءً على حالة المفتاح
        if entertainment_enabled:
            fun_text = (
                "🎮 قائمة أوامر الترفيه:\n\n"
                "• /give : إهداء لقب عشوائي لصديق 🎁\n"
                "• /stats : عرض إحصائياتك 📊\n"
                "• /play : تشغيل موسيقى (إذا كان مدعوماً) 🎵"
            )
        else:
            fun_text = "🚫 عذراً: أوامر الترفيه معطلة حالياً من قبل الإدارة."
            
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة", callback_data='main_menu')]]
        query.edit_message_text(text=fun_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data == 'main_menu':
        # العودة للواجهة الأساسية التي صممناها سابقاً
        # سنعيد إرسال نفس أزرار القائمة الرئيسية
        query.edit_message_text(
            text="✨ أهلاً بك في لوحة تحكم لولي!\nإختر القسم الذي تريد استكشافه:",
            reply_markup=main_menu_keyboard() # نفترض أننا وضعنا الأزرار في دالة منفصلة
        )
def track(update, context):
    # 🔐 حماية: التأكد أنك المطور (المعرف مسحوب من Railway)
    if update.effective_user.id != DEVELOPER_ID:
        return 

    try:
        # أخذ الرقم الذي كتبته بعد الأمر /track
        target_id = int(context.args[0])
        
        if target_id not in tracked_users:
            tracked_users.append(target_id)
            update.message.reply_text(f"🎯 تم إضافة {target_id} لليستة.")
        else:
            update.message.reply_text("موجود أصلاً.")
            
    except (IndexError, ValueError):
        # في حال لم تكتب رقماً بعد الأمر
        update.message.reply_text("اكتب الأيدي كذا: /track 12345")
def log_user(user_id):
    """حفظ آيدي المستخدم الجديد"""
    if not os.path.exists(USER_FILE):
        open(USER_FILE, "w").close()

    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()

    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(f"{user_id}\n")
from telegram import ChatPermissions

def mute_all(update, context):
    # 👮 التأكد من أن المنفذ هو مشرف
    user_status = context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id).status
    if user_status not in ['administrator', 'creator']:
        return 

    # 🎯 التحقق من وجود رد على رسالة الشخص المستهدف
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        
        # 🚫 ضبط كافة الصلاحيات على False
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        # ⛓️ تطبيق القيود
        context.bot.restrict_chat_member(update.effective_chat.id, target_id, permissions=permissions)
        update.message.reply_text("🚫 تم إلغاء كافة صلاحيات العضو بنجاح.")
    else:
        update.message.reply_text("يرجى الرد على رسالة العضو لإلغاء صلاحياته.")
def stats(update: Update, context: CallbackContext):
    """عرض عدد المستخدمين للمطور فقط"""
    if not update.effective_user or update.effective_user.id != DEVELOPER_ID:
        return

    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            count = len(f.read().splitlines())
        update.message.reply_text(f"📊 إحصائيات لولي:\nعدد المستخدمين: {count}")
    else:
        update.message.reply_text("📊 لا يوجد مستخدمين بعد.")
def pin_message(update, context):
    # 1. التأكد من أن مرسل الأمر مشرف 🛡️
    user_id = update.effective_user.id
    user_status = context.bot.get_chat_member(update.effective_chat.id, user_id).status
    if user_status not in ['administrator', 'creator'] and user_id != DEVELOPER_ID:
        return 

    # 2. التحقق من وجود رد على الرسالة المراد تثبيتها 📌
    if update.message.reply_to_message:
        message_id = update.message.reply_to_message.message_id
        
        # تنفيذ التثبيت
        try:
            context.bot.pin_chat_message(update.effective_chat.id, message_id)
            update.message.reply_text("📌 تم تثبيت الرسالة بنجاح.")
        except Exception as e:
            update.message.reply_text(f"❌ حدث خطأ: {e}")
    else:
        update.message.reply_text("يرجى الرد على الرسالة التي تريد تثبيتها!")
def broadcast(update: Update, context: CallbackContext):
    """إرسال رسالة للجميع (للمطور فقط)"""
    if not update.effective_user or update.effective_user.id != DEVELOPER_ID:
        return

    if not context.args:
        update.message.reply_text("استخدم: /broadcast رسالة هنا")
        return

    message = " ".join(context.args)
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            users = f.read().splitlines()
        for uid in users:
            try:
                context.bot.send_message(chat_id=int(uid), text=message)
            except Exception:
                continue
    update.message.reply_text("✅ تم إرسال الرسالة إلى جميع المستخدمين.")
from telegram import ChatPermissions

def unmute_user(update, context):
    # 👮 التأكد من أن المنفذ هو مشرف في المجموعة
    user_status = context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id).status
    if user_status not in ['administrator', 'creator']:
        return 

    # 🎯 التحقق من وجود رد على رسالة العضو المراد فك تقييده
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        
        # ✅ إعادة تفعيل كافة الصلاحيات
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_invite_users=True
        )
        
        # 🔓 تنفيذ فك التقييد
        context.bot.restrict_chat_member(update.effective_chat.id, target_id, permissions=permissions)
        update.message.reply_text("✅ تم فك التقييد عن العضو، يمكنه الآن التفاعل.")
    else:
        update.message.reply_text("يرجى الرد على رسالة العضو لفك تقييده.")
def start(update: Update, context: CallbackContext):
    """دالة الترحيب الخاصة بالبوت لولي"""
    user = update.effective_user
    if user:
        user_name = user.first_name or "صديقي"
        log_user(user.id)
    else:
        user_name = "صديقي"

    welcome_text = (
        f"أهلاً بك يا {user_name}! ✨\n"
        f"أنا صديقتك {BOT_NAME}.\n\n"
        "أستطيع تحميل الصوتيات من اليوتيوب وبجودة عالية.\n"
        "فقط أرسل لي: /play متبوعاً باسم المقطع."
    )
    update.message.reply_text(welcome_text)
def toggle_fun(update, context):
    global entertainment_enabled
    
    # 👮 التأكد من أن المستخدم مشرف
    user_status = context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id).status
    if user_status not in ['administrator', 'creator']:
        return

    command = update.message.text.split()[0] # الحصول على اسم الأمر
    
    if "disable" in command:
        entertainment_enabled = False
        update.message.reply_text("🚫 تم تعطيل أوامر الترفيه في هذه المجموعة.")
    else:
        entertainment_enabled = True
        update.message.reply_text("✅ تم تفعيل أوامر الترفيه مرة أخرى!")
def admin_help(update: Update, context: CallbackContext):
    """دليل أوامر المطور"""
    if not update.effective_user or update.effective_user.id != DEVELOPER_ID:
        return

    help_text = (
        "🛠 لوحة تحكم لولي:\n\n"
        "📊 /stats - لعرض عدد المستخدمين\n"
        "📢 /broadcast - لإرسال رسالة للجميع\n"
        "🧹 /clean - لتنظيف الملفات المؤقتة"
    )
    update.message.reply_text(help_text)
def smart_responses(update: Update, context: CallbackContext):
    """نظام الردود التلقائية الذكي"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user_name = update.effective_user.first_name if update.effective_user else "صديقي"

    replies = {
        "مرحبا": f"وعليكم السلام ورحمة الله وبركاته يا {user_name} ✨، كيف يمكن لـ {BOT_NAME} مساعدتك؟",
        "شكرا": "العفو! هذا واجبي دائماً 🎀",
        "لولي": "نعم! أنا هنا، هل تريدين تحميل مقطع جديد؟ 🎶",
        "تحبك": "وأنا أحبكم جميعاً! شكراً لثقتكم بـ لولي 💖",
    }

    for key, response in replies.items():
        if key in text:
            update.message.reply_text(response)
            return

def clean_files(update: Update, context: CallbackContext):
    """تنظيف مجلد التحميلات يدوياً (للمطور فقط)"""
    if not update.effective_user or update.effective_user.id != DEVELOPER_ID:
        return

    if os.path.exists(DOWNLOADS_DIR):
        import shutil
        shutil.rmtree(DOWNLOADS_DIR, ignore_errors=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    update.message.reply_text("✅ تم تنظيف السيرفر وحذف جميع الملفات المؤقتة.")

def games(update: Update, context: CallbackContext):
    """لعبة حجر ورقة مقص أو رمي النرد"""
    if not update.message or not update.message.text:
        return

    cmd = update.message.text
    if "نرد" in cmd:
        score = random.randint(1, 6)
        try:
            update.message.reply_dice()
        except Exception:
            pass
        update.message.reply_text(f"حظك اليوم هو: {score} 🎲")
    elif "حظي" in cmd:
        fortunes = ["يومك سعيد جداً 🌟", "ستسمع خبراً جميلاً 🌸",
                    "تحلَّ بالصبر قليلاً ⏳", "مفاجأة في الطريق إليك 🎁"]
        update.message.reply_text(f"توقعي لكِ اليوم: {random.choice(fortunes)}")


def play_music(update: Update, context: CallbackContext):
    """دالة البحث والتحميل والمعالجة الحقيقية"""
    query = " ".join(context.args or [])
    if not query:
        update.message.reply_text(f"💡 من فضلك، أخبري {BOT_NAME} ماذا تريدين أن تسمعي؟\nمثال: /play save your tears", parse_mode='Markdown')
        return

    progress_msg = update.message.reply_text(f"🔍 {BOT_NAME} تبحث الآن... يرجى الانتظار ثوانٍ.")
    ensure_downloads()

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'outtmpl': f'{DOWNLOADS_DIR}/%(title)s.%(ext)s',
    }

    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info)
            
        update.message.reply_audio(
            audio=open(file_path, 'rb'),
            title=info.get('title', 'Audio'),
            caption=f"تم التحميل بواسطة {BOT_NAME} 🎀"
        )
        
        if os.path.exists(file_path):
            os.remove(file_path) # تنظيف تلقائي فورياً
        progress_msg.delete()
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text(f"❌ اعتذر منكِ، واجهتُ مشكلة في التحميل.\nالسبب: {str(e)}")

def main():
    if not BOT_TOKEN:
        print("❌ خطأ: BOT_TOKEN غير موجود!")
        return

    ensure_downloads()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(CommandHandler("track", track))
    dp.add_handler(CommandHandler("untrack", untrack))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("pin", pin_message))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CommandHandler("enable_fun", toggle_fun))
    dp.add_handler(CommandHandler("disable_fun", toggle_fun))
    dp.add_handler(CommandHandler("clean", clean_files))
    dp.add_handler(CommandHandler("admin", admin_help))
    dp.add_handler(CommandHandler("give", give_nickname))
    dp.add_handler(CommandHandler("play", play_music))
    dp.add_handler(CommandHandler("muteall", mute_all))
    dp.add_handler(MessageHandler(Filters.regex(r'(نرد|حظي)'), games))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, smart_responses))
    dp.add_handler(CommandHandler("unmute", unmute_user))
    print(f"🚀 {BOT_NAME} جاهزة للعمل الآن!")
    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()










