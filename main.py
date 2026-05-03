import os
import asyncio
import logging
import tempfile
import shutil
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

WELCOME_MESSAGE = """
🎵 Welcome to Ringtone Pro Bot! 🎵

I am your personal high-speed ringtone provider. Just send me the name of any song, movie BGM, or artist, and I will instantly fetch the Top 3 best quality MP3 ringtones for you.

⚡ Features:
• High-Quality MP3 Audio
• Super-fast processing
• Direct Telegram Files (No ads or links)

💡 Need assistance? Click /help
"""

HELP_MESSAGE = """
🛠️ Ringtone Pro Bot Help Center 🛠️

How to use me?
1. Do not send YouTube links. Just type the name of the song.
2. Add words like 'BGM', 'instrumental', or 'flute' for better results.
   👉 Example: KGF emotional bgm
   👉 Example: Arijit Singh sad ringtone

Why didn't I get my ringtone?
• Sometimes YouTube blocks requests. Just wait 1 minute and try again.
• Check if the spelling is correct.

Is this bot free?
• Yes! 100% Free and NO ADS. Enjoy downloading!
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_MESSAGE)

async def search_and_send_ringtones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    
    if not user_query:
        await update.message.reply_text("Please send a song name or ringtone name to search.")
        return
    
    status_message = await update.message.reply_text(f"🔍 Searching for: {user_query}\n⏳ Please wait...")
    
    search_query = f"ytsearch3:{user_query} ringtone audio"
    
    temp_dir = tempfile.mkdtemp()
    downloaded_files = []
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '256',
            }],
            'outtmpl': os.path.join(temp_dir, '%(title).100s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'download_archive': None,
            'ignoreerrors': True,
            'no_color': True,
            'external_downloader': 'aria2c',
            'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M'],
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 5,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_message.edit_text(f"🔍 Searching: {user_query}\n⬇️ Downloading audio files...")
            
            info = ydl.extract_info(search_query, download=True)
            
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry is None:
                        continue
                    
                    video_title = entry.get('title', 'Unknown')
                    video_id = entry.get('id', str(uuid.uuid4())[:8])
                    
                    mp3_filename = None
                    for file in os.listdir(temp_dir):
                        if file.endswith('.mp3'):
                            file_path = os.path.join(temp_dir, file)
                            if os.path.getsize(file_path) > 0:
                                mp3_filename = file_path
                                break
                    
                    if mp3_filename:
                        new_filename = os.path.join(temp_dir, f"{video_title[:80]}.mp3")
                        if mp3_filename != new_filename:
                            shutil.move(mp3_filename, new_filename)
                        downloaded_files.append((new_filename, video_title))
            else:
                await status_message.edit_text("❌ No results found. Please try a different search term.\n\nTip: Add words like 'ringtone', 'bgm', or 'instrumental' for better results.")
                return
        
        if not downloaded_files:
            await status_message.edit_text("❌ Failed to download audio. Please try again later or use a different search term.")
            return
        
        await status_message.edit_text(f"📤 Sending {len(downloaded_files)} ringtones...")
        
        for idx, (file_path, title) in enumerate(downloaded_files, 1):
            try:
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                
                if file_size_mb > 50:
                    await update.message.reply_text(f"⚠️ {title}\nFile too large ({file_size_mb:.1f}MB), skipping...")
                    continue
                
                await status_message.edit_text(f"📤 Sending ringtone {idx}/{len(downloaded_files)}: {title[:50]}...")
                
                with open(file_path, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=title[:100],
                        performer="Ringtone Pro Bot",
                        caption=f"🎵 {title}\n\nDownloaded via @RingtoneProBot"
                    )
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error sending file {title}: {e}")
                await update.message.reply_text(f"⚠️ Failed to send: {title}")
        
        await status_message.delete()
        
    except Exception as e:
        logger.error(f"Main error: {e}")
        await status_message.edit_text(f"❌ An error occurred. Please try again later.\n\nError: {str(e)[:100]}")
    
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ An unexpected error occurred. Please try again.")
    except:
        pass

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Please replace YOUR_BOT_TOKEN_HERE with your actual bot token!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_send_ringtones))
    
    application.add_error_handler(error_handler)
    
    print("✅ Ringtone Pro Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import yt_dlp
    main()
