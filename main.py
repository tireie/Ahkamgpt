import os, re, logging, sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import httpx

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load tokens from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not BOT_TOKEN or not TOGETHER_API_KEY:
    logging.error("Missing BOT_TOKEN or TOGETHER_API_KEY environment variable.")
    sys.exit(1)

# Helper function to detect Arabic text
def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Choose Arabic or English based on the user's language setting
    user_lang = update.effective_user.language_code if update.effective_user else None
    if user_lang and user_lang.lower().startswith("ar"):
        welcome_text = (
            "مرحبًا! أنا بوت الفتاوى. "
            "يمكنني الإجابة عن أسئلتك بناءً على الفتاوى الرسمية لسماحة السيد علي الخامنئي. "
            "اكتب سؤالك لأساعدك."
        )
    else:
        welcome_text = (
            "Hello! I am a fatwa assistant bot. "
            "I can answer your questions based on the official fatwas of Sayyed Ali Khamenei. "
            "Please send your question, and I will assist you."
        )
    await update.message.reply_text(welcome_text)

# Message handler for user queries
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = (update.message.text or "").strip()
    if not user_text:
        return  # ignore empty messages
    
    # Detect language of the user message
    is_arabic = contains_arabic(user_text)
    
    # System prompt enforcing fatwa-only policy and proper language response
    system_prompt = (
        "You are an AI assistant that strictly answers questions based on the official religious rulings (fatwas) of "
        "Sayyed Ali Khamenei. Use only information from official sources such as Khamenei’s official website (khamenei.ir) "
        "or Ajwiba (ajsite.ir). If the user's question is in Arabic, provide your answer in Arabic; if the question is in English, "
        "provide your answer in English. Do not provide any answer that is not supported by Sayyed Ali Khamenei’s fatwas. "
        "Do not guess or provide unofficial information. If there is no relevant fatwa available, state clearly that no fatwa is available on the topic."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]
    
    # Show "typing" action while processing
    try:
        await update.message.reply_chat_action("typing")
    except Exception as e:
        logging.warning(f"Failed to send chat action: {e}")
    
    # Prepare API request to Together AI
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Qwen/Qwen1.5-7B-Chat",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.0
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(api_url, json=payload, headers=headers, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logging.error(f"API request failed: {e}")
        # Send a fallback error message to the user
        if is_arabic:
            await update.message.reply_text("عذرًا، الخدمة غير متاحة حاليًا. الرجاء المحاولة مرة أخرى لاحقًا.")
        else:
            await update.message.reply_text("Sorry, the service is currently unavailable. Please try again later.")
        return
    
    # Extract reply from API response
    reply_text = None
    if data.get("choices"):
        first_choice = data["choices"][0]
        # Check the expected chat completion format
        if first_choice.get("message") and first_choice["message"].get("content"):
            reply_text = first_choice["message"]["content"]
        elif first_choice.get("text"):
            reply_text = first_choice["text"]
    
    # Handle case with no content (no fatwa available or empty response)
    if not reply_text or not reply_text.strip():
        if is_arabic:
            reply_text = "لا توجد فتوى متاحة لهذا السؤال."
        else:
            reply_text = "No fatwa is available for this question."
    
    # Send the answer back to the user
    await update.message.reply_text(reply_text.strip())

def main() -> None:
    # Initialize the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Start the bot (polling Telegram for new messages)
    application.run_polling()

if __name__ == "__main__":
    main()