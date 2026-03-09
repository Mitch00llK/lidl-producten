# Lidl Product API

JSON-database met Lidl producten, automatisch bijgewerkt via GitHub Actions.

## Gebruik in BoodschappenApp

1. Deploy deze map naar een GitHub repo
2. In de app: **Producten** → **Lidl catalogus** → voer de raw URL in:
   ```
   https://raw.githubusercontent.com/JOUW_USERNAME/JOUW_REPO/main/products.json
   ```
3. Tik **Ophalen van API (snel)**

## Setup

1. Maak een **nieuwe GitHub repo** (bijv. `lidl-producten`)
2. Push de inhoud van deze map naar die repo
3. Eerste run: **Actions** → **Scrape Lidl products** → **Run workflow**
4. Daarna: automatisch elke zondag om 04:00 NL tijd

## Output

`products.json` – array van producten:
```json
[
  {
    "productId": 100399230,
    "name": "RVS melkopschuimer",
    "price": 24.99,
    "imageURL": "https://www.lidl.nl/assets/...",
    "category": "Koken & bakken"
  }
]
```

## Lokaal testen

```bash
cd lidl-api
pip install -r requirements.txt
python -m playwright install chromium
python scraper.py
# → products.json (ca. 1100+ producten)
```

De scraper gebruikt Playwright (headless Chromium) omdat Lidl productdata via JavaScript rendert.
