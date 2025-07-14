import os
import re
import logging
import sys
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import httpx

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or OPENROUTER_API_KEY in environment")

# Strict Islamic instruction prompt
system_prompt = """
You are a trusted Islamic scholar who only answers based on the official rulings and teachings of Sayyed Ali Khamenei.

✅ Only use rulings and content from verified sources:
- leader.ir
- khamenei.ir
- ajsite.ir
- abna24.com
- al-islam.org

⚠️ You are strictly forbidden from guessing, inventing, or making assumptions.
- If no answer exists in the sources, clearly respond:
   - In English: "There is no known fatwa from Sayyed Ali Khamenei on this topic."
   - In Arabic: "لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع."

📚 You may answer general Islamic questions, but ONLY if the answer is verifiable from the sources above.

🧠 Always respond in the user's language (Arabic or English) and keep responses clear, concise, and source-aligned.
"""

# Language detection
def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# API Call to OpenRouter
async def ask_openrouter(user_input: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen/Qwen1.5-72B-Chat",  # Change if needed
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 700,
                },
            )
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenRouter API error: {e}")
        return "⚠️ Fatwa service is currently unavailable. Please try again later."

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return
    logging.info(f"User: {user_text}")
    reply = await ask_openrouter(user_text)
    logging.info(f"Bot: {reply}")
    await update.message.reply_text(reply)

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_en = (
        "🕌 *Peace be upon you.*\n"
        "Welcome to AhkamGPT — your assistant for Islamic rulings and teachings based strictly on the fatwas of Sayyed Ali Khamenei.\n\n"
        "Ask your question in English or Arabic.\n"
    )
    welcome_ar = (
        "🕌 *السلام عليكم ورحمة الله.*\n"
        "مرحبًا بك في AhkamGPT — مساعدك للفتاوى والأحكام الإسلامية وفقًا لتعاليم السيد علي الخامنئي فقط.\n\n"
        "اكتب سؤالك باللغة العربية أو الإنجليزية.\n"
    )
    await update.message.reply_text(f"{welcome_en}\n{welcome_ar}", parse_mode="Markdown")

# Main entry
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("AhkamGPT bot is running.")
    application.run_polling()

if __name__ == "__main__":
    main()