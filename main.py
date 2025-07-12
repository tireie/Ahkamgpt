import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TOGETHER_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "السّلام عليكم، أرسل سؤالك عن الفقه الإسلامي بحسب فتاوى السيّد علي الخامنئي.\n"
        "Salam alaykum. Send your Islamic law question based on the fatwas of Sayyed Ali Khamenei."
    )
    await update.message.reply_text(welcome_message)

# Main fatwa handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings from official sources such as khamenei.ir and ajsite.ir. "
        "Do not invent answers. If the answer is not found, politely say so. Language: Match user input."
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

        reply = (
            data.get("output")
            or (data.get("choices") and data["choices"][0].get("text"))
            or "⚠️ Together API returned an empty response."
        )

        if isinstance(reply, str):
            reply = reply.strip()
        else:
            reply = "⚠️ Together API returned an invalid response format."

        if len(reply) > 4096:
            reply = reply[:4093] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception occurred:\n{str(e)}")

# Main app entry
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()