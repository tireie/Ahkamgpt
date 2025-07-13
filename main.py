import os
import re
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Load tokens
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or OPENROUTER_API_KEY")

# System prompts
SYSTEM_PROMPT_EN = (
    "You are a trusted Islamic jurist answering only based on the official religious rulings (fatwas) of "
    "Sayyed Ali Khamenei. Use only official sources such as khamenei.ir and ajsite.ir.\n\n"
    "You must:\n"
    "1. Only provide rulings explicitly found in Sayyed Khamenei’s official fatwas.\n"
    "2. Never guess, generalize, or use rulings from other scholars.\n"
    "3. If no fatwa exists, reply: \"There is no known fatwa from Sayyed Ali Khamenei on this topic.\"\n"
    "4. Answer in the user's language. Be concise, accurate, and avoid personal interpretation."
)

SYSTEM_PROMPT_AR = (
    "أنت فقيه إسلامي موثوق تجيب فقط استنادًا إلى الفتاوى الرسمية للسيد علي الخامنئي. "
    "استخدم فقط المصادر الرسمية مثل khamenei.ir و ajsite.ir.\n\n"
    "يجب عليك:\n"
    "1. تقديم الأحكام الموجودة فقط في فتاوى السيد علي الخامنئي.\n"
    "2. لا تخمن أو تعمم أو تستخدم فتاوى من مراجع آخرين.\n"
    "3. إذا لم توجد فتوى، أجب: \"لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.\"\n"
    "4. أجب بلغة المستخدم بدقة واختصار، دون تفسير شخصي."
)

# Language detection
def is_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# Qwen model via OpenRouter
MODEL_ID = "qwen/qwen3-30b-a3b"

async def ask_openrouter(system_prompt: str, user_input: str) -> str:
    try:
        response = await httpx.AsyncClient().post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://yourdomain.com",  # optional
                "X-Title": "AhkamGPT Fatwa Bot"
            },
            json={
                "model": MODEL_ID,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.2,
                "max_tokens": 512
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return (
            "لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع." if is_arabic(user_input)
            else "There is no known fatwa from Sayyed Ali Khamenei on this topic."
        )

# Telegram handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    if not user_input:
        return
    system_prompt = SYSTEM_PROMPT_AR if is_arabic(user_input) else SYSTEM_PROMPT_EN
    reply = await ask_openrouter(system_prompt, user_input)
    await update.message.reply_text(reply)

# Main entry
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("AhkamGPT bot (Qwen3) started.")
    app.run_polling()

if __name__ == "__main__":
    main()