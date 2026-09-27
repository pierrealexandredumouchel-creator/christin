from modules.ai import ai_reply

def auto_voice(bot, user, channel, message):
    prompt = f"Décide si cet utilisateur mérite +v sur IRC: {user} dit: {message}. Répond 'oui' ou 'non'."
    reply = ai_reply(prompt).lower()
    if "oui" in reply:
        bot.sendraw(f"MODE {channel} +v {user}")
