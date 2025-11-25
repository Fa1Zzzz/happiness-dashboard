# app.py
# ============================================
# Global Happiness, Health, Life Expectancy & Peace Dashboard
# - Light gradient background (B)
# - English labels + insights
# - Single-color interactive charts
# - Stable-ish world map (interactive hover, layout preserved)
# Requires:
#   - World-happiness-report-2024.csv
#   - life expectancy.csv
#   - peace_index.csv
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

# Light gradient background
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom, #4A0E23, #701934, #9E2F4C);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)


PRIMARY_COLOR = "#4FC3F7"  # single accent color


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
    """
    Tries to parse the Global Peace Index CSV.
    Assumes semicolon-separated, with first column = Country
    and some numeric columns representing yearly scores.
    We pick the most "filled" numeric column as Peace_Score.
    """
    # Many peace index files are ';'-separated
    df = pd.read_csv(path, sep=';', engine='python')

    # Ensure first column is Country
    df = df.rename(columns={df.columns[0]: "Country"})

    # Try to find the best numeric column for peace score
    candidates = df.columns[1:]
    best_col = None
    best_non_null = -1

    for c in candidates:
        s = pd.to_numeric(df[c].astype(str).str.replace(",", "."),
                          errors="coerce")
        non_null = s.notna().sum()
        if non_null > best_non_null:
            best_non_null = non_null
            best_col = c

    if best_col is not None:
        df["Peace_Score"] = pd.to_numeric(
            df[best_col].astype(str).str.replace(",", "."),
            errors="coerce"
        )
    else:
        # Fallback: last column
        df["Peace_Score"] = pd.to_numeric(
            df.iloc[:, -1].astype(str).str.replace(",", "."),
            errors="coerce"
        )

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
selected_regions = st.sidebar.multiselect(
    "Select region(s)",
    options=all_regions,
    default=all_regions,
)

income_options = (
    merged_df["Income_Group"].dropna().unique().tolist()
    if "Income_Group" in merged_df.columns
    else []
)
selected_income = []
if income_options:
    selected_income = st.sidebar.multiselect(
        "Select income group(s)",
        options=sorted(income_options),
        default=income_options,
    )

filtered_df = merged_df.copy()
if selected_regions:
    filtered_df = filtered_df[filtered_df["H_Region"].isin(selected_regions)]
if selected_income and "Income_Group" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Income_Group"].isin(selected_income)]

st.sidebar.markdown("---")
st.sidebar.caption("All charts use one accent color and remain fully interactive.")


# ------------------ Plot Helpers ------------------
def single_color_scatter(df, x, y, hover=None, title=""):
    fig = px.scatter(df, x=x, y=y, hover_data=hover)
    fig.update_traces(marker=dict(color=PRIMARY_COLOR, size=9, line=dict(width=0)))
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=430,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def single_color_bar(df, x, y, orientation="v", title=""):
    fig = px.bar(
        df,
        x=x if orientation == "v" else None,
        y=y if orientation == "v" else None,
        orientation=orientation,
    )
    fig.update_traces(marker_color=PRIMARY_COLOR)
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=430,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


# ------------------ Main Title + Overview ------------------
st.title("🌍 Global Happiness, Health, Life Expectancy & Peace Dashboard")

st.markdown(
    """
    ### Dashboard Overview
    This interactive dashboard explores how **happiness levels** around the world relate to:
    - **Health and life expectancy**
    - **Economic conditions**
    - **Environmental and nutrition factors**
    - **Global peace and stability**

    Use the filters in the sidebar to focus on specific regions or income groups,
    and read the insight under each chart to understand what the comparison shows and why it matters.
    """
)


# ------------------ Tabs ------------------
tab_overview, tab_happy, tab_health, tab_econ, tab_peace, tab_insights = st.tabs(
    [
        "Overview",
        "Happiness",
        "Health & Life Expectancy",
        "Economic Factors",
        "Peace & Stability",
        "Insights & Conclusion",
    ]
)


# ========== TAB 1: OVERVIEW ==========
with tab_overview:
    st.subheader("Global Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Average Happiness Score",
            f"{filtered_df['Happiness_Score'].mean():.2f}"
        )
    with col2:
        if "Life_Expectancy" in filtered_df.columns:
            st.metric(
                "Average Life Expectancy",
                f"{filtered_df['Life_Expectancy'].mean():.1f} years"
            )
        else:
            st.metric("Average Life Expectancy", "N/A")
    with col3:
        st.metric(
            "Countries in Selection",
            filtered_df["Country"].nunique()
        )

    st.markdown("### World Happiness Map")

    # Stable-ish map (layout preserved via uirevision; hover still interactive)
    map_df = filtered_df.copy()
    fig_map = px.choropleth(
        map_df,
        locations="Country",
        locationmode="country names",
        color="Happiness_Score",
        color_continuous_scale="Blues",
        title="Happiness Score by Country (2024)",
    )
    fig_map.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
        uirevision="world-happiness-map",
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown(
        """
        #### Insight
        This map compares countries based on their overall **happiness score**.
        Darker shades indicate higher happiness levels. You can use the sidebar filters
        to focus on specific regions or income groups and see how the global pattern changes.
        """
    )


# ========== TAB 2: HAPPINESS ==========
with tab_happy:
    st.subheader("Happiness Analysis")

    col1, col2 = st.columns(2)

    with col1:
        top10 = filtered_df.sort_values("Happiness_Score", ascending=False).head(10)
        fig_top10 = single_color_bar(
            top10,
            x="Country",
            y="Happiness_Score",
            title="Top 10 Happiest Countries"
        )
        st.plotly_chart(fig_top10, use_container_width=True)
        st.markdown(
            """
            **Insight:**  
            This bar chart compares the **10 happiest countries** based on their happiness scores.
            It highlights which countries consistently appear at the top of global rankings and can be
            used to explore common patterns between them (e.g., high income, strong social support, stability).
            """
        )

    with col2:
        bottom10 = filtered_df.sort_values("Happiness_Score", ascending=True).head(10)
        fig_bottom10 = single_color_bar(
            bottom10,
            x="Country",
            y="Happiness_Score",
            title="Bottom 10 Countries by Happiness"
        )
        st.plotly_chart(fig_bottom10, use_container_width=True)
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

    with col3:
        if "Social_support" in filtered_df.columns:
            df_soc = filtered_df.dropna(subset=["Social_support", "Happiness_Score"])
            fig_soc = single_color_scatter(
                df_soc,
                x="Social_support",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Social Support",
            )
            st.plotly_chart(fig_soc, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This scatter plot compares **happiness** with **social support**.
                Countries where people report stronger social support networks tend
                to have higher happiness scores, suggesting that friends, family,
                and community play a central role in well-being.
                """
            )

    with col4:
        if "Freedom" in filtered_df.columns:
            df_free = filtered_df.dropna(subset=["Freedom", "Happiness_Score"])
            fig_free = single_color_scatter(
                df_free,
                x="Freedom",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Freedom to Make Life Choices",
            )
            st.plotly_chart(fig_free, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                Here, happiness is compared with **freedom to make life choices**.
                The general pattern shows that people are happier in countries where
                they feel free to decide about their own lives, careers, and personal paths.
                """
            )


# ========== TAB 3: HEALTH & LIFE EXPECTANCY ==========
with tab_health:
    st.subheader("Health & Life Expectancy")

    if "Life_Expectancy" not in filtered_df.columns:
        st.warning("Life expectancy data is not available for the current selection.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            df_life = filtered_df.dropna(subset=["Life_Expectancy", "Happiness_Score"])
            fig_life = single_color_scatter(
                df_life,
                x="Life_Expectancy",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Life Expectancy",
            )
            st.plotly_chart(fig_life, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This chart compares **happiness** with **life expectancy**.
                In many cases, countries where people live longer also report higher happiness,
                reflecting the role of health systems, living conditions, and overall quality of life.
                """
            )

        with col2:
            if "Health_Expenditure_pct" in filtered_df.columns:
                df_hexp = filtered_df.dropna(subset=["Health_Expenditure_pct", "Happiness_Score"])
                fig_health = single_color_scatter(
                    df_hexp,
                    x="Health_Expenditure_pct",
                    y="Happiness_Score",
                    hover=["Country"],
                    title="Happiness vs Health Expenditure (% of GDP)",
                )
                st.plotly_chart(fig_health, use_container_width=True)
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

        if "CO2_emissions" in filtered_df.columns:
            with col3:
                df_co2 = filtered_df.dropna(subset=["CO2_emissions", "Happiness_Score"])
                fig_co2 = single_color_scatter(
                    df_co2,
                    x="CO2_emissions",
                    y="Happiness_Score",
                    hover=["Country"],
                    title="Happiness vs CO₂ Emissions",
                )
                st.plotly_chart(fig_co2, use_container_width=True)
                st.markdown(
                    """
                    **Insight:**  
                    This plot compares **happiness** with **CO₂ emissions**.
                    It can be used to explore whether more industrialized (and often more polluting) countries
                    trade off environmental quality for higher income and reported well-being.
                    """
                )

        if "Undernourishment_pct" in filtered_df.columns:
            with col4:
                df_und = filtered_df.dropna(subset=["Undernourishment_pct", "Happiness_Score"])
                fig_und = single_color_scatter(
                    df_und,
                    x="Undernourishment_pct",
                    y="Happiness_Score",
                    hover=["Country"],
                    title="Happiness vs Undernourishment (%)",
                )
                st.plotly_chart(fig_und, use_container_width=True)
                st.markdown(
                    """
                    **Insight:**  
                    Here, happiness is compared with **undernourishment levels**.
                    Countries with higher rates of undernourishment tend to have lower happiness,
                    which highlights how basic needs (food and nutrition) remain fundamental to well-being.
                    """
                )


# ========== TAB 4: ECONOMIC FACTORS ==========
with tab_econ:
    st.subheader("Economic Factors")

    col1, col2 = st.columns(2)

    if "Log_GDP_per_capita" in filtered_df.columns:
        with col1:
            df_gdp = filtered_df.dropna(subset=["Log_GDP_per_capita", "Happiness_Score"])
            fig_gdp = single_color_scatter(
                df_gdp,
                x="Log_GDP_per_capita",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Log GDP per Capita",
            )
            st.plotly_chart(fig_gdp, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This chart compares **income levels (log GDP per capita)** with happiness.
                While higher income generally supports better living standards and happiness,
                the relationship is not perfectly linear, and other social and institutional
                factors also play a significant role.
                """
            )

    if "Unemployment_pct" in filtered_df.columns:
        with col2:
            df_unemp = filtered_df.dropna(subset=["Unemployment_pct", "Happiness_Score"])
            fig_unemp = single_color_scatter(
                df_unemp,
                x="Unemployment_pct",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Unemployment Rate",
            )
            st.plotly_chart(fig_unemp, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This plot compares **unemployment rates** with happiness.
                Higher unemployment is typically associated with lower happiness, as it affects
                financial security, social status, and mental health.
                """
            )

    st.markdown("---")

    if "Income_Group" in filtered_df.columns:
        st.markdown("### Happiness by Income Group")
        box_df = filtered_df.dropna(subset=["Income_Group", "Happiness_Score"])
        fig_box = px.box(
            box_df,
            x="Income_Group",
            y="Happiness_Score",
            template="plotly_white",
        )
        fig_box.update_traces(marker_color=PRIMARY_COLOR)
        fig_box.update_layout(
            height=430,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_box, use_container_width=True)
        st.markdown(
            """
            **Insight:**  
            This box plot compares **happiness scores across different income groups**.
            It shows how high-income countries usually report higher happiness on average,
            but also that income alone cannot explain all differences in well-being.
            """
        )


# ========== TAB 5: PEACE & STABILITY ==========
with tab_peace:
    st.subheader("Peace & Stability (Global Peace Index)")

    if "Peace_Score" not in filtered_df.columns:
        st.warning("Peace index data is not available.")
    else:
        col1, col2 = st.columns(2)

        # Note: in many peace indices, lower score = more peaceful
        with col1:
            df_peace = filtered_df.dropna(subset=["Peace_Score", "Happiness_Score"])
            fig_peace_happy = single_color_scatter(
                df_peace,
                x="Peace_Score",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Peace Index Score",
            )
            st.plotly_chart(fig_peace_happy, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This chart compares **happiness** with a **peace index score**.
                In many peace indices, a **lower score means more peace**.
                The relationship helps illustrate how safety, conflict levels, and stability
                are connected to how people feel about their lives.
                """
            )

        with col2:
            # Most and least peaceful based on Peace_Score (ascending)
            df_peace_rank = df_peace.copy()
            most_peaceful = df_peace_rank.sort_values("Peace_Score", ascending=True).head(10)
            fig_most_peaceful = single_color_bar(
                most_peaceful,
                x="Country",
                y="Peace_Score",
                title="Top 10 Most Peaceful Countries (Lower Score = More Peace)"
            )
            st.plotly_chart(fig_most_peaceful, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This bar chart shows the **10 most peaceful countries** according to the peace index.
                It is useful for identifying countries that combine stability, low conflict, and often
                higher levels of happiness and human development.
                """
            )

        st.markdown("---")

        if "H_Region" in filtered_df.columns:
            st.markdown("### Peace Index by Region")
            df_region_peace = filtered_df.dropna(subset=["H_Region", "Peace_Score"])
            fig_region_peace = px.box(
                df_region_peace,
                x="H_Region",
                y="Peace_Score",
                template="plotly_white",
            )
            fig_region_peace.update_traces(marker_color=PRIMARY_COLOR)
            fig_region_peace.update_layout(
                height=430,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_region_peace, use_container_width=True)
            st.markdown(
                """
                **Insight:**  
                This box plot compares **peace scores across regions**.
                It helps reveal which regions are generally more stable and which face higher
                levels of conflict or insecurity, providing context for differences in happiness.
                """
            )


# ========== TAB 6: INSIGHTS & CONCLUSION ==========
with tab_insights:
    st.subheader("Insights & Conclusion (Draft)")

    st.markdown(
        """
        ### 1. Overall Patterns  

        - **Happiness** tends to be higher in countries with:
          - Strong **social support**
          - Greater **freedom to make life choices**
          - Higher **life expectancy**  
        - Economic strength (measured by **log GDP per capita**) is important, but
          **it is not the only driver of well-being**.

        ### 2. Health, Environment & Nutrition  

        - Countries that invest more in **healthcare** often show both higher life expectancy and higher happiness.
        - **Undernourishment** and poor nutritional conditions are linked with lower happiness scores.
        - **CO₂ emissions** highlight a potential trade-off between industrialization, income, and environmental quality.

        ### 3. Economy, Employment & Income Groups  

        - **Unemployment** is a consistent risk factor for lower happiness, as it affects financial and social stability.
        - High-income countries usually report higher happiness on average, but differences within the same income group
          show that **institutions, governance, and culture** also matter.

        ### 4. Peace & Stability  

        - More **peaceful and stable countries** (lower peace index scores) tend to have higher levels of happiness.
        - Regional comparisons show that conflict and insecurity can significantly reduce well-being even when income levels
          are moderate or high.

        ### 5. How to Use This Dashboard  

        - As an **exploratory tool** for understanding global well-being.
        - As a **supporting analysis** for an academic report on happiness, health, and peace.
        - As a base for **future modeling**, such as predicting happiness from health, economic, and peace indicators.
        """
    )

    st.info(
        "You can reuse and adapt these insights in the Discussion and Conclusion sections "
        "of your written report. If you want, I can help you convert them into a polished academic text."
    )

