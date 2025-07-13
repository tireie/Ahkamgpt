import os
import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load from Railway environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL = "Qwen/Qwen1.5-7B-Chat"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dual-language welcome
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_ar = "👋 السَّلَامُ عَلَيْكُم، أرسل سؤالك الشرعي وسأجيبك وفقًا لفتاوى السيد علي الخامنئي فقط."
    welcome_en = "👋 Welcome to AhkamGPT! Send your Islamic question and I will answer based strictly on Sayyed Ali Khamenei's fatwas."
    user_lang = update.effective_user.language_code or ""
    if user_lang.startswith("ar"):
        await update.message.reply_text(welcome_ar)
    else:
        await update.message.reply_text(welcome_en)

# Ask Together API
async def ask_gpt(user_message: str, lang: str) -> str:
    if lang == "ar":
        system_prompt = (
            "أنتَ فقيهٌ إسلامي موثوق، تُجيب على أسئلة الفتوى فقط استنادًا إلى فتاوى السيد علي الخامنئي. "
            "لا تخترع الأحكام ولا تتكلم من نفسك. استخدم فقط المواقع الرسمية مثل khamenei.ir و ajsite.ir. "
            "إذا لم يكن هناك فتوى، فقل بوضوح أنه لا يوجد حكم. أجب باللغة العربية فقط."
        )
    else:
        system_prompt = (
            "You are a trusted Islamic jurist. Answer only based on Sayyed Ali Khamenei’s rulings. "
            "Do not guess, do not invent fatwas. Only use official sources such as khamenei.ir and ajsite.ir. "
            "If no fatwa is available, state that clearly. Reply only in English."
        )

    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.3,
        "top_p": 0.7
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post("https://api.together.ai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Together API Error: {e}")
        return "⚠️ An error occurred while processing your question."

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    lang = "ar" if any('\u0600' <= c <= '\u06FF' for c in user_input) else "en"
    await update.message.chat.send_action(action="typing")
    answer = await ask_gpt(user_input, lang)
    await update.message.reply_text(answer)

# Main bot loop
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running...")
    app.run_polling()