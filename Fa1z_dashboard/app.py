# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Global Happiness Dashboard", page_icon="😊", layout="wide")

# ---------- helpers ----------
@st.cache_data
def load_csv(file_or_path):
    df = pd.read_csv(file_or_path)
    df.columns = [c.strip() for c in df.columns]
    return df

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    # خرائط الأسماء الشائعة عبر نسخ التقرير
    low = {c.lower(): c for c in df.columns}

    def pick(*cands):
        for c in cands:
            if c in low:
                return low[c]
        return None

    mapping = {}
    country = pick("country name", "country", "countryname", "name")
    year    = pick("year")
    region  = pick("regional indicator", "region", "regional_indicator", "subregion", "continent")

    score   = pick("ladder score", "life ladder", "happiness score", "score")
    gdp     = pick("logged gdp per capita", "gdp per capita", "log gdp per capita", "gdp")
    social  = pick("social support", "social_support")
    healthy = pick("healthy life expectancy at birth", "healthy life expectancy", "life expectancy")
    freedom = pick("freedom to make life choices", "freedom")
    generosity = pick("generosity")  # قد لا يوجد
    corruption = pick("perceptions of corruption", "corruption")  # قد لا يوجد

    if country:   mapping[country]   = "Country"
    if year:      mapping[year]      = "Year"
    if region:    mapping[region]    = "Region"

    if score:     mapping[score]     = "HappinessScore"
    if gdp:       mapping[gdp]       = "GDPperCapita"
    if social:    mapping[social]    = "SocialSupport"
    if healthy:   mapping[healthy]   = "HealthyLife"
    if freedom:   mapping[freedom]   = "Freedom"
    if generosity:mapping[generosity]= "Generosity"
    if corruption: mapping[corruption]= "Corruption"

    df = df.rename(columns=mapping).copy()

    numeric = ["HappinessScore","GDPperCapita","SocialSupport","HealthyLife","Freedom","Generosity","Corruption"]
    for c in numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "Year" not in df.columns:
        df["Year"] = pd.NA
    if "Region" not in df.columns:
        df["Region"] = "Unknown"
    return df

# ---------- load data ----------
st.title("Global AI Happiness Dashboard")
st.caption("Interactive dashboard for World Happiness (supports 2024 CSV and similar schemas).")

uploaded = st.sidebar.file_uploader("ارفع ملف World-happiness-report-2024.csv", type=["csv"])
if uploaded is not None:
    raw = load_csv(uploaded)
else:
    # غيّر المسار لو ملفك في مكان مختلف
    DEFAULT_PATH = "World-happiness-report-2024.csv"
    try:
        raw = load_csv(DEFAULT_PATH)
    except Exception:
        st.warning("ارفَع الملف من الشريط الجانبي أو ضع World-happiness-report-2024.csv بجانب app.py")
        st.stop()

df = normalize_cols(raw)

required = ["Country","Region","HappinessScore"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"أعمدة ناقصة: {missing}. تأكد من أسماء الأعمدة في ملفك.")
    st.write("الأعمدة المتوفرة:", list(df.columns))
    st.stop()

# ---------- sidebar filters ----------
st.sidebar.header("Filters")
all_regions = sorted(df["Region"].dropna().unique().tolist())
sel_regions = st.sidebar.multiselect("Select Region(s)", options=all_regions, default=all_regions)

years = sorted([int(y) for y in df["Year"].dropna().unique()]) if df["Year"].notna().any() else []
sel_year = st.sidebar.selectbox("Year", options=["(All)"]+years, index=0)

metrics = [c for c in ["HappinessScore","GDPperCapita","SocialSupport","HealthyLife","Freedom","Generosity","Corruption"] if c in df.columns]
primary_metric = st.sidebar.selectbox("Primary metric (for cards & rankings)", options=metrics, index=0)

top_n = st.sidebar.slider("Top N countries (charts)", 5, 25, 10)

# apply filters
f = df[df["Region"].isin(sel_regions)].copy()
if sel_year != "(All)":
    f = f[f["Year"] == sel_year]

if f.empty:
    st.warning("لا توجد بيانات بعد تطبيق الفلاتر.")
    st.stop()

# ---------- header text ----------
st.markdown(
"""
This dashboard lets you explore happiness across regions using core dimensions:
**Happiness Score**, **GDP per Capita**, **Social Support**, **Healthy Life Expectancy**, **Freedom**, **Generosity**, and **Perceived Corruption** (where available).
Use the filters to focus on regions or a specific year; all sections update instantly.
"""
)

# ---------- tabs ----------
tab_overview, tab_viz, tab_table, tab_conc = st.tabs(["Overview", "Visualizations", "Data Table", "Conclusion & Recommendations"])

# ---------- OVERVIEW ----------
with tab_overview:
    st.subheader("Summary Metrics")
    c1,c2,c3,c4 = st.columns(4)
    countries_cnt = f["Country"].nunique()
    avg_metric = float(f[primary_metric].mean())
    global_avg = float(df[primary_metric].mean())
    top_row = f.sort_values(primary_metric, ascending=False).head(1)
    top_country = top_row.iloc[0]["Country"]
    top_value = float(top_row.iloc[0][primary_metric])
    reg_means = f.groupby("Region")[primary_metric].mean().sort_values(ascending=False)
    best_region = reg_means.index[0]; best_region_val = float(reg_means.iloc[0])

    with c1: st.metric("Countries", countries_cnt)
    with c2: st.metric(f"Average {primary_metric}", f"{avg_metric:.2f}", delta=f"{avg_metric-global_avg:+.2f} vs global")
    with c3: st.metric("Top Country", top_country, delta=f"{top_value:.2f}")
    with c4: st.metric("Best Region (avg)", best_region, delta=f"{best_region_val:.2f}")

    st.divider()
    st.subheader("Top Countries")
    ranked = f[["Country","Region","Year",primary_metric]+[c for c in metrics if c!=primary_metric]].sort_values(primary_metric, ascending=False)
    st.dataframe(ranked.head(30), use_container_width=True)

# ---------- VISUALIZATIONS ----------
with tab_viz:
    left, right = st.columns([1,1])

    with left:
        st.markdown(f"**Top {top_n} by {primary_metric}**")
        top_df = f.sort_values(primary_metric, ascending=False).head(top_n)
        fig, ax = plt.subplots(figsize=(9,5))
        ax.bar(top_df["Country"], top_df[primary_metric])
        ax.set_ylabel(primary_metric)
        ax.set_xticklabels(top_df["Country"], rotation=45, ha="right")
        st.pyplot(fig)

    with right:
        st.markdown("**Distribution of Happiness Scores**")
        fig2, ax2 = plt.subplots(figsize=(9,5))
        ax2.hist(f["HappinessScore"].dropna(), bins=15)
        ax2.set_xlabel("Happiness Score")
        ax2.set_ylabel("Number of countries")
        st.pyplot(fig2)

    st.markdown("***")
    # Scatter: GDP vs Happiness
    if "GDPperCapita" in f.columns:
        st.markdown("**Happiness vs GDP per Capita**")
        x = f["GDPperCapita"].astype(float)
        y = f["HappinessScore"].astype(float)
        fig3, ax3 = plt.subplots(figsize=(8,6))
        ax3.scatter(x, y)
        ax3.set_xlabel("GDP per Capita (logged)")
        ax3.set_ylabel("Happiness Score")
        # خط انحدار بسيط
        ok = ~(x.isna() | y.isna())
        if ok.sum() > 2:
            m, b = np.polyfit(x[ok], y[ok], 1)
            xs = np.linspace(x[ok].min(), x[ok].max(), 100)
            ax3.plot(xs, m*xs + b)
        st.pyplot(fig3)

    # Boxplot by region (matplotlib only)
    st.markdown("**Regional Distribution (Boxplot)**")
    regions_order = sorted(f["Region"].unique().tolist())
    data_by_region = [f.loc[f["Region"]==r, "HappinessScore"].dropna().values for r in regions_order]
    fig4, ax4 = plt.subplots(figsize=(10,5))
    ax4.boxplot(data_by_region, labels=regions_order, showfliers=True)
    ax4.set_ylabel("Happiness Score")
    plt.setp(ax4.get_xticklabels(), rotation=30, ha="right")
    st.pyplot(fig4)

# ---------- DATA TABLE ----------
with tab_table:
    st.subheader("Full Data (filtered)")
    st.dataframe(f[["Country","Region","Year"]+metrics], use_container_width=True)

# ---------- CONCLUSION ----------
with tab_conc:
    st.subheader("Conclusion & Recommendations")
    st.write(
        "- Use the **filters** to compare regions and spot high performers.\n"
        "- Look at **Top N** to highlight best countries; combine with **GDP vs Score** to see income–happiness patterns.\n"
        "- Use **Boxplot** to understand spread and outliers within each region.\n"
        "- Consider tracking changes by **Year** if your CSV includes multiple years."
    )