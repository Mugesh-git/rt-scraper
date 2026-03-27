# ─────────────────────────────────────────────
#  dashboard.py
#  Streamlit dashboard for RT scraped data
#  Run: streamlit run dashboard.py
# ─────────────────────────────────────────────

import os
import glob
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🍅 RT Movie Intelligence",
    page_icon="🍅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 { font-family: 'DM Serif Display', serif; }

/* Dark cinematic sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0d0d1a 0%, #1a0a0a 100%);
    border-right: 1px solid #2a2a3a;
}
section[data-testid="stSidebar"] * { color: #e8e0d0 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label { color: #fa5252 !important; font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #16213e 100%);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.metric-card .value { font-size: 2.2rem; font-weight: 700; color: #fa5252; font-family: 'DM Serif Display', serif; }
.metric-card .label { font-size: 0.78rem; color: #888; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }

/* Section headers */
.section-header {
    display: flex; align-items: center; gap: 10px;
    border-left: 4px solid #fa5252;
    padding-left: 12px;
    margin: 2rem 0 1rem 0;
}
.section-header h3 { margin: 0; color: #1a1a2e; font-size: 1.3rem; }

/* Unrated badge */
.unrated-badge {
    background: #4a0e0e;
    color: #ffaaaa;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #f0f0f0; }
.stTabs [data-baseweb="tab"] {
    background: #f8f8f8;
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    font-weight: 500;
    border: 1px solid #e0e0e0;
    border-bottom: none;
}
.stTabs [aria-selected="true"] {
    background: #fa5252 !important;
    color: white !important;
    border-color: #fa5252 !important;
}

/* DataFrame tweaks */
.dataframe { font-size: 0.82rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
OUTPUT_DIR = "outputs"

@st.cache_data(ttl=60)
def load_excel_data(path: str, sheet: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(path, sheet_name=sheet)
        return df
    except Exception:
        return pd.DataFrame()


def find_latest_files():
    rated_files   = sorted(glob.glob(os.path.join(OUTPUT_DIR, "RT_Movies_Rated_*.xlsx")),   reverse=True)
    unrated_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "RT_Movies_Unrated_*.xlsx")), reverse=True)
    return (rated_files[0]   if rated_files   else None,
            unrated_files[0] if unrated_files else None)


def prep_general(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    # Normalise column names
    df.columns = [c.strip() for c in df.columns]

    score_col = next((c for c in df.columns if "tomato" in c.lower()), None)
    if score_col:
        df["Score"] = pd.to_numeric(
            df[score_col].astype(str).str.replace("%", "").str.strip(),
            errors="coerce"
        )

    date_col = next((c for c in df.columns if "release" in c.lower() and "month" not in c.lower()), None)
    if date_col:
        df["ReleaseDate"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=False)
        df["Month"]       = df["ReleaseDate"].dt.to_period("M").astype(str)
        df["Year"]        = df["ReleaseDate"].dt.year
        df["MonthName"]   = df["ReleaseDate"].dt.strftime("%B")
        df["Day"]         = df["ReleaseDate"].dt.day

    genre_col = next((c for c in df.columns if "genre" in c.lower()), None)
    if genre_col:
        df["Genre"] = df[genre_col].fillna("Unknown")

    return df


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem;">
        <div style="font-size:3rem">🍅</div>
        <div style="font-size:1.2rem; font-family:'DM Serif Display',serif; color:#fa5252; font-weight:700;">
            RT Intelligence
        </div>
        <div style="font-size:0.72rem; color:#666; margin-top:4px; text-transform:uppercase; letter-spacing:0.1em;">
            Movie Analytics Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    rated_file, unrated_file = find_latest_files()

    if not rated_file:
        st.warning("No data found. Run the scraper first.")
        st.info("python main.py")
        st.stop()

    ts_str = os.path.basename(rated_file).replace("RT_Movies_Rated_","").replace(".xlsx","")
    try:
        scraped_at = datetime.strptime(ts_str, "%Y%m%d_%H%M%S").strftime("%d %b %Y, %H:%M")
    except Exception:
        scraped_at = ts_str
    st.markdown(f"<div style='font-size:0.72rem;color:#888;text-align:center;margin-bottom:1rem'>Last scraped: {scraped_at}</div>", unsafe_allow_html=True)

    # Load data
    df_gen = prep_general(load_excel_data(rated_file, "General Info"))
    df_ins = load_excel_data(rated_file, "Movie Insights") if not df_gen.empty else pd.DataFrame()

    st.markdown("---")
    st.markdown("### 🎛 Filters")

    # Date range filter
    if "ReleaseDate" in df_gen.columns:
        min_d = df_gen["ReleaseDate"].dropna().min()
        max_d = df_gen["ReleaseDate"].dropna().max()
        if pd.notna(min_d) and pd.notna(max_d):
            date_range = st.date_input(
                "Release Date Range",
                value=(min_d.date(), max_d.date()),
                min_value=min_d.date(),
                max_value=max_d.date(),
            )
        else:
            date_range = None
    else:
        date_range = None

    # Month multi-select
    if "MonthName" in df_gen.columns:
        all_months = sorted(df_gen["MonthName"].dropna().unique().tolist())
        sel_months = st.multiselect("Filter by Month", all_months, default=all_months)
    else:
        sel_months = []

    # Score range
    if "Score" in df_gen.columns:
        score_min, score_max = st.slider(
            "Tomatometer Range (%)",
            min_value=0, max_value=100,
            value=(0, 100), step=5
        )
    else:
        score_min, score_max = 0, 100

    # Genre filter
    if "Genre" in df_gen.columns:
        all_genres = sorted(df_gen["Genre"].dropna().unique().tolist())
        sel_genres = st.multiselect("Filter by Genre", all_genres, default=all_genres)
    else:
        sel_genres = []

    st.markdown("---")
    show_unrated = st.checkbox("Show Unrated Section", value=True)
    dark_charts  = st.checkbox("Dark chart theme", value=True)

CHART_TEMPLATE = "plotly_dark" if dark_charts else "plotly_white"
TOMATO_COLOR   = "#fa5252"
COLORS_PALETTE = px.colors.qualitative.Bold


# ── Apply filters ─────────────────────────────────────────────────────────────
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    filtered = df.copy()

    if date_range and len(date_range) == 2 and "ReleaseDate" in filtered.columns:
        start, end = date_range
        filtered = filtered[
            (filtered["ReleaseDate"].dt.date >= start) &
            (filtered["ReleaseDate"].dt.date <= end)
        ]

    if sel_months and "MonthName" in filtered.columns:
        filtered = filtered[filtered["MonthName"].isin(sel_months)]

    if "Score" in filtered.columns:
        filtered = filtered[
            (filtered["Score"] >= score_min) &
            (filtered["Score"] <= score_max)
        ]

    if sel_genres and "Genre" in filtered.columns:
        filtered = filtered[filtered["Genre"].isin(sel_genres)]

    return filtered


df_filtered = apply_filters(df_gen)


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 1.5rem 0 0.5rem">
    <h1 style="font-family:'DM Serif Display',serif; font-size:2.4rem; margin:0; color:#1a1a2e">
        🍅 Rotten Tomatoes Intelligence
    </h1>
    <p style="color:#888; margin-top:6px; font-size:0.9rem">
        Interactive analytics for your scraped movie dataset
    </p>
</div>
""", unsafe_allow_html=True)

# ── KPI metrics ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_rated   = len(df_filtered)
avg_score     = df_filtered["Score"].mean() if "Score" in df_filtered.columns else 0
fresh_count   = int((df_filtered["Score"] >= 60).sum()) if "Score" in df_filtered.columns else 0
rotten_count  = int((df_filtered["Score"] < 60).sum())  if "Score" in df_filtered.columns else 0
genres_count  = df_filtered["Genre"].nunique() if "Genre" in df_filtered.columns else 0

with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="value">{total_rated}</div>
        <div class="label">Movies Found</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="value">{avg_score:.0f}%</div>
        <div class="label">Avg Tomatometer</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class="metric-card">
        <div class="value" style="color:#4caf50">{fresh_count}</div>
        <div class="label">🍅 Fresh (≥60%)</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""<div class="metric-card">
        <div class="value" style="color:#fa5252">{rotten_count}</div>
        <div class="label">🤢 Rotten (&lt;60%)</div>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""<div class="metric-card">
        <div class="value" style="color:#ffb700">{genres_count}</div>
        <div class="label">Genres</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_overview, tab_timeline, tab_genres, tab_explore, tab_unrated = st.tabs([
    "📊 Overview", "📅 Timeline", "🎬 Genres", "🔍 Explore", "⚠️ Unrated"
])


# ─── TAB 1 : OVERVIEW ────────────────────────────────────────────────────────
with tab_overview:
    st.markdown("#### Score Distribution")

    col_a, col_b = st.columns([1.6, 1])

    with col_a:
        if "Score" in df_filtered.columns and not df_filtered["Score"].dropna().empty:
            fig_hist = px.histogram(
                df_filtered.dropna(subset=["Score"]),
                x="Score", nbins=20,
                color_discrete_sequence=[TOMATO_COLOR],
                template=CHART_TEMPLATE,
                labels={"Score": "Tomatometer (%)"},
            )
            fig_hist.add_vline(x=60, line_dash="dash", line_color="#ffb700",
                               annotation_text="Fresh threshold (60%)",
                               annotation_position="top right")
            fig_hist.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
                height=320,
                bargap=0.05,
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        if "Score" in df_filtered.columns:
            fresh   = int((df_filtered["Score"] >= 60).sum())
            rotten  = int((df_filtered["Score"] <  60).sum())
            fig_pie = go.Figure(go.Pie(
                labels=["🍅 Fresh", "🤢 Rotten"],
                values=[fresh, rotten],
                hole=0.55,
                marker_colors=["#4caf50", "#fa5252"],
                textinfo="label+percent",
                hoverinfo="label+value",
            ))
            fig_pie.update_layout(
                template=CHART_TEMPLATE,
                margin=dict(l=0, r=0, t=10, b=0),
                height=320,
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # Top 10 movies by score
    st.markdown("#### 🏆 Top 10 Highest Rated")
    if "Score" in df_filtered.columns and "Title" in df_filtered.columns:
        top10 = df_filtered.nlargest(10, "Score")[["Title", "Score", "release_month" if "release_month" in df_filtered.columns else "Month"]].reset_index(drop=True)
        top10.index += 1
        fig_bar = px.bar(
            top10, x="Score", y="Title",
            orientation="h",
            color="Score",
            color_continuous_scale=["#fa5252", "#ffb700", "#4caf50"],
            template=CHART_TEMPLATE,
            text="Score",
        )
        fig_bar.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_bar.update_layout(
            height=380, margin=dict(l=0, r=60, t=10, b=0),
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# ─── TAB 2 : TIMELINE ────────────────────────────────────────────────────────
with tab_timeline:
    st.markdown("#### Movies Released by Month")

    if "Month" in df_filtered.columns and not df_filtered.empty:
        monthly = (
            df_filtered.groupby("Month")
            .agg(Count=("Title", "count"), AvgScore=("Score", "mean"))
            .reset_index()
            .sort_values("Month")
        )

        fig_line = go.Figure()
        fig_line.add_trace(go.Bar(
            x=monthly["Month"], y=monthly["Count"],
            name="# Movies",
            marker_color=TOMATO_COLOR,
            opacity=0.7,
            yaxis="y",
        ))
        fig_line.add_trace(go.Scatter(
            x=monthly["Month"], y=monthly["AvgScore"].round(1),
            name="Avg Score (%)",
            mode="lines+markers",
            line=dict(color="#ffb700", width=2.5),
            marker=dict(size=7),
            yaxis="y2",
        ))
        fig_line.update_layout(
            template=CHART_TEMPLATE,
            height=380,
            margin=dict(l=0, r=60, t=20, b=0),
            legend=dict(orientation="h", y=1.08),
            yaxis=dict(title="# Movies"),
            yaxis2=dict(title="Avg Tomatometer (%)", overlaying="y", side="right"),
            xaxis=dict(tickangle=-30),
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # Day-of-month heatmap-style
        st.markdown("#### Day of Month Release Pattern")
        if "Day" in df_filtered.columns:
            day_counts = df_filtered["Day"].value_counts().sort_index().reset_index()
            day_counts.columns = ["Day", "Count"]
            fig_day = px.bar(
                day_counts, x="Day", y="Count",
                template=CHART_TEMPLATE,
                color="Count",
                color_continuous_scale=["#1a0a0a", TOMATO_COLOR],
                labels={"Day": "Day of Month", "Count": "# Movies Released"},
            )
            fig_day.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig_day, use_container_width=True)

    else:
        st.info("No date data available to plot timeline.")


# ─── TAB 3 : GENRES ──────────────────────────────────────────────────────────
with tab_genres:
    st.markdown("#### Genre Distribution")

    if "Genre" in df_filtered.columns and not df_filtered.empty:
        col_g1, col_g2 = st.columns(2)

        genre_counts = df_filtered["Genre"].value_counts().reset_index()
        genre_counts.columns = ["Genre", "Count"]

        with col_g1:
            fig_gpie = px.pie(
                genre_counts.head(10), names="Genre", values="Count",
                template=CHART_TEMPLATE,
                color_discrete_sequence=COLORS_PALETTE,
                hole=0.4,
            )
            fig_gpie.update_layout(height=360, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_gpie, use_container_width=True)

        with col_g2:
            fig_gbar = px.bar(
                genre_counts.head(12), x="Count", y="Genre",
                orientation="h",
                template=CHART_TEMPLATE,
                color="Count",
                color_continuous_scale=["#1a0a0a", TOMATO_COLOR, "#ffb700"],
            )
            fig_gbar.update_layout(
                height=360, margin=dict(l=0, r=0, t=20, b=0),
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_gbar, use_container_width=True)

        # Genre vs avg score
        st.markdown("#### Avg Tomatometer by Genre")
        if "Score" in df_filtered.columns:
            genre_score = (
                df_filtered.groupby("Genre")["Score"]
                .agg(["mean", "count"])
                .reset_index()
                .rename(columns={"mean": "AvgScore", "count": "Count"})
                .sort_values("AvgScore", ascending=False)
                .head(15)
            )
            fig_gs = px.bar(
                genre_score, x="Genre", y="AvgScore",
                template=CHART_TEMPLATE,
                color="AvgScore",
                color_continuous_scale=["#fa5252", "#ffb700", "#4caf50"],
                text="AvgScore",
            )
            fig_gs.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
            fig_gs.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig_gs, use_container_width=True)
    else:
        st.info("Genre data not available — run with 'Both' scraping mode to get genre info.")


# ─── TAB 4 : EXPLORE ─────────────────────────────────────────────────────────
with tab_explore:
    st.markdown("#### 🔍 Full Movie Table")

    display_cols = [c for c in ["Title", "Score", "MonthName", "Year", "Genre", "ReleaseDate", "Link"]
                    if c in df_filtered.columns]
    df_display = df_filtered[display_cols].copy()

    if "Score" in df_display.columns:
        df_display = df_display.sort_values("Score", ascending=False)

    # Search box
    search = st.text_input("Search by title", placeholder="e.g. Dune…")
    if search:
        df_display = df_display[df_display["Title"].str.contains(search, case=False, na=False)]

    st.dataframe(
        df_display.reset_index(drop=True),
        use_container_width=True,
        height=480,
        column_config={
            "Score":       st.column_config.ProgressColumn("Tomatometer (%)", min_value=0, max_value=100),
            "Link":        st.column_config.LinkColumn("RT Link"),
            "ReleaseDate": st.column_config.DateColumn("Release Date"),
        }
    )
    st.caption(f"Showing {len(df_display)} movies matching current filters.")

    # Insights table if available
    if not df_ins.empty:
        st.markdown("#### 🎬 Movie Insights")
        st.dataframe(df_ins, use_container_width=True, height=380)


# ─── TAB 5 : UNRATED ─────────────────────────────────────────────────────────
with tab_unrated:
    st.markdown("""
    <div style="background:#4a0e0e;border-left:4px solid #fa5252;padding:12px 16px;border-radius:6px;margin-bottom:1rem">
        <b style="color:#ffaaaa">⚠️ Unrated Movies</b>
        <span style="color:#cc8888;font-size:0.85rem;margin-left:8px">
            These movies have no Tomatometer score and are excluded from main analytics.
        </span>
    </div>
    """, unsafe_allow_html=True)

    if show_unrated and unrated_file and os.path.exists(unrated_file):
        df_unrated = load_excel_data(unrated_file, "Not Rated Yet")
        if not df_unrated.empty:
            st.metric("Total Unrated Movies", len(df_unrated))

            ucols = [c for c in ["Title", "Release Date", "Month/Year", "Link", "Reason"]
                     if c in df_unrated.columns]
            st.dataframe(
                df_unrated[ucols] if ucols else df_unrated,
                use_container_width=True,
                height=400,
                column_config={"Link": st.column_config.LinkColumn("RT Link")}
            )

            # Mini chart: unrated by month
            if "Month/Year" in df_unrated.columns:
                st.markdown("#### Unrated Movies by Month")
                uc = df_unrated["Month/Year"].value_counts().reset_index()
                uc.columns = ["Month", "Count"]
                fig_u = px.bar(uc, x="Month", y="Count",
                               color_discrete_sequence=["#7a1a1a"],
                               template=CHART_TEMPLATE)
                fig_u.update_layout(height=260, margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig_u, use_container_width=True)
        else:
            st.success("🎉 No unrated movies found in this scrape!")
    elif not show_unrated:
        st.info("Enable 'Show Unrated Section' in the sidebar to see this data.")
    else:
        st.warning("Unrated data file not found. Run the scraper first.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#888;font-size:0.75rem;margin-top:3rem;padding-top:1rem;border-top:1px solid #eee">
    🍅 RT Movie Intelligence · Built with Streamlit + Plotly · Data from Rotten Tomatoes
</div>
""", unsafe_allow_html=True)
