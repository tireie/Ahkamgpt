import os, re, logging, sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import httpx

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load tokens from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not BOT_TOKEN or not TOGETHER_API_KEY:
    logging.error("Missing BOT_TOKEN or TOGETHER_API_KEY environment variable.")
    sys.exit(1)

# Helper function to detect Arabic text
def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# System prompt
system_prompt = (
    "You are a trusted Islamic jurist answering only based on the official religious rulings (fatwas) of Sayyed Ali Khamenei. "
    "You must strictly follow his jurisprudence and use only official sources such as khamenei.ir and ajsite.ir. "
    "Do not guess. Do not invent fatwas. Do not give rulings from other scholars or schools. "
    "If no fatwa exists for the question, clearly say: "
    "- \"There is no known fatwa from Sayyed Ali Khamenei on this topic.\" (in English), or "
    "- \"لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.\" (in Arabic). "
    "If the user's question is in Arabic, reply in Arabic. If it is in English, reply in English. "
    "You must be accurate, concise, and avoid any generalizations or personal interpretations."
)

# Ask Together API
async def ask_together(user_input: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    try:
        response = await httpx.AsyncClient().post(
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
            },
            timeout=30
        )
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Error calling Together API: {e}")
        return "⚠️ Error contacting fatwa service."

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return
    logging.info(f"Received message: {user_text}")
    reply = await ask_together(user_text)
    await update.message.reply_text(reply)

# Start bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    logging.info("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()