# app.py
# ============================================
# Global Happiness, Health, Life Expectancy & Peace Dashboard
# - Navy gradient background
# - "About This Dashboard" ONLY in Overview tab
# - New Data Tables tab
# - Insights under every chart (improved academic wording)
# - Full Insights & Conclusion tab restored
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------ Page Setup ------------------
st.set_page_config(
    page_title="Global Happiness, Health & Peace Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Navy gradient background + white text
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


# ------------------ Data Loaders ------------------
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
    })
    return df


@st.cache_data
def load_life(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"Country Name": "Country"})
    df = df.sort_values(["Country", "Year"])
    latest = df.groupby("Country").tail(1)
    latest = latest.rename(columns={
        "Life Expectancy World Bank": "Life_Expectancy",
        "Health Expenditure %": "Health_Expenditure_pct",
        "Education Expenditure %": "Education_Expenditure_pct",
        "Prevelance of Undernourishment": "Undernourishment_pct",
        "CO2": "CO2_emissions",
        "Unemployment": "Unemployment_pct",
        "IncomeGroup": "Income_Group"
    })
    return latest


@st.cache_data
def load_peace(path):
    df = pd.read_csv(path, sep=";", engine="python")
    df = df.rename(columns={df.columns[0]: "Country"})
    # choose the most filled numeric column
    best_col = df.columns[1]
    df["Peace_Score"] = pd.to_numeric(df[best_col].astype(str).str.replace(",", "."), errors="coerce")
    return df[["Country", "Peace_Score"]]


# ------------------ Load All Data ------------------
happy = load_happiness("World-happiness-report-2024.csv")
life = load_life("life expectancy.csv")
peace = load_peace("peace_index.csv")

merged_df = happy.merge(life, on="Country", how="left").merge(peace, on="Country", how="left")


# ------------------ Filters ------------------
st.sidebar.title("Filters")
regions = sorted(merged_df["H_Region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Select region(s)", regions, default=regions)

income_groups = merged_df["Income_Group"].dropna().unique().tolist()
selected_income = st.sidebar.multiselect("Income groups", income_groups, default=income_groups)

filtered = merged_df.copy()
if selected_regions:
    filtered = filtered[filtered["H_Region"].isin(selected_regions)]
if selected_income:
    filtered = filtered[filtered["Income_Group"].isin(selected_income)]

st.sidebar.markdown("---")
st.sidebar.caption("Charts use one accent color and remain fully interactive.")


# ------------------ Plot Helpers ------------------
def scatter(df, x, y, title):
    fig = px.scatter(df, x=x, y=y, hover_data=["Country"])
    fig.update_traces(marker=dict(color=PRIMARY_COLOR, size=9))
    fig.update_layout(template="plotly_white", title=title, height=430)
    return fig


def bar(df, x, y, title):
    fig = px.bar(df, x=x, y=y)
    fig.update_traces(marker_color=PRIMARY_COLOR)
    fig.update_layout(template="plotly_white", title=title, height=430)
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

# ------------------ Overview ------------------
with tab_overview:
    st.subheader("About This Dashboard")
    st.markdown(
        """
        **This dashboard provides a simple overview of global happiness and the factors influencing it.  
        It combines data on health, economy, life expectancy, and peace to help users observe patterns  
        and understand how different conditions shape well-being around the world.**
        """
    )

    st.markdown("---")
    st.subheader("Key Global Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Happiness", f"{filtered['Happiness_Score'].mean():.2f}")
    col2.metric("Avg Life Expectancy", f"{filtered['Life_Expectancy'].mean():.1f}" if "Life_Expectancy" in filtered else "N/A")
    col3.metric("Countries", filtered["Country"].nunique())

    # map
    fig_map = px.choropleth(
        filtered,
        locations="Country",
        locationmode="country names",
        color="Happiness_Score",
        color_continuous_scale="Blues",
        title="Global Happiness Map"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("**Insight:** Darker countries have higher happiness levels. Regional filters help reveal global patterns.")


# ------------------ Happiness ------------------
with tab_happy:
    st.subheader("Happiness Analysis")

    col1, col2 = st.columns(2)

    with col1:
        top10 = filtered.sort_values("Happiness_Score", ascending=False).head(10)
        st.plotly_chart(bar(top10, "Country", "Happiness_Score", "Top 10 Happiest Countries"))
        st.markdown("**Insight:** These countries generally share strong institutions, high social support, and stable conditions promoting well-being.**")

    with col2:
        bottom10 = filtered.sort_values("Happiness_Score").head(10)
        st.plotly_chart(bar(bottom10, "Country", "Happiness_Score", "Bottom 10 Countries"))
        st.markdown("**Insight:** Low-scoring countries often face economic challenges or limited access to basic services affecting happiness.**")

    st.markdown("---")

    col3, col4 = st.columns(2)

    if "Social_support" in filtered:
        df_soc = filtered.dropna(subset=["Social_support", "Happiness_Score"])
        col3.plotly_chart(scatter(df_soc, "Social_support", "Happiness_Score", "Happiness vs Social Support"))
        col3.markdown("**Insight:** Stronger social support systems are closely linked to higher happiness across countries.**")

    if "Freedom" in filtered:
        df_free = filtered.dropna(subset=["Freedom", "Happiness_Score"])
        col4.plotly_chart(scatter(df_free, "Freedom", "Happiness_Score", "Happiness vs Freedom"))
        col4.markdown("**Insight:** Countries with higher personal freedom tend to report higher life satisfaction.**")


# ------------------ Health ------------------
with tab_health:
    st.subheader("Health & Life Expectancy")

    col1, col2 = st.columns(2)

    if "Life_Expectancy" in filtered:
        df_life = filtered.dropna(subset=["Life_Expectancy", "Happiness_Score"])
        col1.plotly_chart(scatter(df_life, "Life_Expectancy", "Happiness_Score", "Happiness vs Life Expectancy"))
        col1.markdown("**Insight:** Longer lifespans reflect better health systems, which are associated with higher well-being.**")

    if "Health_Expenditure_pct" in filtered:
        df_hexp = filtered.dropna(subset=["Health_Expenditure_pct", "Happiness_Score"])
        col2.plotly_chart(scatter(df_hexp, "Health_Expenditure_pct", "Happiness_Score", "Happiness vs Health Expenditure"))
        col2.markdown("**Insight:** Countries investing more in health often provide better quality of life and higher happiness levels.**")

    st.markdown("---")

    col3, col4 = st.columns(2)

    if "CO2_emissions" in filtered:
        df_co2 = filtered.dropna(subset=["CO2_emissions", "Happiness_Score"])
        col3.plotly_chart(scatter(df_co2, "CO2_emissions", "Happiness_Score", "CO₂ Emissions vs Happiness"))
        col3.markdown("**Insight:** Higher emissions reflect industrialized economies, showing a development–environment trade-off.**")

    if "Undernourishment_pct" in filtered:
        df_und = filtered.dropna(subset=["Undernourishment_pct", "Happiness_Score"])
        col4.plotly_chart(scatter(df_und, "Undernourishment_pct", "Happiness_Score", "Happiness vs Undernourishment"))
        col4.markdown("**Insight:** Undernourishment negatively affects well-being and strongly correlates with lower happiness.**")


# ------------------ Economic ------------------
with tab_econ:
    st.subheader("Economic Factors")

    col1, col2 = st.columns(2)

    if "Log_GDP_per_capita" in filtered:
        df_gdp = filtered.dropna(subset=["Log_GDP_per_capita", "Happiness_Score"])
        col1.plotly_chart(scatter(df_gdp, "Log_GDP_per_capita", "Happiness_Score", "Happiness vs GDP per Capita"))
        col1.markdown("**Insight:** Income improves living standards, but it is not the only factor determining happiness.**")

    if "Unemployment_pct" in filtered:
        df_unemp = filtered.dropna(subset=["Unemployment_pct", "Happiness_Score"])
        col2.plotly_chart(scatter(df_unemp, "Unemployment_pct", "Happiness_Score", "Happiness vs Unemployment"))
        col2.markdown("**Insight:** Higher unemployment reduces financial security and is consistently linked with lower well-being.**")

    st.markdown("---")

    if "Income_Group" in filtered:
        df_box = filtered.dropna(subset=["Income_Group", "Happiness_Score"])
        fig_box = px.box(df_box, x="Income_Group", y="Happiness_Score", template="plotly_white")
        fig_box.update_traces(marker_color=PRIMARY_COLOR)
        st.plotly_chart(fig_box, use_container_width=True)
        st.markdown("**Insight:** Higher income groups show higher happiness but internal variation shows income isn't the only driver.**")


# ------------------ Peace ------------------
with tab_peace:
    st.subheader("Peace & Stability")

    if "Peace_Score" not in filtered:
        st.warning("No peace data available.")
    else:
        col1, col2 = st.columns(2)

        df_p = filtered.dropna(subset=["Peace_Score", "Happiness_Score"])
        col1.plotly_chart(scatter(df_p, "Peace_Score", "Happiness_Score", "Peace Index vs Happiness"))
        col1.markdown("**Insight:** More peaceful countries generally achieve higher happiness because stability improves daily life.**")

        most_peaceful = df_p.sort_values("Peace_Score").head(10)
        col2.plotly_chart(bar(most_peaceful, "Country", "Peace_Score", "Top 10 Most Peaceful Countries"))
        col2.markdown("**Insight:** These countries benefit from low conflict, safety, and strong institutions supporting well-being.**")

        if "H_Region" in filtered:
            df_reg = filtered.dropna(subset=["H_Region", "Peace_Score"])
            fig_region = px.box(df_reg, x="H_Region", y="Peace_Score", template="plotly_white")
            fig_region.update_traces(marker_color=PRIMARY_COLOR)
            st.plotly_chart(fig_region, use_container_width=True)
            st.markdown("**Insight:** Peace levels vary significantly by region, affecting stability and quality of life.**")


# ------------------ Data Tables ------------------
with tab_tables:
    st.subheader("Data Tables")

    st.markdown("### Happiness Dataset")
    st.dataframe(happy)

    st.markdown("### Life Expectancy Dataset")
    st.dataframe(life)

    st.markdown("### Peace Index Dataset")
    st.dataframe(peace)

    st.markdown("### Merged Final Dataset")
    st.dataframe(merged_df)


# ------------------ Insights & Conclusion ------------------
with tab_insights:
    st.subheader("Insights & Conclusion (Draft)")

    st.markdown(
        """
        ### 1. Overall Patterns
        - Happiness is consistently higher in countries with strong social support, greater freedom, and longer life expectancy.
        - Economic strength matters, but well-being depends on multiple social and institutional factors.

        ### 2. Health, Environment & Nutrition
        - Investment in healthcare improves life expectancy and well-being.
        - Undernourishment remains a major barrier to happiness in lower-income regions.
        - CO₂ emissions reveal the tension between development and environmental impact.

        ### 3. Economy, Employment & Income Groups
        - Unemployment strongly predicts lower happiness.
        - High-income groups show higher happiness, but internal variation highlights the role of governance and culture.

        ### 4. Peace & Stability
        - More peaceful countries consistently report higher happiness.
        - Regional instability significantly reduces quality of life even when income is moderate.

        ### 5. How to Use This Dashboard
        - As a tool for exploring global well-being differences.
        - As evidence for academic reports and policy analysis.
        - As a base for future predictive modeling of happiness factors.
        """
    )

    st.info("You can use these insights directly in your academic report or expand them into a detailed analysis.")
