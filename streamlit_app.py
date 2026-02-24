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
def get_multi_year(custs, years=3):
    return model.run_multi_year_projection(custs, years)


@st.cache_data
def get_monte_carlo(n_sims, seed):
    return model.run_monte_carlo(n_sims, seed)


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
    mc_results = get_monte_carlo(mc_sims, mc_seed)
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

    all_years = get_multi_year(daily_customers)

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

    all_years = get_multi_year(daily_customers)

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
