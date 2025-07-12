import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ENV variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = os.environ.get("TOGETHER_MODEL", "Qwen2.5-7B-Instruct")  # change if needed

# Logging
logging.basicConfig(level=logging.INFO)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📿 *AhkamGPT* is ready.\n\n"
        "🕌 السَّلَامُ عَلَيْكُم، كيف يمكنني مساعدتك في أحكام الشريعة؟\n"
        "💬 You can ask questions in Arabic or English.",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text or ""
    user_message = user_message.strip()

    # Detect language (basic check)
    is_arabic = any('\u0600' <= c <= '\u06FF' for c in user_message)

    if is_arabic:
        system_prompt = (
            "أنتَ فقيهٌ إسلامي مجاز، تُجيب على أسئلة الفتوى فقط استنادًا إلى فتاوى السيد علي الخامنئي. "
            "لا تخترع الأحكام، ولا تجب من نفسك. "
            "اعتمد فقط على المصادر الرسمية مثل khamenei.ir و ajsite.ir. "
            "إذا لم يوجد حكم، فقل ذلك بوضوح. أجب باللغة العربية فقط."
        )
    else:
        system_prompt = (
            "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
            "Only answer based on rulings from official sources like khamenei.ir and ajsite.ir. "
            "Do not invent answers. If no ruling is found, say so clearly. Language: Match user input."
        )

    prompt = f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:"

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": prompt,
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

        # Extract model output
        reply = ""
        if "output" in data:
            if isinstance(data["output"], dict) and "choices" in data["output"]:
                reply = data["output"]["choices"][0].get("text", "").strip()
            elif isinstance(data["output"], str):
                reply = data["output"].strip()
            else:
                reply = "⚠️ Together API returned an unrecognized format."
        else:
            reply = "⚠️ Together API did not return a valid response."

        if not reply:
            reply = "⚠️ Together API returned no valid content."

        if len(reply) > 4096:
            reply = reply[:4093] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception occurred:\n{str(e)}")

# Run bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()