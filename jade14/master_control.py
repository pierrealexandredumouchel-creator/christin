MASTER_LIST = ["alxd", "administrator", "root"]

def is_master(nick):
    return nick.lower() in [m.lower() for m in MASTER_LIST]

def handle_master_privmsg(send_raw, send_message, nick, target, message):
    if not is_master(nick):
        return

    parts = message.split(" ", 1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "say" and arg:
        send_message(target, arg)

    elif cmd == "me" and arg:
        send_raw(f"PRIVMSG {target} :\x01ACTION {arg}\x01")

    elif cmd == "ghost" and arg:
        send_message(target, f"<{nick}> {arg}")

    elif cmd == "join" and arg:
        send_raw(f"JOIN {arg}")

    elif cmd == "part" and arg:
        send_raw(f"PART {arg}")

    elif cmd == "raw" and arg:
        send_raw(arg)
