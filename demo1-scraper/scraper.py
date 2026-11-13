#!/usr/bin/env python3
"""
Demo 1: Web scraper -> CSV / Excel
Target: https://books.toscrape.com/ (a site built for scraping practice)

Features shown:
- Polite crawling: fixed interval between requests, custom User-Agent
- Retry with backoff on HTTP errors
- Pagination handling
- Clean structured output: CSV + Excel (.xlsx) with the same schema

Usage:
    python scraper.py --pages 3
Output:
    output/books.csv, output/books.xlsx
"""
import argparse
import csv
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://books.toscrape.com/"
HEADERS = {"User-Agent": "PortfolioDemoScraper/1.0 (+contact: info@recalm.jp)"}
INTERVAL_SEC = 1.0
MAX_RETRIES = 3


def fetch(url: str) -> BeautifulSoup:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:  # retry with backoff
            last_err = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def parse_page(soup: BeautifulSoup) -> list[dict]:
    rows = []
    for book in soup.select("article.product_pod"):
        title = book.h3.a["title"]
        price = book.select_one(".price_color").get_text(strip=True)
        availability = book.select_one(".availability").get_text(strip=True)
        rating = book.select_one("p.star-rating")["class"][1]
        link = book.h3.a["href"]
        rows.append(
            {
                "title": title,
                "price_gbp": price.replace("£", ""),
                "availability": availability,
                "rating": rating,
                "url": requests.compat.urljoin(BASE, link),
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=3, help="number of catalogue pages to scrape")
    args = ap.parse_args()

    all_rows: list[dict] = []
    for page in range(1, args.pages + 1):
        url = BASE if page == 1 else f"{BASE}catalogue/page-{page}.html"
        soup = fetch(url)
        rows = parse_page(soup)
        all_rows.extend(rows)
        print(f"page {page}: {len(rows)} books (total {len(all_rows)})")
        time.sleep(INTERVAL_SEC)

    out = Path(__file__).parent / "output"
    out.mkdir(exist_ok=True)

    csv_path = out / "books.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    try:
        import pandas as pd

        xlsx_path = out / "books.xlsx"
        pd.DataFrame(all_rows).to_excel(xlsx_path, index=False)
        print(f"wrote {csv_path} and {xlsx_path} ({len(all_rows)} rows)")
    except ImportError:
        print(f"wrote {csv_path} ({len(all_rows)} rows); pandas not available, skipped xlsx")


if __name__ == "__main__":
    main()
