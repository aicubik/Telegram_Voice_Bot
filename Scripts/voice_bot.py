import os
import telebot
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv('Credentials.env')

# Initialize Telegram Bot and Gemini API
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        # 1. Download voice message
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 2. Save file temporarily
        # ... logic ...
        
        # 3. Transcribe with Gemini 1.5 Flash
        # ... logic ...
        
        # 4. Forward results to group
        # ... logic ...
        
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

if __name__ == "__main__":
    bot.polling(none_stop=True)
