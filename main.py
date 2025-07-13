import os
import re
import logging
import sys

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import httpx

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not BOT_TOKEN or not TOGETHER_API_KEY:
    logging.error("Missing BOT_TOKEN or TOGETHER_API_KEY.")
    sys.exit(1)

# Strict fatwa-only system prompt
system_prompt = (
    "You are an Islamic jurist who answers only based on the official fatwas of Sayyed Ali Khamenei, "
    "using only sources from khamenei.ir and ajsite.ir.\n\n"
    "Your answers must follow these rules:\n"
    "1. Only provide rulings explicitly found in Sayyed Khamenei’s official fatwas.\n"
    "2. Do not include rulings from other scholars or Islamic schools.\n"
    "3. If no known fatwa exists:\n"
    "   - In English, respond: \"There is no known fatwa from Sayyed Ali Khamenei on this topic.\"\n"
    "   - In Arabic, respond: \"لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.\"\n"
    "4. Never guess, invent, or assume a fatwa.\n"
    "5. Never list items unless each one is explicitly confirmed by Sayyed Khamenei.\n\n"
    "Always answer in the user's language (Arabic or English), and keep answers concise and accurate."
)

# Detect Arabic in user text
def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# Query Together API
async def ask_together(user_input: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistralai/Mistral-7B-Instruct-v0.3",
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 512
                }
            )
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Together API error: {e}")
        return "⚠️ Fatwa service is currently unavailable. Please try again later."

# Handle Telegram messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return

    logging.info(f"User asked: {user_text}")
    reply = await ask_together(user_text)
    logging.info(f"Reply: {reply}")
    await update.message.reply_text(reply)

# Bot entry point
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("AhkamGPT bot started.")
    application.run_polling()

if __name__ == "__main__":
    main()