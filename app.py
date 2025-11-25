# app.py
# ============================================
# Global Happiness & Life Expectancy Dashboard
# Tabs + Gradient background + single-color charts
# Requires:
#   - World-happiness-report-2024.csv
#   - life expectancy.csv
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------ Page Setup ------------------
st.set_page_config(
    page_title="Global Happiness & Life Expectancy Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Gradient background + base styling
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
    }
    /* Make main blocks a bit transparent so charts stand out */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# One consistent chart color
PRIMARY_COLOR = "#4FC3F7"  # سماوي جميل


# ------------------ Data Load & Merge ------------------
@st.cache_data
def load_happiness(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # توحيد أسماء الأعمدة لسهولة التعامل
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
    # ترتيب حسب السعادة
    df["Happiness_Rank"] = df["Happiness_Score"].rank(ascending=False, method="min").astype(int)
    return df


@st.cache_data
def load_life(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # توحيد اسم الدولة
    df = df.rename(columns={"Country Name": "Country"})
    # ناخذ أحدث سنة متوفرة لكل دولة
    df = df.sort_values(["Country", "Year"])
    latest = df.groupby("Country").tail(1).reset_index(drop=True)
    # إعادة تسمية بعض الأعمدة لتكون أوضح
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
def build_merged(happy_path: str, life_path: str) -> pd.DataFrame:
    h = load_happiness(happy_path)
    l = load_life(life_path)

    # دمج حسب الدولة
    merged = h.merge(l, on="Country", how="left", suffixes=("", "_life"))

    # اختيار بعض الأعمدة الرقمية للـ correlation لاحقاً
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
    ]
    # قد تكون بعض الأعمدة غير موجودة في بعض الملفات، نفلتر الموجود فقط
    numeric_cols = [c for c in numeric_cols if c in merged.columns]
    merged_numeric = merged[numeric_cols].select_dtypes(include=["float64", "int64"])
    return merged, merged_numeric.columns.tolist()


# ------------------ Load Data ------------------
HAPPINESS_PATH = "World-happiness-report-2024.csv"
LIFE_PATH = "life expectancy.csv"

merged_df, numeric_cols = build_merged(HAPPINESS_PATH, LIFE_PATH)

# ------------------ Sidebar Filters ------------------
st.sidebar.title("Filters")

all_regions = sorted(merged_df["H_Region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect(
    "Select Region(s)",
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
        "Select Income Group(s)",
        options=sorted(income_options),
        default=income_options,
    )

filtered_df = merged_df.copy()
if selected_regions:
    filtered_df = filtered_df[filtered_df["H_Region"].isin(selected_regions)]
if selected_income and "Income_Group" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Income_Group"].isin(selected_income)]

st.sidebar.markdown("---")
st.sidebar.caption("All charts use a single accent color and are interactive.")


# ------------------ Helper: Single-color Plotly ------------------
def single_color_scatter(df, x, y, hover=None, title=""):
    fig = px.scatter(
        df,
        x=x,
        y=y,
        hover_data=hover,
    )
    # نجعل كل النقاط نفس اللون
    fig.update_traces(marker=dict(color=PRIMARY_COLOR, size=9, line=dict(width=0)))
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=450,
        margin=dict(l=10, r=10, t=50, b=10),
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
        height=450,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# ------------------ Title ------------------
st.title("🌍 Global Happiness, Health & Life Expectancy Dashboard")
st.caption("Interactive analysis using World Happiness Report 2024 + Life Expectancy & Health indicators.")


# ------------------ Tabs ------------------
tab_overview, tab_happy, tab_health, tab_econ, tab_insights = st.tabs(
    ["Overview", "Happiness Analysis", "Health & Life Expectancy", "Economic Factors", "Insights & Conclusion"]
)


# ========== TAB 1: OVERVIEW ==========
with tab_overview:
    st.subheader("Global Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Avg Happiness Score",
            f"{filtered_df['Happiness_Score'].mean():.2f}"
        )
    with col2:
        if "Life_Expectancy" in filtered_df.columns:
            st.metric(
                "Avg Life Expectancy",
                f"{filtered_df['Life_Expectancy'].mean():.1f} years"
            )
        else:
            st.metric("Avg Life Expectancy", "N/A")
    with col3:
        st.metric(
            "Countries in Filter",
            filtered_df["Country"].nunique()
        )

    st.markdown("### World Happiness Map")

    # خريطة عالمية بسيطة حسب درجة السعادة
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
        margin=dict(l=0, r=0, t=50, b=0),
        height=520,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown(
        """
        **ملاحظة تحليليّة سريعة:**
        - الدول ذات السعادة العالية غالبًا تظهر في أوروبا الغربية وبعض دول مرتفعة الدخل.
        - بإمكانك تغيير المناطق (Region) من الـ Sidebar لمقارنة مناطق معينة فقط.
        """
    )


# ========== TAB 2: HAPPINESS ANALYSIS ==========
with tab_happy:
    st.subheader("Happiness Drivers")

    col1, col2 = st.columns(2)

    with col1:
        # Top 10 happiest countries
        top10 = filtered_df.sort_values("Happiness_Score", ascending=False).head(10)
        fig_top10 = single_color_bar(
            top10,
            x="Country",
            y="Happiness_Score",
            title="Top 10 Happiest Countries"
        )
        st.plotly_chart(fig_top10, use_container_width=True)

    with col2:
        bottom10 = filtered_df.sort_values("Happiness_Score", ascending=True).head(10)
        fig_bottom10 = single_color_bar(
            bottom10,
            x="Country",
            y="Happiness_Score",
            title="Bottom 10 Countries by Happiness"
        )
        st.plotly_chart(fig_bottom10, use_container_width=True)

    st.markdown("---")
    st.markdown("### Relationship with Key Happiness Factors")

    col3, col4 = st.columns(2)
    # Happiness vs Social Support
    with col3:
        if "Social_support" in filtered_df.columns:
            fig_soc = single_color_scatter(
                filtered_df.dropna(subset=["Social_support", "Happiness_Score"]),
                x="Social_support",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Social Support",
            )
            st.plotly_chart(fig_soc, use_container_width=True)

    # Happiness vs Freedom
    with col4:
        if "Freedom" in filtered_df.columns:
            fig_free = single_color_scatter(
                filtered_df.dropna(subset=["Freedom", "Happiness_Score"]),
                x="Freedom",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Freedom to Make Life Choices",
            )
            st.plotly_chart(fig_free, use_container_width=True)

    st.markdown(
        """
        **قراءة سريعة:**  
        - غالبًا تلاحظ أن الدول ذات *الدعم الاجتماعي الأعلى* و *حرية الاختيار الأكبر* تمتلك درجات سعادة أعلى.
        """
    )


# ========== TAB 3: HEALTH & LIFE EXPECTANCY ==========
with tab_health:
    st.subheader("Health, Environment & Life Expectancy")

    if "Life_Expectancy" not in filtered_df.columns:
        st.warning("Life expectancy data not available for the current selection.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            fig_life = single_color_scatter(
                filtered_df.dropna(subset=["Life_Expectancy", "Happiness_Score"]),
                x="Life_Expectancy",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Life Expectancy",
            )
            st.plotly_chart(fig_life, use_container_width=True)

        with col2:
            if "Health_Expenditure_pct" in filtered_df.columns:
                fig_health_spend = single_color_scatter(
                    filtered_df.dropna(subset=["Health_Expenditure_pct", "Happiness_Score"]),
                    x="Health_Expenditure_pct",
                    y="Happiness_Score",
                    hover=["Country"],
                    title="Happiness vs Health Expenditure (% of GDP)",
                )
                st.plotly_chart(fig_health_spend, use_container_width=True)

        st.markdown("---")

        col3, col4 = st.columns(2)

        # CO2 vs Happiness
        if "CO2_emissions" in filtered_df.columns:
            with col3:
                fig_co2 = single_color_scatter(
                    filtered_df.dropna(subset=["CO2_emissions", "Happiness_Score"]),
                    x="CO2_emissions",
                    y="Happiness_Score",
                    hover=["Country"],
                    title="Happiness vs CO₂ Emissions",
                )
                st.plotly_chart(fig_co2, use_container_width=True)

        # Undernourishment vs Happiness
        if "Undernourishment_pct" in filtered_df.columns:
            with col4:
                fig_und = single_color_scatter(
                    filtered_df.dropna(subset=["Undernourishment_pct", "Happiness_Score"]),
                    x="Undernourishment_pct",
                    y="Happiness_Score",
                    hover=["Country"],
                    title="Happiness vs Undernourishment (%)",
                )
                st.plotly_chart(fig_und, use_container_width=True)

        st.markdown(
            """
            **ملاحظات تحليليّة محتملة:**
            - الدول ذات *العمر المتوقع الأعلى* تميل غالبًا لأن تكون أسعد.
            - ارتفاع الإنفاق الصحي قد يرتبط بسعادة أعلى، لكن العلاقة ليست خطية دائمًا.
            - التلوث (CO₂) وسوء التغذية قد يكونان عوامل ضغط على جودة الحياة والسعادة.
            """
        )


# ========== TAB 4: ECONOMIC FACTORS ==========
with tab_econ:
    st.subheader("Economic Context")

    col1, col2 = st.columns(2)

    # Happiness vs Log GDP per capita
    if "Log_GDP_per_capita" in filtered_df.columns:
        with col1:
            fig_gdp = single_color_scatter(
                filtered_df.dropna(subset=["Log_GDP_per_capita", "Happiness_Score"]),
                x="Log_GDP_per_capita",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Log GDP per Capita",
            )
            st.plotly_chart(fig_gdp, use_container_width=True)

    # Happiness vs Unemployment
    if "Unemployment_pct" in filtered_df.columns:
        with col2:
            fig_unemp = single_color_scatter(
                filtered_df.dropna(subset=["Unemployment_pct", "Happiness_Score"]),
                x="Unemployment_pct",
                y="Happiness_Score",
                hover=["Country"],
                title="Happiness vs Unemployment Rate",
            )
            st.plotly_chart(fig_unemp, use_container_width=True)

    st.markdown("---")

    # Boxplot by Income Group (لو متوفر)
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
            height=450,
            margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown(
        """
        **إطار اقتصادي عام:**
        - الدول ذات الدخل الأعلى غالبًا تمتلك متوسط سعادة أعلى، لكن ليس دائمًا.
        - البطالة عامل مهم في خفض الرضا عن الحياة.
        """
    )


# ========== TAB 5: INSIGHTS & CONCLUSION ==========
with tab_insights:
    st.subheader("Insights & Conclusion (Draft)")

    st.markdown(
        """
        ### 1. Key Observations  
        - There is a **positive relationship** between happiness and both:
          - **Social support**
          - **Freedom to make life choices**
        - Countries with **higher life expectancy** tend to report **higher happiness scores**.
        - Economic strength (log GDP per capita) is associated with happiness, but **it is not the only driver**.
        
        ### 2. Health & Environment
        - Higher **health expenditure** is often linked with both:
          - Better life expectancy  
          - Higher happiness levels  
        - Environmental stressors such as **CO₂ emissions** and **undernourishment** can negatively affect overall well-being.

        ### 3. Economic & Social Context
        - **Income group** matters: high-income countries usually rank higher in happiness,
          but **social cohesion, governance, and public services** also play a critical role.
        - **Unemployment** is a consistent risk factor for lower happiness.

        ### 4. Possible Extensions
        - إضافة بعد زمني (time-series) لو توفّرت بيانات لعدة سنوات.
        - بناء نماذج تنبؤية للتنبؤ بدرجة السعادة بناءً على الصحة والاقتصاد والبيئة.
        - مقارنة مناطق معيّنة (مثل دول الخليج، أوروبا، شرق آسيا) بشكل أعمق.
        """
    )

    st.info(
        "تقدر تستخدم هذه الملاحظات كنقطة بداية لقسم الـ Discussion و Conclusion في تقريرك النهائي. "
        "لو حاب، أقدر أكتب لك نسخة أكاديمية جاهزة باللغة الإنجليزية بناءً على هذه النتائج."
    )
