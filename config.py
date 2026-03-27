# ─────────────────────────────────────────────
#  RT Scraper — Central Configuration
# ─────────────────────────────────────────────

BASE_URL = "https://www.rottentomatoes.com"

# Selenium driver settings
HEADLESS          = True          # Set False to watch the browser
PAGE_LOAD_TIMEOUT = 30            # seconds
IMPLICIT_WAIT     = 8             # seconds for element detection

# Polite scraping delays (seconds)
DELAY_BETWEEN_PAGES    = 1.5
DELAY_BETWEEN_MOVIES   = 0.8
LOAD_MORE_WAIT         = 2.5      # wait after clicking "Load More"

# Output
OUTPUT_DIR          = "outputs"
RATED_EXCEL         = "RT_Movies_Rated.xlsx"
UNRATED_EXCEL       = "RT_Movies_Unrated.xlsx"

# Sheets
GENERAL_SHEET       = "General Info"
INSIGHTS_SHEET      = "Movie Insights"
UNRATED_SHEET       = "Not Rated Yet"

# Request headers (used as fallback without Selenium)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
