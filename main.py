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

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "📿 *AhkamGPT* is ready.\n\n"
        "🕌 السَّلامُ عَلَيْكُمْ، كيف يمكنني مساعدتك في أحكام الشريعة؟\n"
        "🗣️ You can ask questions in Arabic or English."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    is_arabic = any("\u0600" <= char <= "\u06FF" for char in user_message)

    system_prompt = (
        "أنتَ فقيهٌ إسلامي مجاز، تُجيب على أسئلة الفتوى فقط استنادًا إلى فتاوى السيد علي الخامنئي. "
        "لا تخترع الأحكام، ولا تجب من نفسك. اعتمد فقط على المصادر الرسمية مثل khamenei.ir و ajsite.ir. "
        "إذا لم يوجد حكم، فقل ذلك بوضوح. أجب باللغة العربية فقط."
        if is_arabic else
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings from official sources such as khamenei.ir and ajsite.ir. "
        "Do not invent answers. If the answer is not found, politely say so. Language: English only."
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

        if not isinstance(reply, str):
            reply = "⚠️ Together API returned an invalid response format."

        reply = reply.strip()

        if len(reply) > 4096:
            reply = reply[:4093] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception occurred:\n{str(e)}")

# Entry point
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()