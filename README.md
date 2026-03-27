# 🍅 RT Advanced Movie Scraper v2.0

A production-grade Rotten Tomatoes scraper with **Selenium-powered Load More pagination**, structured Excel exports, and a full **Streamlit analytics dashboard**.

---

## 📁 Project Structure

```
rt_scraper/
├── main.py                 ← Run this to scrape
├── dashboard.py            ← Run this for the dashboard
├── config.py               ← All settings in one place
├── requirements.txt
├── scraper/
│   ├── loader.py           ← Selenium + Load More handler
│   ├── general.py          ← General listing scraper
│   ├── linker.py           ← Movie link collector
│   └── insights.py         ← Deep detail scraper
├── storage/
│   └── excel_writer.py     ← Styled Excel output
└── outputs/                ← Auto-created, all Excel files saved here
```

---

## ⚡ Installation

```bash
pip install -r requirements.txt
```

Chrome must be installed on your machine. `webdriver-manager` handles the ChromeDriver automatically.

---

## 🚀 Usage

### Step 1 — Scrape

```bash
python main.py
```

You will be prompted for:
1. **URL** — paste any Rotten Tomatoes browse page, e.g.:
   - `https://www.rottentomatoes.com/browse/movies_at_home/critics:certified_fresh`
   - `https://www.rottentomatoes.com/browse/movies_in_theaters/sort:top_box_office`
2. **Movie count** — how many movies to scrape (e.g. `50`). The scraper will click **Load More** automatically until enough movies are loaded.
3. **Mode**:
   - `1` — General only (fast: title, date, Tomatometer)
   - `2` — Insights only (synopsis, cast, genre, director…)
   - `3` — Both (full dataset)

### Step 2 — Dashboard

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501` automatically.

---

## 📊 Dashboard Features

| Feature | Detail |
|---|---|
| KPI Cards | Total movies, avg score, fresh/rotten counts, genre count |
| Overview tab | Score histogram, fresh/rotten pie, top 10 bar chart |
| Timeline tab | Movies by month (bar + line), day-of-month pattern |
| Genres tab | Genre pie, genre bar, avg score by genre |
| Explore tab | Searchable full table with score progress bars |
| Unrated tab | Separate section for movies with no Tomatometer |
| Sidebar filters | Date range, month, score range, genre |

---

## 📂 Excel Output

Two files are created in `outputs/` per scrape run (timestamped):

**`RT_Movies_Rated_YYYYMMDD_HHMMSS.xlsx`**
- Sheet: `General Info` — title, date, score, link
- Sheet: `Movie Insights` — synopsis, cast, genre, director (if mode 2 or 3)

**`RT_Movies_Unrated_YYYYMMDD_HHMMSS.xlsx`**
- Sheet: `Not Rated Yet` — movies with no Tomatometer score

---

## ⚙️ Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `HEADLESS` | `True` | Set `False` to watch the browser |
| `DELAY_BETWEEN_MOVIES` | `0.8s` | Polite delay between detail requests |
| `LOAD_MORE_WAIT` | `2.5s` | Wait after clicking Load More |
| `PAGE_LOAD_TIMEOUT` | `30s` | Selenium page load timeout |

---

## 📝 Notes

- Rotten Tomatoes may occasionally update their HTML structure. If scraping breaks, check the selectors in `scraper/loader.py` and `scraper/general.py`.
- Unrated movies (no Tomatometer) are separated automatically — they appear in the Unrated Excel file and the dashboard's Unrated tab.
- Log file `scraper.log` is created in the project root for debugging.
