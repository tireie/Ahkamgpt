import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

# Setup logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "📿 *AhkamGPT* is ready.\n\n"
        "🕌 أَهلاً وَسَهلاً، كيف يمكنني مساعدتك في أحكام الشريعة؟\n\n"
        "_You can ask questions in Arabic, English, or Farsi._"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings from official sources like khamenei.ir and ajsite.ir. Do not make up rulings. "
        "Language: Match user input."
    )

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:",
        "max_tokens": 512,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)
        if response.ok:
            result = response.json()
            reply = result.get("output", "").strip()

            if reply:
                # Limit Telegram message length
                if len(reply) > 4096:
                    reply = reply[:4093] + "..."

                await update.message.reply_text(reply)
            else:
                await update.message.reply_text("⚠️ Together API returned an empty response.")
        else:
            logging.error(f"Together API error: {response.text}")
            await update.message.reply_text("⚠️ Error from Together API.")
    except Exception as e:
        logging.exception("Exception during Together API call:")
        await update.message.reply_text("⚠️ Exception occurred: " + str(e))

# Main entry point
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()