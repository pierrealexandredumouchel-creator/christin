import os
import random

INSULTE_FILE = "/opt/christine24/insultes.txt"

def load_insultes():
    if not os.path.exists(INSULTE_FILE):
        return []
    with open(INSULTE_FILE, "r") as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def save_insulte(text):
    with open(INSULTE_FILE, "a") as f:
        f.write(text + "\n")
    return "Insulte ajoutée."

def get_random_insulte():
    insultes = load_insultes()
    if not insultes:
        return "Aucune insulte enregistrée."
    return random.choice(insultes)

def list_insultes():
    insultes = load_insultes()
    if not insultes:
        return "Aucune insulte enregistrée."
    out = []
    for i, ins in enumerate(insultes):
        out.append(f"{i}: {ins}")
    return " | ".join(out)

def delete_insulte(idx):
    insultes = load_insultes()
    try:
        idx = int(idx)
        removed = insultes.pop(idx)
        with open(INSULTE_FILE, "w") as f:
            for ins in insultes:
                f.write(ins + "\n")
        return f"Insulte supprimée: {removed}"
    except:
        return "Index invalide."
