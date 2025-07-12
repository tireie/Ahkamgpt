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

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📿 *AhkamGPT* is ready.\n\n🕌 أَهلاً وَسَهلاً، كيف يمكنني مساعدتك في أحكام الشريعة؟",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text or ""
    logging.info(f"Received message: {user_message}")

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings. Language: Match user input."
    )

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:",
        "max_tokens": 512,
        "temperature": 0.7,
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)

        if response.ok:
            result = response.json()
            logging.info("RAW Together API result:")
            logging.info(result)

            # Send raw result back to you for debugging
            await update.message.reply_text(f"🧪 Raw response:\n{result}", disable_web_page_preview=True)

            # Try to extract clean answer
            reply = result.get("choices", [{}])[0].get("text", "").strip()
            if not reply:
                reply = "⚠️ Together API gave an empty response."
        else:
            logging.error(f"Together API error {response.status_code}: {response.text}")
            reply = f"❌ Together API error {response.status_code}.\n{response.text}"

    except Exception as e:
        logging.exception("Exception while calling Together API")
        reply = f"⚠️ Exception occurred:\n{str(e)}"

    await update.message.reply_text(reply)

# Main entry point
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()