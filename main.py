import os
import re
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import httpx

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or OPENROUTER_API_KEY")

# System instructions
instructions = """
You are a trusted Islamic assistant who only provides answers based on the official jurisprudence (Ahkam) and religious teachings of Sayyed Ali Khamenei.

📌 You must strictly follow the following rules:

1. Only answer using verified, official sources:
   - https://khamenei.ir
   - https://leader.ir
   - https://ajsite.ir
   - https://abna24.com
   - https://al-islam.org

2. If there is no known ruling from Sayyed Ali Khamenei on the question:
   - In English, reply: "There is no known fatwa from Sayyed Ali Khamenei on this topic."
   - In Arabic, reply: "لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع."

3. Never guess, summarize, or infer rulings. Do not make up references. Only quote rulings that are explicitly published by Sayyed Khamenei or his official offices.

4. If the user’s question is about general Islamic topics (not rulings), still respond only based on the same sources above.

💬 Always answer in the same language the user asked (Arabic or English).
✂️ Be concise, precise, and avoid listing items unless explicitly confirmed by official fatwas.

You are not allowed to improvise or speculate under any circumstances.
"""

# Detect Arabic
def is_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# GPT-4 via OpenRouter
async def ask_openrouter(user_input: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yourdomain.com"
        }

        data = {
            "model": "openai/gpt-4",
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }

        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return "⚠️ Fatwa service is currently unavailable."

# /start command handler (bilingual)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🕌 **السلام عليكم ورحمة الله وبركاته**\n"
        "🕌 **Peace and blessings be upon you.**\n\n"
        "🤖 **أهلاً بك في AhkamGPT — مساعدك للإجابة عن الأحكام الشرعية بناءً على فتاوى السيد علي الخامنئي.**\n"
        "🤖 **Welcome to AhkamGPT — your assistant for Islamic rulings based on Sayyed Ali Khamenei’s fatwas.**\n\n"
        "🗣️ **يمكنك طرح الأسئلة بالعربية أو الإنجليزية.**\n"
        "🗣️ **You may ask questions in Arabic or English.**\n\n"
        "📌 **كل الإجابات تعتمد فقط على المصادر الرسمية المعتمدة.**\n"
        "📌 **All answers are based strictly on official verified sources only.**"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

# Main message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return

    logger.info(f"User: {user_text}")
    reply = await ask_openrouter(user_text)
    logger.info(f"Bot: {reply}")
    await update.message.reply_text(reply)

# App entry point
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 AhkamGPT bot started using GPT-4.")
    app.run_polling()

if __name__ == "__main__":
    main()