import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

def init_ai(config_path="/opt/christine24/jade14/config.json"):
    load_dotenv(os.path.join(os.path.dirname(config_path), ".env"))
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key and os.path.exists(config_path):
        with open(config_path, "r") as f:
            cfg = json.load(f)
        api_key = cfg.get("gemini_api_key")

    if not api_key:
        return None

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

model = None

def ai_reply(prompt):
    global model
    if model is None:
        model = init_ai()

    if model is None:
        return "[AI] Clé API manquante."

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[AI ERROR] {e}"
