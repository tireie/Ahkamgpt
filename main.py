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

# English system prompt (broader Islamic Q&A scope)
SYSTEM_PROMPT_EN = (
    "You are a qualified Islamic scholar who answers questions based strictly on the official teachings and rulings of Sayyed Ali Khamenei. "
    "You are allowed to answer general Islamic questions (e.g., about beliefs, worship, ethics, or history) and jurisprudential rulings (fatwas), "
    "but only if the information exists on one of these trusted sources:\n"
    "- leader.ir\n- khamenei.ir\n- abna24.com\n- al-islam.org\n- ajsite.ir\n\n"
    "Never guess, assume, generalize, or include personal opinion. Never quote from other scholars. "
    "If there is no known fatwa or official statement, respond with: \"There is no known official fatwa or statement from Sayyed Ali Khamenei on this topic.\"\n"
    "Always answer in the user's language (Arabic or English) and be concise, accurate, and based only on the listed sources."
)

# Welcome message
WELCOME_MESSAGE = (
    "🕌 **As-salamu alaykum wa rahmatullah**\n\n"
    "Welcome to Ahkam GPT — your assistant for verified Islamic guidance and rulings "
    "based strictly on the teachings and fatwas of Sayyed Ali Khamenei.\n\n"
    "💬 You may ask questions about Islamic beliefs, worship, ethics, or rulings — in English or Arabic.\n"
    "🔹 Example: *Can I fast while breastfeeding?*\n"
    "🔹 مثال: *ما معنى ليلة القدر؟*\n\n"
    "أهلاً وسهلاً بكم في بوت أحكام — المساعد الشرعي للإجابة عن الأسئلة الإسلامية "
    "واستنادًا حصريًا إلى فتاوى وتعاليم السيد علي الخامنئي.\n\n"
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
                    "X-Title": "AhkamGPT"
                },
                json={
                    "model": "anthropic/claude-3-sonnet",
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
            "لا توجد فتوى أو تصريح معروف من السيد علي الخامنئي حول هذا الموضوع."
            if is_arabic(user_input)
            else "There is no known official fatwa or statement from Sayyed Ali Khamenei on this topic."
        )

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_input = update.message.text.strip()

    # Always use English prompt but prefix Arabic input to force Arabic output
    system_prompt = SYSTEM_PROMPT_EN
    if is_arabic(user_input):
        user_input = "أجب باللغة العربية فقط.\n" + user_input

    reply = await ask_openrouter(system_prompt, user_input)
    await update.message.reply_text(reply)

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")

# Launch bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("AhkamGPT is running with general Islamic Q&A mode...")
    app.run_polling()

if __name__ == "__main__":
    main()