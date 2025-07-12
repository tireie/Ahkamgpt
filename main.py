import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

# Logging
logging.basicConfig(level=logging.INFO)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧪 Test mode: Ask me 'What is 2 + 2?' to verify Together API is working.",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text or ""
    logging.info(f"Received message: {user_message}")

    # Minimal prompt for API testing
    prompt = f"User: What is 2 + 2?\n\nAssistant:"

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": prompt.strip(),
        "max_tokens": 50,
        "temperature": 0.5,
        "top_p": 1.0
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)

        if response.ok:
            result = response.json()
            logging.info("Together API response:")
            logging.info(result)

            reply = result.get("choices", [{}])[0].get("text", "").strip()
            if not reply:
                reply = "⚠️ Together API returned an empty response."
        else:
            logging.error(f"Together API error {response.status_code}: {response.text}")
            reply = f"❌ Together API error {response.status_code}.\n{response.text[:1000]}"

    except Exception as e:
        logging.exception("Exception while calling Together API")
        reply = f"⚠️ Exception occurred:\n{str(e)}"

    await update.message.reply_text(reply[:4000])

# App entry
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()