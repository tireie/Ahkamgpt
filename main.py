import os, re, logging, sys from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters import httpx

Configure logging

logging.basicConfig( format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO )

Load tokens from environment variables

BOT_TOKEN = os.environ.get("BOT_TOKEN") TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY") if not BOT_TOKEN or not TOGETHER_API_KEY: logging.error("Missing BOT_TOKEN or TOGETHER_API_KEY environment variable.") sys.exit(1)

Helper function to detect Arabic text

def contains_arabic(text: str) -> bool: return bool(re.search(r'[\u0600-\u06FF]', text))

/start command handler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: user_lang = update.effective_user.language_code if update.effective_user else None if user_lang and user_lang.lower().startswith("ar"): welcome_text = ( "\u0645\u0631\u062d\u0628\u0627\u064b! \u0623\u0646\u0627 \u0628\u0648\u062a \u0627\u0644\u0641\u062a\u0627\u0648\u0649. " "\u064a\u0645\u0643\u0646\u0646\u064a \u0627\u0644\u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0623\u0633\u0626\u0644\u062a\u0643 \u0628\u0646\u0627\u0621\u064b \u0639\u0644\u0649 \u0627\u0644\u0641\u062a\u0627\u0648\u0649 \u0627\u0644\u0631\u0633\u0645\u064a\u0629 \u0644\u0633\u0645\u0627\u062d\u0629 \u0627\u0644\u0633\u064a\u062f \u0639\u0644\u064a \u0627\u0644\u062e\u0627\u0645\u0646\u0626\u064a. " "\u0627\u0643\u062a\u0628 \u0633\u0624\u0627\u0644\u0643 \u0644\u0623\u0633\u0627\u0639\u062f\u0643." ) else: welcome_text = ( "Hello! I am a fatwa assistant bot. " "I can answer your questions based on the official fatwas of Sayyed Ali Khamenei. " "Please send your question, and I will assist you." ) await update.message.reply_text(welcome_text)

Message handler for user queries

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: user_text = (update.message.text or "").strip() if not user_text: return

is_arabic = contains_arabic(user_text)

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

try:
    await update.message.reply_chat_action("typing")
except Exception as e:
    logging.warning(f"Failed to send chat action: {e}")

api_url = "https://api.together.xyz/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": "mistralai/Mistral-7B-Instruct-v0.3",
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
    if is_arabic:
        await update.message.reply_text("\u0639\u0630\u0631\u0627\u064b\u060c \u0627\u0644\u062e\u062f\u0645\u0629 \u063a\u064a\u0631 \u0645\u062a\u0627\u062d\u0629 \u062d\u0627\u0644\u064a\u0627\u064b. \u064a\u0631\u062c\u0649 \u0627\u0644\u0645\u062d\u0627\u0648\u0644\u0629 \u0644\u0627\u062d\u0642\u0627\u064b.")
    else:
        await update.message.reply_text("Sorry, the service is currently unavailable. Please try again later.")
    return

reply_text = None
if data.get("choices"):
    first_choice = data["choices"][0]
    if first_choice.get("message") and first_choice["message"].get("content"):
        reply_text = first_choice["message"]["content"]
    elif first_choice.get("text"):
        reply_text = first_choice["text"]

if not reply_text or not reply_text.strip():
    reply_text = "\u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u062a\u0648\u0649 \u0645\u062a\u0627\u062d\u0629 \u0644\u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644." if is_arabic else "No fatwa is available for this question."

await update.message.reply_text(reply_text.strip())

def main() -> None: application = ApplicationBuilder().token(BOT_TOKEN).build() application.add_handler(CommandHandler("start", start)) application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) application.run_polling()

if name == "main": main()

