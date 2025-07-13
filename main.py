import os
import re
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Load required environment variables (Telegram bot token and Together API key)
BOT_TOKEN = os.getenv("BOT_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not BOT_TOKEN or not TOGETHER_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or TOGETHER_API_KEY environment variables.")

# Define the system prompt that instructs the AI model to only use official fatwas.
SYSTEM_PROMPT = (
    "You are an assistant that only provides answers based on the official fatwas of "
    "Sayyed Ali Khamenei (from khamenei.ir or ajsite.ir). Answer **only** with a direct quote or content "
    "from those fatwas, without additional commentary. If you do not know of an official fatwa on the user's question, "
    "respond with exactly:\n"
    "- English: \"There is no known fatwa from Sayyed Ali Khamenei on this topic.\"\n"
    "- Arabic: \"لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.\"\n"
    "Always answer in the same language that the question was asked."
)

def detect_language(text: str) -> str:
    """
    Detect the language of the input text. Returns 'ar' for Arabic and 'en' for English (default).
    """
    # Simple detection: check for Arabic characters
    if re.search(r'[\u0600-\u06FF]', text):
        return 'ar'
    else:
        return 'en'

async def query_together_api(question: str) -> str:
    """
    Send the question to the Together AI chat completion API with the system prompt.
    Returns the model's answer as a string, or None if an error occurred.
    """
    # Prepare the messages payload for the chat completion request
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",  # Mistral-7B-Instruct model (version 0.1)0
        "messages": messages,
        "max_tokens": 512  # limit the response length if needed
    }
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Use asyncio.to_thread to avoid blocking the event loop with a synchronous request
        response = await asyncio.to_thread(
            requests.post, "https://api.together.xyz/v1/chat/completions", 
            headers=headers, json=payload, timeout=15
        )
    except Exception as e:
        print(f"Error connecting to Together API: {e}")
        return None

    if response.status_code != 200:
        # Log non-200 responses for debugging
        print(f"Together API error {response.status_code}: {response.text}")
        return None

    # Parse the JSON response to get the assistant's reply
    data = response.json()
    try:
        # The Together API is OpenAI-compatible for chat; extract the assistant message content1
        answer = data["choices"][0]["message"]["content"]
    except KeyError:
        # Fallback parsing in case of a different response format
        choices = data.get("choices")
        if choices:
            answer = choices[0].get("text", "")
        else:
            answer = ""
    return answer.strip()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming Telegram messages (text only) and send the appropriate response."""
    user_text = (update.message.text or "").strip()
    if not user_text:
        return  # Ignore empty messages or messages with only whitespace

    # Detect the language of the user's question
    lang = detect_language(user_text)
    # Query the Together AI API for an answer based on Khamenei's fatwas
    answer = await query_together_api(user_text)

    # If the API call failed or returned no answer, send the fallback response
    if answer is None or answer == "":
        if lang == 'ar':
            await update.message.reply_text("لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع.")
        else:
            await update.message.reply_text("There is no known fatwa from Sayyed Ali Khamenei on this topic.")
        return

    # If the model responded in the opposite language by mistake, adjust the fallback language
    if lang == 'ar' and answer.lower().startswith("there is no known fatwa"):
        answer = "لا توجد فتوى معروفة من السيد علي الخامنئي حول هذا الموضوع."
    elif lang == 'en' and "لا توجد فتوى" in answer:
        answer = "There is no known fatwa from Sayyed Ali Khamenei on this topic."

    # Reply with the model's answer (already in the appropriate language)
    await update.message.reply_text(answer)

if __name__ == "__main__":
    # Initialize the Telegram bot application for polling
    application = Application.builder().token(BOT_TOKEN).build()
    # Only handle text messages (ignore non-text to avoid errors)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling Telegram for new messages (this will run until the process is stopped)
    print("Bot is polling Telegram for messages...")
    application.run_polling()