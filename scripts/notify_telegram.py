"""
Invia una notifica su Telegram quando il sito viene aggiornato.
Richiede le variabili d'ambiente TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID,
impostate come secrets del repository GitHub.
"""
import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram non configurato, salto la notifica.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


def main():
    # TODO: leggere quali attività sono nuove rispetto all'ultimo
    # aggiornamento e comporre un messaggio reale con i dettagli.
    send_message("Il sito delle attività è stato aggiornato.")


if __name__ == "__main__":
    main()
