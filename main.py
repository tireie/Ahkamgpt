import os
import re
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Load tokens from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TELEGRAM_TOKEN or not TOGETHER_API_KEY:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TOGETHER_API_KEY in environment")

# System prompts for English and Arabic users
SYSTEM_PROMPT_EN = (
    "You are an assistant answering Islamic jurisprudence questions. "
    "You must answer *only* based on official fatwas of Sayyed Ali Khamenei from khamenei.ir and ajsite.ir. "
    "Do not guess or provide any other information. Answer concisely and accurately, without verbosity. "
    "If there is no known fatwa for the question, reply exactly: \"There is no known fatwa from Sayyed Ali Khamenei on this topic.\""
)
SYSTEM_PROMPT_AR = (
    "أنت مساعد للإجابة على أسئلة الفقه الإسلامي بناءً فقط على فتاوى رسمية للسيد علي خامنئي من khamenei.ir و ajsite.ir. "
    "لا تقم بالتخمين أو إضافة أي معلومات أخرى. أجب بإيجاز ودقة دون إطالة. "
    "إذا لم توجد فتوى معروفة حول السؤال، فأجب بالضبط: \"لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.\""
)

def is_arabic(text: str) -> bool:
    """Simple check if the text contains Arabic characters."""
    return bool(re.search(r'[\u0600-\u06FF]', text))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text.strip()
    if not user_text:
        return

    # Determine language and set system prompt and fallback accordingly
    if is_arabic(user_text):
        system_prompt = SYSTEM_PROMPT_AR
    else:
        system_prompt = SYSTEM_PROMPT_EN

    # Prepare the payload for Together AI chat completions3
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
    }

    # Call Together API
    try:
        response = httpx.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Extract the assistant's reply
        answer = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # In case of any error, use fallback response
        if is_arabic(user_text):
            answer = "لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع."
        else:
            answer = "There is no known fatwa from Sayyed Ali Khamenei on this topic."

    # Reply to the user
    await update.message.reply_text(answer)

def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    # Handle text messages (excluding commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()