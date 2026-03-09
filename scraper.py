#!/usr/bin/env python3
"""
Lidl product scraper – haalt producten op van lidl.nl en output JSON.
Gebruikt door GitHub Actions; output: products.json
"""
import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "https://www.lidl.nl"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SEARCH_TERMS = [
    "melk", "brood", "kaas", "yoghurt", "vlees", "kip", "vis", "eieren", "boter",
    "rijst", "pasta", "pizza", "groente", "fruit", "aardappelen", "chips", "koekjes",
    "chocolade", "koffie", "thee", "sap", "frisdrank", "bier", "wijn", "water",
    "ontbijt", "muesli", "jam", "hagelslag", "pindakaas", "soep", "saus", "olie",
    "bloem", "suiker", "kruiden", "conserven", "diepvries", "ijs",
    "schoonmaak", "wasmiddel", "shampoo", "douchegel", "tandpasta", "deodorant",
    "toiletpapier", "keukenrol", "afwasmiddel",
]


def fetch_page(term: str) -> str:
    url = f"{BASE_URL}/q/search?q={urllib.parse.quote(term)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "nl-NL,nl;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


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
        block = html[start : start + 4000]

        title = first_group(block, r'"title":"([^"]+)"')
        if not title:
            continue

        clean_title = (
            title.replace("\\u0026", "&")
            .replace("&#39;", "'")
            .strip()
        )
        if not clean_title:
            continue

        price = 0.0
        if p := first_group(block, r'"price":\s*(\d+\.?\d*)'):
            price = float(p)
        if price == 0 and (p := first_group(block, r'"oldPrice":\s*(\d+\.?\d*)')):
            price = float(p)

        image_url = first_group(block, r'"mouseoverImage":"(https://[^"]+)"') or first_group(
            block, r'"image":"(https://[^"]+)"'
        )

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


def main():
    all_products = {}
    total = len(SEARCH_TERMS)

    for i, term in enumerate(SEARCH_TERMS, 1):
        print(f"[{i}/{total}] {term}...", flush=True)
        try:
            html = fetch_page(term)
            products = parse_products(html)
            for p in products:
                all_products[p["productId"]] = p
            print(f"  → {len(products)} producten, totaal {len(all_products)}", flush=True)
        except Exception as e:
            print(f"  ✗ Fout: {e}", flush=True)

        if i < total:
            time.sleep(0.8)

    output = list(all_products.values())
    out_path = Path(__file__).parent / "products.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=0)

    print(f"\nKlaar: {len(output)} unieke producten → {out_path}")


if __name__ == "__main__":
    main()
