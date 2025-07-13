import os
import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")

MODEL = "Qwen/Qwen2.5-7B-Chat"

SYSTEM_PROMPT = """You are a qualified Islamic scholar answering fatwas based only on the rulings of Sayyed Ali Khamenei. Only respond with what is present in his official sources such as khamenei.ir and ajsite.org. Do not invent answers. Respond in the same language the question is asked in (Arabic or English)."""

async def query_together_api(message: str):
    try:
        response = httpx.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.2,
                "max_tokens": 1024,
                "top_p": 0.95,
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"API error: {e}")
        return "⚠️ An error occurred while processing your question."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕌 Welcome to AhkamGPT.\n\nAsk me your Islamic questions, and I’ll answer based on the fatwas of Sayyed Ali Khamenei (from khamenei.ir and ajsite.org).\n\nمثال: هل يجوز الإفطار أثناء الحيض؟\nExample: Can I fast while breastfeeding?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logging.info(f"Received: {user_message}")
    reply = await query_together_api(user_message)
    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()