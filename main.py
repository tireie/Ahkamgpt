import os
import logging
import sys
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import httpx

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or OPENROUTER_API_KEY")

# Strict system prompt
system_prompt = (
    "You are an Islamic scholar who answers questions only based on the official rulings and teachings "
    "of Sayyed Ali Khamenei. You must only use trusted sources including:\n"
    "- khamenei.ir\n"
    "- ajsite.ir\n"
    "- leader.ir\n"
    "- abna24.com\n"
    "- al-islam.org\n\n"
    "Rules:\n"
    "1. If no ruling or verified answer exists, say:\n"
    '   - English: "There is no known ruling or teaching from Sayyed Ali Khamenei on this topic."\n'
    '   - Arabic: "لا يوجد رأي معروف للسيد علي الخامنئي حول هذا الموضوع."\n'
    "2. Never guess or assume an answer.\n"
    "3. Only answer from the listed sources.\n"
    "4. Support both fatwa rulings and general Islamic guidance.\n"
    "5. Always answer in the user's language (Arabic or English).\n"
    "6. Keep answers concise, accurate, and respectful."
)

# Detect Arabic
def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# Ask OpenRouter Claude 3 Sonnet
async def ask_openrouter(prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-sonnet",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1024,
                    "temperature": 0.2
                }
            )
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenRouter error: {e}")
        return "⚠️ Sorry, the fatwa service is currently unavailable."

# /start handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🕌 **Ahkam GPT**\n\n"
        "السلام عليكم ورحمة الله وبركاته\n"
        "Welcome! You can ask questions about Islamic rulings and teachings based strictly on the official fatwas and views of Sayyed Ali Khamenei.\n\n"
        "❓ Example:\n"
        "- Can I fast while breastfeeding?\n"
        "- ما حكم بلع بقايا الطعام أثناء الصيام؟"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

# Handle normal messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return
    logging.info(f"User asked: {user_text}")
    reply = await ask_openrouter(user_text)
    logging.info(f"Bot reply: {reply}")
    await update.message.reply_text(reply)

# Run the bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("AhkamGPT Telegram bot started.")
    application.run_polling()

if __name__ == "__main__":
    main()