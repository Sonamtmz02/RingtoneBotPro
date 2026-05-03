import os
import re
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7768342919:AAGVPWmaBsJHBQvSDrd4MY7LVx5eTKemF10"
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎵 *Welcome to Ringtone Pro Bot* 🎵

Simply send me a song name or ringtone name.

Example: `shape of you`
I will send you the top 3 matching ringtones as MP3 files!

⚡ Fast downloads
✅ High quality audio
🎵 Best ringtones

Made with ❤️
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def search_and_download_single(query: str, result_index: int, download_id: str) -> str:
    search_query = f"ytsearch{result_index+1}:{query} ringtone"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(DOWNLOAD_DIR / f"{download_id}_result{result_index+1}_%(title).50s.%(ext)s"),
        'quiet': True,
        'no_warnings': True,
        'extract_audio': True,
        'audio_format': 'mp3',
        'audio_quality': '192K',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            filename = ydl.prepare_filename(info['entries'][0])
            if filename.endswith('.webm') or filename.endswith('.m4a'):
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            return filename
    except Exception as e:
        logger.error(f"Download error for {query}: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    user_id = update.effective_user.id
    download_id = f"user_{user_id}_{int(asyncio.get_event_loop().time())}"
    
    if not query:
        await update.message.reply_text("❌ Please send a valid ringtone name!")
        return
    
    status_msg = await update.message.reply_text(f"🔍 Searching for *{query}* ringtones...\n\n⏳ Finding the best 3 results...", parse_mode="Markdown")
    
    downloaded_files = []
    success_count = 0
    
    for i in range(3):
        try:
            await status_msg.edit_text(f"🔍 Searching for *{query}* ringtones...\n\n📥 Downloading result {i+1}/3...", parse_mode="Markdown")
            
            filename = await search_and_download_single(query, i, download_id)
            
            if filename and os.path.exists(filename):
                downloaded_files.append(filename)
                success_count += 1
                await asyncio.sleep(0.5)
            else:
                await update.message.reply_text(f"⚠️ Result {i+1} could not be downloaded. Skipping...")
                
        except Exception as e:
            logger.error(f"Error downloading result {i+1}: {e}")
            continue
    
    if success_count == 0:
        await status_msg.edit_text(f"❌ Couldn't find ringtones for *{query}*. Try a different name!", parse_mode="Markdown")
        return
    
    await status_msg.edit_text(f"✅ Found {success_count} ringtones! Sending now...", parse_mode="Markdown")
    
    for i, filepath in enumerate(downloaded_files):
        try:
            original_filename = os.path.basename(filepath)
            clean_filename = re.sub(r'\.(webm|m4a|mp4|mkv)$', '.mp3', original_filename)
            clean_filename = re.sub(r'^[^a-zA-Z0-9]', '', clean_filename)[:60]
            
            with open(filepath, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    filename=clean_filename,
                    title=f"🎵 {query.title()} - Ringtone {i+1}",
                    performer="Ringtone Pro Bot",
                    caption=f"✅ Ringtone {i+1} of {success_count}\n🔔 Set as ringtone!",
                    reply_to_message_id=update.message.message_id
                )
        except Exception as e:
            logger.error(f"Upload error: {e}")
            await update.message.reply_text(f"❌ Failed to send ringtone {i+1}")
    
    for filepath in downloaded_files:
        try:
            os.remove(filepath)
        except:
            pass
    
    await update.message.reply_text(f"🎉 *All {success_count} ringtones sent!*\n\nSend another song name to get more ringtones!", parse_mode="Markdown")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Ringtone Pro Bot is running...")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await app.updater.stop()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())