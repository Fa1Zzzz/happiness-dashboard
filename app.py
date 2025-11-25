
# app.py — Final Version with Navy Blue Gradient + Overview Tab Only + Data Tables
# ------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------ Page Setup ------------------
st.set_page_config(
    page_title="Global Happiness, Health, Life Expectancy & Peace Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom, #0A1A2F, #123155, #1C4A80);
        color: white !important;
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
""", unsafe_allow_html=True)

PRIMARY_COLOR = "#4FC3F7"


# ------------------ Load Data ------------------
@st.cache_data
def load_happiness(path):
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Country name": "Country",
        "Regional indicator": "H_Region",
        "Ladder score": "Happiness_Score",
        "Log GDP per capita": "Log_GDP_per_capita",
        "Social support": "Social_support",
        "Healthy life expectancy": "Healthy_life_expectancy",
        "Freedom to make life choices": "Freedom",
        "Generosity": "Generosity",
        "Perceptions of corruption": "Corruption",
        "Dystopia + residual": "Dystopia_residual"
    })
    df["Happiness_Rank"] = df["Happiness_Score"].rank(ascending=False, method="min").astype(int)
    return df


@st.cache_data
def load_life(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"Country Name": "Country"})
    df = df.sort_values(["Country", "Year"])
    latest = df.groupby("Country").tail(1).reset_index(drop=True)
    latest = latest.rename(columns={
        "Region": "WB_Region",
        "IncomeGroup": "Income_Group",
        "Life Expectancy World Bank": "Life_Expectancy",
        "Health Expenditure %": "Health_Expenditure_pct",
        "Education Expenditure %": "Education_Expenditure_pct",
        "Prevelance of Undernourishment": "Undernourishment_pct",
        "CO2": "CO2_emissions",
        "Unemployment": "Unemployment_pct"
    })
    return latest


@st.cache_data
def load_peace(path):
    df = pd.read_csv(path, sep=";", engine="python")
    df = df.rename(columns={df.columns[0]: "Country"})
    if "2023" in df.columns:
        df["Peace_Score"] = pd.to_numeric(df["2023"].astype(str).str.replace(",", "."), errors="coerce")
    else:
        df["Peace_Score"] = pd.to_numeric(df.iloc[:, -1].astype(str).str.replace(",", "."), errors="coerce")
    return df[["Country", "Peace_Score"]]


@st.cache_data
def merge_all(hp, lf, pc):
    df = hp.merge(lf, on="Country", how="left").merge(pc, on="Country", how="left")
    return df


hp = load_happiness("World-happiness-report-2024.csv")
lf = load_life("life expectancy.csv")
pc = load_peace("peace_index.csv")
merged_df = merge_all(hp, lf, pc)


# ------------------ Sidebar Filters ------------------
st.sidebar.title("Filters")

regions = sorted(hp["H_Region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Select Regions", options=regions, default=regions)

income_groups = merged_df["Income_Group"].dropna().unique().tolist()
selected_income = st.sidebar.multiselect("Select Income Groups", options=income_groups, default=income_groups)

filtered_df = merged_df.copy()
if selected_regions:
    filtered_df = filtered_df[filtered_df["H_Region"].isin(selected_regions)]
if selected_income:
    filtered_df = filtered_df[filtered_df["Income_Group"].isin(selected_income)]

st.sidebar.caption("Charts update automatically based on selection.")


# ------------------ Tabs ------------------
tab_overview, tab_happy, tab_health, tab_econ, tab_peace, tab_tables, tab_insights = st.tabs(
    [
        "Overview",
        "Happiness",
        "Health & Life Expectancy",
        "Economic Factors",
        "Peace & Stability",
        "Data Tables",
        "Insights & Conclusion"
    ]
)


# ------------------ Overview Tab ------------------
with tab_overview:
    st.header("About This Dashboard")
    st.markdown(
        """
        This dashboard explores how **happiness**, **health**, 
        **life expectancy**, **economic factors**, and **peace levels** interact globally.  
        You can filter regions and income groups from the sidebar.  
        Each chart includes insights to help interpret patterns and relationships.
        """
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Happiness", f"{filtered_df['Happiness_Score'].mean():.2f}")
    col2.metric("Avg Life Expectancy", f"{filtered_df['Life_Expectancy'].mean():.1f}")
    col3.metric("Countries Count", filtered_df['Country'].nunique())

    st.subheader("World Happiness Map")
    fig_map = px.choropleth(
        filtered_df,
        locations="Country",
        locationmode="country names",
        color="Happiness_Score",
        title="Happiness Score by Country (2024)",
        color_continuous_scale="Blues"
    )
    fig_map.update_layout(uirevision="static", height=500, template="plotly_white")
    st.plotly_chart(fig_map, use_container_width=True)


# ------------------ Happiness Tab ------------------
with tab_happy:
    st.header("Happiness Analysis")

    col1, col2 = st.columns(2)

    top10 = filtered_df.sort_values("Happiness_Score", ascending=False).head(10)
    fig_top10 = px.bar(top10, x="Country", y="Happiness_Score", title="Top 10 Happiest Countries")
    fig_top10.update_traces(marker_color=PRIMARY_COLOR)
    col1.plotly_chart(fig_top10, use_container_width=True)

    bottom10 = filtered_df.sort_values("Happiness_Score").head(10)
    fig_bottom10 = px.bar(bottom10, x="Country", y="Happiness_Score", title="Bottom 10 Happiest Countries")
    fig_bottom10.update_traces(marker_color=PRIMARY_COLOR)
    col2.plotly_chart(fig_bottom10, use_container_width=True)


# ------------------ Health & Life Expectancy Tab ------------------
with tab_health:
    st.header("Health & Life Expectancy")

    col1, col2 = st.columns(2)

    fig_life = px.scatter(filtered_df, x="Life_Expectancy", y="Happiness_Score",
                          hover_data=["Country"], title="Happiness vs Life Expectancy")
    fig_life.update_traces(marker_color=PRIMARY_COLOR)
    col1.plotly_chart(fig_life, use_container_width=True)

    fig_hexp = px.scatter(filtered_df, x="Health_Expenditure_pct", y="Happiness_Score",
                          hover_data=["Country"], title="Happiness vs Health Expenditure (%)")
    fig_hexp.update_traces(marker_color=PRIMARY_COLOR)
    col2.plotly_chart(fig_hexp, use_container_width=True)


# ------------------ Economic Factors Tab ------------------
with tab_econ:
    st.header("Economic Factors")

    col1, col2 = st.columns(2)

    fig_gdp = px.scatter(filtered_df, x="Log_GDP_per_capita", y="Happiness_Score",
                         hover_data=["Country"], title="Happiness vs GDP per Capita")
    fig_gdp.update_traces(marker_color=PRIMARY_COLOR)
    col1.plotly_chart(fig_gdp, use_container_width=True)

    fig_unemp = px.scatter(filtered_df, x="Unemployment_pct", y="Happiness_Score",
                           hover_data=["Country"], title="Happiness vs Unemployment Rate")
    fig_unemp.update_traces(marker_color=PRIMARY_COLOR)
    col2.plotly_chart(fig_unemp, use_container_width=True)


# ------------------ Peace & Stability Tab ------------------
with tab_peace:
    st.header("Peace & Stability")

    fig_peace = px.scatter(filtered_df, x="Peace_Score", y="Happiness_Score",
                           hover_data=["Country"], title="Happiness vs Peace Index (2023)")
    fig_peace.update_traces(marker_color=PRIMARY_COLOR)
    st.plotly_chart(fig_peace, use_container_width=True)


# ------------------ Data Tables Tab ------------------
with tab_tables:
    st.header("Data Tables")

    st.subheader("World Happiness 2024")
    st.dataframe(hp)

    st.subheader("Life Expectancy Dataset")
    st.dataframe(lf)

    st.subheader("Peace Index (2023)")
    st.dataframe(pc)

    st.subheader("Merged Dataset")
    st.dataframe(merged_df)


# ------------------ Insights & Conclusion Tab ------------------
with tab_insights:
    st.header("Insights & Conclusion")
    st.markdown(
        """
        - Happiness increases with social support, freedom, and life expectancy.  
        - Unemployment, poor nutrition, and conflict reduce happiness.  
        - High-income countries generally score better, but peace and governance also matter.
        """
    )
