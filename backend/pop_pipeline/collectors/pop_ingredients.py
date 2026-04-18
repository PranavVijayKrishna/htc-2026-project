import httpx
import json
from bs4 import BeautifulSoup
from pathlib import Path
import re

BASE_URL = "https://www.popus.com"


def get_product_handles():
    """Crawl /collections/all to find all product handles."""
    handles = []
    page = 1

    while True:
        resp = httpx.get(
            f"{BASE_URL}/collections/all",
            params={"page": page},
            headers={"User-Agent": "Mozilla/5.0"},
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("a[href*='/products/']")

        if not links:
            break

        for link in links:
            handle = link["href"].split("/products/")[-1].split("?")[0]
            if handle and handle not in handles:
                handles.append(handle)

        page += 1

    return handles


def fetch_product(handle):
    """Use Shopify's built-in JSON API."""
    resp = httpx.get(
        f"{BASE_URL}/products/{handle}.json",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    if resp.status_code == 200:
        return resp.json().get("product", {})
    return None


def parse_ingredients(html):
    """Extract ingredients by finding text between 'Ingredients:' and the next bold element."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(string=lambda t: t and "ingredients:" in t.lower()):
        parent = tag.parent

        ingredients_text = []
        for sibling in parent.next_siblings:
            # Stop at the next bold element
            if sibling.name in ("b", "strong"):
                break
            if hasattr(sibling, "get_text"):
                ingredients_text.append(sibling.get_text(separator=" "))
            elif isinstance(sibling, str):
                ingredients_text.append(sibling)

        result = " ".join(ingredients_text).strip()
        if result:
            return result

    return None


def scrape_all_ingredients():
    Path("raw_cache").mkdir(exist_ok=True)
    handles = get_product_handles()
    print(f"Found {len(handles)} products")

    all_ingredients = set()

    with open("raw_cache/popus_raw_ingredients.txt", "w", encoding="utf-8") as f:
        for handle in handles:
            product = fetch_product(handle)
            if not product:
                continue

            html = product.get("body_html", "")
            after = parse_ingredients(html)

            if after:
                f.write(f"{after}")

                for ingredient in after.split(","):
                    cleaned = " ".join(ingredient.strip().lower().split())  # normalize whitespace
                    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()       # remove (...)
                    if cleaned:
                        all_ingredients.add(cleaned)

            print(f"✓ {product.get('title')}")

    out = Path("raw_cache/popus_ingredients.json")
    out.write_text(json.dumps(sorted(all_ingredients), indent=2))
    print(f"\n{len(all_ingredients)} unique ingredients → {out}")
    return all_ingredients


def test_single(handle):
    """Test parsing on a single product handle."""
    product = fetch_product(handle)
    if not product:
        print("Product not found")
        return

    html = product.get("body_html", "")
    after = parse_ingredients(html)

    if after:
        print(after)
    else:
        print("No ingredients found")


if __name__ == "__main__":
    # test_single("ginger-honey-crystal-assorted-30-sachets")
    scrape_all_ingredients()