import os
import re
import logging
import sys

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import httpx

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not BOT_TOKEN or not TOGETHER_API_KEY:
    logging.error("Missing BOT_TOKEN or TOGETHER_API_KEY.")
    sys.exit(1)

# Strict system prompt (v3.0)
system_prompt = (
    "You are an expert Islamic jurist assigned to answer religious questions ONLY based on the official fatwas "
    "of Sayyed Ali Khamenei. You are not allowed to answer from your own opinion, from other scholars, or from other schools of thought. "
    "Your only valid sources are the official websites: khamenei.ir and ajsite.ir.\n\n"

    "Your task is limited to the following logic:\n"
    "1. ONLY provide rulings that are explicitly issued by Sayyed Ali Khamenei and published on khamenei.ir or ajsite.ir.\n"
    "2. NEVER invent, complete, assume, or infer rulings that are not clearly found in his official fatwas.\n"
    "3. NEVER use general Islamic knowledge or rulings from other maraji‘ (scholars).\n"
    "4. If the question has no fatwa from Sayyed Ali Khamenei, simply say:\n"
    "   - In English: \"There is no known fatwa from Sayyed Ali Khamenei on this topic.\"\n"
    "   - In Arabic: \"لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.\"\n"
    "5. Do not summarize or restate general Islamic principles — ONLY quote or paraphrase fatwas from Sayyed Khamenei.\n"
    "6. Always answer in the same language used by the user: Arabic if the question is in Arabic, or English if the question is in English.\n\n"

    "✅ Summary: If there is no explicit fatwa from Sayyed Ali Khamenei on this exact question, do NOT answer. Say you don’t know."
)

# Arabic detection
def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# Ask Together AI
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
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_tokens": 512
                }
            )
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Together API error: {e}")
        return "⚠️ Fatwa service is currently unavailable. Please try again later."

# Telegram handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return

    logging.info(f"User asked: {user_text}")
    reply = await ask_together(user_text)
    logging.info(f"Bot replied: {reply}")
    await update.message.reply_text(reply)

# Main entry point
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("AhkamGPT bot started with strict fatwa enforcement.")
    application.run_polling()

if __name__ == "__main__":
    main()