import os
import logging
import requests
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from googletrans import Translator

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

# Logging setup
logging.basicConfig(level=logging.INFO)

# Translator instance
translator = Translator()

# Function to detect Arabic
def is_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📿 *AhkamGPT* is ready.\n\n"
        "🕌 السَّلامُ عَلَيْكُم، كيف يمكنني مساعدتك في أحكام الشريعة؟\n\n"
        "You can ask questions in Arabic, English, or Farsi.",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    is_ar = is_arabic(user_message)

    # Translate Arabic to English
    translated_input = translator.translate(user_message, src='ar', dest='en').text if is_ar else user_message

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings from official sources such as khamenei.ir and ajsite.ir. "
        "Do not invent answers. If the answer is not found, politely say so. "
        "Language: Match user input."
    )

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {system_prompt}\n\nUser: {translated_input}\n\nAssistant:",
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

        if "output" in data and "choices" in data["output"]:
            reply = data["output"]["choices"][0].get("text", "").strip()
        else:
            reply = "⚠️ Together API returned an invalid response format."

        if not reply:
            reply = "⚠️ Together API returned no valid content."

        # Optionally translate back to Arabic
        if is_ar:
            reply = translator.translate(reply, src='en', dest='ar').text

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