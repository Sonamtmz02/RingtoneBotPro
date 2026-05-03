import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import uuid

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Ringtone Pro Bot!\nSend me ringtone name to search and download.")

async def search_ringtone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query or len(query.strip()) == 0:
        await update.message.reply_text("Please send a ringtone name.")
        return
    
    search_msg = await update.message.reply_text(f"Searching YouTube for: {query}")
    
    search_query = f"{query} ringtone"
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_generic_extractor': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_url = f"ytsearch5:{search_query}"
            info = ydl.extract_info(search_url, download=False)
            entries = info.get('entries', [])
        
        ringtone_videos = []
        seen_ids = set()
        
        for entry in entries:
            if entry and entry.get('id') not in seen_ids:
                duration = entry.get('duration', 0) or 0
                if duration <= 120:
                    ringtone_videos.append(entry)
                    seen_ids.add(entry['id'])
        
        if len(ringtone_videos) < 3:
            for entry in entries:
                if entry and entry.get('id') not in seen_ids:
                    ringtone_videos.append(entry)
                    seen_ids.add(entry['id'])
                    if len(ringtone_videos) >= 3:
                        break
        
        if len(ringtone_videos) == 0:
            await search_msg.edit_text("No ringtone found. Try different name.")
            return
        
        await search_msg.edit_text(f"Found {min(3, len(ringtone_videos))} ringtones. Downloading...")
        
        sent_count = 0
        for idx, video in enumerate(ringtone_videos[:3]):
            if sent_count >= 3:
                break
            
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            video_title = video.get('title', f'Ringtone_{idx+1}')
            
            status_msg = await update.message.reply_text(f"Downloading {idx+1}/3: {video_title[:50]}...")
            
            file_path = await download_audio(video_url)
            
            if file_path:
                with open(file_path, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=video_title[:64],
                        performer="Ringtone Pro Bot",
                        filename=f"{video_title[:30]}.mp3"
                    )
                os.remove(file_path)
                sent_count += 1
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"Failed to download: {video_title[:50]}")
        
        if sent_count > 0:
            await search_msg.delete()
        else:
            await search_msg.edit_text("Download failed. Please try again.")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await search_msg.edit_text("Error occurred. Please try again later.")

async def download_audio(url):
    download_id = str(uuid.uuid4())[:8]
    output_path = f"downloads/{download_id}"
    os.makedirs("downloads", exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
        'outtmpl': f'{output_path}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M'],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        mp3_file = f"{output_path}.mp3"
        if os.path.exists(mp3_file) and os.path.getsize(mp3_file) > 0:
            return mp3_file
        return None
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return None

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_ringtone))
    
    logger.info("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
