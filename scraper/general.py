# ─────────────────────────────────────────────
#  scraper/general.py
#  Extract general info (title, date, rating)
#  from the browse/listing page.
# ─────────────────────────────────────────────

import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

log = logging.getLogger(__name__)


def _clean(text: str) -> str:
    """Strip whitespace, newlines, and the word 'Streaming'."""
    text = text.strip().replace("Streaming", "").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(raw: str):
    """Try to parse a release date string into a datetime object."""
    raw = _clean(raw)
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%b %Y", "%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def scrape_general(soup: BeautifulSoup, max_movies: int) -> tuple[list[dict], list[dict]]:
    """
    Parse the browse page soup.
    Returns two lists:
      - rated   : movies with a valid Tomatometer score
      - unrated : movies missing a score
    """
    rated   = []
    unrated = []

    containers = soup.find_all("div", class_="flex-container")
    log.info(f"Found {len(containers)} movie containers on page.")

    serial = 0
    for container in containers:
        if serial >= max_movies:
            break

        titles   = container.find_all("span", class_="p--small")
        dates    = container.find_all("span", class_="smaller")
        scores   = container.find_all("rt-text", slot="criticsScore")

        count = min(len(titles), len(dates))
        for i in range(count):
            if serial >= max_movies:
                break

            name    = _clean(titles[i].get_text())
            date_raw = _clean(dates[i].get_text())
            score   = scores[i].get_text(strip=True) if i < len(scores) else ""

            # Build href link for this movie if available
            link_tag = container.find_all("a", href=True)
            href = ""
            if i < len(link_tag):
                raw_href = link_tag[i].get("href", "")
                href = (config.BASE_URL + raw_href) if raw_href.startswith("/m/") else raw_href

            dt = _parse_date(date_raw)
            record = {
                "s_no"        : serial + 1,
                "title"       : name,
                "release_date": date_raw,
                "release_dt"  : dt,
                "release_month": dt.strftime("%B %Y") if dt else "Unknown",
                "tomatometer" : score,
                "link"        : href,
            }

            if not name:
                continue

            if score and score not in ("", "--", "N/A"):
                rated.append(record)
                log.debug(f"  [{serial+1}] {name} | {date_raw} | {score}")
            else:
                unrated.append(record)
                log.debug(f"  [{serial+1}] {name} | {date_raw} | NO SCORE → unrated bucket")

            serial += 1

    log.info(f"General scrape complete → {len(rated)} rated, {len(unrated)} unrated.")
    return rated, unrated
