from modules.ai import ai_reply

def resume_channel(logfile="/opt/christine24/jade14/logs/irc.log"):
    try:
        with open(logfile, "r") as f:
            data = f.read()[-5000:]
        return ai_reply(f"Résume ce channel IRC: {data}")
    except:
        return "Impossible de lire le log."
