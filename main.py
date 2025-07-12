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

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📿 *AhkamGPT* is ready.\n\n🕌 أَهلاً وَسَهلاً، كيف يمكنني مساعدتك في أحكام الشريعة؟\n\n"
        "⚖️ I answer based on the rulings of Sayyed Ali Khamenei only.\n"
        "📚 Based on official sources like:\n- https://www.khamenei.ir\n- https://www.ajsite.ir",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings. Language: Match user input. "
        "Use only official sources like khamenei.ir and ajsite.ir. Do not make up rulings."
    )

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:",
        "max_tokens": 512,
        "temperature": 0.3,
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)

        if not response.ok:
            await update.message.reply_text("⚠️ Together API error. Please try again later.")
            return

        result = response.json()
        reply = result.get("output")

        if not reply:
            try:
                reply = result["choices"][0]["text"].strip()
            except Exception:
                reply = "⚠️ Together API returned an empty or invalid response."

        # Trim long replies for Telegram
        if len(reply) > 4096:
            reply = reply[:4093] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception occurred: {str(e)}")

# Main function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()