async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    system_prompt = (
        "You are a qualified Islamic scholar answering fatwas based on Sayyed Ali Khamenei's jurisprudence. "
        "Only answer based on his rulings. Language: Match user input. "
        "Use only official sources like khamenei.ir and ajsite.ir. Do not make up rulings."
    )

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": TOGETHER_MODEL,
        "prompt": f"System: {system_prompt}\n\nUser: {user_message}\n\nAssistant:",
        "max_tokens": 512,
        "temperature": 0.3,
    }

    try:
        response = requests.post("https://api.together.xyz/inference", headers=headers, json=payload)

        if not response.ok:
            await update.message.reply_text("⚠️ Together API error. Please try again later.")
            return

        result = response.json()

        # Safely extract text
        reply = result.get("output") or result.get("choices", [{}])[0].get("text") or ""

        if not isinstance(reply, str):
            reply = str(reply)

        reply = reply.strip()

        # Enforce Telegram limit
        if len(reply) > 4096:
            reply = reply[:4093] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Exception occurred: {str(e)}")