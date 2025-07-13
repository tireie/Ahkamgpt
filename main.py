import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load from Railway environment
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = "Qwen/Qwen1.5-7B-Chat"  # Better Arabic support

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt
SYSTEM_PROMPT = """You are a qualified Islamic scholar answering fatwas based only on the rulings of Sayyed Ali Khamenei. Do not guess or create fatwas. Use only the official sources like khamenei.ir and