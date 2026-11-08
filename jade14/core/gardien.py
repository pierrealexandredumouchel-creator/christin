"""Gardien : Christine et Tanya veillent sur Daniel (danou) et Marc.

Pas d'IRC à apprendre pour eux : les bots s'en occupent.
- Christine (« protectrice ») : accueille Daniel et Marc, et prend leur défense
  sur le canal si quelqu'un les kicke ou les bannit.
- Tanya (« tactique ») : avertit alxd en privé et réinvite la personne kickée.

Jamais de contre-attaque automatique (pas de kick, pas d'unban) : les bots ne se
battent pas avec les ops du canal.

    gardien(ligne_irc, nick_du_bot, role) -> liste de lignes IRC brutes à envoyer
"""
import fnmatch
import random
import time

MAITRE = "alxd"

# Daniel se connecte avec KVIrc (ident « kvirc »), Marc avec l'ident « marc_m ».
# Le nick seul ne suffit pas : l'ident ET le fournisseur doivent correspondre.
PROTEGES = {
    "daniel": {
        "nicks": ("danou", "danou44", "danou_", "danou44_"),
        "idents": ("kvirc", "danou"),
        "hotes": (".videotron.ca",),
        "nom": "Daniel",
    },
    "marc": {
        "nicks": ("marc", "marc_m", "marc_", "marc_m_"),
        "idents": ("marc_m", "marc"),
        "hotes": (".videotron.ca",),
        "nom": "Marc",
    },
}

# Ceux qui ont le droit de kicker sans que les gardiennes réagissent.
CONFIANCE_HOTES = ("@alxd.kekistan.faith", "@alerion.users.undernet.org", "@pandemie.users.undernet.org")

ACCUEIL = {
    "daniel": (
        "Danou est dans la place 🛡️ Bienvenue chez vous, Daniel. Si quelqu'un te niaise, Christine veille.",
        "Salut Daniel 🛡️ Installe-toi, je garde la porte.",
        "Ah, Danou ! Le canal est plus solide quand t'es là 🛡️",
    ),
    "marc": (
        "Marc est arrivé 🛡️ Salut Marc ! Christine monte la garde, t'as rien à craindre ici.",
        "Bienvenue Marc 🛡️ Pis… alxd te cherche pour un dîner. T'es libre quand ? 😉",
        "Marc ! Enfin 🛡️ Petite mission pour toi : un dîner avec alxd. Je surveille ta réponse.",
    ),
}

DEFENSE = (
    "Hé, on touche pas à {nom} 🛡️ Il est sous la protection de Christine.",
    "{nom} est un ami de la maison 🛡️ On se calme, la gang.",
    "Doucement 🛡️ {nom}, c'est de la famille ici.",
)

_vus = {}        # clé -> dernier « nick!ident@hote » connu
_accueillis = {}  # (clé, canal) -> moment du dernier accueil
DELAI_ACCUEIL = 4 * 3600


def _decoupe(prefixe):
    nick, _, reste = prefixe.partition("!")
    ident, _, hote = reste.partition("@")
    return nick, ident.lstrip("~").casefold(), hote.casefold()


def qui(prefixe):
    """Clé du protégé (« daniel », « marc ») si le préfixe IRC correspond, sinon None."""
    nick, ident, hote = _decoupe(prefixe)
    for cle, p in PROTEGES.items():
        if (nick.casefold() in p["nicks"]
                and ident in p["idents"]
                and hote.endswith(p["hotes"])):
            return cle
    return None


def _de_confiance(prefixe):
    p = prefixe.casefold()
    return any(h in p for h in CONFIANCE_HOTES)


def _cible_du_ban(masque):
    m = masque.casefold()
    for cle, pref in _vus.items():
        if fnmatch.fnmatchcase(pref.casefold(), m):
            return cle
    return None


def gardien(ligne, nick_bot, role):
    if not ligne.startswith(":"):
        return []
    morceaux = ligne[1:].split(" ")
    if len(morceaux) < 3:
        return []
    prefixe, cmd = morceaux[0], morceaux[1].upper()
    canal = morceaux[2].lstrip(":")
    if not canal.startswith("#"):
        return []

    # Arrivée d'un protégé : on retient son host, Christine l'accueille.
    if cmd == "JOIN":
        cle = qui(prefixe)
        if not cle:
            return []
        _vus[cle] = prefixe
        nick = prefixe.split("!")[0]
        if nick.casefold() == nick_bot.casefold() or role != "christine":
            return []
        k = (cle, canal.casefold())
        if time.time() - _accueillis.get(k, 0) < DELAI_ACCUEIL:
            return []
        _accueillis[k] = time.time()
        return [f"PRIVMSG {canal} :{nick}: {random.choice(ACCUEIL[cle])}"]

    # Kick d'un protégé.
    if cmd == "KICK" and len(morceaux) >= 4:
        victime = morceaux[3]
        cle = next((c for c, pref in _vus.items()
                    if pref.split("!")[0].casefold() == victime.casefold()), None)
        # Après un redémarrage, le bot n'a pas vu le JOIN : on se fie au nick.
        cle = cle or next((c for c, p in PROTEGES.items() if victime.casefold() in p["nicks"]), None)
        if not cle or _de_confiance(prefixe):
            return []
        auteur = prefixe.split("!")[0]
        raison = " ".join(morceaux[4:]).lstrip(":")[:120]
        nom = PROTEGES[cle]["nom"]
        if role == "christine":
            return [f"PRIVMSG {canal} :{random.choice(DEFENSE).format(nom=nom)}"]
        if role == "tanya":
            return [f"PRIVMSG {MAITRE} :[Garde] {victime} ({nom}) kické de {canal} par {auteur} : {raison or 'sans raison'}",
                    f"INVITE {victime} {canal}"]
        return []

    # Ban qui vise un protégé (on avertit, on ne débannit pas).
    if cmd == "MODE" and len(morceaux) >= 5 and morceaux[3].startswith("+") and "b" in morceaux[3]:
        cle = next((c for m in morceaux[4:] if (c := _cible_du_ban(m))), None)
        if not cle or _de_confiance(prefixe):
            return []
        auteur = prefixe.split("!")[0]
        nom = PROTEGES[cle]["nom"]
        if role == "christine":
            return [f"PRIVMSG {canal} :{auteur}, {nom} est un ami de la maison 🛡️ alxd est averti."]
        if role == "tanya":
            return [f"PRIVMSG {MAITRE} :[Garde] Ban sur {nom} dans {canal} par {auteur} : {' '.join(morceaux[4:])}"]
    return []
