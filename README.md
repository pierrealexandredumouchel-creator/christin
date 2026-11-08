<p align="center"><img src="christine.png" width="180" alt="Christine, petit fantôme Ghost Royale avec sa couronne et son bouclier"></p>

<h1 align="center">Christine24</h1>
<p align="center"><em>La gardienne calme de #montreal et l'opératrice technique du Ghost Royale.</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white" alt="Python 3">
  <img src="https://img.shields.io/badge/IRC-Undernet-6f42c1" alt="IRC Undernet">
  <img src="https://img.shields.io/badge/r%C3%A9seau-IPv6-2ea44f" alt="IPv6">
  <img src="https://img.shields.io/badge/IA-Ollama%20local-black" alt="Ollama">
</p>

## Qui elle est

Christine garde le calme sur **#montreal** et **#kodi** : quand ça chauffe, elle désamorce avec
une blague plutôt qu'un kick. Elle aide aussi pour les questions techniques (Linux, réseau, IRC).

## Ce qu'elle fait

- **GhostBrain** : discute avec l'IA locale (Ollama) et suit la discussion du canal.
- **Gardien** (`core/gardien.py`) : garde un œil sur l'ambiance du canal.
- Chasse au canard, commandes admin, reconnexion patiente.

## Commandes

| Commande | Effet |
|---|---|
| `christine …` / `!christine <texte>` | Lui parler |
| `!duckhunt` · `!shoot` · `!score` | Chasse au canard |
| `!hello` · `!ping` | Les classiques |
| `!say` · `!addadmin` · `!admins` · `!resetduck` | Admin |

## Structure

Le code est dans [`jade14/`](jade14/) : Christine est née d'une copie de Jade, d'où le nom du dossier.

| Chemin | Rôle |
|---|---|
| `jade14/jade14.py` | Point d'entrée, connexion IRC |
| `jade14/config.json` | Serveur, nick, canaux |
| `jade14/core/` | GhostBrain, gardien, client Ollama, personas |
| `jade14/modules/` | Commandes, admin, chasse au canard, reconnexion |
| `jade14/master_control.py` | Commandes privilégiées (doit être présent au déploiement) |
| `jade14/personalities/christine24.txt` | Sa personnalité |

## Lancer

```bash
cd jade14
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python3 jade14.py
```

## Secrets

Les mots de passe (X, canaux) et les clés API vont dans un fichier `.env` sur le serveur, **jamais** dans le dépôt. Les bases de données, logs et sauvegardes sont ignorés par git.

---

<p align="center">Fait partie de la flotte <a href="https://github.com/pierrealexandredumouchel-creator"><b>Ghost Royale</b></a> : Jade · Christine · Anya · Tanya · Millie 👻</p>
