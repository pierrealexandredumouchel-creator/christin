import re
from modules.admin import add_admin, list_admins
from modules.permissions import is_master, is_trusted
from modules.duckhunt import reset_duck, score, shoot, spawn_duck
from modules import mairie


def handle_command(bot, line):
    parts = line.split(" ")
    user = parts[0].split("!")[0].replace(":", "")
    chan = parts[2]
    msg = " ".join(parts[3:]).replace(":", "", 1)
    hostmask = parts[0][1:]

    # Mairie de #montreal : règlements municipaux, proclamations, conseil.
    if mairie.handle(bot, user, hostmask, chan, msg):
        return

    # GHOST TARGET COMMANDS V3 christine24
    aliases = (
        "!christine",
        "!christine24",
        "!christin",
        "!christin24",
    )

    text = msg.strip()
    lowered = text.casefold()

    alias = next(
        (
            item
            for item in aliases
            if (
                lowered == item
                or lowered.startswith(item + " ")
            )
        ),
        None,
    )

    if alias is not None:
        host = parts[0][1:].casefold()

        print(
            f"[ChristineTarget] "
            f"user={user!r} "
            f"host={host!r} "
            f"msg={msg!r}",
            flush=True,
        )

        allowed = is_master(user, hostmask)

        if not allowed:
            bot.send(chan, f"{user}: accès refusé.")
            return

        payload = text[len(alias):].strip() or "help"
        args = payload.split(maxsplit=2)
        action = args[0].casefold()

        if action == "help":
            bot.send(
                chan,
                "Commandes Christine: help, status, "
                "join, part, say, action. Mairie : !reglement, "
                "!sujets, !arrondissements, !311, !mairesse, "
                "!proclamation, !conseil, !veto.",
            )
            return

        if action == "status":
            bot.send(
                chan,
                "Christine24 online. Routeur ciblé actif.",
            )
            return

        if action in ("join", "part"):
            if len(args) < 2:
                bot.send(
                    chan,
                    f"Usage: !christine {action} #canal",
                )
                return

            channel = args[1]

            if not re.fullmatch(
                r"#[^\x00\x07\r\n ,:]+",
                channel,
            ):
                bot.send(chan, "Canal invalide.")
                return

            if action == "join":
                bot.sock.send(
                    f"JOIN {channel}\r\n".encode()
                )
                bot.send(
                    chan,
                    f"Je rejoins {channel}.",
                )
            else:
                bot.sock.send(
                    (
                        f"PART {channel} "
                        f":Commande de {user}\r\n"
                    ).encode()
                )

            return

        if action in ("say", "action"):
            if len(args) < 3:
                bot.send(
                    chan,
                    f"Usage: !christine {action} "
                    "#canal texte",
                )
                return

            destination = args[1]
            message = " ".join(
                args[2]
                .replace("\r", " ")
                .replace("\n", " ")
                .split()
            )[:350]

            if not re.fullmatch(
                r"#[^\x00\x07\r\n ,:]+",
                destination,
            ):
                bot.send(chan, "Canal invalide.")
                return

            if not message:
                bot.send(chan, "Texte vide.")
                return

            if action == "say":
                bot.send(destination, message)
            else:
                bot.sock.send(
                    (
                        f"PRIVMSG {destination} :"
                        f"\x01ACTION {message}\x01\r\n"
                    ).encode()
                )

            return

        bot.send(
            chan,
            f"Commande inconnue: {action}. "
            "Utilise !christine help.",
        )
        return


    if msg.startswith("!ping"):
        bot.send(chan, "pong")

    if msg.startswith("!hello"):
        bot.send(chan, f"Salut {user}, ici JADE14 Ghost Royale.")

    if msg.startswith("!say "):
        # Réservé aux admins : sinon n'importe qui fait dire n'importe quoi à Christine.
        if not is_trusted(user, hostmask):
            bot.send(chan, f"{user}: Tu n'es pas admin.")
            return
        bot.send(chan, msg[5:])

    if msg.startswith("!duckhunt"):
        spawn_duck(bot, chan)

    if msg.startswith("!shoot"):
        shoot(bot, user, chan)

    if msg.startswith("!score"):
        score(bot, user, chan)

    if msg.startswith("!resetduck"):
        if not is_trusted(user, hostmask):
            bot.send(chan, f"{user}: Tu n'es pas admin.")
            return
        reset_duck(bot, chan)

    if msg.startswith("!addadmin"):
        if not is_master(user, hostmask):
            bot.send(chan, f"{user}: Seul le maitre peut ajouter un admin.")
            return

        bits = msg.split()
        if len(bits) != 3:
            bot.send(chan, "Usage: !addadmin <nick> <hote>  (ex: !addadmin bob bob.users.undernet.org)")
            return
        entry = bits[1] + "@" + bits[2].lstrip("@").lower()
        if add_admin(entry):
            bot.send(chan, f"Admin ajoute: {entry}")
        else:
            bot.send(chan, f"{entry} est deja admin.")
        return

    if msg.startswith("!admins"):
        bot.send(chan, "Admins: " + list_admins())
