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

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🎵 Welcome to Ringtone Pro Bot! 🎵\n\n"
        "I am your personal high-speed ringtone provider. "
        "Just send me the name of any song, movie BGM, or artist, and I will instantly fetch the Top 3 best quality MP3 ringtones for you.\n\n"
        "⚡ Features:\n"
        "• High-Quality MP3 Audio\n"
        "• Super-fast processing\n"
        "• Direct Telegram Files (No ads or links)\n\n"
        "💡 Need assistance? Click /help"
    )
    bot.reply_to(message, welcome_text)

# --- HELP COMMAND ---
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🛠️ **Ringtone Pro Bot Help Center** 🛠️\n\n"
        "**How to use me?**\n"
        "1. Do not send YouTube links. Just type the name of the song.\n"
        "2. Add words like 'BGM', 'instrumental', or 'flute' for better results.\n"
        "   👉 *Example:* KGF emotional bgm\n"
        "   👉 *Example:* Arijit Singh sad ringtone\n\n"
        "**Why didn't I get my ringtone?**\n"
        "• Sometimes YouTube blocks requests. Just wait 1 minute and try again.\n"
        "• Check if the spelling is correct.\n\n"
        "**Is this bot free?**\n"
        "• Yes! 100% Free and NO ADS. Enjoy downloading!"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# --- MAIN DOWNLOAD LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_ringtone_search(message):
    query = message.text
    chat_id = message.chat.id
    
    bot.send_message(chat_id, "Searching... Please wait ⏳")
    
    # MAGIC SETTINGS: Bypassing YouTube Server Blocks
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'downloads/{chat_id}_%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
        'noplaylist': True,
        'quiet': True,
        'extract_audio': True,
        'max_downloads': 3,
        'nocheckcertificate': True,
        # Spoofing as an Android device to stop YouTube from blocking Render IP
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
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
        bot.send_message(chat_id, "⚠️ Network busy! YouTube is strictly checking requests right now. Please try again after 1-2 minutes.")
        
        # Cleanup broken files
        error_files = glob.glob(f'downloads/{chat_id}_*')
        for file in error_files:
            try:
                os.remove(file)
            except:
                pass

if __name__ == "__main__":
    bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
