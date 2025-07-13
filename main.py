import os, re, logging, sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import httpx

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load tokens from Railway environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not BOT_TOKEN or not TOGETHER_API_KEY:
    logging.error("Missing BOT_TOKEN or TOGETHER_API_KEY environment variable.")
    sys.exit(1)

# Detect Arabic text
def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_lang = update.effective_user.language_code if update.effective_user else ""
    if user_lang.lower().startswith("ar"):
        await update.message.reply_text(
            "👋 مرحبًا! أرسل سؤالك الشرعي وسأجيبك فقط وفقًا لفتاوى سماحة السيد علي الخامنئي من المصادر الرسمية."
        )
    else:
        await update.message.reply_text(
            "👋 Welcome! Send your Islamic question and I will answer strictly based on Sayyed Ali Khamenei's official rulings."
        )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = (update.message.text or "").strip()
    if not user_text:
        return

    is_arabic = contains_arabic(user_text)

    system_prompt = (
        "You are a qualified Islamic scholar. Answer fatwa questions strictly based on Sayyed Ali Khamenei’s rulings. "
        "Only use khamenei.ir and ajsite.ir as references. "
        "If no official fatwa exists, say so. Do not guess or invent. "
        f"Answer in {'Arabic' if is_arabic else 'English'}."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]

    try:
        await update.message.reply_chat_action("typing")
    except Exception as e:
        logging.warning(f"Chat action failed: {e}")

    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 1000
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logging.error(f"API Error: {e}")
        msg = "عذرًا، حدث خطأ في الخدمة. حاول لاحقًا." if is_arabic else "Sorry, the service is currently unavailable. Please try again later."
        await update.message.reply_text(msg)
        return

    reply_text = ""
    if data.get("choices"):
        reply = data["choices"][0]
        if reply.get("message") and reply["message"].get("content"):
            reply_text = reply["message"]["content"]
        elif reply.get("text"):
            reply_text = reply["text"]

    if not reply_text.strip():
        reply_text = "لا توجد فتوى متاحة لهذا السؤال." if is_arabic else "No fatwa is available for this question."

    await update.message.reply_text(reply_text.strip())

# Launch bot
def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__