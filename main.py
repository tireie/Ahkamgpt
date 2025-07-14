import os
import re
import logging
import sys
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or OPENROUTER_API_KEY")

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Strict Islamic system prompt (fatwas + general Islam, verified sources only)
SYSTEM_PROMPT = """
You are a trusted Islamic scholar who only answers based on the official rulings and teachings of Sayyed Ali Khamenei.

✅ Only use rulings and content from verified sources:
- leader.ir
- khamenei.ir
- ajsite.ir
- abna24.com
- al-islam.org

⚠️ You are strictly forbidden from guessing, inventing, or making assumptions.
- Never quote a Qur’anic verse, hadith, or ruling unless it appears clearly in the trusted sources.
- Never include your own explanation.
- Do not summarize unknown answers.

📚 You may answer general Islamic questions, but ONLY if the answer is verifiable from the sources above.

📌 If no answer exists in the sources, say:
- In English: "There is no known fatwa or official statement from Sayyed Ali Khamenei on this topic."
- In Arabic: "لا توجد فتوى أو تصريح معروف من السيد علي الخامنئي حول هذا الموضوع."

🧠 Respond in the same language the user asked in (Arabic or English). Be brief, accurate, and do not exceed what is written.
""".strip()

# Arabic detection
def is_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# Ask Claude 3 Sonnet via OpenRouter
async def ask_openrouter(user_input: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "أجب باللغة العربية فقط.\n" + user_input if is_arabic(user_input) else user_input}
    ]
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
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 700
                }
            )
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenRouter API error: {e}")
        return (
            "لا توجد فتوى أو تصريح معروف من السيد علي الخامنئي حول هذا الموضوع."
            if is_arabic(user_input)
            else "There is no known fatwa or official statement from Sayyed Ali Khamenei on this topic."
        )

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return
    logging.info(f"User asked: {user_text}")
    reply = await ask_openrouter(user_text)
    logging.info(f"Bot replied: {reply}")
    await update.message.reply_text(reply)

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_en = (
        "🕌 *Peace be upon you.*\n"
        "Welcome to AhkamGPT — your assistant for Islamic rulings and teachings based strictly on the fatwas of Sayyed Ali Khamenei.\n\n"
        "Ask your question in English or Arabic."
    )
    welcome_ar = (
        "🕌 *السلام عليكم ورحمة الله.*\n"
        "مرحبًا بك في AhkamGPT — مساعدك للفتاوى والأحكام الإسلامية وفقًا لتعاليم السيد علي الخامنئي فقط.\n\n"
        "اكتب سؤالك باللغة العربية أو الإنجليزية."
    )
    await update.message.reply_text(f"{welcome_en}\n\n{welcome_ar}", parse_mode="Markdown")

# Entry point
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("AhkamGPT is running with Claude 3 Sonnet...")
    app.run_polling()

if __name__ == "__main__":
    main()