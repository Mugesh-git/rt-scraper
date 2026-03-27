# ─────────────────────────────────────────────
#  scraper/insights.py
#  Deep scrape each movie's detail page:
#  synopsis, cast, genre, director, rating…
# ─────────────────────────────────────────────

import time
import logging
import requests
from bs4 import BeautifulSoup
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

log = logging.getLogger(__name__)

_session = requests.Session()
_session.headers.update(config.HEADERS)


def _get_soup(url: str) -> BeautifulSoup | None:
    """Fetch a URL and return its soup, or None on failure."""
    try:
        r = _session.get(url, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        log.warning(f"  Failed to fetch {url}: {e}")
        return None


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def scrape_insights(links: list[str]) -> tuple[list[dict], list[dict]]:
    """
    Scrape detailed info for each movie link.
    Returns:
      - rated_insights   : movies with audience/critic scores
      - unrated_insights : movies with no scores at all
    """
    rated   = []
    unrated = []
    total   = len(links)

    for idx, url in enumerate(links, 1):
        log.info(f"  [{idx}/{total}] Scraping insights → {url}")
        soup = _get_soup(url)
        if soup is None:
            continue

        record = {"link": url}

        # ── Title ──────────────────────────────────────────────────────────
        title_tags = soup.find_all("rt-text", {"slot": "title"})
        record["title"] = _clean(title_tags[1].text) if len(title_tags) > 1 else _clean(title_tags[0].text) if title_tags else "Unknown"

        # ── Synopsis ───────────────────────────────────────────────────────
        synopsis = ""
        for wrap in soup.find_all("div", class_="synopsis-wrap"):
            parts = list(wrap.children)
            for i, p in enumerate(parts):
                if hasattr(p, "text") and len(p.text.strip()) > 40:
                    synopsis = _clean(p.text)
                    break
            if synopsis:
                break
        record["synopsis"] = synopsis

        # ── Structured metadata (Director, Genre, Rating, etc.) ────────────
        for cw in soup.find_all("div", class_="content-wrap"):
            for cat in cw.find_all("div", class_="category-wrap"):
                keys   = cat.find_all("rt-text", class_="key")
                values = cat.find_all("dd")
                for k, v in zip(keys, values):
                    field = _clean(k.text).lower().replace(" ", "_")
                    val   = _clean(v.get_text(separator=" "))
                    record[field] = val

        # ── Cast ───────────────────────────────────────────────────────────
        cast_entries = []
        for div in soup.find_all("div", slot="content"):
            for person in div.find_all("div", slot="insetText"):
                name_tag = person.find("p", class_="name")
                role_tag = person.find("p", class_="role")
                if name_tag and role_tag:
                    cast_entries.append(f"{_clean(name_tag.text)} as {_clean(role_tag.text)}")
        record["cast_and_crew"] = ", ".join(cast_entries)

        # ── Scores ─────────────────────────────────────────────────────────
        critic_score   = soup.find("rt-text", {"slot": "criticsScore"})
        audience_score = soup.find("rt-text", {"slot": "audienceScore"})
        record["tomatometer"]    = _clean(critic_score.text)   if critic_score   else ""
        record["audience_score"] = _clean(audience_score.text) if audience_score else ""

        # ── Bucket: rated vs unrated ───────────────────────────────────────
        if record["tomatometer"] or record["audience_score"]:
            rated.append(record)
        else:
            unrated.append(record)

        time.sleep(config.DELAY_BETWEEN_MOVIES)

    log.info(f"Insights complete → {len(rated)} rated, {len(unrated)} unrated.")
    return rated, unrated
