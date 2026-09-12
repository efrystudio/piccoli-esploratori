"""
Script di aggiornamento attività.
Eseguito da GitHub Actions due volte a settimana (vedi
.github/workflows/update-activities.yml).
Vedi kids-activities-project-brief.md per il contesto completo del progetto.

Flusso:
1. Scarica il testo di ogni fonte in SOURCES.
2. Invia il testo a Claude, che estrae e classifica le attività adatte a un
   bambino di 6 anni nelle 5 categorie concordate (Workshop, Open Day,
   Teatro, Letture Animate, Event), escludendo Torino città per le fonti
   regionali.
3. Filtra per validità (categoria, città, data non passata).
4. Unisce con data/activities.json esistente, rimuovendo duplicati e
   attività scadute.
5. Salva il file aggiornato e la lista delle attività nuove
   (data/last_update_diff.json), usata dallo script di notifica Telegram.
"""
import json
import os
import re
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "activities.json"
DIFF_FILE = ROOT / "data" / "last_update_diff.json"

VALID_CATEGORIES = ["Workshop", "Open Day", "Teatro", "Letture Animate", "Event"]
TARGET_CITIES = ["Orbassano", "Rivalta di Torino", "Rivoli"]

SOURCES = [
    "https://www.comune.orbassano.to.it/it",
    "https://www.comune.rivalta.to.it",
    "https://www.comune.rivoli.to.it",
    "https://bct.comune.torino.it/eventi-attivita",
    "https://www.torinobimbi.it/corsi-e-laboratori",
    "https://www.castellodirivoli.org/educazione/attivita-famiglie/",
    "https://www.lelucidellarivalta.com/eventi/",
]

EXTRACTION_SYSTEM_PROMPT = """Sei un assistente che estrae attività per bambini da pagine web di enti locali italiani.

Il tuo compito: leggere il testo di una pagina e restituire SOLO un array JSON (nessun testo prima o dopo, nessun blocco di codice) con le attività adatte a un bambino di 6 anni, nelle città di Orbassano, Rivalta di Torino e Rivoli.

Se la pagina copre un'area più ampia (es. tutta la città di Torino o l'intera area metropolitana), includi SOLO le attività che si svolgono esplicitamente a Orbassano, Rivalta di Torino o Rivoli. Escludi sempre le attività a Torino città o in altri comuni.

Categorie valide, usa sempre una di queste (mai altre):
- "Workshop": qualsiasi attività pratica/laboratorio, in qualsiasi tema (scienza, arte, STEM, origami, lego, robotica, pasta, ecc). Se il testo usa le parole "laboratorio"/"laboratori"/"workshop", è Workshop.
- "Open Day": giornate porte aperte, visite guidate gratuite.
- "Teatro": spettacoli/mostre teatrali (NON laboratori teatrali, quelli sono Workshop).
- "Letture Animate": letture ad alta voce, narrazioni per bambini.
- "Event": qualsiasi altra attività adatta che non rientra nelle categorie sopra.

Per ogni attività restituisci un oggetto con ESATTAMENTE questi campi:
{
  "category": una delle 5 categorie sopra,
  "title": titolo breve,
  "desc": descrizione di massimo 70 caratteri,
  "city": una tra "Orbassano", "Rivalta di Torino", "Rivoli",
  "venue": nome del luogo,
  "date": "YYYY-MM-DD",
  "time": "HH:MM" (stima 16:00 se non specificato),
  "durationMin": numero (stima 60 se non specificato),
  "ageMin": numero (deve includere 6, se non specificato usa 3),
  "ageMax": numero (deve includere 6, se non specificato usa 10),
  "image": null,
  "link": l'URL della pagina sorgente fornita
}

Se non trovi nessuna attività adatta, restituisci un array vuoto: []
Non inventare attività che non sono nel testo. Non includere eventi con data già passata rispetto a oggi.
"""


def fetch_text(url: str) -> str:
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Impossibile scaricare {url}: {e}")
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return text[:15000]  # limite prudente di lunghezza per il prompt


def extract_activities(client: Anthropic, source_url: str, page_text: str):
    if not page_text:
        return []
    today = date.today().isoformat()
    user_prompt = (
        f"Data di oggi: {today}\n"
        f"URL sorgente: {source_url}\n\n"
        f"Testo della pagina:\n{page_text}"
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
        items = json.loads(raw)
        return items if isinstance(items, list) else []
    except Exception as e:
        print(f"  Estrazione fallita per {source_url}: {e}")
        return []


def is_valid(item: dict) -> bool:
    if item.get("category") not in VALID_CATEGORIES:
        return False
    if item.get("city") not in TARGET_CITIES:
        return False
    try:
        d = date.fromisoformat(item.get("date", ""))
    except (ValueError, TypeError):
        return False
    return d >= date.today()


def dedupe_key(item: dict):
    return (
        item.get("title", "").strip().lower(),
        item.get("date"),
        item.get("venue", "").strip().lower(),
    )


def load_existing():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def main():
    existing = load_existing()
    print(f"Attività attuali nel file: {len(existing)}")

    existing = [a for a in existing if is_valid(a)]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key) if api_key else None

    new_items = []
    if client:
        for url in SOURCES:
            print(f"Scarico: {url}")
            text = fetch_text(url)
            items = extract_activities(client, url, text)
            valid_items = [i for i in items if is_valid(i)]
            print(f"  {len(valid_items)} attività valide trovate")
            new_items.extend(valid_items)
    else:
        print("ANTHROPIC_API_KEY non impostata, salto l'estrazione.")

    existing_keys = {dedupe_key(a) for a in existing}
    added = []
    for item in new_items:
        key = dedupe_key(item)
        if key not in existing_keys:
            existing_keys.add(key)
            added.append(item)

    merged = existing + added
    for i, item in enumerate(merged, start=1):
        item["id"] = i

    DATA_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    DIFF_FILE.write_text(json.dumps(added, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Totale attività dopo l'aggiornamento: {len(merged)} ({len(added)} nuove)")


if __name__ == "__main__":
    main()
