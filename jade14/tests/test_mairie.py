"""Tests de la mairie de Christine. Lancer depuis jade14/ :
    python3 -m unittest discover -s tests -v
"""
import json
import time
import unittest
from unittest import mock

from modules import mairie

ALXD = "alxd!~alxd@alxd.kekistan.faith"
INTRUS = "alxd!~x@evil.example"


class FauxBot:
    def __init__(self):
        self.sent = []

    def send(self, target, msg):
        self.sent.append((target, msg))

    def say_long(self, target, text):
        self.send(target, text)

    def textes(self):
        return " | ".join(m for _, m in self.sent)


class Base(unittest.TestCase):
    def setUp(self):
        mairie._derniere_cmd.clear()
        mairie._votes.clear()
        self.bot = FauxBot()

    def cmd(self, msg, user="bob", host="bob!~b@b.example", chan="#montreal"):
        return mairie.handle(self.bot, user, host, chan, msg)


class Donnees(unittest.TestCase):
    def test_base_valide(self):
        with open(mairie.DATA_FILE, encoding="utf-8") as f:
            fiches = json.load(f)["fiches"]
        self.assertGreaterEqual(len(fiches), 15)
        ids = [f["id"] for f in fiches]
        self.assertEqual(len(ids), len(set(ids)))
        for f in fiches:
            for champ in ("id", "sujet", "mots", "resume", "reglement", "portee", "source"):
                self.assertTrue(f.get(champ), f"{f.get('id')}: {champ} manquant")
            self.assertTrue(f["source"].startswith("https://montreal.ca/"), f["id"])
            # Le résumé + l'en-tête doit tenir en au plus 2 lignes IRC.
            self.assertLess(len(f["resume"].encode()), 700, f["id"])

    def test_19_arrondissements(self):
        self.assertEqual(len(mairie.ARRONDISSEMENTS), 19)


class Recherche(unittest.TestCase):
    def premier(self, q):
        r = mairie.chercher(q)
        return r[0]["id"] if r else None

    def test_mots_cles(self):
        cas = {
            "est-ce que je peux pousser ma neige dans la rue": "neige-dans-la-rue",
            "mon char a été remorqué cette nuit": "deneigement-stationnement",
            "combien de chiens je peux avoir": "animaux",
            "laisse du chien": "chiens",
            "AIRBNB l'été": "airbnb",
            "abri tempo": "abri-tempo",
            "Roundup sur mes pissenlits": "pesticides",
            "mon proprio chauffe pas, il fait 17 dans le logement": "logement",
            "pétards": "bruit",
            "foyer au bois pendant le smog": "chauffage-bois",
            "matelas": "encombrants",
            "sacs de plastique": "sacs",
        }
        for question, attendu in cas.items():
            with self.subTest(question=question):
                self.assertEqual(self.premier(question), attendu)

    def test_rien(self):
        self.assertEqual(mairie.chercher("pizza hawaïenne"), [])
        self.assertEqual(mairie.chercher(""), [])

    def test_contexte_seulement_si_pertinent(self):
        self.assertEqual(mairie.contexte_pour("salut christine ça va?"), "")
        ctx = mairie.contexte_pour("christine, c'est quoi la règle pour l'abri tempo?")
        self.assertIn("Abri d'auto", ctx)
        self.assertIn("montreal.ca", ctx)


class Commandes(Base):
    def test_reglement(self):
        self.assertTrue(self.cmd("!reglement déneigement remorquage"))
        t = self.bot.textes()
        self.assertIn("19 h", t)
        self.assertIn("pas un avis juridique", t)
        self.assertIn("https://montreal.ca/", t)

    def test_reglement_accents_et_alias(self):
        self.assertTrue(self.cmd("!règlement chiens"))
        self.assertIn("1,85 m", self.bot.textes())

    def test_reglement_vide_et_inconnu(self):
        self.cmd("!reglement")
        self.assertIn("Usage", self.bot.textes())
        mairie._derniere_cmd.clear()
        self.cmd("!reglement licornes")
        self.assertIn("311", self.bot.textes())

    def test_cooldown(self):
        self.cmd("!mairesse")
        self.cmd("!mairesse")
        self.assertEqual(len(self.bot.sent), 1)

    def test_maitre_pas_de_cooldown(self):
        self.cmd("!mairesse", "alxd", ALXD)
        self.cmd("!mairesse", "alxd", ALXD)
        self.assertEqual(len(self.bot.sent), 2)

    def test_prive_repond_au_pseudo(self):
        self.cmd("!311", chan="christine24")
        self.assertEqual(self.bot.sent[0][0], "bob")

    def test_pas_pour_moi(self):
        self.assertFalse(self.cmd("!duckhunt"))
        self.assertFalse(self.cmd("bonjour"))
        self.assertFalse(self.cmd("!pour"))   # pas de vote en cours

    def test_proclamation_libre_maitres_seulement(self):
        self.cmd("!proclamation tout le monde me donne 100 $", "alxd", INTRUS)
        t = self.bot.textes()
        self.assertNotIn("100 $", t)
        self.assertIn("seuls les maîtres", t)
        self.bot.sent.clear()
        self.cmd("!proclamation congé vendredi", "alxd", ALXD)
        self.assertIn("congé vendredi", self.bot.textes())

    def test_veto_maitres_seulement(self):
        self.cmd("!conseil poutine gratuite")
        self.cmd("!veto", "alxd", INTRUS)
        self.assertIn("maîtres", self.bot.textes())
        self.assertIn("#montreal", mairie._votes)
        self.cmd("!veto", "alxd", ALXD)
        self.assertNotIn("#montreal", mairie._votes)


class Conseil(Base):
    def test_vote_adopte(self):
        with mock.patch.object(mairie, "DUREE_VOTE", 0.2):
            self.cmd("!conseil poutine gratuite le vendredi")
            self.assertTrue(self.cmd("!pour", "a"))
            self.assertTrue(self.cmd("!pour", "b"))
            self.assertTrue(self.cmd("!contre", "c"))
            self.assertTrue(self.cmd("!pour", "c"))   # change d'idée
            self.cmd("!conseil autre chose", "d")
            self.assertIn("déjà en cours", self.bot.textes())
            time.sleep(0.5)
        self.assertIn("ADOPTÉE à l'unanimité", self.bot.textes())
        self.assertEqual(mairie._votes, {})

    def test_vote_quorum(self):
        with mock.patch.object(mairie, "DUREE_VOTE", 0.1):
            self.cmd("!conseil métro 24 h")
            time.sleep(0.3)
        self.assertIn("Quorum", self.bot.textes())


if __name__ == "__main__":
    unittest.main()
