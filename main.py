import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

# Logging setup
logging.basicConfig(level=logging.INFO)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📿 *AhkamGPT* is ready.\n\n"
        "🕌 *السّلامُ عَلَيكُم، كيف يمكنني مساعدتك في أحكام الشريعة؟*\n"
        "🗣️ *Peace be upon you — how can I assist you with Islamic rulings?*\n\n"
        "💡 I answer in Arabic, English, or Farsi, based strictly on Sayyed Ali Khamenei’s official rulings "
        "from sources like khamenei.ir and ajsite.ir. If no ruling is found, I will let you know — no answers will be invented.",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings from official sources such as khamenei.ir and ajsite.ir. "
        "Do not fabricate or assume any answers. If the ruling is not found, reply that it was not located. "
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

        if "output" in data and "choices" in data["output"]:
            reply = data["output"]["choices"][0].get("text", "").strip()
        else:
            reply = "⚠️ Together API returned an invalid response format."

        if not reply:
            reply = "⚠️ Together API returned no valid content."

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