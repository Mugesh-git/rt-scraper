#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  main.py  ·  RT Advanced Movie Scraper
#  Usage:  python main.py
# ─────────────────────────────────────────────

import logging
import sys
import os

# ── Logging setup ─────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ── Imports ────────────────────────────────────
from scraper.loader   import fetch_page_with_target
from scraper.general  import scrape_general
from scraper.linker   import collect_links
from scraper.insights import scrape_insights
from storage.excel_writer import save_excel
import config


# ── Helpers ────────────────────────────────────
def _banner():
    print("""
╔══════════════════════════════════════════════════╗
║    🍅  Rotten Tomatoes Advanced Scraper v2.0     ║
║         Powered by Selenium + BeautifulSoup       ║
╚══════════════════════════════════════════════════╝
    """)


def _ask_url() -> str:
    print("Paste a Rotten Tomatoes browse URL.")
    print("Examples:")
    print("  • https://www.rottentomatoes.com/browse/movies_at_home/critics:certified_fresh")
    print("  • https://www.rottentomatoes.com/browse/movies_in_theaters/sort:top_box_office")
    url = input("\n🔗 URL: ").strip()
    if not url.startswith("http"):
        log.error("Invalid URL. Please paste a full https:// address.")
        sys.exit(1)
    return url


def _ask_count() -> int:
    while True:
        try:
            n = int(input("🎬 How many movies to scrape? (e.g. 50): ").strip())
            if n < 1:
                raise ValueError
            return n
        except ValueError:
            print("  Please enter a positive number.")


def _ask_mode() -> int:
    print("""
Choose scraping mode:
  [1] General only  — title, release date, Tomatometer
  [2] Insights only — synopsis, cast, genre, director…
  [3] Both          — full dataset (slower)
    """)
    while True:
        try:
            mode = int(input("Mode [1/2/3]: ").strip())
            if mode in (1, 2, 3):
                return mode
        except ValueError:
            pass
        print("  Enter 1, 2, or 3.")


# ── Main ────────────────────────────────────────
def main():
    _banner()

    url        = _ask_url()
    max_movies = _ask_count()
    mode       = _ask_mode()

    log.info(f"Target URL   : {url}")
    log.info(f"Target count : {max_movies}")
    log.info(f"Scrape mode  : {mode}")
    print("\n🚀 Opening browser and loading page (this may take a moment)…\n")

    # ── Step 1: Load page with Selenium (clicking Load More as needed) ──
    soup = fetch_page_with_target(url, max_movies)

    rated_general   = []
    unrated_general = []
    rated_insights  = []
    unrated_insights = []

    # ── Step 2: General scrape ──────────────────────────────────────────
    if mode in (1, 3):
        print("\n📋 Scraping general movie data…")
        rated_general, unrated_general = scrape_general(soup, max_movies)
        log.info(f"General: {len(rated_general)} rated, {len(unrated_general)} unrated")

    # ── Step 3: Insights scrape ─────────────────────────────────────────
    if mode in (2, 3):
        print("\n🔍 Collecting movie detail links…")
        links = collect_links(soup, max_movies)

        print(f"\n🎬 Scraping insights for {len(links)} movies…")
        rated_insights, unrated_insights = scrape_insights(links)
        log.info(f"Insights: {len(rated_insights)} rated, {len(unrated_insights)} unrated")

    # ── Step 4: Write Excel ─────────────────────────────────────────────
    print("\n💾 Saving to Excel…")
    rated_path, unrated_path = save_excel(
        rated_general    = rated_general,
        unrated_general  = unrated_general,
        rated_insights   = rated_insights   if mode in (2, 3) else None,
        unrated_insights = unrated_insights if mode in (2, 3) else None,
    )

    # ── Summary ─────────────────────────────────────────────────────────
    print(f"""
╔══════════════════════════════════════════════════╗
║  ✅  Scrape Complete!                             ║
╠══════════════════════════════════════════════════╣
║  Rated movies   : {(len(rated_general) or len(rated_insights)):<28} ║
║  Unrated movies : {(len(unrated_general) + len(unrated_insights)):<28} ║
║                                                  ║
║  📁 Rated Excel   → {os.path.basename(rated_path):<27} ║
║  📁 Unrated Excel → {os.path.basename(unrated_path):<27} ║
╠══════════════════════════════════════════════════╣
║  🍅 Launch dashboard:                             ║
║     streamlit run dashboard.py                   ║
╚══════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
