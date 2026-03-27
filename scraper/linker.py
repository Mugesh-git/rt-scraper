# ─────────────────────────────────────────────
#  scraper/linker.py
#  Collect individual movie page links from
#  the already-loaded browse page soup.
# ─────────────────────────────────────────────

import logging
from bs4 import BeautifulSoup
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

log = logging.getLogger(__name__)


def collect_links(soup: BeautifulSoup, max_movies: int) -> list[str]:
    """
    Extract up to `max_movies` unique movie detail links
    from the browse page soup.
    """
    seen  = set()
    links = []

    wrap = soup.find_all("div", class_="discovery-tiles__wrap")
    if not wrap:
        # Fallback: search all anchor tags with /m/ path
        wrap = [soup]

    for section in wrap:
        for a in section.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("/m/"):
                continue
            full = config.BASE_URL + href
            if full not in seen:
                seen.add(full)
                links.append(full)
            if len(links) >= max_movies:
                break
        if len(links) >= max_movies:
            break

    log.info(f"Collected {len(links)} unique movie links.")
    return links
