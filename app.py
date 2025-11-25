# app.py
# ============================================
# Global Happiness, Health, Life Expectancy & Peace Dashboard
# - Navy gradient background
# - "About This Dashboard" ONLY inside Overview tab
# - New Data Tables tab
# - No other sections changed
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

# Navy blue gradient background
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom, #0A1A2F, #123155, #1C4A80);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        color: white !important;
        font-size: 0.95rem;
        font-weight: 600;
    }
    h1, h2, h3, h4, h5, h6, p, .metric {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

PRIMARY_COLOR = "#4FC3F7"


# ------------------ Data Load Helpers ------------------
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
    df = pd.read_csv(path, sep=";", engine="python")
    df = df.rename(columns={df.columns[0]: "Country"})

    candidates = df.columns[1:]
    best_col = None
    best_non_null = -1

    for c in candidates:
        s = pd.to_numeric(df[c].astype(str).replace(",", ".", regex=False), errors="coerce")
        non_null = s.notna().sum()
        if non_null > best_non_null:
            best_non_null = non_null
            best_col = c

    if best_col:
        df["Peace_Score"] = pd.to_numeric(df[best_col].astype(str).str.replace(",", "."), errors="coerce")
    else:
        df["Peace_Score"] = pd.to_numeric(df.iloc[:, -1].astype(str).str.replace(",", "."), errors="coerce")

    return df[["Country", "Peace_Score"]]


@st.cache_data
def build_merged(happy_path: str, life_path: str, peace_path: str):
    h = load_happiness(happy_path)
    l = load_life(life_path)
    p = load_peace(peace_path)

    merged = h.merge(l, on="Country", how="left").merge(p, on="Country", how="left")

    numeric_cols = [
        "Happiness_Score",
        "Log_GDP_per_capita",
        "Social_support",
        "Healthy_life_expectancy",
        "Freedom",
        "Generosity",
        "Corruption",
        "Dystopia_residual",
        "Life_Expectancy",
        "Health_Expenditure_pct",
        "Education_Expenditure_pct",
        "Undernourishment_pct",
        "CO2_emissions",
        "Unemployment_pct",
        "Peace_Score",
    ]

    numeric_cols = [c for c in numeric_cols if c in merged.columns]
    return merged, numeric_cols


# ------------------ Load Data ------------------
HAPPINESS_PATH = "World-happiness-report-2024.csv"
LIFE_PATH = "life expectancy.csv"
PEACE_PATH = "peace_index.csv"

merged_df, numeric_cols = build_merged(HAPPINESS_PATH, LIFE_PATH, PEACE_PATH)


# ------------------ Sidebar Filters ------------------
st.sidebar.title("Filters")

all_regions = sorted(merged_df["H_Region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Select region(s)", all_regions, default=all_regions)

income_options = merged_df["Income_Group"].dropna().unique().tolist() if "Income_Group" in merged_df else []
selected_income = []
if income_options:
    selected_income = st.sidebar.multiselect("Select income group(s)", sorted(income_options), default=income_options)

filtered_df = merged_df.copy()
if selected_regions:
    filtered_df = filtered_df[filtered_df["H_Region"].isin(selected_regions)]
if selected_income and "Income_Group" in filtered_df:
    filtered_df = filtered_df[filtered_df["Income_Group"].isin(selected_income)]

st.sidebar.markdown("---")
st.sidebar.caption("All charts use one accent color and remain fully interactive.")


# ------------------ Plot Helpers ------------------
def single_color_scatter(df, x, y, hover=None, title=""):
    fig = px.scatter(df, x=x, y=y, hover_data=hover)
    fig.update_traces(marker=dict(color=PRIMARY_COLOR, size=9))
    fig.update_layout(template="plotly_white", height=430, margin=dict(l=10, r=10, t=40, b=10), title=title)
    return fig


def single_color_bar(df, x, y, orientation="v", title=""):
    fig = px.bar(df, x=x if orientation == "v" else None, y=y if orientation == "v" else None,
                 orientation=orientation)
    fig.update_traces(marker_color=PRIMARY_COLOR)
    fig.update_layout(template="plotly_white", height=430, margin=dict(l=10, r=10, t=40, b=10), title=title)
    return fig


# ------------------ Tabs ------------------
tab_overview, tab_happy, tab_health, tab_econ, tab_peace, tab_tables, tab_insights = st.tabs(
    [
        "Overview",
        "Happiness",
        "Health & Life Expectancy",
        "Economic Factors",
        "Peace & Stability",
        "Data Tables",
        "Insights & Conclusion",
    ]
)

# ========== TAB 1: OVERVIEW ==========
with tab_overview:
    st.subheader("About This Dashboard")

    st.markdown(
        """
        This dashboard provides a combined view of:
        - Global **happiness levels**
        - **Life expectancy** and key health indicators  
        - **Economic factors** such as GDP and unemployment  
        - **Peace and stability** using global peace index data  

        It helps users explore relationships between well-being, health, economy, and security.
        """
    )

    st.markdown("---")
    st.subheader("Global Overview Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Average Happiness Score", f"{filtered_df['Happiness_Score'].mean():.2f}")
    col2.metric("Average Life Expectancy", f"{filtered_df['Life_Expectancy'].mean():.1f} years" if "Life_Expectancy" in filtered_df else "N/A")
    col3.metric("Countries in Selection", filtered_df["Country"].nunique())

    st.markdown("### World Happiness Map")

    map_df = filtered_df.copy()
    fig_map = px.choropleth(
        map_df,
        locations="Country",
        locationmode="country names",
        color="Happiness_Score",
        color_continuous_scale="Blues",
        title="Happiness Score by Country (2024)",
    )
    fig_map.update_layout(template="plotly_white", height=520, margin=dict(l=0, r=0, t=40, b=0), uirevision="map")
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown(
        """
        **Insight:**  
        Darker regions represent higher happiness scores.  
        Use the sidebar filters to explore patterns by region or income group.
        """
    )


# ========== TAB 2: HAPPINESS ==========
with tab_happy:
    st.subheader("Happiness Analysis")

    col1, col2 = st.columns(2)

    with col1:
        top10 = filtered_df.sort_values("Happiness_Score", ascending=False).head(10)
        st.plotly_chart(single_color_bar(top10, "Country", "Happiness_Score", title="Top 10 Happiest Countries"), use_container_width=True)

    with col2:
        bottom10 = filtered_df.sort_values("Happiness_Score", ascending=True).head(10)
        st.plotly_chart(single_color_bar(bottom10, "Country", "Happiness_Score", title="Bottom 10 Countries"), use_container_width=True)

    st.markdown("---")
    st.subheader("Key Happiness Drivers")

    col3, col4 = st.columns(2)

    if "Social_support" in filtered_df:
        df_soc = filtered_df.dropna(subset=["Social_support", "Happiness_Score"])
        col3.plotly_chart(single_color_scatter(df_soc, "Social_support", "Happiness_Score", hover=["Country"],
                                               title="Happiness vs Social Support"), use_container_width=True)

    if "Freedom" in filtered_df:
        df_free = filtered_df.dropna(subset=["Freedom", "Happiness_Score"])
        col4.plotly_chart(single_color_scatter(df_free, "Freedom", "Happiness_Score", hover=["Country"],
                                               title="Happiness vs Freedom"), use_container_width=True)


# ========== TAB 3: HEALTH ==========
with tab_health:
    st.subheader("Health & Life Expectancy")

    if "Life_Expectancy" not in filtered_df.columns:
        st.warning("Life expectancy data not available.")
    else:
        col1, col2 = st.columns(2)

        df_life = filtered_df.dropna(subset=["Life_Expectancy", "Happiness_Score"])
        col1.plotly_chart(
            single_color_scatter(df_life, "Life_Expectancy", "Happiness_Score", hover=["Country"],
                                 title="Happiness vs Life Expectancy"),
            use_container_width=True
        )

        if "Health_Expenditure_pct" in filtered_df:
            df_hexp = filtered_df.dropna(subset=["Health_Expenditure_pct", "Happiness_Score"])
            col2.plotly_chart(
                single_color_scatter(df_hexp, "Health_Expenditure_pct", "Happiness_Score", hover=["Country"],
                                     title="Happiness vs Health Expenditure"),
                use_container_width=True
            )

        st.markdown("---")
        col3, col4 = st.columns(2)

        if "CO2_emissions" in filtered_df:
            df_co2 = filtered_df.dropna(subset=["CO2_emissions", "Happiness_Score"])
            col3.plotly_chart(single_color_scatter(df_co2, "CO2_emissions", "Happiness_Score", hover=["Country"],
                                                   title="Happiness vs CO₂ Emissions"), use_container_width=True)

        if "Undernourishment_pct" in filtered_df:
            df_und = filtered_df.dropna(subset=["Undernourishment_pct", "Happiness_Score"])
            col4.plotly_chart(single_color_scatter(df_und, "Undernourishment_pct", "Happiness_Score", hover=["Country"],
                                                   title="Happiness vs Undernourishment"), use_container_width=True)


# ========== TAB 4: ECONOMY ==========
with tab_econ:
    st.subheader("Economic Factors")

    col1, col2 = st.columns(2)

    if "Log_GDP_per_capita" in filtered_df:
        df_gdp = filtered_df.dropna(subset=["Log_GDP_per_capita", "Happiness_Score"])
        col1.plotly_chart(
            single_color_scatter(df_gdp, "Log_GDP_per_capita", "Happiness_Score", hover=["Country"],
                                 title="Happiness vs Log GDP per Capita"),
            use_container_width=True
        )

    if "Unemployment_pct" in filtered_df:
        df_unemp = filtered_df.dropna(subset=["Unemployment_pct", "Happiness_Score"])
        col2.plotly_chart(
            single_color_scatter(df_unemp, "Unemployment_pct", "Happiness_Score", hover=["Country"],
                                 title="Happiness vs Unemployment Rate"),
            use_container_width=True
        )

    st.markdown("---")

    if "Income_Group" in filtered_df:
        df_box = filtered_df.dropna(subset=["Income_Group", "Happiness_Score"])
        fig_box = px.box(df_box, x="Income_Group", y="Happiness_Score", template="plotly_white")
        fig_box.update_traces(marker_color=PRIMARY_COLOR)
        st.plotly_chart(fig_box, use_container_width=True)


# ========== TAB 5: PEACE ==========
with tab_peace:
    st.subheader("Peace & Stability")

    if "Peace_Score" not in filtered_df:
        st.warning("Peace data unavailable.")
    else:
        col1, col2 = st.columns(2)

        df_peace = filtered_df.dropna(subset=["Peace_Score", "Happiness_Score"])
        col1.plotly_chart(single_color_scatter(df_peace, "Peace_Score", "Happiness_Score", hover=["Country"],
                                               title="Happiness vs Peace Index"), use_container_width=True)

        most_peaceful = df_peace.sort_values("Peace_Score", ascending=True).head(10)
        col2.plotly_chart(single_color_bar(most_peaceful, "Country", "Peace_Score",
                                           title="Top 10 Most Peaceful Countries"), use_container_width=True)

        if "H_Region" in filtered_df:
            df_reg = filtered_df.dropna(subset=["H_Region", "Peace_Score"])
            fig_reg = px.box(df_reg, x="H_Region", y="Peace_Score", template="plotly_white")
            fig_reg.update_traces(marker_color=PRIMARY_COLOR)
            st.plotly_chart(fig_reg, use_container_width=True)


# ========== TAB 6: DATA TABLES ==========
with tab_tables:
    st.subheader("Data Tables")

    st.markdown("### Happiness Dataset")
    st.dataframe(load_happiness(HAPPINESS_PATH))

    st.markdown("### Life Expectancy Dataset")
    st.dataframe(load_life(LIFE_PATH))

    st.markdown("### Peace Index Dataset")
    st.dataframe(load_peace(PEACE_PATH))

    st.markdown("### Merged Final Dataset")
    st.dataframe(merged_df)


# ========== TAB 7: INSIGHTS ==========
with tab_insights:
    st.subheader("Insights & Conclusion")
    st.markdown(
        """
        - Happiness increases with social support, life expectancy, and freedom.
        - Health investments reduce undernourishment and increase well-being.
        - Economic strength matters, but unemployment reduces happiness significantly.
        - Peaceful countries (lower index scores) report higher well-being.
        """
    )
