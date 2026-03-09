#!/usr/bin/env python3
"""
Lidl product scraper – haalt producten op van lidl.nl en output JSON.
Gebruikt Playwright voor volledige server-rendered productdata.
Output: products.json
"""
import html as html_module
import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://www.lidl.nl"

SEARCH_TERMS = [
    "melk", "brood", "kaas", "yoghurt", "vlees", "kip", "vis", "eieren", "boter",
    "rijst", "pasta", "pizza", "groente", "fruit", "aardappelen", "chips", "koekjes",
    "chocolade", "koffie", "thee", "sap", "frisdrank", "bier", "wijn", "water",
    "ontbijt", "muesli", "jam", "hagelslag", "pindakaas", "soep", "saus", "olie",
    "bloem", "suiker", "kruiden", "conserven", "diepvries", "ijs",
    "schoonmaak", "wasmiddel", "shampoo", "douchegel", "tandpasta", "deodorant",
    "toiletpapier", "keukenrol", "afwasmiddel",
]


def first_group(block: str, pattern: str) -> str | None:
    m = re.search(pattern, block)
    return m.group(1) if m and m.lastindex >= 1 else None


def parse_products(html: str) -> list[dict]:
    results = []
    seen_ids = set()

    for m in re.finditer(r'"productId":\s*(\d+)', html):
        product_id = int(m.group(1))
        if product_id in seen_ids:
            continue

        start = m.start()
        # Prijs staat vaak vóór productId in de JSON; blok naar beide kanten
        block_start = max(0, start - 3500)
        block = html[block_start : start + 2500]
        pid_pos_in_block = start - block_start

        title = first_group(block, r'"title":"([^"]+)"')
        if not title:
            continue

        clean_title = (
            title.replace("\\u0026", "&")
            .replace("&#39;", "'")
            .replace("&nbsp;", " ")
            .strip()
        )
        if not clean_title or len(clean_title) < 2:
            continue

        # Prijs staat meestal vóór productId; zoek laatste match in het deel vóór productId
        price = 0.0
        before_pid = block[:pid_pos_in_block]
        for pm in re.finditer(r'"price":\s*(\d+\.?\d*)', before_pid):
            price = float(pm.group(1))
        if price == 0:
            if p := first_group(block, r'"oldPrice":\s*(\d+\.?\d*)'):
                price = float(p)
        if price == 0 and (p := first_group(block, r'"deletedPrice":\s*(\d+\.?\d*)')):
            price = float(p)

        image_url = first_group(block, r'"mouseoverImage":"(https://[^"]+)"') or first_group(
            block, r'"image":"(https://[^"]+)"'
        )
        if not image_url and (img := first_group(block, r'"image":"(https://[^"]+)"')):
            image_url = img

        category = None
        if full := first_group(block, r'"wonCategoryPrimary":"([^"]+)"'):
            category = full.split("/")[-1] if "/" in full else full

        results.append({
            "productId": product_id,
            "name": clean_title,
            "price": round(price, 2),
            "imageURL": image_url,
            "category": category,
        })
        seen_ids.add(product_id)

    return results


def fetch_with_playwright(term: str, page) -> str:
    url = f"{BASE_URL}/q/search?q={term}"
    page.goto(url, wait_until="load", timeout=60000)
    time.sleep(2)  # Laat productgrid renderen
    raw = page.content()
    return html_module.unescape(raw)


def main():
    all_products = {}
    total = len(SEARCH_TERMS)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="nl-NL",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        try:
            for i, term in enumerate(SEARCH_TERMS, 1):
                print(f"[{i}/{total}] {term}...", flush=True)
                try:
                    html = fetch_with_playwright(term, page)
                    products = parse_products(html)
                    for p in products:
                        all_products[p["productId"]] = p
                    print(f"  → {len(products)} producten, totaal {len(all_products)}", flush=True)
                except Exception as e:
                    print(f"  ✗ Fout: {e}", flush=True)

                if i < total:
                    time.sleep(0.5)
        finally:
            browser.close()

    output = list(all_products.values())
    out_path = Path(__file__).parent / "products.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=0)

    print(f"\nKlaar: {len(output)} unieke producten → {out_path}")


if __name__ == "__main__":
    main()
