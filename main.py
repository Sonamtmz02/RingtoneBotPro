import os
import logging
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get Bot Token from Environment Variable
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN provided. Please set it in your environment variables.")

def get_youtube_audio_url(query):
    """
    Searches YouTube for the query and returns the top 3 video URLs.
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'default_search': 'ytsearch3' # Search top 3 results
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch3:{query}", download=False)
            if result and 'entries' in result:
                entries = result['entries']
                urls = []
                for entry in entries:
                    if entry:
                        urls.append(entry['url'])
                return urls
            else:
                return []
    except Exception as e:
        logger.error(f"Error searching YouTube: {e}")
        return []

async def download_and_send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, video_url: str, title: str):
    """
    Downloads audio from YouTube URL and sends it to the user.    """
    chat_id = update.effective_chat.id
    
    # Send a temporary message indicating processing
    status_msg = await context.bot.send_message(chat_id=chat_id, text=f"⬇️ Downloading: {title}...")

    # Define yt-dlp options for audio extraction
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            # yt-dlp changes extension to mp3 after post-processing
            mp3_filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            if os.path.exists(mp3_filename):
                # Send the audio file
                with open(mp3_filename, 'rb') as audio_file:
                    await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio_file,
                        title=title,
                        caption=f"🎵 {title}\n\n✅ Downloaded via Ringtone Pro Bot"
                    )
            else:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text="❌ Failed to generate MP3 file."
                )
                
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        await context.bot.edit_message_text(
            chat_id=chat_id,            message_id=status_msg.message_id,
            text=f"❌ Error: Could not download this ringtone. Try another one."
        )
    finally:
        # Cleanup
        os.chdir(original_cwd)
        # Remove temp directory and files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Delete the status message
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎵 Welcome to Ringtone Pro Bot! 🎵\n\n"
        "I am your personal high-speed ringtone provider. Just send me the name of any song, movie BGM, or artist, and I will instantly fetch the Top 3 best quality MP3 ringtones for you.\n\n"
        "⚡ Features:\n"
        "• High-Quality MP3 Audio\n"
        "• Super-fast processing\n"
        "• Direct Telegram Files (No ads or links)\n\n"
        "💡 Need assistance? Click /help"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠️ Ringtone Pro Bot Help Center 🛠️\n\n"
        "How to use me?\n"
        "1. Do not send YouTube links. Just type the name of the song.\n"
        "2. Add words like 'BGM', 'instrumental', or 'flute' for better results.\n"
        "   👉 Example: KGF emotional bgm\n"
        "   👉 Example: Arijit Singh sad ringtone\n\n"
        "Why didn't I get my ringtone?\n"
        "• Sometimes YouTube blocks requests. Just wait 1 minute and try again.\n"
        "• Check if the spelling is correct.\n\n"
        "Is this bot free?\n"
        "• Yes! 100% Free and NO ADS. Enjoy downloading!"
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    
    if not user_query:
        return

    await update.message.reply_text("🔍 Searching for best ringtones...")
    # Search YouTube for top 3 results
    video_urls = get_youtube_audio_url(user_query)

    if not video_urls:
        await update.message.reply_text("❌ No results found. Please try a different keyword.")
        return

    # Process each of the top 3 results
    for i, url in enumerate(video_urls):
        try:
            # Extract basic info for title
            ydl_opts = {'quiet': True, 'extract_flat': False}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', f'Ringtone {i+1}')
                
            # Download and send
            await download_and_send_audio(update, context, url, title)
            
        except Exception as e:
            logger.error(f"Failed to process result {i+1}: {e}")
            continue

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
