"""Commandes privilégiées de Christine (menu mIRC du maître).

Un maître est reconnu par son pseudo ET son hôte : un pseudo seul se vole
en deux secondes sur Undernet. Pas de commande « raw » : elle permettait
d'envoyer n'importe quoi au serveur au nom du bot.
"""

MASTERS = {
    "alxd": (
        "@alxd.kekistan.faith",
        "@alerion.users.undernet.org",
    ),
}


def is_master(nick, hostmask):
    """hostmask : préfixe IRC complet, ex. « alxd!~alxd@alxd.kekistan.faith »."""
    allowed_hosts = MASTERS.get(str(nick).casefold())
    if not allowed_hosts:
        return False
    hostmask = str(hostmask).casefold()
    return any(host in hostmask for host in allowed_hosts)


def _clean(text):
    # Empêche d'injecter une deuxième commande IRC via un saut de ligne.
    return str(text).replace("\r", "").replace("\n", "").strip()


def handle_master_privmsg(send_raw, send_message, nick, hostmask, target, message):
    if not is_master(nick, hostmask):
        return False

    parts = _clean(message).split(" ", 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "say" and arg:
        send_message(target, arg)

    elif cmd == "me" and arg:
        send_raw(f"PRIVMSG {target} :\x01ACTION {arg}\x01")

    elif cmd == "ghost" and arg:
        send_message(target, f"<{nick}> {arg}")

    elif cmd == "join" and arg.startswith("#"):
        send_raw(f"JOIN {arg.split()[0]}")

    elif cmd == "part" and arg.startswith("#"):
        send_raw(f"PART {arg.split()[0]}")

    else:
        return False

    return True
