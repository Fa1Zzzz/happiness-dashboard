# app.py
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Global Happiness Dashboard", page_icon="😊", layout="wide")

# ----------------- Optional plotting (Plotly) -----------------
import plotly.express as px
import plotly.graph_objects as go

# ----------------- Helpers -----------------
@st.cache_data
def load_csv_local(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    low = {c.lower(): c for c in df.columns}
    def pick(*cands):
        for c in cands:
            if c in low:
                return low[c]
        return None

    mapping = {}
    country = pick("country name","country","countryname","name")
    year    = pick("year")
    region  = pick("regional indicator","region","regional_indicator","subregion","continent")
    score   = pick("ladder score","life ladder","happiness score","score")
    gdp     = pick("logged gdp per capita","gdp per capita","log gdp per capita","gdp")
    social  = pick("social support","social_support")
    healthy = pick("healthy life expectancy at birth","healthy life expectancy","life expectancy")
    freedom = pick("freedom to make life choices","freedom")
    generosity = pick("generosity")
    corruption = pick("perceptions of corruption","corruption")

    if country: mapping[country] = "Country"
    if year: mapping[year] = "Year"
    if region: mapping[region] = "Region"
    if score: mapping[score] = "HappinessScore"
    if gdp: mapping[gdp] = "GDPperCapita"
    if social: mapping[social] = "SocialSupport"
    if healthy: mapping[healthy] = "HealthyLife"
    if freedom: mapping[freedom] = "Freedom"
    if generosity: mapping[generosity] = "Generosity"
    if corruption: mapping[corruption] = "Corruption"

    df = df.rename(columns=mapping).copy()
    for c in ["HappinessScore","GDPperCapita","SocialSupport","HealthyLife","Freedom","Generosity","Corruption"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "Year" not in df.columns:   df["Year"] = pd.NA
    if "Region" not in df.columns: df["Region"] = "Unknown"
    return df

def burgundy_scale(light="#F5E6EB", mid="#B03A5B", dark="#6A0F2E"):
    """Continuous colorscale from light to dark burgundy."""
    return [
        (0.0,  light),
        (0.5,  mid),
        (1.0,  dark),
    ]

def get_colorscale(name: str):
    if name == "Burgundy":
        return burgundy_scale()
    if name == "Viridis":
        return px.colors.sequential.Viridis
    if name == "Blues":
        return px.colors.sequential.Blues
    if name == "Greens":
        return px.colors.sequential.Greens
    return burgundy_scale()

# ----------------- Load data (NO upload widget) -----------------
CSV_PATH = "World-happiness-report-2024.csv"
try:
    raw = load_csv_local(CSV_PATH)
except Exception:
    st.error("لم يتم العثور على الملف 'World-happiness-report-2024.csv' بجانب app.py. ضعه في نفس المجلد ثم أعد التشغيل.")
    st.stop()

df = normalize_cols(raw)

required = ["Country","Region","HappinessScore"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"أعمدة ناقصة: {missing}")
    st.stop()

# ----------------- Sidebar controls -----------------
st.sidebar.header("Filters")
years_all = sorted([int(y) for y in df["Year"].dropna().unique()]) if df["Year"].notna().any() else []
sel_year = st.sidebar.selectbox("السنة", options=years_all or ["(All)"], index=(len(years_all)-1 if years_all else 0))

regions_all = ["(All)"] + sorted(df["Region"].dropna().unique().tolist())
sel_region = st.sidebar.selectbox("المنطقة", options=regions_all, index=0)

metrics_all = [c for c in ["HappinessScore","GDPperCapita","SocialSupport","HealthyLife","Freedom","Generosity","Corruption"] if c in df.columns]
primary_metric = st.sidebar.selectbox("المقياس الرئيسي (للترتيب والخريطة)", options=metrics_all, index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("Chart Controls")
bar_metric = st.sidebar.selectbox("Bar metric (Top N)", options=metrics_all, index=metrics_all.index("HappinessScore") if "HappinessScore" in metrics_all else 0)
top_n = st.sidebar.slider("Top N", 5, 30, 10)
bar_color_seq = st.sidebar.selectbox("Bar color palette", options=["Burgundy","Blues","Greens","Viridis"], index=0)

hist_metric = st.sidebar.selectbox("Histogram metric", options=metrics_all, index=metrics_all.index("HappinessScore") if "HappinessScore" in metrics_all else 0)
hist_bins = st.sidebar.slider("Histogram bins", 8, 40, 15)
hist_color_seq = st.sidebar.selectbox("Histogram palette", options=["Burgundy","Blues","Greens","Viridis"], index=0)

scatter_x = st.sidebar.selectbox("Scatter X", options=metrics_all, index=metrics_all.index("GDPperCapita") if "GDPperCapita" in metrics_all else 0)
scatter_y = st.sidebar.selectbox("Scatter Y", options=metrics_all, index=metrics_all.index("HappinessScore") if "HappinessScore" in metrics_all else 0)
scatter_color = st.sidebar.selectbox("Color by", options=["Region","None"] + metrics_all, index=0)
scatter_size = st.sidebar.selectbox("Size by", options=["None"] + metrics_all, index=0)
scatter_palette = st.sidebar.selectbox("Scatter palette", options=["Burgundy","Blues","Greens","Viridis"], index=0)
show_fit = st.sidebar.checkbox("Show linear fit", value=True)

st.sidebar.markdown("---")
map_palette = st.sidebar.selectbox("Map palette", options=["Burgundy","Blues","Greens","Viridis"], index=0)

# ----------------- Apply filters -----------------
f = df.copy()
if years_all:
    f = f[f["Year"] == sel_year]
if sel_region != "(All)":
    f = f[f["Region"] == sel_region]

if f.empty:
    st.warning("لا توجد بيانات بعد تطبيق الفلاتر.")
    st.stop()

# ----------------- Header -----------------
st.title("Global Happiness Dashboard")
st.caption("لوحة تفاعلية: فلاتر سنة/منطقة + تشارتس تفاعلية + خريطة تحت الجدول.")

# ----------------- KPIs -----------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Countries", f["Country"].nunique())
with c2:
    st.metric(f"Average {primary_metric}", f"{f[primary_metric].mean():.2f}")
with c3:
    top_row = f.sort_values(primary_metric, ascending=False).head(1)
    st.metric("Top Country", top_row.iloc[0]["Country"], delta=f"{float(top_row.iloc[0][primary_metric]):.2f}")
with c4:
    reg_means = f.groupby("Region")[primary_metric].mean().sort_values(ascending=False)
    if not reg_means.empty:
        st.metric("Best Region (avg)", reg_means.index[0], delta=f"{float(reg_means.iloc[0]):.2f}")

st.divider()

# ----------------- Charts (interactive) -----------------
colA, colB = st.columns(2)

with colA:
    st.subheader("Top Countries (Bar)")
    top_df = f.sort_values(bar_metric, ascending=False).head(top_n)
    fig_bar = px.bar(
        top_df,
        x="Country",
        y=bar_metric,
        color="Country",
        color_discrete_sequence=get_colorscale(bar_color_seq),
        hover_data=["Region"] + [c for c in metrics_all if c != bar_metric],
    )
    fig_bar.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=400, xaxis_tickangle=-40, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with colB:
    st.subheader("Distribution (Histogram)")
    fig_hist = px.histogram(
        f.dropna(subset=[hist_metric]),
        x=hist_metric,
        nbins=hist_bins,
        color_discrete_sequence=get_colorscale(hist_color_seq),
    )
    fig_hist.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=400, yaxis_title="Count")
    st.plotly_chart(fig_hist, use_container_width=True)

st.subheader("Scatter (interactive)")
scatter_df = f.dropna(subset=[scatter_x, scatter_y]).copy()

# Base scatter
if scatter_color == "None":
    fig_sc = px.scatter(
        scatter_df,
        x=scatter_x, y=scatter_y,
        size=(None if scatter_size=="None" else scatter_size),
        hover_name="Country",
        color_discrete_sequence=get_colorscale(scatter_palette),
    )
else:
    fig_sc = px.scatter(
        scatter_df,
        x=scatter_x, y=scatter_y,
        color=scatter_color,
        size=(None if scatter_size=="None" else scatter_size),
        hover_name="Country",
        color_discrete_sequence=get_colorscale(scatter_palette),
    )

# Optional linear fit with numpy (no extra deps)
if show_fit:
    x = scatter_df[scatter_x].astype(float)
    y = scatter_df[scatter_y].astype(float)
    ok = ~(x.isna() | y.isna() | ~np.isfinite(x) | ~np.isfinite(y))
    x_ok, y_ok = x[ok], y[ok]
    if len(x_ok) > 2:
        m, b = np.polyfit(x_ok, y_ok, 1)
        xs = np.linspace(x_ok.min(), x_ok.max(), 200)
        fig_sc.add_trace(
            go.Scatter(x=xs, y=m*xs + b, mode="lines", name="Linear fit", line=dict(width=2))
        )

fig_sc.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=520, xaxis_title=scatter_x, yaxis_title=scatter_y)
st.plotly_chart(fig_sc, use_container_width=True)

st.divider()

# ----------------- Data Table -----------------
st.subheader("Data Table (filtered)")
table_cols = ["Country","Region","Year"] + metrics_all
st.dataframe(f[table_cols].sort_values(primary_metric, ascending=False), use_container_width=True)

# ----------------- Map UNDER the table -----------------
st.subheader("Choropleth Map")
map_df = f.dropna(subset=["Country", primary_metric]).copy()
if map_df.empty:
    st.info("لا توجد بيانات صالحة للخريطة بعد التصفية.")
else:
    # تدرّج برغندي افتراضي مع إمكانية تغييره
    cs = get_colorscale(map_palette)
    fig_map = px.choropleth(
        map_df,
        locations="Country",
        locationmode="country names",
        color=primary_metric,
        hover_name="Country",
        color_continuous_scale=cs,
    )
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=520,
        coloraxis_colorbar=dict(title=primary_metric),
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ----------------- Footer -----------------
st.caption("Built with Streamlit + Plotly. Colorscale defaults to Burgundy; يمكنك تغييره من الشريط الجانبي.")
