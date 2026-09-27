#!/bin/bash

CONFIG="/opt/christine24/jade14/config.json"

echo "[AutoFix] Vérification du config.json..."

# Config propre attendu
read -r -d '' GOODCFG << 'EOF'
{
    "server": "irc.undernet.org",
    "port": 6667,
    "nick": "christine24",
    "ident": "christine24",
    "realname": "Ghost Royale Bot",
    "channels": ["#kodi", "#montreal"],
    "channel_password": "qpaptWUb",
    "gemini_api_key": ""
}
EOF

# Vérifier si JSON valide
if ! jq empty "$CONFIG" 2>/dev/null; then
    echo "[AutoFix] JSON cassé → reconstruction..."
    echo "$GOODCFG" > "$CONFIG"
    exit 0
fi

# JSON valide → vérifier les champs
NICK=$(jq -r '.nick' "$CONFIG")
CHANNELS=$(jq -r '.channels | join(",")' "$CONFIG")

FIXED=0

if [ "$NICK" != "christine24" ]; then
    echo "[AutoFix] Correction du nick..."
    jq '.nick="christine24" | .ident="christine24"' "$CONFIG" > "$CONFIG.tmp"
    mv "$CONFIG.tmp" "$CONFIG"
    FIXED=1
fi

if [[ "$CHANNELS" != *"montreal"* ]]; then
    echo "[AutoFix] Correction des channels..."
    jq '.channels=["#kodi","#montreal"]' "$CONFIG" > "$CONFIG.tmp"
    mv "$CONFIG.tmp" "$CONFIG"
    FIXED=1
fi

if ! jq -e '.gemini_api_key' "$CONFIG" >/dev/null; then
    echo "[AutoFix] Ajout du champ gemini_api_key..."
    jq '.gemini_api_key=""' "$CONFIG" > "$CONFIG.tmp"
    mv "$CONFIG.tmp" "$CONFIG"
    FIXED=1
fi

if [ "$FIXED" -eq 1 ]; then
    echo "[AutoFix] Config réparé."
else
    echo "[AutoFix] Aucun problème détecté."
fi

