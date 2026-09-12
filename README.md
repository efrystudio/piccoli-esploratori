# Piccoli Esploratori

Sito con le attività per bambini (6 anni) a Orbassano, Rivalta di Torino
e Rivoli. Vedi `kids-activities-project-brief.md` per tutte le decisioni
di progetto.

## Struttura
- `index.html`, `calendario.html` — le due pagine del sito
- `assets/style.css`, `assets/app.js` — stile e logica, condivisi dalle due pagine
- `data/activities.json` — i dati delle attività, aggiornati automaticamente
- `scripts/` — script Python per lo scraping/classificazione e la notifica Telegram
- `.github/workflows/update-activities.yml` — l'automazione (due volte a settimana)

## Setup su GitHub
1. Crea un repository nuovo (vuoto) sul tuo account GitHub.
2. Carica tutti questi file nel repository (via `git push`, oppure
   "Add file → Upload files" dal sito di GitHub).
3. Settings → Pages → Source: "Deploy from a branch", branch `main`,
   cartella `/ (root)`.
4. Settings → Secrets and variables → Actions, aggiungi:
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
5. Il sito sarà online su `https://<tuo-utente>.github.io/<nome-repo>/`

## Stato attuale
Il front-end funziona con dati di esempio (`data/activities.json`).
`scripts/update_activities.py` è ora la versione reale: scarica ogni
fonte, la invia a Claude per l'estrazione e la classificazione, filtra
e unisce i risultati. Richiede il secret `ANTHROPIC_API_KEY` per
funzionare. `scripts/notify_telegram.py` invia le attività nuove nel
gruppo Telegram, richiede `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.
