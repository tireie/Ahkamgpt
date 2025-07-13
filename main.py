import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load your Telegram bot token and Together API key from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)

# Model info
TOGETHER_API_URL = "https://api.together.ai/v1/chat/completions"
MODEL_NAME = "Qwen/Qwen1.5-7B-Chat"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Ask me any Islamic question based on Sayyed Khamenei’s fatwas.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a qualified Islamic scholar answering fatwas based only on Sayyed Ali Khamenei's rulings. "
                    "Answer in the user's language (English, Arabic, or Farsi) and be brief and accurate."
                ),
            },
            {"role": "user", "content": user_message},
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(TOGETHER_API_URL, headers=headers, json=data)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"Together API Error: {e}")
        await update.message.reply_text("⚠️ An error occurred while processing your question.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()