import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Replace with your Together.ai model
TOGETHER_API_URL = "https://api.together.xyz/v1/completions"
TOGETHER_MODEL = "Qwen1.5-14B-Chat"  # Or your preferred model
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")

SYSTEM_PROMPT = """
You are a qualified Islamic scholar answering fatwas based on the rulings of Sayyed Ali Khamenei. Only answer based on his rulings.
Language: Respond in the language of the question — either Arabic or English.
"""

async def ask_gpt(user_input: str) -> str:
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {SYSTEM_PROMPT}\nUser: {user_input}\nAssistant:",
        "max_tokens": 512,
        "temperature": 0.2,
        "top_p": 0.95,
        "stop": ["User:", "System:"]
    }

    response = requests.post(TOGETHER_API_URL, headers=headers, json=data)
    
    try:
        result = response.json()
        return result.get("choices", [{}])[0].get("text", "⚠️ No valid response from model.")
    except Exception as e:
        logger.error(f"Error parsing Together API response: {e}")
        return "⚠️ Together API did not return a valid response."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await update.message.chat.send_action(action="typing")
    answer = await ask_gpt(user_input)
    await update.message.reply_text(answer)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("السلام عليكم! اسألني عن أحكام الشريعة الإسلامية حسب فتاوى السيد علي الخامنئي.")

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token or not TOGETHER_API_KEY:
        logger.error("Missing TELEGRAM_TOKEN or TOGETHER_API_KEY in environment variables.")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()