"""
The Cube | Del Valle Sports Bar & Event Center
Streamlit Financial Model Dashboard
"""

import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import random

# Import the model
sys.path.insert(0, os.path.dirname(__file__))
import the_cube_model as model

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="The Cube | Financial Model",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_dollar(val):
    """Format as dollar string."""
    if val < 0:
        return f"-${abs(val):,.0f}"
    return f"${val:,.0f}"


def fmt_pct(val):
    return f"{val:.1f}%"


# =============================================================================
# SIDEBAR — GLOBAL INPUTS
# =============================================================================
st.sidebar.title("The Cube")
st.sidebar.caption("Del Valle Sports Bar & Event Center")
st.sidebar.markdown("---")
st.sidebar.subheader("Model Inputs")

daily_customers = st.sidebar.slider(
    "Daily Customers (avg)", 40, 200, 100, step=5,
    help="Average daily customer count across weekdays and weekends"
)
weekday_check = st.sidebar.slider(
    "Weekday Avg Check ($)", 15.0, 40.0, 25.71, step=0.50,
    format="$%.2f"
)
weekend_check = st.sidebar.slider(
    "Weekend Avg Check ($)", 20.0, 60.0, 36.63, step=0.50,
    format="$%.2f"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Program Assumptions")
booster_pct = st.sidebar.slider(
    "Booster Program Effectiveness", 0.0, 2.0, 1.0, step=0.1,
    help="1.0 = base case, 0.0 = no boosters, 1.5 = 50% above base"
)
seasonal_pct = st.sidebar.slider(
    "Seasonal Event Strength", 0.0, 2.0, 1.0, step=0.1,
    help="1.0 = base case (Super Bowl, March Madness, NYE)"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Monte Carlo")
mc_seed = st.sidebar.number_input("Random Seed", value=42, step=1)
mc_sims = st.sidebar.selectbox("Simulations", [1000, 5000, 10000], index=2)


# =============================================================================
# CACHED COMPUTATIONS
# =============================================================================
@st.cache_data
def get_annual_projection(custs, yr, wk_chk, we_chk, booster, seasonal):
    months, annual = model.run_annual_projection(
        custs, year=yr,
        weekday_check=wk_chk, weekend_check=we_chk,
        booster_pct=booster, seasonal_pct=seasonal,
    )
    return months, annual


@st.cache_data
def get_multi_year(custs, years=3, wk_chk=None, we_chk=None, booster=1.0, seasonal=1.0):
    return model.run_multi_year_projection(
        custs, years,
        base_weekday_check=wk_chk,
        base_weekend_check=we_chk,
        booster_pct=booster,
        seasonal_pct=seasonal,
    )


@st.cache_data
def get_monte_carlo(n_sims, seed, base_customers=100, base_wk_chk=None, base_we_chk=None,
                    base_booster=1.0, base_seasonal=1.0):
    return model.run_monte_carlo(
        n_sims, seed,
        base_customers=base_customers,
        base_weekday_check=base_wk_chk,
        base_weekend_check=base_we_chk,
        base_booster_pct=base_booster,
        base_seasonal_pct=base_seasonal,
    )


@st.cache_data
def get_scenario_results():
    results = {}
    for name, params in model.SCENARIOS.items():
        _, ann = model.run_annual_projection(
            params["daily_customers"],
            weekday_check=params["weekday_check"],
            weekend_check=params["weekend_check"],
            cota_events_override=params["cota_events"],
            booster_pct=params.get("booster_pct", 1.0),
            seasonal_pct=params.get("seasonal_pct", 1.0),
        )
        results[name] = ann
    return results


def months_to_df(months):
    """Convert list of monthly result dicts to a pandas DataFrame."""
    rows = []
    for m in months:
        cota = m["cota_bar_uplift"] + m["cota_parking"]
        rows.append({
            "Month": MONTH_NAMES[m["month"] - 1],
            "Gross Revenue": m["total_gross_revenue"],
            "Bar Revenue": m["bar_revenue"],
            "COTA": cota,
            "Event Rentals": m["rental_gross"],
            "LED": m["led_gross"],
            "Food Trucks": m["truck_gross"],
            "Boosters": m["booster_revenue"],
            "Seasonal": m["seasonal_revenue"],
            "NOI": m["noi"],
            "DSCR": m["monthly_dscr"],
            "Labor": m["labor_cost"],
            "CC Fees": m["cc_processing"],
            "Shrinkage": m["shrinkage"],
            "Cash Flow": m["net_cash_flow"],
        })
    return pd.DataFrame(rows)


# =============================================================================
# MAIN CONTENT — TABS
# =============================================================================
st.title("The Cube | Financial Model")
st.caption("13903 FM 812, Del Valle, TX 78617  •  SBA 7(a) Loan: $1,923,698")

tabs = st.tabs([
    "Dashboard",
    "Annual Projection",
    "Sensitivity",
    "Break-Even",
    "Monte Carlo",
    "Scenarios",
    "Multi-Year",
    "Cash Reserve",
    "Waterfall",
    "Lender Summary",
    "📖 Model Overview",
])


# =============================================================================
# TAB 0: DASHBOARD
# =============================================================================
with tabs[0]:
    months, annual = get_annual_projection(
        daily_customers, 1, weekday_check, weekend_check,
        booster_pct, seasonal_pct
    )
    df = months_to_df(months)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual Revenue", fmt_dollar(annual["total_gross"]))
    c2.metric("Annual DSCR", f"{annual['annual_dscr']:.2f}x")
    c3.metric("Free Cash Flow", fmt_dollar(annual["total_net_cash"]))
    c4.metric("Min Monthly DSCR", f"{annual['min_monthly_dscr']:.2f}x")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Revenue Breakdown")
        rev_data = {
            "Stream": ["Bar Ops", "COTA Bar", "COTA Parking", "Rentals",
                        "LED", "Food Trucks", "Boosters", "Seasonal"],
            "Revenue": [annual["total_bar"], annual["total_cota_bar"],
                        annual["total_cota_parking"], annual["total_rentals"],
                        annual["total_led"], annual["total_trucks"],
                        annual["total_boosters"], annual["total_seasonal"]],
        }
        fig_pie = px.pie(
            pd.DataFrame(rev_data), values="Revenue", names="Stream",
            hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Monthly Revenue & DSCR")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["Month"], y=df["Gross Revenue"],
            name="Gross Revenue", marker_color="#4E79A7"
        ))
        fig.add_trace(go.Scatter(
            x=df["Month"], y=df["DSCR"],
            name="DSCR", yaxis="y2",
            mode="lines+markers", marker_color="#E15759",
            line=dict(width=3)
        ))
        fig.add_hline(y=1.25, line_dash="dash", line_color="red",
                      annotation_text="Lender Min (1.25x)", yref="y2")
        fig.update_layout(
            yaxis=dict(title="Revenue ($)", tickformat="$,.0f"),
            yaxis2=dict(title="DSCR", overlaying="y", side="right", tickformat=".2f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# TAB 1: ANNUAL PROJECTION
# =============================================================================
with tabs[1]:
    st.header("Year 1 Annual Projection")
    months, annual = get_annual_projection(
        daily_customers, 1, weekday_check, weekend_check,
        booster_pct, seasonal_pct
    )
    df = months_to_df(months)

    # Stacked bar chart of revenue streams
    stream_cols = ["Bar Revenue", "COTA", "Event Rentals", "LED",
                   "Food Trucks", "Boosters", "Seasonal"]
    fig_stack = go.Figure()
    colors = px.colors.qualitative.Set2
    for i, col in enumerate(stream_cols):
        fig_stack.add_trace(go.Bar(
            x=df["Month"], y=df[col], name=col,
            marker_color=colors[i % len(colors)]
        ))
    fig_stack.update_layout(
        barmode="stack",
        yaxis=dict(title="Revenue ($)", tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # Summary metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue", fmt_dollar(annual["total_gross"]))
    c2.metric("DSCR", f"{annual['annual_dscr']:.2f}x")
    c3.metric("Free Cash Flow", fmt_dollar(annual["total_net_cash"]))
    c4.metric("Total Labor", fmt_dollar(annual["total_labor"]))
    c5.metric("COTA Costs", fmt_dollar(annual["total_cota_cost"]))

    # Revenue stream percentages
    st.subheader("Revenue Streams")
    stream_data = {
        "Stream": ["Daily Bar Ops", "COTA Bar Uplift", "COTA Parking",
                    "Event Rentals", "LED Advertising", "Food Trucks",
                    "Weekday Boosters", "Seasonal Events"],
        "Annual": [annual["total_bar"], annual["total_cota_bar"],
                   annual["total_cota_parking"], annual["total_rentals"],
                   annual["total_led"], annual["total_trucks"],
                   annual["total_boosters"], annual["total_seasonal"]],
    }
    stream_df = pd.DataFrame(stream_data)
    stream_df["% of Total"] = stream_df["Annual"] / annual["total_gross"] * 100
    stream_df["Annual"] = stream_df["Annual"].apply(fmt_dollar)
    stream_df["% of Total"] = stream_df["% of Total"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(stream_df, use_container_width=True, hide_index=True)

    # Monthly detail table
    st.subheader("Monthly Detail")
    display_df = df[["Month", "Gross Revenue", "Bar Revenue", "COTA",
                     "NOI", "Cash Flow", "DSCR"]].copy()
    for col in ["Gross Revenue", "Bar Revenue", "COTA", "NOI", "Cash Flow"]:
        display_df[col] = display_df[col].apply(fmt_dollar)
    display_df["DSCR"] = display_df["DSCR"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 2: SENSITIVITY ANALYSIS
# =============================================================================
with tabs[2]:
    st.header("Sensitivity Analysis")

    # 1. Customer count sensitivity
    st.subheader("1. Daily Customer Count Impact (Year 1)")
    cust_rows = []
    for custs in [60, 70, 80, 90, 100, 113, 130, 150, 175]:
        _, ann = model.run_annual_projection(custs)
        cust_rows.append({
            "Customers/Day": custs,
            "Annual Revenue": ann["total_gross"],
            "Annual NOI": ann["total_noi"],
            "DSCR": ann["annual_dscr"],
            "Free Cash Flow": ann["total_net_cash"],
        })
    cust_df = pd.DataFrame(cust_rows)

    fig_cust = go.Figure()
    fig_cust.add_trace(go.Bar(
        x=cust_df["Customers/Day"], y=cust_df["Free Cash Flow"],
        name="Free Cash Flow", marker_color="#4E79A7"
    ))
    fig_cust.add_trace(go.Scatter(
        x=cust_df["Customers/Day"], y=cust_df["DSCR"],
        name="DSCR", yaxis="y2", mode="lines+markers",
        marker_color="#E15759", line=dict(width=3)
    ))
    fig_cust.add_hline(y=1.25, line_dash="dash", line_color="red",
                       annotation_text="Lender Min", yref="y2")
    fig_cust.add_hline(y=0, line_dash="solid", line_color="gray", yref="y1")
    fig_cust.update_layout(
        yaxis=dict(title="Free Cash Flow ($)", tickformat="$,.0f"),
        yaxis2=dict(title="DSCR", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_cust, use_container_width=True)

    disp = cust_df.copy()
    for col in ["Annual Revenue", "Annual NOI", "Free Cash Flow"]:
        disp[col] = disp[col].apply(fmt_dollar)
    disp["DSCR"] = disp["DSCR"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # 2. Average check sensitivity
    st.subheader("2. Average Check Size Impact (at 100 customers/day)")
    check_rows = []
    for wk, we in [(20, 28), (22, 32), (25, 35), (28, 40), (30, 45), (35, 50)]:
        _, ann = model.run_annual_projection(100, weekday_check=wk, weekend_check=we)
        check_rows.append({
            "Weekday / Weekend": f"${wk} / ${we}",
            "Annual Revenue": ann["total_gross"],
            "DSCR": ann["annual_dscr"],
            "Free Cash Flow": ann["total_net_cash"],
        })
    check_df = pd.DataFrame(check_rows)
    disp2 = check_df.copy()
    for col in ["Annual Revenue", "Free Cash Flow"]:
        disp2[col] = disp2[col].apply(fmt_dollar)
    disp2["DSCR"] = disp2["DSCR"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(disp2, use_container_width=True, hide_index=True)

    # 3. COTA decline stress test
    st.subheader("3. COTA Decline Stress Test (100 customers/day)")
    full_events = []
    for m in range(1, 13):
        for tier in model.COTA_EVENTS_BY_MONTH.get(m, []):
            full_events.append((m, tier))
    decline_rows = []
    for pct in [0, 25, 50, 75, 100]:
        remaining = max(0, int(len(full_events) * (1 - pct / 100)))
        kept = full_events[:remaining]
        override = {m: [] for m in range(1, 13)}
        for month, tier in kept:
            override[month].append(tier)
        _, ann = model.run_annual_projection(100, cota_events_override=override)
        cota_rev = ann["total_cota_bar"] + ann["total_cota_parking"]
        viable = "YES" if ann["annual_dscr"] >= 1.25 else (
            "CAUTION" if ann["annual_dscr"] >= 1.0 else "NO")
        decline_rows.append({
            "COTA Decline": f"{pct}%",
            "COTA Revenue": fmt_dollar(cota_rev),
            "DSCR": f"{ann['annual_dscr']:.2f}x",
            "Viable?": viable,
        })
    st.dataframe(pd.DataFrame(decline_rows), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 3: BREAK-EVEN
# =============================================================================
with tabs[3]:
    st.header("Break-Even Calculator")

    rentals = model.calc_event_rental_revenue()
    led = model.calc_led_revenue()
    trucks = model.calc_food_truck_revenue()
    ancillary = rentals["net"] + led["net"] + trucks["net"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Fixed Costs", fmt_dollar(model.MONTHLY_NUT))
    c2.metric("Ancillary Monthly Income", fmt_dollar(ancillary))
    c3.metric("Net Monthly Gap", fmt_dollar(model.MONTHLY_NUT - ancillary))

    st.subheader("Break-Even Customers by DSCR Target")
    st.caption("Assumes avg seasonality, no COTA events (worst case)")

    targets = [
        ("Break-even", 1.0), ("Lender Min", 1.25),
        ("Comfortable", 1.50), ("Strong", 2.0), ("Excellent", 2.5),
    ]
    be_rows = []
    for label, target in targets:
        lo, hi = 10, 500
        while hi - lo > 1:
            mid = (lo + hi) // 2
            _, ann = model.run_annual_projection(
                mid, cota_events_override={m: [] for m in range(1, 13)}
            )
            if ann["annual_dscr"] >= target:
                hi = mid
            else:
                lo = mid
        _, ann = model.run_annual_projection(
            hi, cota_events_override={m: [] for m in range(1, 13)}
        )
        monthly_rev = ann["total_gross"] / 12
        penetration = (hi * 30.4 / model.LOCAL_HOUSEHOLDS) * 100
        be_rows.append({
            "DSCR Target": f"{label} ({target:.2f}x)",
            "Monthly Revenue": fmt_dollar(monthly_rev),
            "Daily Customers": hi,
            "HH Penetration": f"{penetration:.1f}%",
        })
    st.dataframe(pd.DataFrame(be_rows), use_container_width=True, hide_index=True)

    # Bar chart
    be_df = pd.DataFrame(be_rows)
    fig_be = px.bar(
        be_df, x="DSCR Target", y="Daily Customers",
        color_discrete_sequence=["#4E79A7"],
        text="Daily Customers"
    )
    fig_be.add_hline(y=100, line_dash="dash", line_color="green",
                     annotation_text="Base Case (100)")
    fig_be.update_layout(margin=dict(t=40, b=40))
    st.plotly_chart(fig_be, use_container_width=True)

    st.info(f"Market: {model.LOCAL_HOUSEHOLDS:,} households + "
            f"{model.TESLA_EMPLOYEES:,} Tesla employees + "
            f"{model.ANNUAL_COTA_VISITORS:,} annual COTA visitors")


# =============================================================================
# TAB 4: MONTE CARLO
# =============================================================================
with tabs[4]:
    st.header(f"Monte Carlo Simulation ({mc_sims:,} scenarios)")

    # Suppress print output from run_monte_carlo
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    mc_results = get_monte_carlo(mc_sims, mc_seed, daily_customers, weekday_check, weekend_check,
                                 booster_pct, seasonal_pct)
    sys.stdout = old_stdout

    revenues = sorted([r["revenue"] for r in mc_results])
    dscrs = sorted([r["dscr"] for r in mc_results])
    cfs = sorted([r["cash_flow"] for r in mc_results])

    def percentile(data, pct):
        idx = int(len(data) * pct / 100)
        return data[min(idx, len(data) - 1)]

    # Probability KPIs
    st.subheader("Probability Analysis")
    p1, p2, p3, p4, p5 = st.columns(5)
    pct_1 = sum(1 for d in dscrs if d >= 1.0) / len(dscrs) * 100
    pct_125 = sum(1 for d in dscrs if d >= 1.25) / len(dscrs) * 100
    pct_15 = sum(1 for d in dscrs if d >= 1.5) / len(dscrs) * 100
    pct_2 = sum(1 for d in dscrs if d >= 2.0) / len(dscrs) * 100
    pct_pos = sum(1 for c in cfs if c > 0) / len(cfs) * 100
    p1.metric("P(DSCR >= 1.0x)", f"{pct_1:.1f}%")
    p2.metric("P(DSCR >= 1.25x)", f"{pct_125:.1f}%")
    p3.metric("P(DSCR >= 1.5x)", f"{pct_15:.1f}%")
    p4.metric("P(DSCR >= 2.0x)", f"{pct_2:.1f}%")
    p5.metric("P(CF > $0)", f"{pct_pos:.1f}%")

    # Percentile table
    st.subheader("Distribution Summary")
    perc_data = {
        "Metric": ["Annual Revenue", "Annual DSCR", "Free Cash Flow"],
        "P5": [fmt_dollar(percentile(revenues, 5)),
               f"{percentile(dscrs, 5):.2f}x",
               fmt_dollar(percentile(cfs, 5))],
        "P25": [fmt_dollar(percentile(revenues, 25)),
                f"{percentile(dscrs, 25):.2f}x",
                fmt_dollar(percentile(cfs, 25))],
        "Median": [fmt_dollar(percentile(revenues, 50)),
                   f"{percentile(dscrs, 50):.2f}x",
                   fmt_dollar(percentile(cfs, 50))],
        "P75": [fmt_dollar(percentile(revenues, 75)),
                f"{percentile(dscrs, 75):.2f}x",
                fmt_dollar(percentile(cfs, 75))],
        "P95": [fmt_dollar(percentile(revenues, 95)),
                f"{percentile(dscrs, 95):.2f}x",
                fmt_dollar(percentile(cfs, 95))],
    }
    st.dataframe(pd.DataFrame(perc_data), use_container_width=True, hide_index=True)

    # Histograms
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("DSCR Distribution")
        fig_dscr = px.histogram(
            x=dscrs, nbins=60, labels={"x": "Annual DSCR"},
            color_discrete_sequence=["#4E79A7"]
        )
        fig_dscr.add_vline(x=1.25, line_dash="dash", line_color="red",
                           annotation_text="Lender Min")
        fig_dscr.add_vline(x=1.0, line_dash="dash", line_color="orange",
                           annotation_text="Break-even")
        fig_dscr.update_layout(margin=dict(t=40, b=40), showlegend=False)
        st.plotly_chart(fig_dscr, use_container_width=True)

    with col_r:
        st.subheader("Free Cash Flow Distribution")
        fig_cf = px.histogram(
            x=cfs, nbins=60, labels={"x": "Free Cash Flow ($)"},
            color_discrete_sequence=["#59A14F"]
        )
        fig_cf.add_vline(x=0, line_dash="dash", line_color="red",
                         annotation_text="Break-even")
        fig_cf.update_layout(margin=dict(t=40, b=40), showlegend=False,
                             xaxis_tickformat="$,.0f")
        st.plotly_chart(fig_cf, use_container_width=True)

    # Randomized variables note
    st.caption(
        "Randomized: Daily customers (40-200), weekday check ($18-$35), "
        "weekend check ($25-$50), COTA events (8-15/yr), boosters (30%-180%), "
        "seasonal (40%-150%), event rentals (Y1 ramp +/- 1), "
        "food trucks (Y1 ramp +/- 1), LED (Y1 ramp +/- $300). "
        "COGS held constant at 30%."
    )


# =============================================================================
# TAB 5: SCENARIO COMPARISON
# =============================================================================
with tabs[5]:
    st.header("Scenario Comparison")

    scenario_results = get_scenario_results()

    # Build comparison DataFrame
    rows = []
    for name in model.SCENARIOS:
        ann = scenario_results[name]
        rows.append({
            "Scenario": name,
            "Customers/Day": model.SCENARIOS[name]["daily_customers"],
            "Annual Revenue": ann["total_gross"],
            "Free Cash Flow": ann["total_net_cash"],
            "DSCR": ann["annual_dscr"],
            "Min Month DSCR": ann["min_monthly_dscr"],
            "Bar Revenue": ann["total_bar"],
            "COTA Revenue": ann["total_cota_bar"] + ann["total_cota_parking"],
        })
    sc_df = pd.DataFrame(rows)

    # Grouped bar chart — Revenue + Cash Flow
    fig_sc = go.Figure()
    fig_sc.add_trace(go.Bar(
        x=sc_df["Scenario"], y=sc_df["Annual Revenue"],
        name="Annual Revenue", marker_color="#4E79A7"
    ))
    fig_sc.add_trace(go.Bar(
        x=sc_df["Scenario"], y=sc_df["Free Cash Flow"],
        name="Free Cash Flow", marker_color="#59A14F"
    ))
    fig_sc.add_trace(go.Scatter(
        x=sc_df["Scenario"], y=sc_df["DSCR"],
        name="DSCR", yaxis="y2", mode="lines+markers",
        marker_color="#E15759", line=dict(width=3),
    ))
    fig_sc.add_hline(y=1.25, line_dash="dash", line_color="red",
                     annotation_text="Lender Min", yref="y2")
    fig_sc.update_layout(
        barmode="group",
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        yaxis2=dict(title="DSCR", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    # Table
    disp_sc = sc_df.copy()
    for col in ["Annual Revenue", "Free Cash Flow", "Bar Revenue", "COTA Revenue"]:
        disp_sc[col] = disp_sc[col].apply(fmt_dollar)
    disp_sc["DSCR"] = disp_sc["DSCR"].apply(lambda x: f"{x:.2f}x")
    disp_sc["Min Month DSCR"] = disp_sc["Min Month DSCR"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(disp_sc, use_container_width=True, hide_index=True)

    # Descriptions
    st.subheader("Scenario Definitions")
    for name, params in model.SCENARIOS.items():
        st.markdown(f"**{name}:** {params['desc']}")


# =============================================================================
# TAB 6: MULTI-YEAR PROJECTION
# =============================================================================
with tabs[6]:
    st.header("Multi-Year Projection (Years 1-3)")

    all_years = get_multi_year(daily_customers, wk_chk=weekday_check, we_chk=weekend_check,
                                booster=booster_pct, seasonal=seasonal_pct)

    # Build summary rows
    my_rows = []
    for yr, months_data, ann in all_years:
        my_rows.append({
            "Year": f"Year {yr}",
            "Customers/Day": int(100 * ann["growth_mult"]),
            "Annual Revenue": ann["total_gross"],
            "Bar Ops": ann["total_bar"],
            "COTA Events": ann["total_cota_bar"] + ann["total_cota_parking"],
            "Event Rentals": ann["total_rentals"],
            "LED": ann["total_led"],
            "Food Trucks": ann["total_trucks"],
            "Boosters + Seasonal": ann["total_boosters"] + ann["total_seasonal"],
            "Cost Inflation": ann["cost_inflation_adj"],
            "Free Cash Flow": ann["total_net_cash"],
            "DSCR": ann["annual_dscr"],
        })
    my_df = pd.DataFrame(my_rows)

    # Grouped bar chart
    fig_my = go.Figure()
    fig_my.add_trace(go.Bar(
        x=my_df["Year"], y=my_df["Annual Revenue"],
        name="Revenue", marker_color="#4E79A7"
    ))
    fig_my.add_trace(go.Bar(
        x=my_df["Year"], y=my_df["Free Cash Flow"],
        name="Free Cash Flow", marker_color="#59A14F"
    ))
    fig_my.add_trace(go.Scatter(
        x=my_df["Year"], y=my_df["DSCR"],
        name="DSCR", yaxis="y2", mode="lines+markers",
        marker_color="#E15759", line=dict(width=3, dash="dot"),
        marker=dict(size=12)
    ))
    fig_my.update_layout(
        barmode="group",
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        yaxis2=dict(title="DSCR", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_my, use_container_width=True)

    # Table
    disp_my = my_df.copy()
    dollar_cols = ["Annual Revenue", "Bar Ops", "COTA Events", "Event Rentals",
                   "LED", "Food Trucks", "Boosters + Seasonal",
                   "Cost Inflation", "Free Cash Flow"]
    for col in dollar_cols:
        disp_my[col] = disp_my[col].apply(fmt_dollar)
    disp_my["DSCR"] = disp_my["DSCR"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(disp_my, use_container_width=True, hide_index=True)

    st.subheader("Assumptions")
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue Growth", f"{model.ANNUAL_GROWTH_RATE:.0%}/year")
    c2.metric("Cost Inflation", f"{model.ANNUAL_COST_INFLATION:.0%}/year")
    c3.metric("Debt Service", f"${model.MONTHLY_DEBT_SERVICE:,.0f}/mo (fixed)")
    st.caption(
        "Year 1: 9-month ramp, Y1 truck/LED/rental ramps. "
        "Year 2+: Steady state (3 trucks, 5 LED contracts, 3 rentals/mo @ $4K)."
    )


# =============================================================================
# TAB 7: CASH RESERVE TRACKER
# =============================================================================
with tabs[7]:
    st.header("Cash Reserve Tracker")

    all_years = get_multi_year(daily_customers, wk_chk=weekday_check, we_chk=weekend_check,
                                booster=booster_pct, seasonal=seasonal_pct)

    balance = model.OPENING_CASH_RESERVE
    min_balance = balance
    min_month_label = "Month 1"
    months_negative = 0
    cumulative_cf = 0
    break_even_month = None

    tracker_rows = []
    for yr, months_data, ann in all_years:
        for m in months_data:
            cf = m["net_cash_flow"]
            if yr > 1:
                cost_mult = (1 + model.ANNUAL_COST_INFLATION) ** (yr - 1)
                base_non_debt = model.MONTHLY_NUT - model.FIXED_COSTS["debt_service"]
                cf -= base_non_debt * (cost_mult - 1)

            cumulative_cf += cf
            balance += cf
            month_num = (yr - 1) * 12 + m["month"]
            label = f"Y{yr} {MONTH_NAMES[m['month'] - 1]}"

            if balance < min_balance:
                min_balance = balance
                min_month_label = label

            if cf < 0:
                months_negative += 1

            if break_even_month is None and cumulative_cf > 0:
                break_even_month = (month_num, label)

            tracker_rows.append({
                "Month #": month_num,
                "Period": label,
                "Monthly CF": cf,
                "Cumulative CF": cumulative_cf,
                "Cash Balance": balance,
            })

    tr_df = pd.DataFrame(tracker_rows)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Opening Reserve", fmt_dollar(model.OPENING_CASH_RESERVE))
    c2.metric("Lowest Balance", fmt_dollar(min_balance),
              delta=min_month_label, delta_color="off")
    c3.metric("Months Negative CF", str(months_negative))
    if break_even_month:
        c4.metric("Cumulative Break-Even", f"Month {break_even_month[0]}",
                  delta=break_even_month[1], delta_color="off")
    else:
        c4.metric("Cumulative Break-Even", "Not reached")

    if min_balance > 0:
        st.success(f"Cash reserve never goes negative. Minimum cushion: {fmt_dollar(min_balance)}")
    else:
        st.error(f"Cash reserve goes NEGATIVE. Shortfall: {fmt_dollar(abs(min_balance))}")

    # Line chart
    fig_cr = go.Figure()
    fig_cr.add_trace(go.Scatter(
        x=tr_df["Period"], y=tr_df["Cash Balance"],
        name="Cash Balance", fill="tozeroy",
        line=dict(color="#4E79A7", width=2),
        fillcolor="rgba(78, 121, 167, 0.2)"
    ))
    fig_cr.add_trace(go.Bar(
        x=tr_df["Period"], y=tr_df["Monthly CF"],
        name="Monthly Cash Flow", marker_color=[
            "#59A14F" if v >= 0 else "#E15759" for v in tr_df["Monthly CF"]
        ],
        opacity=0.6,
    ))
    fig_cr.add_hline(y=0, line_color="gray")
    fig_cr.update_layout(
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_cr, use_container_width=True)

    # Detail table
    st.subheader("Monthly Detail")
    disp_tr = tr_df.copy()
    for col in ["Monthly CF", "Cumulative CF", "Cash Balance"]:
        disp_tr[col] = disp_tr[col].apply(fmt_dollar)
    st.dataframe(disp_tr, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 8: CASH FLOW WATERFALL
# =============================================================================
with tabs[8]:
    st.header("Year 1 Cash Flow Waterfall")

    months, annual = get_annual_projection(
        daily_customers, 1, weekday_check, weekend_check,
        booster_pct, seasonal_pct
    )

    gross = annual["total_gross"]
    bar_like = (annual["total_bar"] + annual["total_cota_bar"]
                + annual["total_boosters"] + annual["total_seasonal"])
    cogs = bar_like * model.COGS_RATE
    grt = bar_like * model.GRT_RATE
    cc = annual["total_cc_processing"]
    shrinkage = annual["total_shrinkage"]
    cota_cost = annual["total_cota_cost"]
    labor = annual["total_labor"]
    fixed_ex = (model.MONTHLY_NUT - model.FIXED_COSTS["base_labor_5_staff"]
                - model.FIXED_COSTS["debt_service"]) * 12
    debt = model.ANNUAL_DEBT_SERVICE
    free_cf = gross - cogs - grt - cc - shrinkage - cota_cost - labor - fixed_ex - debt

    # Plotly waterfall
    labels = ["Gross Revenue", "COGS (30%)", "TX GRT (6.7%)", "CC Processing",
              "Shrinkage", "COTA Costs", "Labor", "Fixed Costs", "Debt Service",
              "Free Cash Flow"]
    values = [gross, -cogs, -grt, -cc, -shrinkage, -cota_cost,
              -labor, -fixed_ex, -debt, 0]  # last is total
    measures = ["absolute"] + ["relative"] * 8 + ["total"]

    fig_wf = go.Figure(go.Waterfall(
        x=labels, y=values, measure=measures,
        connector={"line": {"color": "rgba(0,0,0,0.3)", "width": 1}},
        increasing={"marker": {"color": "#4E79A7"}},
        decreasing={"marker": {"color": "#E15759"}},
        totals={"marker": {"color": "#59A14F" if free_cf >= 0 else "#E15759"}},
        textposition="outside",
        text=[fmt_dollar(abs(v)) if v != 0 else fmt_dollar(free_cf) for v in values],
    ))
    fig_wf.update_layout(
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        margin=dict(t=40, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    # Margin analysis
    st.subheader("Margin Analysis")
    total_costs = cogs + grt + cc + shrinkage + cota_cost + labor + fixed_ex + debt
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Margin", f"{(1 - model.COGS_RATE - model.GRT_RATE) * 100:.1f}%")
    c2.metric("Total Cost Ratio", f"{total_costs / gross * 100:.1f}%")
    c3.metric("Free CF Margin", f"{free_cf / gross * 100:.1f}%")
    c4.metric("Free CF / Customer / Day", fmt_dollar(free_cf / 365))

    # Detailed breakdown table
    st.subheader("Cost Layer Detail")
    wf_rows = [
        {"Layer": "Gross Revenue", "Amount": fmt_dollar(gross), "% of Revenue": "100.0%"},
        {"Layer": "COGS (30%)", "Amount": f"({fmt_dollar(cogs)})", "% of Revenue": fmt_pct(cogs/gross*100)},
        {"Layer": "TX GRT (6.7%)", "Amount": f"({fmt_dollar(grt)})", "% of Revenue": fmt_pct(grt/gross*100)},
        {"Layer": "CC Processing", "Amount": f"({fmt_dollar(cc)})", "% of Revenue": fmt_pct(cc/gross*100)},
        {"Layer": "Shrinkage", "Amount": f"({fmt_dollar(shrinkage)})", "% of Revenue": fmt_pct(shrinkage/gross*100)},
        {"Layer": "COTA Inc. Costs", "Amount": f"({fmt_dollar(cota_cost)})", "% of Revenue": fmt_pct(cota_cost/gross*100)},
        {"Layer": "Labor (scaled)", "Amount": f"({fmt_dollar(labor)})", "% of Revenue": fmt_pct(labor/gross*100)},
        {"Layer": "Fixed Costs", "Amount": f"({fmt_dollar(fixed_ex)})", "% of Revenue": fmt_pct(fixed_ex/gross*100)},
        {"Layer": "Debt Service", "Amount": f"({fmt_dollar(debt)})", "% of Revenue": fmt_pct(debt/gross*100)},
        {"Layer": "FREE CASH FLOW", "Amount": fmt_dollar(free_cf), "% of Revenue": fmt_pct(free_cf/gross*100)},
    ]
    st.dataframe(pd.DataFrame(wf_rows), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 9: LENDER SUMMARY
# =============================================================================
with tabs[9]:
    st.header("Lender-Ready Summary")
    st.subheader("The Cube | Del Valle Sports Bar & Event Center")
    st.caption("SBA 7(a) Loan Application Support")

    # Loan Terms
    st.markdown("---")
    st.subheader("Loan Terms")
    lt1, lt2, lt3, lt4 = st.columns(4)
    lt1.metric("Loan Amount", fmt_dollar(model.TOTAL_LOAN))
    lt2.metric("Interest Rate", f"{model.INTEREST_RATE:.2%}")
    lt3.metric("Term", "25 years")
    lt4.metric("Monthly P&I", f"${model.MONTHLY_DEBT_SERVICE:,.2f}")

    lt5, lt6, lt7 = st.columns(3)
    lt5.metric("Annual Debt Service", fmt_dollar(model.ANNUAL_DEBT_SERVICE))
    lt6.metric("Post-Construction Value", fmt_dollar(model.POST_CONSTRUCTION_VALUE))
    lt7.metric("LTV", f"{model.LTV:.0%}")

    # Use of Funds
    st.markdown("---")
    st.subheader("Use of Funds")
    uses = [
        ("Building construction (5K sqft)", 575_000),
        ("Outdoor area build", 115_000),
        ("Septic & land prep", 105_000),
        ("Parking lot (450 spaces)", 85_000),
        ("GC + ops consultant fees", 118_800),
        ("Startup costs (FF&E, LED, POS)", 568_000),
        ("Contingency + operating runway", 186_000),
        ("Interest during build + ramp", 170_898),
    ]
    use_df = pd.DataFrame(uses, columns=["Item", "Amount"])
    use_df["Amount"] = use_df["Amount"].apply(fmt_dollar)
    st.dataframe(use_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total: {fmt_dollar(sum(a for _, a in uses))}**")

    # Collateral
    st.markdown("---")
    st.subheader("Collateral")
    coll = [
        ("Land (4.5 acres)", 1_200_000),
        ("New-build (5,000 sqft)", 575_000),
        ("Sewage infrastructure", 350_000),
        ("Improvements & FF&E", 375_000),
    ]
    coll_df = pd.DataFrame(coll, columns=["Asset", "Value"])
    coll_df["Value"] = coll_df["Value"].apply(fmt_dollar)
    st.dataframe(coll_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total Collateral: {fmt_dollar(model.POST_CONSTRUCTION_VALUE)}**")

    # Monthly Fixed Expenses
    st.markdown("---")
    st.subheader("Monthly Fixed Expenses (The Nut)")
    nut_rows = []
    for label, amt in model.FIXED_COSTS.items():
        nut_rows.append({
            "Expense": label.replace("_", " ").title(),
            "Monthly": fmt_dollar(amt),
        })
    nut_df = pd.DataFrame(nut_rows)
    st.dataframe(nut_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total Monthly Nut: {fmt_dollar(model.MONTHLY_NUT)}** | "
                f"**Annual: {fmt_dollar(model.MONTHLY_NUT * 12)}**")

    # Year 1 Performance
    st.markdown("---")
    st.subheader("Projected Performance (Year 1)")

    cons_cota = None  # full calendar
    _, conservative = model.run_annual_projection(
        90, weekday_check=25.71, weekend_check=36.63,
        booster_pct=0.5, seasonal_pct=0.75
    )
    _, base = model.run_annual_projection(100)

    perf_l, perf_r = st.columns(2)
    with perf_l:
        st.markdown("**Conservative** (90 custs, 50% boosters)")
        st.metric("Revenue", fmt_dollar(conservative["total_gross"]))
        st.metric("Free Cash Flow", fmt_dollar(conservative["total_net_cash"]))
        st.metric("DSCR", f"{conservative['annual_dscr']:.2f}x")
    with perf_r:
        st.markdown("**Base Case** (100 custs, full boosters)")
        st.metric("Revenue", fmt_dollar(base["total_gross"]))
        st.metric("Free Cash Flow", fmt_dollar(base["total_net_cash"]))
        st.metric("DSCR", f"{base['annual_dscr']:.2f}x")

    # Multi-year trajectory
    st.markdown("---")
    st.subheader("Projected Trajectory (Base Case)")
    all_years = get_multi_year(100)
    traj_rows = []
    for yr, _, ann in all_years:
        traj_rows.append({
            "Year": f"Year {yr}",
            "Annual Revenue": fmt_dollar(ann["total_gross"]),
            "Free Cash Flow": fmt_dollar(ann["total_net_cash"]),
            "DSCR": f"{ann['annual_dscr']:.2f}x",
        })
    st.dataframe(pd.DataFrame(traj_rows), use_container_width=True, hide_index=True)

    # Revenue Streams
    st.markdown("---")
    st.subheader("Revenue Streams (Base Case Year 1)")
    rev_rows = [
        ("Daily Bar Operations", base["total_bar"]),
        ("COTA Events (bar + parking)", base["total_cota_bar"] + base["total_cota_parking"]),
        ("Private Event Rentals", base["total_rentals"]),
        ("LED Advertising", base["total_led"]),
        ("Food Truck Partnerships", base["total_trucks"]),
        ("Weekday Booster Programs", base["total_boosters"]),
        ("Seasonal Events", base["total_seasonal"]),
    ]
    rev_df = pd.DataFrame(rev_rows, columns=["Stream", "Annual"])
    rev_df["% of Total"] = rev_df["Annual"] / base["total_gross"] * 100
    rev_df["Annual"] = rev_df["Annual"].apply(fmt_dollar)
    rev_df["% of Total"] = rev_df["% of Total"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(rev_df, use_container_width=True, hide_index=True)

    # Risk Mitigants
    st.markdown("---")
    st.subheader("Risk Mitigants")
    mitigants = [
        "Zero direct competition within 10-mile radius",
        "3-5 year first-mover advantage (below chain threshold)",
        "Beverage-only model: $0 kitchen OpEx, 28-30% COGS",
        "4.5 acres with on-site septic = infrastructure moat",
        "Outside COTA PUD = no square-footage caps on liquor",
        f"${580_000:,} post-construction equity cushion",
        "800 sqft LED wall = premium ad revenue asset",
        "Weekday booster programs add $12K-$26K/mo incremental",
    ]
    for m in mitigants:
        st.markdown(f"- {m}")


# =============================================================================
# TAB 10: MODEL OVERVIEW
# =============================================================================
with tabs[10]:
    st.header("📊 How The Model Works")
    st.caption("Source: The Cube — Financial Model Overview (Notion) · February 27, 2026")

    st.markdown(
        """
        The financial model is a **full-stack Python simulation** covering 8 revenue streams,
        dynamic labor scaling, tiered COTA event economics, a 9-month Year 1 ramp-up,
        Monte Carlo simulation (10,000 scenarios), and multi-year projections.
        It represents the most granular and executable version of The Cube's financial analysis.
        """
    )

    st.markdown("---")

    # ── Section 1: Revenue Streams ──────────────────────────────────────────
    with st.expander("1. Revenue Streams", expanded=True):
        streams = pd.DataFrame([
            ("1. Daily Bar Ops",     "Happy hour + prime time (3pm–close weekdays, all-day weekends)",    "~$56K–$90K / mo",      "63.3% after COGS + GRT"),
            ("2. COTA Parking",      "450 spaces at $25–$80/space across 12 events/yr",                  "Event months only",    "~95%"),
            ("3. COTA Bar Uplift",   "Incremental bar sales during COTA events",                          "Event months only",    "63.3% (same as bar)"),
            ("4. Event Rentals",     "Private bookings at $2,500–$4,000 avg",                             "$12,000 (3/mo)",       "85%"),
            ("5. LED Advertising",   "800 sqft LED wall, 5 contracts @ $500/mo",                          "$2,500",               "90%"),
            ("6. Food Trucks",       "3 trucks: pad rent ($900) + 12% revenue share",                     "$8,100",               "100% (no kitchen OpEx)"),
            ("7. Weekday Boosters",  "Tesla partnership, trivia, industry night, food truck combos",       "$9,300",               "63.3% (bar-like)"),
            ("8. Seasonal Events",   "Super Bowl, March Madness, NYE",                                     "~$47K/yr total",      "63.3% (bar-like)"),
        ], columns=["Stream", "Description", "Steady-State Monthly", "Margin Profile"])
        st.dataframe(streams, use_container_width=True, hide_index=True)

    # ── Section 2: Core Assumptions ─────────────────────────────────────────
    with st.expander("2. Core Assumptions"):
        col_loan, col_nut = st.columns(2)

        with col_loan:
            st.subheader("Loan & Debt")
            loan_df = pd.DataFrame([
                ("Total SBA 7(a) Loan",      "$1,923,698"),
                ("Interest Rate",             "9.75%"),
                ("Term",                      "25 years"),
                ("Monthly Debt Service",      "$17,142.79"),
                ("Annual Debt Service",       "$205,713"),
                ("Post-Construction Value",   "$2,500,000"),
                ("LTV",                       "77%"),
            ], columns=["Parameter", "Value"])
            st.dataframe(loan_df, use_container_width=True, hide_index=True)

        with col_nut:
            st.subheader('Monthly Fixed Costs ("The Nut")')
            nut_df = pd.DataFrame([
                ("Debt Service",         "$17,143"),
                ("Base Labor (5 staff)", "$14,950"),
                ("Property Tax",         "$4,500"),
                ("Insurance",            "$3,000"),
                ("Maintenance Reserve",  "$2,500"),
                ("Utilities",            "$2,200"),
                ("Marketing",            "$1,500"),
                ("Cable/Sports Packages","$1,500"),
                ("POS/Tech Subscriptions","$1,000"),
                ("Miscellaneous",        "$1,000"),
                ("Licenses/Permits",     "$500"),
                ("**Total Monthly Nut**","**$49,793**"),
                ("**Annual Fixed Costs**","**$597,516**"),
            ], columns=["Line Item", "Monthly Cost"])
            st.dataframe(nut_df, use_container_width=True, hide_index=True)

        st.info(
            "**Additional Variable Costs** — Credit card processing: 2.8% on 85% of bar-like revenue (~2.38% effective). "
            "Shrinkage: 2.5% of beverage COGS (breakage + theft). Dynamic labor scaling: staff increases from 5→10 as daily "
            "customers grow past 100. COTA incremental costs: $1K–$50K per event depending on tier."
        )

    # ── Section 3: Year 1 Ramp-Up Model ─────────────────────────────────────
    with st.expander("3. Year 1 Ramp-Up Model"):
        st.markdown(
            "The model applies a **9-month ramp** from 30% to 100% of steady-state capacity, "
            "reflecting the reality that a new bar in a rural area with no existing foot traffic "
            "takes time to build awareness."
        )
        ramp_df = pd.DataFrame([
            (1,     "30%",  "~30",  "Grand opening buzz, limited awareness"),
            (2,     "35%",  "~35",  "Post-opening dip, building regulars"),
            (3,     "42%",  "~42",  "March Madness helps"),
            (4,     "50%",  "~50",  "MotoGP month, still early"),
            (5,     "58%",  "~58",  "Word-of-mouth building"),
            (6,     "65%",  "~65",  "Summer gap partially offsets growth"),
            (7,     "72%",  "~72",  "Boosters launch, food trucks settled"),
            (8,     "80%",  "~80",  "NFL preseason, approaching steady state"),
            (9,     "90%",  "~90",  "NFL + college football pull"),
            ("10–12","100%","~100", "✅ Steady state reached"),
        ], columns=["Month", "Capacity %", "Eff. Daily Customers", "Key Driver"])
        st.dataframe(ramp_df, use_container_width=True, hide_index=True)

        st.markdown("**Ancillary Stream Year 1 Ramps**")
        st.markdown(
            "- **Event Rentals:** Zero bookings months 1–3, growing from 1/mo to 3/mo by month 10. "
            "Avg booking starts at $2,500 (small events) and grows to $3,500 (corporate) by month 12.\n"
            "- **LED Advertising:** 1 contract in months 1–2, scaling to 5 contracts by month 10.\n"
            "- **Food Trucks:** 1 anchor truck months 1–3, growing to 3 by month 11.\n"
            "- **Weekday Boosters:** Don't launch until month 7, reach full base by month 12."
        )

    # ── Section 4: Seasonality ───────────────────────────────────────────────
    with st.expander("4. Seasonality Model"):
        season_df = pd.DataFrame([
            ("Jan", "0.75", "Post-holiday lull, NFL playoffs"),
            ("Feb", "0.60", "🔴 Quietest month (Super Bowl spike but low volume)"),
            ("Mar", "0.80", "March Madness, F1 season start, MLS"),
            ("Apr", "0.90", "MLB + NBA/NHL stretch run"),
            ("May", "0.85", "MotoGP at COTA, NBA/NHL playoffs"),
            ("Jun", "0.70", "Summer gap begins"),
            ("Jul", "0.65", "Deep summer gap, MLB carries"),
            ("Aug", "0.70", "NFL preseason, college football hype"),
            ("Sep", "0.85", "NFL starts, college football peak"),
            ("Oct", "1.00", "🟢 PEAK — 'Sports Equinox' + F1 USGP"),
            ("Nov", "0.95", "NFL + college + NBA/NHL full swing"),
            ("Dec", "0.80", "Bowl season, holidays slow mid-month"),
        ], columns=["Month", "Multiplier", "Key Sports Drivers"])

        col_chart, col_table = st.columns([3, 2])
        with col_chart:
            season_plot_df = pd.DataFrame({
                "Month": ["Jan","Feb","Mar","Apr","May","Jun",
                          "Jul","Aug","Sep","Oct","Nov","Dec"],
                "Multiplier": [0.75,0.60,0.80,0.90,0.85,0.70,
                               0.65,0.70,0.85,1.00,0.95,0.80],
            })
            fig_season = px.bar(
                season_plot_df, x="Month", y="Multiplier",
                color="Multiplier",
                color_continuous_scale=["#E15759","#F28E2B","#59A14F"],
                range_color=[0.5, 1.0],
            )
            fig_season.add_hline(y=1.0, line_dash="dash", line_color="gray",
                                  annotation_text="Steady State")
            fig_season.update_layout(
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(t=20, b=20),
                yaxis=dict(title="Seasonality Multiplier", range=[0, 1.15]),
            )
            st.plotly_chart(fig_season, use_container_width=True)
        with col_table:
            st.dataframe(season_df, use_container_width=True, hide_index=True)

    # ── Section 5: COTA Event Tier Economics ─────────────────────────────────
    with st.expander("5. COTA Event Tier Economics"):
        cota_df = pd.DataFrame([
            ("🔴 F1 USGP",      "$80",  "100%",  3, "$60,000",  "$50,000",  "~$168,000"),
            ("🟠 MotoGP",       "$55",  "93%",   3, "$27,000",  "$38,000",  "~$96,000"),
            ("🟠 NASCAR",       "$50",  "80%",   2, "$15,000",  "$30,000",  "~$51,000"),
            ("🟡 WEC 6 Hours",  "$35",  "70%",   2, "$9,000",   "$18,000",  "~$31,000"),
            ("🟡 GT/TransAm",   "$25",  "35%",   2, "$4,500",   "$8,000",   "~$12,400"),
            ("🔵 Concert",      "$30",  "55%",   1, "$3,000",   "$5,000",   "~$10,400"),
            ("🔵 Festival",     "$30",  "45%",   2, "$2,500",   "$6,000",   "~$14,600"),
            ("⚪ Track Day",    "$0",   "10%",   1, "$1,500",   "$1,000",   "~$1,500"),
        ], columns=["Tier / Event", "Parking $/Space", "Lot Occupancy",
                    "Days", "Bar Uplift", "Inc. Cost", "Est. Gross"])
        st.dataframe(cota_df, use_container_width=True, hide_index=True)
        st.caption(
            "Base case calendar: 12 events/yr — 1×F1, 1×MotoGP, 1×NASCAR, 1×WEC, "
            "2×GT/TransAm, 4×Concerts, 2×Festivals"
        )

    # ── Section 6: Danger Zone & Break-Even ──────────────────────────────────
    with st.expander("6. Danger Zone & Break-Even Thresholds"):
        be_thr = pd.DataFrame([
            ("Break-Even (Cash Flow = $0)",         "~$69,972",  "~80",   "1.00x"),
            ("⚠️ Danger Zone Floor (Lender Min)",   "~$76,744",  "~88",   "1.25x"),
            ("✅ Comfortable Operations",            "~$99,362",  "~113",  "2.09x"),
        ], columns=["Threshold", "Monthly Revenue", "Daily Customers", "DSCR"])
        st.dataframe(be_thr, use_container_width=True, hide_index=True)
        st.info(
            "**Key insight:** Break-even analysis runs with zero COTA events, zero boosters, and zero seasonal "
            "events — a pure 'can the bar survive on its own' test. At 100 customers/day with the full revenue "
            "mix, the base case DSCR is significantly above 1.25x."
        )

    # ── Section 7: Sensitivity ───────────────────────────────────────────────
    with st.expander("7. Sensitivity Analysis Summary"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**Customer Count (Strongest Lever)**")
            st.markdown(
                "- **60/day:** Revenue drops dramatically, DSCR likely below 1.0x\n"
                "- **80/day:** Near break-even territory\n"
                "- **100/day (base):** Healthy DSCR above lender minimum\n"
                "- **130+/day:** Strong free cash flow, DSCR well above 2.0x"
            )
            st.markdown("**COTA Event Mix**")
            st.markdown(
                "- **No COTA events:** Business must survive on bar ops alone — tight but possible at 100+ customers/day\n"
                "- **Big 3 only (F1+MotoGP+NASCAR):** Captures ~65–75% of total COTA revenue\n"
                "- **Full 12 events (base case):** $372K–$581K annual COTA contribution"
            )
        with col_s2:
            st.markdown("**Average Check Size**")
            st.markdown(
                "- Weekday check dropping from $25.71 to $20 significantly compresses margins\n"
                "- Weekend check is the bigger lever — moving from $36.63 to $45+ creates substantial upside"
            )
            st.markdown("**COTA Decline Stress Test**")
            st.markdown(
                "- **50% COTA decline:** DSCR remains above lender minimum — the business survives\n"
                "- **75% COTA decline:** Begins approaching danger zone depending on bar performance\n"
                "- **100% COTA loss:** Viable only if daily bar customers exceed ~110/day consistently"
            )

    # ── Section 8: Monte Carlo ───────────────────────────────────────────────
    with st.expander("8. Monte Carlo Simulation (10,000 Scenarios)"):
        st.markdown(
            "The model randomizes **9 variables simultaneously** across 10,000 Year 1 simulations. "
            "COGS is held constant at 30% per the beverage-only model's tight pour-cost controls."
        )
        mc_inputs = pd.DataFrame([
            ("Daily customers",    "40–200",      "100",       "std 20"),
            ("Weekday check",      "$18–$35",     "$25.71",    "—"),
            ("Weekend check",      "$25–$50",     "$36.63",    "—"),
            ("COTA events/yr",     "8–15",        "12",        "Big 4 fixed, variable concerts/festivals"),
            ("Booster programs",   "30%–180%",    "100%",      "of base"),
            ("Seasonal events",    "40%–150%",    "100%",      "of base"),
            ("Event rentals",      "0–4/mo",      "Y1 ramp",   "± 1 booking"),
            ("Food trucks",        "1–3 active",  "Y1 ramp",   "± 1 truck"),
            ("LED advertising",    "$500–$2,500", "Y1 ramp",   "± $300/mo"),
        ], columns=["Variable", "Range", "Base / Mean", "Notes"])
        st.dataframe(mc_inputs, use_container_width=True, hide_index=True)
        st.success(
            "**Key finding:** The Cube's diversified revenue model and low fixed-cost structure make it "
            "resilient across a wide range of operating conditions. The primary variable that swings outcomes "
            "is **daily customer count** — not COTA, not check size, not ancillary streams."
        )

    # ── Section 9: Scenario Comparison ──────────────────────────────────────
    with st.expander("9. Scenario Definitions"):
        sc_def = pd.DataFrame([
            ("Worst Case",   65,  0,   "None",  "No COTA, slow ramp, no boosters"),
            ("Stress Test",  80,  5,   "None",  "Reduced COTA (Big 3 + 2 concerts), zero boosters"),
            ("Conservative", 90,  12,  "50%",   "Modest boosters, full COTA calendar"),
            ("Base Case",    100, 12,  "100%",  "Full model as designed"),
            ("Upside",       135, 15,  "150%",  "Strong year, aggressive boosters"),
        ], columns=["Scenario", "Customers/Day", "COTA Events", "Boosters", "Description"])
        st.dataframe(sc_def, use_container_width=True, hide_index=True)

    # ── Section 10: Multi-Year Trajectory ───────────────────────────────────
    with st.expander("10. Multi-Year Trajectory (Years 1–3)"):
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Growth Assumptions**")
            st.markdown(
                "- Revenue growth: **4%/year** (customer volume + check size)\n"
                "- Cost inflation: **3%/year** (labor, supplies, utilities)\n"
                "- Debt service: **Fixed at $17,143/mo** for full 25-year term"
            )
        with col_g2:
            st.markdown("**Cash Reserve Tracker**")
            st.markdown(
                "- Opening cash reserve: **$186,000** (contingency + operating runway from loan)\n"
                "- Months 1–4: Expected cash-negative due to ramp-up\n"
                "- Critical question: Does the $186K reserve bridge the gap through early cash-burn months?"
            )

    # ── Section 11: Strategic Takeaways ─────────────────────────────────────
    with st.expander("11. Strategic Takeaways", expanded=True):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("**✅ What the Model Confirms**")
            st.markdown(
                "1. **Viable at 100 customers/day** with the full revenue mix — DSCR comfortably above lender minimum\n"
                "2. **COTA events are high-margin bonus revenue**, not the foundation — the bar survives without them\n"
                "3. **F1 is the singular mega-event** — 30–40% of all COTA revenue alone\n"
                "4. **Beverage-only model is the moat** — $0 kitchen OpEx keeps break-even achievable at modest traffic\n"
                "5. **Diversification works** — 8 independent revenue streams reduce single-point-of-failure risk"
            )
        with col_t2:
            st.markdown("**⚠️ What the Model Flags**")
            st.markdown(
                "1. **Year 1 Months 1–6 will be cash-negative** — the $186K reserve must bridge this gap\n"
                "2. **The Nut at $49,793 sets a high break-even bar** — ~$78,660/mo in revenue needed\n"
                "3. **Booster programs are unproven** — delayed to Month 7 and ramped gradually, compressing Year 1\n"
                "4. **February is the danger month** — 0.60 seasonality multiplier + no COTA events = lowest revenue month"
            )
