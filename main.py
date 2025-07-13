import os
import re
import asyncio
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env (if present) and system environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("TOGETHER_API_KEY")
if not BOT_TOKEN or not API_KEY:
    logger.error("BOT_TOKEN or TOGETHER_API_KEY is not set in the environment.")
    raise RuntimeError("Missing BOT_TOKEN or TOGETHER_API_KEY environment variables")

def detect_language(text: str) -> str:
    """Simple language detection: returns 'ar' if any Arabic script char is in text, else 'en'. """
    if re.search(r'[\u0600-\u06FF]', text):
        return 'ar'
    return 'en'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages: send query to Qwen2.5-7B-Instruct model and reply with its answer."""
    lang = 'en'
    try:
        # Ensure the update has text (not e.g. sticker)
        if not update.message or not update.message.text:
            return
        user_text = update.message.text
        lang = detect_language(user_text)
        # Prepare system prompt in the appropriate language
        if lang == 'ar':
            system_prompt = (
                "أنت مساعد ذكاء اصطناعي يقدم الإجابات وفقًا لأحكام الفقه الإسلامي لآية الله السيد علي الخامنئي "
                "عندما يكون ذلك مناسبًا. أجب دائمًا بنفس لغة السؤال المطروح من قبل المستخدم."
            )
        else:
            system_prompt = (
                "You are an AI assistant that provides answers according to the Islamic jurisprudence rulings of "
                "Ayatollah Sayyid Ali Khamenei when relevant. Always respond in the same language as the user's question."
            )
        # Build the chat prompt for the model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
        payload = {"model": "Qwen/Qwen2.5-7B-Instruct-Turbo", "messages": messages}
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        # Call Together API (run in a thread to avoid blocking the async loop)
        loop = asyncio.get_running_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload, timeout=60)
            )
        except requests.RequestException as e:
            # Network or connection error
            logger.error("Request to Together API failed: %s", e)
            error_reply = ("Sorry, I couldn't reach the AI service. Please try again later."
                           if lang == 'en' else
                           "عذرًا، لم أتمكن من الوصول إلى خدمة الذكاء الاصطناعي. يرجى المحاولة مرة أخرى لاحقًا.")
            await update.message.reply_text(error_reply)
            return
        if resp.status_code != 200:
            # API returned an error status (e.g., 400 or 500)
            logger.error("Together API returned status %d: %s", resp.status_code, resp.text[:100])
            error_reply = ("Sorry, something went wrong while processing your request."
                           if lang == 'en' else
                           "عذرًا، حدث خطأ ما أثناء معالجة طلبك.")
            await update.message.reply_text(error_reply)
            return
        # Parse the API response
        try:
            data = resp.json()
        except ValueError as e:
            logger.error("Failed to parse JSON from Together API: %s; response text: %.100s", e, resp.text)
            error_reply = ("Sorry, something went wrong while processing the AI response."
                           if lang == 'en' else
                           "عذرًا، حدث خطأ أثناء معالجة الإجابة من الذكاء الاصطناعي.")
            await update.message.reply_text(error_reply)
            return
        # Extract the assistant's answer from the response
        answer = None
        try:
            answer = data.get("choices", [{}])[0].get("message", {}).get("content")
        except Exception as e:
            logger.error("Error extracting answer from response: %s; data: %s", e, data)
        if not answer:
            # If no answer was found in the response
            error_reply = ("Sorry, I couldn't generate an answer at this time."
                           if lang == 'en' else
                           "عذرًا، لم أتمكن من توليد إجابة في هذا الوقت.")
            await update.message.reply_text(error_reply)
            return
        # Send the answer to the user (split into multiple messages if too long for one message)
        if len(answer) <= 4096:
            await update.message.reply_text(answer)
        else:
            for i in range(0, len(answer), 4096):
                part = answer[i:i+4096]
                try:
                    await update.message.reply_text(part)
                except Exception as e:
                    logger.error("Failed to send message part: %s", e)
                    break
    except Exception as e:
        # Catch-all for any unexpected errors in handling
        logger.exception("Unexpected error in handle_message: %s", e)
        error_reply = ("Sorry, something went wrong." if lang == 'en' else "عذرًا، حدث خطأ ما.")
        try:
            await update.message.reply_text(error_reply)
        except Exception:
            pass

if __name__ == "__main__":
    # Initialize the bot application and register the handler
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Start polling for updates (use polling to run on Railway, drop_pending_updates to prevent duplicate handlers)
    application.run_polling(drop_pending_updates=True)