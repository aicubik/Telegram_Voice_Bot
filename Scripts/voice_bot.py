# ============================================================
# DEPRECATED — This file is no longer used.
# The main bot logic has been moved to tg_assistant_bot.py.
# This file is kept only as a historical reference.
# ============================================================

import os
import telebot
from dotenv import load_dotenv

# Load environment variables
load_dotenv('Credentials.env')

# Initialize Telegram Bot
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

# NOTE: This was the original prototype that used Google Gemini API.
# It has been replaced by tg_assistant_bot.py which uses Groq + OpenRouter.
# Do NOT run this file.
