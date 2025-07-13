import os import logging import httpx from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

Load token from environment variable or hardcode for local testing

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN" TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or "YOUR_TOGETHER_API_KEY" MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

Prompt template with language routing

PROMPT_TEMPLATE = '''System: You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. Only use rulings that exist on khamenei.ir or ajsite.ir. Never invent or guess answers. If no ruling exists, reply: "No fatwa is found on this topic." Language: {lang}

User: {question}'''

Logging setup

logging.basicConfig(level=logging.INFO) logger = logging.getLogger("AhkamGPT")

Function to detect language (very basic)

def detect_language(text: str) -> str: if any(c in text for c in "ضصثقفغعهخحجچشسیبلاهتنمکگ1234567890أإآىئءة"): return "Arabic" elif any(c in text for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"): return "English" else: return "English"

Query Together API

async def ask_together(question: str, lang: str) -> str: headers = { "Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json" } payload = { "model": MODEL_NAME, "messages": [ {"role": "system", "content": PROMPT_TEMPLATE.format(lang=lang, question=question)} ], "temperature": 0.2, "top_p": 0.95 }

async with httpx.AsyncClient(timeout=60) as client:
    response = await client.post("https://api.together.ai/v1/chat/completions", json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()

Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🕌 Welcome to AhkamGPT. Ask me Islamic rulings based on Sayyed Ali Khamenei's fatwas in Arabic or English.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): question = update.message.text.strip() lang = detect_language(question) try: reply = await ask_together(question, lang) except Exception as e: logger.error(f"API error: {e}") reply = "⚠️ An error occurred while processing your question." await update.message.reply_text(reply)

Main runner

if name == 'main': app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)) logger.info("✅ Bot is running...") app.run_polling()

