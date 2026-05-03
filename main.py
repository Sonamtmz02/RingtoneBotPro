import telebot
import yt_dlp
import os
import glob
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- DUMMY WEB SERVER TO KEEP RENDER HAPPY ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running smoothly on Render!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, DummyHandler)
    httpd.serve_forever()

server_thread = threading.Thread(target=run_dummy_server)
server_thread.daemon = True
server_thread.start()
# ---------------------------------------------

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

if not os.path.exists('downloads'):
    os.makedirs('downloads')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🎵 Welcome to Ringtone Pro Bot! 🎵\n\n"
        "I am your personal high-speed ringtone provider. "
        "Just send me the name of any song, movie BGM, or artist, and I will instantly fetch the Top 3 best quality MP3 ringtones for you.\n\n"
        "⚡ Features:\n"
        "• High-Quality MP3 Audio\n"
        "• Super-fast processing\n"
        "• Direct Telegram Files (No ads or links)\n\n"
        "🎧 How to use:\n"
        "Simply type the song name below and hit send!\n"
        "Example: Animal movie bgm"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_ringtone_search(message):
    query = message.text
    chat_id = message.chat.id
    
    bot.send_message(chat_id, "Searching... Please wait ⏳")
    
    # ULTIMATE SAFE SETTINGS FOR RENDER & YOUTUBE
    ydl_opts = {
        'format': 'bestaudio/best',
        # Removed Title from name, using ID to prevent special character crashes
        'outtmpl': f'downloads/{chat_id}_%(id)s.%(ext)s', 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
        # REMOVED ARIA2C - This was the villain causing YouTube to block us!
        'noplaylist': True,
        'quiet': True,
        'extract_audio': True,
        'ignoreerrors': True, # If 1 video fails, it won't crash the bot, it will move to next
        'max_downloads': 3 # Strictly limit to 3 to avoid timeouts
    }
    
    search_query = f"ytsearch3:{query} ringtone short"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        downloaded_files = glob.glob(f'downloads/{chat_id}_*.mp3')
        
        if not downloaded_files:
            bot.send_message(chat_id, "Sorry, I couldn't find good ringtones for this. Please try a different name.")
            return

        for file_path in downloaded_files:
            with open(file_path, 'rb') as audio:
                bot.send_audio(chat_id, audio)
            os.remove(file_path) 
            
        bot.send_message(chat_id, "✅ Enjoy your ringtones!")
            
    except Exception as e:
        print(f"CRITICAL ERROR FOR CHAT {chat_id}: {e}")
        bot.send_message(chat_id, "An error occurred. YouTube might be blocking the request. Try again in a minute.")
        
        # Cleanup broken files
        error_files = glob.glob(f'downloads/{chat_id}_*')
        for file in error_files:
            try:
                os.remove(file)
            except:
                pass

if __name__ == "__main__":
    bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
