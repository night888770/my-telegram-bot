import os
import logging
import subprocess
import random
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ---------------------------------------------------------
# المرحلة الأولى: إعداد البيئة وتثبيت الملحقات (FFmpeg)
# ---------------------------------------------------------
try:
    from static_ffmpeg import add_paths as ffmpeg_add_paths
    ffmpeg_add_paths()
except ImportError:
    # في حال عدم وجود المكتبة، يتم تثبيتها وتشغيلها لضمان عمل المعالج الصوتي
    subprocess.run(["pip", "install", "static-ffmpeg"])
    from static_ffmpeg import add_paths as ffmpeg_add_paths
    ffmpeg_add_paths()
USER_FILE = "users.txt"

def log_user(user_id):
    """حفظ آيدي المستخدم الجديد"""
    if not os.path.exists(USER_FILE):
        open(USER_FILE, "w").close()
    
    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()
    
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(f"{user_id}\n")

def stats(update: Update, context: CallbackContext):
    """عرض عدد المستخدمين للمطور فقط"""
    if update.effective_user.id != DEVELOPER_ID:
        return
    
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            count = len(f.read().splitlines())
        update.message.reply_text(f"📊 إحصائيات لولي:\nعدد المستخدمين: {count}")
    else:
        update.message.reply_text("📊 لا يوجد مستخدمين بعد.")
# إعداد السجلات (Logging) لمراقبة أداء "لولي"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("LolyBot")

# ---------------------------------------------------------
# المرحلة الثانية: استيراد بيانات الاعتماد من Railway
# ---------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))
BOT_NAME = "لولي"

# ---------------------------------------------------------
# المرحلة الثالثة: الدوال التشغيلية (Logic)
# ---------------------------------------------------------
def get_support_buttons():
    keyboard = [
        [InlineKeyboardButton("🌟 قيم البوت", url="https://t.me/BotFather")],
        [InlineKeyboardButton("👨‍💻 المطور", url=f"tg://user?id={DEVELOPER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)
def start(update: Update, context: CallbackContext):
    """دالة الترحيب الخاصة بالبوت لولي"""
    user_name = update.effective_user.first_name
    welcome_text = (
        f"أهلاً بك يا {user_name}! ✨\n"
        f"أنا صديقتك  {BOT_NAME}.\n\n"
        "أستطيع تحميل الصوتيات من اليوتيوب وبجودة عالية.\n"
        "فقط أرسل لي: /play متبوعاً باسم المقطع."
    )
    update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    def admin_help(update: Update, context: CallbackContext):
    """دليل أوامر المطور"""
    if update.effective_user.id != DEVELOPER_ID:
        return
    
    help_text = (
        "🛠 لوحة تحكم لولي:\n\n"
        "📊 /stats - لعرض عدد المستخدمين\n"
        "📢 /broadcast - لإرسال رسالة للجميع\n"
        "🧹 /clean - لتنظيف الملفات المؤقتة"
    )
    update.message.reply_text(help_text, parse_mode='Markdown')
    def smart_responses(update: Update, context: CallbackContext):
    """نظام الردود التلقائية الذكي"""
    text = update.message.text.lower()
    user_name = update.effective_user.first_name

    replies = {
        "مرحبا": f"وعليكم السلام ورحمة الله وبركاته يا {user_name} ✨، كيف يمكن لـ لولي مساعدتك؟",
        "شكرا": "العفو! هذا واجبي دائماً 🎀",
        "لولي": "نعم! أنا هنا، هل تريدين تحميل مقطع جديد؟ 🎶",
        "تحبك": "وأنا أحبكم جميعاً! شكراً لثقتكم بـ لولي 💖",
    }

    for key, response in replies.items():
        if key in text:
            update.message.reply_text(response)
            return
def clean_manual(update: Update, context: CallbackContext):
    """تنظيف الوسائط (للمطور ومشرفي القروبات)"""
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    # التحقق من الصلاحية: هل هو المطور؟
    is_developer = (user_id == DEVELOPER_ID)
    
    # التحقق من الصلاحية: هل هو مشرف في القروب؟
    is_admin = False
    if chat_type in ['group', 'supergroup']:
        member = context.bot.get_chat_member(update.effective_chat.id, user_id)
        if member.status in ['administrator', 'creator']:
            is_admin = True

    # إذا لم يكن مطوراً ولا مشرفاً، نرفض الطلب
    if not is_developer and not is_admin:
        update.message.reply_text("❌ عذراً، هذا الأمر مخصص للمطور ومشرفي المجموعة فقط.")
        return

    # تنفيذ عملية التنظيف
    folder = 'downloads'
    if os.path.exists(folder):
        try:
            shutil.rmtree(folder)
            os.makedirs(folder)
            update.message.reply_text("🗑️ تم تنظيف ذاكرة الوسائط بنجاح بواسطة إدارة لولي.")
        except Exception as e:
            update.message.reply_text(f"⚠️ حدث خطأ أثناء التنظيف: {e}")
    else:
        update.message.reply_text("📁 المجلد نظيف بالفعل.")
def clean_files(update: Update, context: CallbackContext):
    """تنظيف مجلد التحميلات يدوياً"""
    if update.effective_user.id != DEVELOPER_ID: return
    
    if os.path.exists("downloads"):
        import shutil
        shutil.rmtree("downloads")
        os.makedirs("downloads")
        update.message.reply_text("✅ تم تنظيف السيرفر وحذف جميع الملفات المؤقتة.")
        def games(update: Update, context: CallbackContext):
    """لعبة حجر ورقة مقص أو رمي النرد"""
    cmd = update.message.text.split()[0]
    
    if "نرد" in cmd:
        score = random.randint(1, 6)
        update.message.reply_dice() # يرسل إيموجي نرد متحرك حقيقي
        update.message.reply_text(f"حظك اليوم هو: {score} 🎲")
    
    elif "حظي" in cmd:
        fortunes = ["يومك سعيد جداً 🌟", "ستسمع خبراً جميلاً 🌸", "تحلَّ بالصبر قليلاً ⏳", "مفاجأة في الطريق إليك 🎁"]
        update.message.reply_text(f"توقعي لكِ اليوم: {random.choice(fortunes)}")
def play_music(update: Update, context: CallbackContext):
    """دالة البحث والتحميل والمعالجة"""
    query = " ".join(context.args)
    if not query:
        update.message.reply_text("💡 من فضلك، أخبر لولي ماذا تريدين أن تسمعي؟\nمثال: /play blinding lights")
        return

    progress_msg = update.message.reply_text(f"🔍 {BOT_NAME} تبحث الآن... يرجى الانتظار ثوانٍ.")

    # إعدادات yt-dlp الاحترافية لتجاوز الحظر (Error 403)
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0', # لتفادي مشاكل الـ IP
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # البحث عن أول نتيجة
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info)
            
        # إرسال الملف الصوتي للمستخدم
        update.message.reply_audio(
            audio=open(file_path, 'rb'),
            title=info.get('title', 'Audio'),
            caption=f"تم التحميل بواسطة {BOT_NAME} 🎀"
        )
        
        # تنظيف الذاكرة وحذف الملف بعد الإرسال
        if os.path.exists(file_path):
            os.remove(file_path)
        progress_msg.delete()

    except Exception as e:
        logger.error(f"Error in Loly: {e}")
        update.message.reply_text(f"❌ اعتذر منكِ، واجهتُ صعوبة في الوصول للمقطع.\nالسبب: {str(e)}")

# ---------------------------------------------------------
# المرحلة الرابعة: التشغيل الرئيسي (Main Entry)
# ---------------------------------------------------------

def main():
    if not BOT_TOKEN:
        print("❌ خطأ: BOT_TOKEN غير موجود في متغيرات Railway!")
        return

    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("broadcast", broadcast))
dp.add_handler(CommandHandler("clean", clean_manual))
    dp.add_handler(CommandHandler("admin", admin_help))

    # 3. الألعاب والردود (يجب أن تكون في النهاية)
    dp.add_handler(MessageHandler(Filters.regex(r'(نرد|حظي)'), games))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, smart_responses))

    print("🚀 لولي جاهزة للعب والعمل الآن!")
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":




    
    main()

