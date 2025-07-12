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

    # Strict system prompt with source restriction
    prompt = f"""
System: You are a qualified Islamic scholar answering fatwas based only on the rulings of Sayyed Ali Khamenei. Do not fabricate or guess answers. Only use verified rulings from official sources such as khamenei.ir and ajsite.ir. If the answer is not found in these sources, reply: "This issue requires direct scholarly consultation."

User: {user_message}

Assistant:"""

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": prompt.strip(),
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)

        if response.ok:
            result = response.json()
            logging.info("Together API response:")
            logging.info(result)

            # Extract assistant reply
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