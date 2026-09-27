from modules.ai import ai_reply

def anti_flood(bot, user, channel, message):
    prompt = f"Analyse si ceci est du flood ou spam: {message}. Répond 'oui' ou 'non'."
    reply = ai_reply(prompt).lower()
    if "oui" in reply:
        bot.sendmsg(channel, f"{user}, arrête de flood.")
