import os import logging import requests from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

Load environment variables

BOT_TOKEN = os.environ.get("BOT_TOKEN") TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY") TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

Logging setup

logging.basicConfig(level=logging.INFO)

Detect if text is Arabic

def is_arabic(text): return any('\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' or '\u08A0' <= char <= '\u08FF' for char in text)

/start command handler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "📿 AhkamGPT is ready.\n\n" "🕌 السلام عليكم، كيف يمكنني مساعدتك في أحكام الشريعة؟\n\n" "You can ask questions in Arabic, English, or Farsi.", parse_mode="Markdown" )

Message handler

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): user_message = update.message.text.strip() arabic = is_arabic(user_message)

system_prompt = (
    "أنت فقيه إسلامي مؤهل تجيب عن الأسئلة الفقهية وفقًا لفتاوى السيد علي الخامنئي فقط، بالاستناد إلى المصادر الرسمية مثل khamenei.ir و ajsite.ir. لا تخترع أجوبة، وإن لم تجد الحكم فاذكر ذلك بأدب."
    if arabic else
    "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. Only answer based on his rulings from official sources such as khamenei.ir and ajsite.ir. Do not invent answers. If the answer is not found, politely say so. Language: Match user input."
)

payload = {
    "model": TOGETHER_MODEL,
    "prompt": f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:",
    "max_tokens": 400,
    "temperature": 0.3,
    "stop": ["User:", "Assistant:"]
}

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
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

Run the bot

def main(): app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) app.run_polling()

if name == "main": main()

