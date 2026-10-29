# Christine24

Bot IRC de #montreal et #kodi sur Undernet : la gardienne calme et l'opératrice technique du Ghost Royale.

Le code est dans [`jade14/`](jade14/) (le bot vient de jade14, d'où le nom du dossier).

## Ce qu'elle fait

- Discute avec GhostBrain (Ollama local) : suit la discussion du canal, répond quand on dit son nom.
- Personnalité : [`jade14/personalities/christine24.txt`](jade14/personalities/christine24.txt)
- Commandes `!christine`, duckhunt (`!duckhunt`, `!shoot`, `!score`), admin : voir [`jade14/commandes.txt`](jade14/commandes.txt)
- Reconnexion patiente (30 s à 10 min) pour éviter le « throttled » d'Undernet.

## Fichiers importants

| Fichier | Rôle |
|---|---|
| `jade14/jade14.py` | Point d'entrée, connexion IRC |
| `jade14/config.json` | Serveur, nick, canaux, bindhost IPv6 |
| `jade14/core/` | GhostBrain, client Ollama, personas |
| `jade14/modules/` | Commandes, admin, duckhunt, reconnexion |
| `jade14/master_control.py` | Commandes privilégiées (doit être présent au déploiement) |
| `fix_config.sh` | Répare `config.json` s'il est cassé |

## Lancer

```bash
cd jade14
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python3 jade14.py
```

Les secrets (mot de passe X, clés API) vont dans `jade14/.env`, jamais dans le dépôt.

## Réseau

IRC en IPv6 seulement : `irc6.undernet.org`, bindhost `2001:470:b2af::3`. Voir [`network-layout.md`](network-layout.md).
