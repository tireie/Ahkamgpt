import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Together API Request Function
def ask_together(prompt):
    url = "https://api.together.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's rulings. Answer only according to his jurisprudence."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        logging.error(f"Together API Error: {response.status_code} - {response.text}")
        return "⚠️ An error occurred while processing your question."

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to AhkamGPT. Ask your Islamic questions based on Sayyed Khamenei's rulings.")

# Main message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await update.message.chat.send_action(action="typing")
    reply = ask_together(user_input)
    await update.message.reply_text(reply)

# Main bot entry point
if __name__ == "__main__":
    if not BOT_TOKEN or not TOGETHER_API_KEY:
        raise Exception("Missing BOT_TOKEN or TOGETHER_API_KEY environment variables")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Bot is running...")
    app.run_polling()