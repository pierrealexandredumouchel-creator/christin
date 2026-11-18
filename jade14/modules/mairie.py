"""Christine, mairesse autoproclamée de #montreal.

Commandes publiques :
  !reglement <mots>     cherche un règlement municipal (stationnement, bruit, chiens...)
  !sujets               liste des sujets connus
  !arrondissements      les 19 arrondissements de Montréal
  !311                  comment joindre la Ville
  !mairesse             une réplique de la mairesse
  !proclamation         une proclamation officielle (pour rire)
  !conseil <idée>       ouvre un vote du conseil (60 s) ; on vote avec !pour ou !contre

Commandes des maîtres (permissions.is_master) :
  !proclamation <texte> proclamation officielle avec ton texte
  !veto                 annule le vote en cours

La base de règlements est dans data/reglements_mtl.json : des résumés faits à
partir de montreal.ca. C'est de l'information générale, pas un avis juridique.
"""

import json
import random
import re
import threading
import time
import unicodedata
from pathlib import Path

from modules.permissions import is_master

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "reglements_mtl.json"

AVERTISSEMENT = "Info générale, pas un avis juridique : vérifie la source ou appelle le 311."

ARRONDISSEMENTS = (
    "Ahuntsic-Cartierville",
    "Anjou",
    "Côte-des-Neiges–Notre-Dame-de-Grâce",
    "Lachine",
    "LaSalle",
    "Le Plateau-Mont-Royal",
    "Le Sud-Ouest",
    "L'Île-Bizard–Sainte-Geneviève",
    "Mercier–Hochelaga-Maisonneuve",
    "Montréal-Nord",
    "Outremont",
    "Pierrefonds-Roxboro",
    "Rivière-des-Prairies–Pointe-aux-Trembles",
    "Rosemont–La Petite-Patrie",
    "Saint-Laurent",
    "Saint-Léonard",
    "Verdun",
    "Ville-Marie",
    "Villeray–Saint-Michel–Parc-Extension",
)

INFO_311 = (
    "Le 311 (514 872-0311) : lundi au vendredi de 8 h 30 à 20 h 30, fins de "
    "semaine et jours fériés de 9 h à 17 h. Les requêtes se font aussi sur montreal.ca. "
    "Urgence ? Le 911, pas la mairesse."
)

REPLIQUES = (
    "La mairesse est dans son bureau, entre deux cônes orange et une pile de plaintes de nids-de-poule.",
    "Mon programme : du déneigement avant le printemps, des cônes orange en voie d'extinction et du pâté chinois au conseil.",
    "J'ai pas de limousine, j'ai une passe OPUS. C'est ça, la vraie classe.",
    "Mon bureau est ouvert à tous les citoyens de #montreal. Essuyez vos bottes, par exemple.",
    "Un nid-de-poule, c'est juste une piscine municipale qui s'assume pas.",
    "La mairesse a parlé : on se stationne à 30 cm du trottoir pis on dit merci au déneigeur.",
    "Je suis la mairesse autoproclamée de #montreal. Les élections ? J'ai voté pour moi, ça compte.",
    "Ma porte est toujours ouverte. Mes heures de bureau, par contre, c'est entre deux opérations de chargement de la neige.",
)

PROCLAMATIONS = (
    "Le cône orange est proclamé emblème floral officiel de #montreal.",
    "Le premier qui dit « il fait frette » avant le 1er décembre paie la tournée de café au conseil.",
    "Le pâté chinois est déclaré plat d'intérêt patrimonial pour l'hiver.",
    "Chaque 1er juillet, on aide au moins un voisin à monter un divan. C'est la loi (pas vraiment).",
    "Les lol du canal sont maintenant une ressource renouvelable.",
    "Il est interdit de niaiser la mairesse avant son premier café. Amende : un beigne.",
    "Les ruelles vertes sont officiellement plus belles que les ruelles beiges.",
    "Un minou qui dort sur un clavier est en réunion. On le dérange pas.",
)

COOLDOWN = 20          # secondes entre deux commandes publiques par canal
DUREE_VOTE = 60        # secondes

_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "de", "du", "d", "l", "a", "au", "aux",
    "et", "ou", "en", "est", "ce", "ca", "c", "je", "tu", "il", "on", "j", "mon", "ma",
    "mes", "ton", "ta", "pour", "par", "sur", "dans", "que", "qui", "quoi", "quel",
    "quelle", "quels", "quelles", "comment", "combien", "pas", "ne", "se", "si",
    "reglement", "reglements", "montreal", "ville", "mairesse", "christine", "est-ce",
    "peut", "peux", "faut", "droit", "avoir", "y", "the",
}

_lock = threading.Lock()
_derniere_cmd = {}
_votes = {}


def _norm(text):
    """Minuscules, sans accents, apostrophes uniformes."""
    text = unicodedata.normalize("NFKD", str(text).casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.replace("’", "'").replace("`", "'")


def _mots(text):
    return [m for m in re.findall(r"[a-z0-9]+", _norm(text)) if m not in _STOPWORDS and len(m) > 1]


def charger(path=DATA_FILE):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("fiches", [])
    except (OSError, ValueError) as error:
        print(f"[Mairie] base de règlements illisible : {error!r}", flush=True)
        return []


FICHES = charger()


def chercher(question, fiches=None, limite=3, score_min=1):
    """Fiches triées par pertinence. Un mot-clé complet trouvé dans la question
    vaut 3 points (plus s'il est long), un mot isolé du sujet vaut 1."""
    fiches = FICHES if fiches is None else fiches
    texte = " " + " ".join(re.findall(r"[a-z0-9']+", _norm(question))) + " "
    mots = set(_mots(question))
    if not mots:
        return []
    resultats = []
    for fiche in fiches:
        score = 0
        for cle in fiche.get("mots", ()):
            cle = " ".join(re.findall(r"[a-z0-9']+", _norm(cle)))
            if cle and (" " + cle + " ") in texte:
                score += 3 + cle.count(" ")
        vus = set(_mots(fiche.get("sujet", "")) + _mots(fiche.get("id", "").replace("-", " ")))
        score += len(mots & vus)
        if score >= score_min:
            resultats.append((score, fiche))
    resultats.sort(key=lambda r: -r[0])
    return [fiche for _, fiche in resultats[:limite]]


def contexte_pour(question, limite=2):
    """Faits à glisser dans le prompt de GhostBrain quand quelqu'un parle de
    règlements. Chaîne vide si rien de pertinent : il faut au moins un
    mot-clé complet (score 3), pas juste un mot qui traîne."""
    trouvees = chercher(question, limite=limite, score_min=3)
    if not trouvees:
        return ""
    lignes = [
        "Règlements municipaux de Montréal pertinents (tirés de montreal.ca, "
        "utilise SEULEMENT ces faits pour les chiffres ; si la réponse n'y est pas, "
        "dis-le et renvoie au 311 ; rappelle que ça peut varier selon l'arrondissement "
        "quand c'est indiqué) :"
    ]
    for fiche in trouvees:
        lignes.append(f"- {fiche['sujet']} : {fiche['resume']}")
        for detail in fiche.get("details", ())[:3]:
            lignes.append(f"  · {detail}")
        lignes.append(f"  Portée : {fiche.get('portee', '?')}. Source : {fiche.get('source', '')}")
    return "\n".join(lignes)


# ----------------------------------------------------------------- commandes

def _cible(bot, user, chan):
    return chan if str(chan).startswith("#") else user


def _trop_tot(cible, commande):
    cle = (str(cible).casefold(), commande)
    maintenant = time.monotonic()
    with _lock:
        if maintenant - _derniere_cmd.get(cle, -COOLDOWN) < COOLDOWN:
            return True
        _derniere_cmd[cle] = maintenant
    return False


def _dire(bot, cible, texte):
    if hasattr(bot, "say_long"):
        bot.say_long(cible, texte)
    else:
        bot.send(cible, texte)


def _fiche_courte(fiche):
    return f"📜 {fiche['sujet']} : {fiche['resume']}"


def _pied(fiche):
    return (
        f"Règlement : {fiche.get('reglement', '?')} · {fiche.get('portee', '?')} · "
        f"Source : {fiche.get('source', 'montreal.ca')} · {AVERTISSEMENT}"
    )


def _sujets():
    return ", ".join(f["id"] for f in FICHES)


def commande_reglement(bot, cible, question):
    if not question:
        bot.send(cible, f"Usage : !reglement <mots>  (ex. !reglement déneigement). Sujets : {_sujets()}")
        return
    trouvees = chercher(question)
    if not trouvees:
        bot.send(
            cible,
            f"La mairesse a fouillé ses classeurs, rien sur « {question[:60]} ». "
            f"Sujets connus : {_sujets()}. Sinon, le 311 sait tout.",
        )
        return
    meilleure = trouvees[0]
    _dire(bot, cible, _fiche_courte(meilleure))
    bot.send(cible, _pied(meilleure))
    if len(trouvees) > 1:
        autres = ", ".join(f["id"] for f in trouvees[1:])
        bot.send(cible, f"Voir aussi : {autres}  (!reglement <sujet>)")


def _ouvrir_vote(bot, cible, user, proposition):
    cle = str(cible).casefold()
    with _lock:
        if cle in _votes:
            bot.send(cible, "Un vote est déjà en cours au conseil. Votez avec !pour ou !contre.")
            return
        vote = {"proposition": proposition, "par": user, "pour": set(), "contre": set()}
        _votes[cle] = vote

    bot.send(
        cible,
        f"🏛️ Séance du conseil ! {user} propose : « {proposition} ». "
        f"Vous avez {DUREE_VOTE} secondes : !pour ou !contre.",
    )

    def fermer():
        with _lock:
            if _votes.get(cle) is not vote:
                return     # veto ou autre vote
            del _votes[cle]
        pour, contre = len(vote["pour"]), len(vote["contre"])
        if pour == 0 and contre == 0:
            verdict = "Quorum pas atteint : tout le monde était parti au dep. Proposition reportée."
        elif pour > contre:
            verdict = (
                "ADOPTÉE à l'unanimité !" if contre == 0
                else f"ADOPTÉE, {pour} pour, {contre} contre."
            )
        elif contre > pour:
            verdict = f"REJETÉE, {pour} pour, {contre} contre. On en reparle au prochain budget."
        else:
            verdict = f"Égalité {pour}-{contre} : la mairesse tranche… et commande de la poutine pour réfléchir. Reportée."
        try:
            bot.send(cible, f"🏛️ « {vote['proposition']} » : {verdict}")
        except Exception as error:
            print(f"[Mairie] fin de vote : {error!r}", flush=True)

    minuterie = threading.Timer(DUREE_VOTE, fermer)
    minuterie.daemon = True
    minuterie.start()


def _voter(bot, cible, user, choix):
    cle = str(cible).casefold()
    qui = str(user).casefold()
    with _lock:
        vote = _votes.get(cle)
        if not vote:
            return False
        vote["pour"].discard(qui)
        vote["contre"].discard(qui)
        vote[choix].add(qui)
    return True


def _veto(bot, cible, user):
    cle = str(cible).casefold()
    with _lock:
        vote = _votes.pop(cle, None)
    if vote:
        bot.send(cible, f"🏛️ Veto de {user} sur « {vote['proposition']} ». La séance est levée.")
    else:
        bot.send(cible, "Aucun vote en cours.")


_CMD = re.compile(r"^!(\S+)\s*(.*)$", re.DOTALL)


def handle(bot, user, hostmask, chan, msg):
    """Traite une commande de la mairie. Retourne True si la commande était
    pour elle (même refusée), False sinon."""
    m = _CMD.match(str(msg).strip())
    if not m:
        return False
    commande = _norm(m.group(1))
    reste = " ".join(m.group(2).replace("\r", " ").replace("\n", " ").split())[:300]
    cible = _cible(bot, user, chan)

    if commande in ("pour", "contre"):
        if _voter(bot, cible, user, commande):
            return True
        return False

    if commande == "veto":
        if not is_master(user, hostmask):
            bot.send(cible, f"{user}: le droit de veto, c'est pour les maîtres de la mairie.")
            return True
        _veto(bot, cible, user)
        return True

    publiques = {
        "reglement", "reglements", "reg", "sujets", "arrondissements", "arrondissement",
        "311", "mairesse", "mairie", "proclamation", "conseil",
    }
    if commande not in publiques:
        return False

    maitre = is_master(user, hostmask)
    # Les maîtres ne sont pas limités ; les votes ont leur propre garde.
    if not maitre and commande != "conseil" and _trop_tot(cible, commande):
        return True

    if commande in ("reglement", "reglements", "reg"):
        commande_reglement(bot, cible, reste)
    elif commande == "sujets":
        bot.send(cible, f"Sujets de la mairie : {_sujets()}. Ex. : !reglement chiens")
    elif commande in ("arrondissements", "arrondissement"):
        _dire(bot, cible, "Les 19 arrondissements : " + ", ".join(ARRONDISSEMENTS) + ".")
    elif commande == "311":
        bot.send(cible, INFO_311)
    elif commande in ("mairesse", "mairie"):
        bot.send(cible, random.choice(REPLIQUES))
    elif commande == "proclamation":
        if reste and not maitre:
            bot.send(cible, f"{user}: seuls les maîtres dictent les proclamations. Voici celle du jour :")
            reste = ""
        texte = reste or random.choice(PROCLAMATIONS)
        bot.send(cible, f"📯 PROCLAMATION DE LA MAIRESSE DE #MONTREAL : {texte}")
    elif commande == "conseil":
        if not reste:
            bot.send(cible, "Usage : !conseil <proposition>  (ex. !conseil poutine gratuite le vendredi)")
        elif str(cible).casefold() in _votes:
            bot.send(cible, "Un vote est déjà en cours au conseil. Votez avec !pour ou !contre.")
        elif not maitre and _trop_tot(cible, "conseil"):
            pass
        else:
            _ouvrir_vote(bot, cible, user, reste[:200])
    return True
