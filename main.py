import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load from Railway environment
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = "Qwen/Qwen1.5-7B-Chat"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt
SYSTEM_PROMPT = """You are a qualified Islamic scholar answering fatwas based only on the rulings of Sayyed Ali Khamenei. Do not guess or create fatwas. Use only the official sources like khamenei.ir and ajsite.ir. If a ruling doesn't exist, say so clearly. Answer in the same language as the question."""

# Ask Together API
async def ask_gpt(question):
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        "temperature": 0.4,
        "top_p": 0.7
    }

    try:
        response = requests.post("https://api.together.ai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        output = response.json()
        return output['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Together API Error: {e}")
        return "⚠️ An error occurred while processing your question."

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_ar = "👋 مرحبًا بك في AhkamGPT! أرسل سؤالك الشرعي وسأجيبك وفقًا لفتاوى السيد علي الخامنئي."
    welcome_en = "👋 Welcome to AhkamGPT! Send your Islamic question and I will answer based on Sayyed Ali Khamenei's rulings."

    user_lang = update.effective_user.language_code
    if user_lang.startswith("ar"):
        await update.message.reply_text(welcome_ar)
    else:
        await update.message.reply_text(welcome_en)

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await update.message.chat.send_action(action="typing")
    answer = await ask_gpt(user_input)
    await update.message.reply_text(answer)

# Main app
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()