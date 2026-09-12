"""
Script di aggiornamento attività.
Eseguito da GitHub Actions due volte a settimana (vedi
.github/workflows/update-activities.yml).

Flusso previsto (vedi kids-activities-project-brief.md per i dettagli):
1. Scaricare l'HTML da ogni fonte in SOURCES.
2. Inviare il contenuto a Claude per estrarre e classificare le attività
   nelle 5 categorie (Workshop, Open Day, Teatro, Letture Animate, Event).
3. Filtrare per età (bambini 6 anni), città (Orbassano, Rivalta di Torino,
   Rivoli) e, per le fonti regionali, escludere Torino stessa.
4. Unire il risultato con data/activities.json esistente: rimuovere
   duplicati e attività la cui data è già passata.
5. Salvare il file aggiornato.

Questo file è uno scheletro: la logica di estrazione con Claude verrà
aggiunta nel prossimo passaggio, non ancora in questa versione.
"""
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "activities.json"

SOURCES = [
    "https://www.comune.orbassano.to.it/it",
    "https://www.comune.rivalta.to.it",
    "https://www.comune.rivoli.to.it",
    "https://bct.comune.torino.it/eventi-attivita",       # richiede filtro dove=
    "https://www.torinobimbi.it/corsi-e-laboratori",       # richiede filtro per città
    "https://www.castellodirivoli.org/educazione/attivita-famiglie/",
    "https://www.lelucidellarivalta.com/eventi/",
]


def load_existing():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def main():
    existing = load_existing()
    print(f"Attività attuali nel file: {len(existing)}")
    # TODO: scaricare ogni fonte in SOURCES, estrarre e classificare le
    # attività con Claude, unire con 'existing', rimuovere duplicati e
    # attività scadute.
    DATA_FILE.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
