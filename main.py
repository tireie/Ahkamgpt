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
    welcome_message = (
        "📿 *AhkamGPT* is ready.\n\n"
        "🕌 أَهلاً وَسَهلاً، كيف يمكنني مساعدتك في أحكام الشريعة؟\n\n"
        "Ask your questions in Arabic, English, or Farsi.\n"
        "_All answers are based on the fatwas of Sayyed Ali Khamenei from official sources such as_ [khamenei.ir](https://khamenei.ir) _and_ [ajsite.ir](https://ajsite.ir)."
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

# Handle all messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings from official sources such as khamenei.ir and ajsite.ir. "
        "Do not invent answers. If the answer is not found, politely say so. "
        "Language: Match user input."
    )

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:",
        "max_tokens": 400,
        "temperature": 0.3,
        "stop": ["User:", "Assistant:"],
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)
        data = response.json()

        if not data:
            reply = "⚠️ Together API returned an empty JSON response."
        elif "output" in data and isinstance(data["output"], str):
            reply = data["output"].strip()
        elif "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
            reply = data["choices"][0].get("text", "").strip()
        else:
            reply = f"⚠️ Unexpected response format:\n```{data}```"

        if not reply:
            reply = "⚠️ Together API returned no valid content."

        if len(reply) > 4096:
            reply = reply[:4093] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception occurred:\n{str(e)}")

# Main entry point
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()