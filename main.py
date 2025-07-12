import os import logging import requests from telegram import Update from telegram.ext import ( ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters )

Set up logging

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

Load environment variables

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY") TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "Qwen1.5B-Instruct") TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

SYSTEM_PROMPT = ( "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's rulings." " Only respond based on verified fatwas from khamenei.ir or ajsite.ir." " If no clear fatwa exists, reply clearly that the ruling is not available." " Respond in the same language used by the user." )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "السلام عليكم، أرسل سؤالك الشرعي وسأجيبك حسب فتاوى السيد علي الخامنئي. \n\nSalam Alaikum! Send your question and I will answer based on the rulings of Sayyed Ali Khamenei." )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): user_message = update.message.text.strip()

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": TOGETHER_MODEL,
    "prompt": f"System: {SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:",
    "max_tokens": 512,
    "temperature": 0.3
}

try:
    response = requests.post(
        "https://api.together.xyz/inference",
        headers=headers,
        json=payload,
        timeout=30
    )
    data = response.json()

    reply = ""
    if "output" in data:
        if isinstance(data["output"], str):
            reply = data["output"].strip()
        elif isinstance(data["output"], dict) and "choices" in data["output"]:
            reply = data["output"]["choices"][0].get("text", "").strip()
    elif "choices" in data:
        reply = data["choices"][0].get("text", "").strip()
    else:
        reply = "⚠️ Together API did not return a valid response."

except Exception as e:
    logging.error(f"Error communicating with Together API: {e}")
    reply = "⚠️ An error occurred while retrieving the fatwa. Please try again later."

await update.message.reply_text(reply)

if name == 'main': app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) app.run_polling()

