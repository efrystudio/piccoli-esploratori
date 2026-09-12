"""
Invia una notifica su Telegram quando ci sono nuove attività.
Legge data/last_update_diff.json (scritto da update_activities.py)
per sapere quali attività sono nuove rispetto all'ultimo aggiornamento.
Richiede TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID come secrets del repository.
"""
import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent
DIFF_FILE = ROOT / "data" / "last_update_diff.json"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram non configurato, salto la notifica.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


def main():
    if not DIFF_FILE.exists():
        print("Nessun file di differenze trovato, nessuna notifica inviata.")
        return
    added = json.loads(DIFF_FILE.read_text(encoding="utf-8"))
    if not added:
        print("Nessuna nuova attività, nessuna notifica inviata.")
        return
    lines = [f"🆕 {len(added)} nuove attività su Piccoli Esploratori:"]
    for a in added:
        lines.append(f"• {a['title']} — {a['city']}, {a['date']}")
    send_message("\n".join(lines))


if __name__ == "__main__":
    main()
