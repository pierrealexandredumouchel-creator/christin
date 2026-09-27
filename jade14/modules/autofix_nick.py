import json
import os
import subprocess

CONFIG_PATH = "/opt/christine24/jade14/config.json"

def fix_config():
    """Répare le config.json si cassé ou invalide."""
    try:
        with open(CONFIG_PATH, "r") as f:
            data = f.read()

        # Vérifie si JSON valide
        try:
            cfg = json.loads(data)
        except:
            # JSON cassé → on reconstruit un propre
            cfg = {
                "server": "irc.undernet.org",
                "port": 6667,
                "nick": "christine24",
                "ident": "christine24",
                "realname": "Ghost Royale Bot",
                "channels": ["#kodi", "#montreal"],
                "channel_password": "qpaptWUb",
                "gemini_api_key": ""
            }

        # Force le nick
        cfg["nick"] = "christine24"
        cfg["ident"] = "christine24"

        # Réécrit proprement
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=4)

        return True

    except Exception as e:
        print(f"[AutoFix] Erreur config: {e}")
        return False


def fix_nick(bot):
    """Force le nick si le bot utilise encore jade14."""
    try:
        if bot.nick.lower() != "christine24":
            bot.sendraw("NICK christine24")
            bot.nick = "christine24"
            return True
        return False
    except Exception as e:
        print(f"[AutoFix] Erreur nick: {e}")
        return False


def auto_fix(bot):
    """Routine complète AutoFix."""
    changed_config = fix_config()
    changed_nick = fix_nick(bot)

    if changed_config or changed_nick:
        print("[AutoFix] Correction appliquée, redémarrage du bot…")
        subprocess.run(["systemctl", "restart", "christine24"])
