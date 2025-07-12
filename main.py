import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

# Logging
logging.basicConfig(level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📿 *AhkamGPT* is ready.\n\n🕌 أَهلاً وَسَهلاً، كيف يمكنني مساعدتك في أحكام الشريعة؟",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings. Use only official sources like khamenei.ir and ajsite.ir. "
        "Keep the response focused and concise. Language: Match user input."
    )

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:",
        "max_tokens": 400,
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)
        data = response.json()

        # Extract text safely
        raw_output = data.get("output") or data.get("choices", [{}])[0].get("text") or ""
        reply = str(raw_output).strip()

        if not reply:
            reply = "⚠️ Together API returned an empty response."

        # Trim if too long for Telegram
        if len(reply) > 4096:
            reply = reply[:4093] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception occurred:\n{str(e)}")

# Run the bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()