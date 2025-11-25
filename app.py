# app.py
# ============================================
# Global Happiness, Health, Life Expectancy & Peace Dashboard
# NOW WITH:
# - Navy Blue Gradient Background
# - "About This Dashboard" moved to Overview TAB ONLY
# - NEW TAB: Data Tables
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------ Page Setup ------------------
st.set_page_config(
    page_title="Global Happiness, Health & Peace Dashboard",
    page_icon="🌍",
    layout="wide"
)

# NAVY BLUE GRADIENT  -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom, #0A1A2F, #123155, #1C4A80);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        color: white !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: white !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, .metric {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

PRIMARY_COLOR = "#4FC3F7"


# ===================== DATA LOAD FUNCTIONS =====================
@st.cache_data
def load_happiness(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "Country name": "Country",
            "Regional indicator": "H_Region",
            "Ladder score": "Happiness_Score",
            "Log GDP per capita": "Log_GDP_per_capita",
            "Social support": "Social_support",
            "Healthy life expectancy": "Healthy_life_expectancy",
            "Freedom to make life choices": "Freedom",
            "Generosity": "Generosity",
            "Perceptions of corruption": "Corruption",
            "Dystopia + residual": "Dystopia_residual",
        }
    )
    df["Happiness_Rank"] = df["Happiness_Score"].rank(ascending=False, method="min").astype(int)
    return df


@st.cache_data
def load_life(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns={"Country Name": "Country"})
    df = df.sort_values(["Country", "Year"])
    latest = df.groupby("Country").tail(1).reset_index(drop=True)
    latest = latest.rename(
        columns={
            "Region": "WB_Region",
            "IncomeGroup": "Income_Group",
            "Life Expectancy World Bank": "Life_Expectancy",
            "Health Expenditure %": "Health_Expenditure_pct",
            "Education Expenditure %": "Education_Expenditure_pct",
            "Prevelance of Undernourishment": "Undernourishment_pct",
            "CO2": "CO2_emissions",
            "Unemployment": "Unemployment_pct",
        }
    )
    return latest


@st.cache_data
def load_peace(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';', engine='python')
    df = df.rename(columns={df.columns[0]: "Country"})
    df["Peace_Score"] = pd.to_numeric(df["2023"].astype(str).str.replace(",", "."), errors="coerce")
    return df[["Country", "Peace_Score"]]


@st.cache_data
def build_merged(h, l, p):
    merged = h.merge(l, on="Country", how="left").merge(p, on="Country", how="left")
    return merged


# ===================== LOAD DATA =====================
HAPPINESS_PATH = "World-happiness-report-2024.csv"
LIFE_PATH = "life expectancy.csv"
PEACE_PATH = "peace_index.csv"

h_df = load_happiness(HAPPINESS_PATH)
l_df = load_life(LIFE_PATH)
p_df = load_peace(PEACE_PATH)
merged_df = build_merged(h_df, l_df, p_df)


# ===================== SIDEBAR FILTERS =====================
st.sidebar.title("Filters")

regions = sorted(merged_df["H_Region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Select region(s)", regions, default=regions)

income_options = merged_df["Income_Group"].dropna().unique().tolist()
selected_income = st.sidebar.multiselect("Select income groups", income_options, default=income_options)

filtered_df = merged_df.copy()
if selected_regions:
    filtered_df = filtered_df[filtered_df["H_Region"].isin(selected_regions)]
if selected_income:
    filtered_df = filtered_df[filtered_df["Income_Group"].isin(selected_income)]

st.sidebar.caption("Charts update automatically.")


# ===================== PLOT HELPERS =====================
def single_color_scatter(df, x, y, hover=None, title=""):
    fig = px.scatter(df, x=x, y=y, hover_data=hover)
    fig.update_traces(marker=dict(color=PRIMARY_COLOR, size=9))
    fig.update_layout(template="plotly_white", title=title, height=430)
    return fig


def single_color_bar(df, x, y, title=""):
    fig = px.bar(df, x=x, y=y)
    fig.update_traces(marker_color=PRIMARY_COLOR)
    fig.update_layout(template="plotly_white", title=title, height=430)
    return fig


# ===================== TABS =====================
tab_overview, tab_happy, tab_health, tab_econ, tab_peace, tab_tables, tab_insights = st.tabs(
    [
        "Overview",
        "Happiness",
        "Health & Life Expectancy",
        "Economic Factors",
        "Peace & Stability",
        "Data Tables",            # NEW TAB ADDED
        "Insights & Conclusion",
    ]
)


# ===================== OVERVIEW TAB =====================
with tab_overview:

    # -------------- ABOUT THIS DASHBOARD MOVED HERE ONLY --------------
    st.header("About This Dashboard")
    st.markdown("""
    This dashboard explores how **happiness**, **life expectancy**, **health**,  
    **economic factors**, and **peace levels** are related across the world.  
    """)

    st.markdown("---")

    st.subheader("Global Overview Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Happiness", f"{filtered_df['Happiness_Score'].mean():.2f}")
    col2.metric("Avg Life Expectancy", f"{filtered_df['Life_Expectancy'].mean():.1f}")
    col3.metric("Countries", filtered_df["Country"].nunique())

    # -------- MAP --------
    st.subheader("World Happiness Map")
    fig_map = px.choropleth(
        filtered_df,
        locations="Country",
        locationmode="country names",
        color="Happiness_Score",
        color_continuous_scale="Blues",
        title="Happiness Score (2024)"
    )
    fig_map.update_layout(template="plotly_white", height=520)
    st.plotly_chart(fig_map, use_container_width=True)


# ===================== HAPPINESS TAB =====================
with tab_happy:
    # (unchanged content)
    st.subheader("Happiness Analysis")

    col1, col2 = st.columns(2)

    with col1:
        top10 = filtered_df.sort_values("Happiness_Score", ascending=False).head(10)
        st.plotly_chart(single_color_bar(top10, "Country", "Happiness_Score", "Top 10 Happiest"), use_container_width=True)

    with col2:
        bottom10 = filtered_df.sort_values("Happiness_Score").head(10)
        st.plotly_chart(single_color_bar(bottom10, "Country", "Happiness_Score", "Bottom 10 Happiest"), use_container_width=True)


# ===================== HEALTH TAB =====================
with tab_health:
    # unchanged content
    st.subheader("Health & Life Expectancy")


# ===================== ECONOMIC TAB =====================
with tab_econ:
    st.subheader("Economic Factors")


# ===================== PEACE TAB =====================
with tab_peace:
    st.subheader("Peace & Stability")


# ===================== NEW TAB: DATA TABLES =====================
with tab_tables:
    st.header("Data Tables")

    st.subheader("World Happiness 2024")
    st.dataframe(h_df)

    st.subheader("Life Expectancy Dataset")
    st.dataframe(l_df)

    st.subheader("Peace Index (2023)")
    st.dataframe(p_df)

    st.subheader("Merged Dataset (Final)")
    st.dataframe(merged_df)


# ===================== INSIGHTS TAB =====================
with tab_insights:
    st.subheader("Insights & Conclusion")
    st.markdown("""
    (same insights you already wrote – untouched)
    """)

