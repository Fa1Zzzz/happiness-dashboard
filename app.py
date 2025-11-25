# app.py
# ============================================
# Global Happiness, Health, Life Expectancy & Peace Dashboard
# - Navy gradient background
# - "About This Dashboard" ONLY in Overview tab
# - Data Tables tab
# - Full original insights restored
# - New dashboard title added above tabs
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
    best_col = df.columns[1]
    df["Peace_Score"] = pd.to_numeric(df[best_col].astype(str).str.replace(",", "."), errors="coerce")
    return df[["Country", "Peace_Score"]]

# Load Data
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

# ------------------ Main Title (NEW) ------------------
st.title("🌍🤔 How Well Is the World Doing?")
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

    # Stable map
    fig_map = px.choropleth(
        filtered,
        locations="Country",
        locationmode="country names",
        color="Happiness_Score",
        color_continuous_scale="Blues",
        title="Global Happiness Map"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown(
        """
        **Insight:**  
        This map compares countries based on their overall **happiness score**.
        Darker shades indicate higher happiness levels. You can use the sidebar filters
        to focus on specific regions or income groups and see how the global pattern changes.
        """
    )


# ------------------ Happiness ------------------
with tab_happy:
    st.subheader("Happiness Analysis")

    col1, col2 = st.columns(2)

    with col1:
        top10 = filtered.sort_values("Happiness_Score", ascending=False).head(10)
        st.plotly_chart(bar(top10, "Country", "Happiness_Score", "Top 10 Happiest Countries"))
        st.markdown(
            """
            **Insight:**  
            This bar chart compares the **10 happiest countries** based on their happiness scores.
            It highlights which countries consistently appear at the top of global rankings and can be
            used to explore common patterns between them (e.g., high income, strong social support, stability).
            """
        )

    with col2:
        bottom10 = filtered.sort_values("Happiness_Score").head(10)
        st.plotly_chart(bar(bottom10, "Country", "Happiness_Score", "Bottom 10 Countries by Happiness"))
        st.markdown(
            """
            **Insight:**  
            This chart shows the **10 countries with the lowest happiness scores**.
            It is useful for identifying where well-being is most at risk and may require
            targeted policies in areas such as health, income, governance, or security.
            """
        )

    st.markdown("---")
    st.markdown("### Key Happiness Drivers")

    col3, col4 = st.columns(2)

    if "Social_support" in filtered:
        df_soc = filtered.dropna(subset=["Social_support", "Happiness_Score"])
        col3.plotly_chart(scatter(df_soc, "Social_support", "Happiness_Score", "Happiness vs Social Support"))
        st.markdown(
            """
            **Insight:**  
            This scatter plot compares **happiness** with **social support**.
            Countries where people report stronger social support networks tend
            to have higher happiness scores, suggesting that friends, family,
            and community play a central role in well-being.
            """
        )

    if "Freedom" in filtered:
        df_free = filtered.dropna(subset=["Freedom", "Happiness_Score"])
        col4.plotly_chart(scatter(df_free, "Freedom", "Happiness_Score", "Happiness vs Freedom to Make Life Choices"))
        st.markdown(
            """
            **Insight:**  
            Here, happiness is compared with **freedom to make life choices**.
            The general pattern shows that people are happier in countries where
            they feel free to decide about their own lives, careers, and personal paths.
            """
        )


# ------------------ Health ------------------
with tab_health:
    st.subheader("Health & Life Expectancy")

    col1, col2 = st.columns(2)

    if "Life_Expectancy" in filtered:
        df_life = filtered.dropna(subset=["Life_Expectancy", "Happiness_Score"])
        col1.plotly_chart(scatter(df_life, "Life_Expectancy", "Happiness_Score", "Happiness vs Life Expectancy"))
        st.markdown(
            """
            **Insight:**  
            This chart compares **happiness** with **life expectancy**.
            In many cases, countries where people live longer also report higher happiness,
            reflecting the role of health systems, living conditions, and overall quality of life.
            """
        )

    if "Health_Expenditure_pct" in filtered:
        df_hexp = filtered.dropna(subset=["Health_Expenditure_pct", "Happiness_Score"])
        col2.plotly_chart(scatter(df_hexp, "Health_Expenditure_pct", "Happiness_Score", "Happiness vs Health Expenditure (% of GDP)"))
        st.markdown(
            """
            **Insight:**  
            This comparison shows how **health spending as a percentage of GDP** relates to happiness.
            Although higher spending does not always guarantee higher happiness, many happier countries
            invest more in healthcare, which supports better access and outcomes.
            """
        )

    st.markdown("---")

    col3, col4 = st.columns(2)

    if "CO2_emissions" in filtered:
        df_co2 = filtered.dropna(subset=["CO2_emissions", "Happiness_Score"])
        col3.plotly_chart(scatter(df_co2, "CO2_emissions", "Happiness_Score", "Happiness vs CO₂ Emissions"))
        st.markdown(
            """
            **Insight:**  
            This plot compares **happiness** with **CO₂ emissions**.
            It can be used to explore whether more industrialized (and often more polluting) countries
            trade off environmental quality for higher income and reported well-being.
            """
        )

    if "Undernourishment_pct" in filtered:
        df_und = filtered.dropna(subset=["Undernourishment_pct", "Happiness_Score"])
        col4.plotly_chart(scatter(df_und, "Undernourishment_pct", "Happiness_Score", "Happiness vs Undernourishment (%)"))
        st.markdown(
            """
            **Insight:**  
            Here, happiness is compared with **undernourishment levels**.
            Countries with higher rates of undernourishment tend to have lower happiness,
            which highlights how basic needs (food and nutrition) remain fundamental to well-being.
            """
        )
# ------------------ Economic Factors ------------------
with tab_econ:
    st.subheader("Economic Factors")

    col1, col2 = st.columns(2)

    if "Log_GDP_per_capita" in filtered:
        df_gdp = filtered.dropna(subset=["Log_GDP_per_capita", "Happiness_Score"])
        col1.plotly_chart(scatter(df_gdp, "Log_GDP_per_capita", "Happiness_Score", "Happiness vs Log GDP per Capita"))
        st.markdown(
            """
            **Insight:**  
            This chart compares **income levels (log GDP per capita)** with happiness.
            While higher income generally supports better living standards and happiness,
            the relationship is not perfectly linear, and other social and institutional
            factors also play a significant role.
            """
        )

    if "Unemployment_pct" in filtered:
        df_unemp = filtered.dropna(subset=["Unemployment_pct", "Happiness_Score"])
        col2.plotly_chart(scatter(df_unemp, "Unemployment_pct", "Happiness_Score", "Happiness vs Unemployment Rate"))
        st.markdown(
            """
            **Insight:**  
            This plot compares **unemployment rates** with happiness.
            Higher unemployment is typically associated with lower happiness, as it affects
            financial security, social status, and mental health.
            """
        )

    st.markdown("---")

    if "Income_Group" in filtered:
        df_box = filtered.dropna(subset=["Income_Group", "Happiness_Score"])
        fig_box = px.box(df_box, x="Income_Group", y="Happiness_Score", template="plotly_white")
        fig_box.update_traces(marker_color=PRIMARY_COLOR)
        st.plotly_chart(fig_box, use_container_width=True)
        st.markdown(
            """
            **Insight:**  
            This box plot compares **happiness scores across different income groups**.
            It shows how high-income countries usually report higher happiness on average,
            but also that income alone cannot explain all differences in well-being.
            """
        )


# ------------------ Peace & Stability ------------------
with tab_peace:
    st.subheader("Peace & Stability (Global Peace Index)")

    if "Peace_Score" not in filtered:
        st.warning("Peace index data is not available.")
    else:
        col1, col2 = st.columns(2)

        df_p = filtered.dropna(subset=["Peace_Score", "Happiness_Score"])
        col1.plotly_chart(scatter(df_p, "Peace_Score", "Happiness_Score", "Happiness vs Peace Index Score"))
        st.markdown(
            """
            **Insight:**  
            This chart compares **happiness** with a **peace index score**.
            In many peace indices, a **lower score means more peace**.
            The relationship helps illustrate how safety, conflict levels, and stability
            are connected to how people feel about their lives.
            """
        )

        most_peaceful = df_p.sort_values("Peace_Score", ascending=True).head(10)
        col2.plotly_chart(bar(most_peaceful, "Country", "Peace_Score", "Top 10 Most Peaceful Countries (Lower Score = More Peace)"))
        st.markdown(
            """
            **Insight:**  
            This bar chart shows the **10 most peaceful countries** according to the peace index.
            It is useful for identifying countries that combine stability, low conflict, and often
            higher levels of happiness and human development.
            """
        )

        st.markdown("---")

        if "H_Region" in filtered:
            df_reg = filtered.dropna(subset=["H_Region", "Peace_Score"])
            fig_region = px.box(df_reg, x="H_Region", y="Peace_Score", template="plotly_white")
            fig_region.update_traces(marker_color=PRIMARY_COLOR)
            st.plotly_chart(fig_region, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This box plot compares **peace scores across regions**.
                It helps reveal which regions are generally more stable and which face higher
                levels of conflict or insecurity, providing context for differences in happiness.
                """
            )


# ------------------ Data Tables ------------------
with tab_tables:
    st.subheader("Raw Data Tables")

    st.markdown("### • Happiness Dataset")
    st.dataframe(happy)

    st.markdown("### • Life Expectancy Dataset")
    st.dataframe(life)

    st.markdown("### • Peace Index Dataset")
    st.dataframe(peace)

    st.markdown("### • Final Merged Dataset")
    st.dataframe(merged_df)


# ------------------ Insights & Conclusion ------------------
with tab_insights:
    st.subheader("Insights & Conclusion (Full Version)")

    st.markdown(
        """
        ### **1. Overall Patterns**
        - **Happiness** tends to be higher in countries with:
          - Strong **social support**
          - Greater **freedom to make life choices**
          - Higher **life expectancy**
        - **Income** plays a role, but it is not the only driver of well-being.

        ### **2. Health, Environment & Nutrition**
        - Countries that invest more in **healthcare** often show both higher life expectancy and higher happiness.
        - **Undernourishment** and poor nutritional conditions are linked with lower happiness scores.
        - **CO₂ emissions** highlight a potential trade-off between industrialization, income, and environmental quality.

        ### **3. Economic Factors**
        - **Unemployment** is a consistent risk factor for lower happiness.
        - High-income countries usually report higher happiness on average.
        - Differences inside each income group show the importance of **institutions, governance, and culture**.

        ### **4. Peace & Stability**
        - More **peaceful and stable countries** (lower peace index scores) tend to have higher happiness.
        - Regional comparisons show that conflict and insecurity can significantly reduce well-being.

        ### **5. How to Use This Dashboard**
        - As an **exploratory tool** for understanding global well-being.
        - As **evidence** for academic reports and research.
        - As a base for **future modeling**, such as predicting happiness from health, economic, and peace indicators.
        """
    )

    st.info(
        "You can reuse and adapt these insights in your written report or have me rewrite them in academic style."
    )
