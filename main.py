import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7768342919:AAGVPWmaBsJHBQvSDrd4MY7LVx5eTKemF10"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ringtone Pro Bot Me Aapka Swagat Hai!\n\n"
        "Kisi Bhi Ringtone Ka Naam Bhejo, Main YouTube Se 3 Ringtone Dhundh Kar Bhej Dunga.\n\n"
        "Example: Teri Baaton Mein Aisa Uljha Jiya Ringtone"
    )

async def search_and_send_ringtones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("Ringtone Search Kar Raha Hu, Thodi Der Wait Karo...")
    
    try:
        search_query = f"{query} ringtone"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            'default_search': 'ytsearch3',
            'source_address': '0.0.0.0',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'ignoreerrors': True,
            'no_color': True,
            'geo_bypass': True,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['js', 'configs', 'webpage']
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_msg.edit_text("YouTube Se Ringtone Download Ho Rahi Hai...")
            
            info = ydl.extract_info(f"ytsearch3:{search_query}", download=False)
            
            if not info or 'entries' not in info or len(info['entries']) == 0:
                await status_msg.edit_text("Koi Ringtone Nahi Mili. Kuch Aur Search Karo.")
                return
            
            entries = [entry for entry in info['entries'] if entry]
            
            if len(entries) == 0:
                await status_msg.edit_text("Koi Ringtone Nahi Mili. Kuch Aur Search Karo.")
                return
            
            await status_msg.edit_text(f"{len(entries)} Ringtone Mili, Ab Download Shuru Karta Hu...")
            
            sent_count = 0
            downloaded_files = []
            
            for i, entry in enumerate(entries[:3], 1):
                try:
                    video_url = entry['webpage_url']
                    video_title = entry.get('title', 'Unknown Title')
                    duration = entry.get('duration', 0)
                    
                    if duration > 120:
                        await update.message.reply_text(f"❌ {i}. {video_title}\nBahut Lamba Video Hai (2 Minute Se Jyada). Skip Kar Raha Hu.")
                        continue
                    
                    temp_status = await update.message.reply_text(f"Downloading {i}/3: {video_title[:50]}...")
                    
                    safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title[:50]
                    output_file = f"{safe_title}.mp3"
                    
                    download_opts = {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'outtmpl': output_file.replace('.mp3', '.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'noplaylist': True,
                        'extract_flat': False,
                        'socket_timeout': 30,
                        'retries': 3,
                        'fragment_retries': 3,
                        'geo_bypass': True,
                        'extractor_args': {
                            'youtube': {
                                'skip': ['dash', 'hls'],
                                'player_skip': ['js', 'configs', 'webpage']
                            }
                        }
                    }
                    
                    with yt_dlp.YoutubeDL(download_opts) as downloader:
                        downloader.download([video_url])
                    
                    if os.path.exists(output_file):
                        file_size = os.path.getsize(output_file)
                        
                        if file_size > 50 * 1024 * 1024:
                            await temp_status.edit_text(f"❌ {i}. {video_title}\nFile Bahut Badi Hai (50MB Se Jyada). Skip Kar Raha Hu.")
                            os.remove(output_file)
                            continue
                        
                        await temp_status.edit_text(f"Uploading {i}/3: {video_title[:50]}...")
                        
                        with open(output_file, 'rb') as audio:
                            await update.message.reply_audio(
                                audio=audio,
                                title=video_title,
                                performer="Ringtone Pro Bot",
                                filename=f"{safe_title}.mp3"
                            )
                        
                        sent_count += 1
                        downloaded_files.append(output_file)
                        await temp_status.delete()
                    
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"Download error for {entry.get('title', 'Unknown')}: {str(e)}")
                    try:
                        await temp_status.edit_text(f"❌ {i}. Download Failed. Skip Kar Raha Hu.")
                    except:
                        pass
                    continue
                    
                except Exception as e:
                    logger.error(f"Error processing {entry.get('title', 'Unknown')}: {str(e)}")
                    try:
                        await temp_status.edit_text(f"❌ {i}. Error Aaya. Skip Kar Raha Hu.")
                    except:
                        pass
                    continue
            
            for file_path in downloaded_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
            
            if sent_count > 0:
                await status_msg.edit_text(f"✅ {sent_count} Ringtone Successfully Send Kar Di!")
            else:
                await status_msg.edit_text("❌ Koi Ringtone Send Nahi Ho Payi. Dobara Try Karo.")
                
    except Exception as e:
        logger.error(f"Main error: {str(e)}")
        await status_msg.edit_text("Kuch Error Aaya. Dobara Try Karo.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_send_ringtones))
    
    print("Bot Started! Bot Ab Ready Hai Ringtone Bhejne Ke Liye...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
