import os
import re
import logging
import sys
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    logging.error("Missing BOT_TOKEN or OPENROUTER_API_KEY.")
    sys.exit(1)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Trusted source list
TRUSTED_SOURCES = [
    "leader.ir",
    "khamenei.ir",
    "abna24.com",
    "al-islam.org",
    "ajsite.ir"  # Additional verified source
]

# System prompts
SYSTEM_PROMPT_EN = (
    "You are a qualified Islamic jurist answering fatwas based strictly on the official rulings of Sayyed Ali Khamenei. "
    "You must only use fatwas published on the following official and trusted websites:\n"
    "- leader.ir\n- khamenei.ir\n- abna24.com\n- al-islam.org\n- ajsite.ir\n\n"
    "Do not guess, generalize, or use rulings from other scholars. "
    "If no fatwa is known, respond with: \"There is no known fatwa from Sayyed Ali Khamenei on this topic.\"\n"
    "Always answer in the user's language. Be accurate, concise, and use only confirmed rulings from the listed sources."
)

SYSTEM_PROMPT_AR = (
    "أنت فقيه إسلامي تجيب عن الأسئلة الشرعية استنادًا فقط إلى الفتاوى الرسمية للسيد علي الخامنئي. "
    "يجب أن تستند إجاباتك حصراً إلى الفتاوى المنشورة على المواقع التالية:\n"
    "- leader.ir\n- khamenei.ir\n- abna24.com\n- al-islam.org\n- ajsite.ir\n\n"
    "لا تخمّن ولا تعمم، ولا تستخدم فتاوى من مراجع آخرين. "
    "إذا لم توجد فتوى، أجب: \"لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.\"\n"
    "أجب دائمًا بلغة المستخدم بدقة واختصار، واستند فقط إلى المصادر المذكورة أعلاه."
)

# Welcome message
WELCOME_MESSAGE = (
    "🕌 **As-salamu alaykum wa rahmatullah**\n\n"
    "Welcome to Ahkam GPT — your assistant for verified Islamic rulings (fatwas) "
    "based strictly on the jurisprudence of Sayyed Ali Khamenei.\n\n"
    "💬 You may ask questions in English or Arabic.\n"
    "🔹 Example: *Can I fast while breastfeeding?*\n"
    "🔹 مثال: *ما حكم بلع بقايا الطعام أثناء الصيام؟*\n\n"
    "أهلاً وسهلاً بكم في بوت أحكام — المساعد الشرعي للإجابة عن الأسئلة الفقهية "
    "استنادًا حصريًا إلى فتاوى السيد علي الخامنئي.\n\n"
    "🗣 يمكنكم طرح الأسئلة بالعربية أو الإنجليزية."
)

# Detect Arabic
def is_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# Ask OpenRouter
async def ask_openrouter(system_prompt: str, user_input: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://yourdomain.com",
                    "X-Title": "AhkamGPT Fatwa Bot"
                },
                json={
                    "model": "qwen/qwen3-32b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 512
                }
            )
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenRouter error: {e}")
        return (
            "لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع."
            if is_arabic(user_input)
            else "There is no known fatwa from Sayyed Ali Khamenei on this topic."
        )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_input = update.message.text.strip()
    system_prompt = SYSTEM_PROMPT_AR if is_arabic(user_input) else SYSTEM_PROMPT_EN
    reply = await ask_openrouter(system_prompt, user_input)
    await update.message.reply_text(reply)

# Start handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("AhkamGPT is running (Qwen3 32B via OpenRouter)...")
    app.run_polling()

if __name__ == "__main__":
    main()