#!/usr/bin/env python3
"""
The Cube | Del Valle Sports Bar & Event Center
Interactive Financial Model
13903 FM 812, Del Valle, TX 78617
Capital Raise: $1,923,698 (SBA 7(a))

Built from Notion feasibility docs (Feb 2026).
"""

import random
import math

# =============================================================================
# SECTION 1: CORE ASSUMPTIONS (from Notion docs)
# =============================================================================

# --- Loan & Debt ---
TOTAL_LOAN = 1_923_698
INTEREST_RATE = 0.0975
LOAN_TERM_YEARS = 25
MONTHLY_DEBT_SERVICE = 17_142.79
ANNUAL_DEBT_SERVICE = 205_713
POST_CONSTRUCTION_VALUE = 2_500_000
LTV = 0.77

# --- Fixed Monthly Costs ("The Nut") ---
# Updated breakdown from Feb 2026 Expense Projection Formula
FIXED_COSTS = {
    "debt_service": 17_143,
    "base_labor_5_staff": 14_950,   # 5 staff @ avg ~$2,990/mo (scales with volume)
    "insurance": 3_000,
    "utilities": 2_200,             # rural location, LED-efficient
    "marketing": 1_500,
    "cable_sports_packages": 1_500,
    "pos_tech_subscriptions": 1_000,
    "licenses_permits": 500,
    "maintenance_reserve": 2_500,   # 4.5-acre property
    "property_tax": 4_500,          # Travis County ~2.1% on $2.5M value = ~$52.5K/yr
    "miscellaneous": 1_000,
}
MONTHLY_NUT = sum(FIXED_COSTS.values())  # ~$49,793

# --- Scaled Labor Model ---
# Base: 5 staff at $14,950/mo handles up to ~100 customers/day
# Add staff as volume grows. Each additional staff member ~$2,990/mo
LABOR_BASE_STAFF = 5
LABOR_BASE_COST = 14_950             # 5 staff monthly
LABOR_COST_PER_STAFF = 2_990         # avg per additional staff member
LABOR_SCALE_THRESHOLDS = [
    # (daily_customers_threshold, total_staff_needed)
    (0,   5),    # 0-100 customers/day: 5 staff (base)
    (101, 6),    # 101-120: add 1 bartender/server
    (121, 7),    # 121-140: add another
    (141, 8),    # 141-160: add another
    (161, 9),    # 161-180: add another
    (181, 10),   # 181+: full crew
]

# --- Variable Cost Add-Ons ---
CC_PROCESSING_RATE = 0.028           # 2.8% of all bar revenue (card transactions ~85%)
CC_CARD_USAGE_RATE = 0.85            # 85% of transactions on card
SHRINKAGE_RATE = 0.025               # 2.5% of beverage COGS (breakage + theft, no food waste)

# --- Revenue Assumptions ---
# Weekday daypart model: Happy Hour (3-7pm) ~$20 avg + Prime Time (7pm-close) ~$27 avg
# Blended weekday: $25.71 (30 HH custs × $20 + 42 PT custs × $27) / 72
AVG_CHECK_WEEKDAY = 25.71
AVG_CHECK_WEEKEND = 36.63   # $35 bev avg + $1.63 food truck revenue share
WEEKDAY_HAPPY_HOUR_CHECK = 20.00
WEEKDAY_PRIME_TIME_CHECK = 27.00
WEEKDAY_HH_CUSTOMERS = 30    # Happy Hour (3pm-7pm)
WEEKDAY_PT_CUSTOMERS = 42    # Prime Time (7pm-close)
WEEKDAY_BASELINE_CUSTOMERS = 72  # HH + PT = 72/day weekday baseline
BLENDED_DAILY_CHECK = (AVG_CHECK_WEEKDAY * 5 + AVG_CHECK_WEEKEND * 2) / 7  # ~28.83

# --- Operating Hours ---
HOURS_WEEKDAY = "3:00 PM - 12:00 AM"   # Mon-Thu (9 hrs)
HOURS_FRIDAY  = "11:00 AM - 2:00 AM"   # Fri (15 hrs)
HOURS_SATURDAY = "11:00 AM - 2:00 AM"  # Sat (15 hrs)
HOURS_SUNDAY  = "11:00 AM - 10:00 PM"  # Sun (11 hrs)

# --- Cost Structure ---
COGS_RATE = 0.30        # beverage COGS (pour cost target 28-30%)
GRT_RATE = 0.067        # TX Mixed Beverage Gross Receipts Tax (alcohol only)
VARIABLE_COST_RATE = COGS_RATE + GRT_RATE  # 36.7% on bar revenue

# --- Venue ---
VENUE_SQFT = 5_000       # building footprint
SEAT_CAPACITY_COMFORTABLE = 225  # midpoint of 200-250 comfortable
SEAT_CAPACITY_MAX = 325          # midpoint of 300-350 max (event mode)
SEAT_CAPACITY = SEAT_CAPACITY_COMFORTABLE  # default for projections
PARKING_SPACES = 450
LAND_ACRES = 4.5
LED_WALL_SQFT = 800      # primary digital LED wall

# --- Market ---
LOCAL_HOUSEHOLDS = 8_754
MEDIAN_HH_INCOME = 78_000
MEDIAN_AGE = 36
TESLA_EMPLOYEES = 20_000   # 20,000+ at Giga Texas (conservative)
ANNUAL_COTA_VISITORS = 700_000
MAJOR_COTA_EVENTS_PER_YEAR = 12

# --- Parking (Event Days) ---
PARKING_PRICE_PER_SPACE = 90   # midpoint of $80-$100/space range
PARKING_OCCUPANCY_RATE = 0.70  # 315 cars/day
DRINK_VOUCHER_PER_CAR = 25
VOUCHER_REDEMPTION_RATE = 0.75  # 75% of parkers redeem
VOUCHER_TRUE_COST_RATE = 0.367  # COGS + GRT on the $25

# --- Event Space Rentals ---
EVENT_RENTAL_MIN = 2_000
EVENT_RENTAL_MAX = 6_000
EVENT_RENTAL_AVG = 4_000      # midpoint, weighted toward corporate bookings
EVENT_RENTALS_PER_YEAR_LOW = 26   # conservative
EVENT_RENTALS_PER_YEAR_HIGH = 40  # optimistic
EVENT_RENTALS_PER_MONTH_STEADY = 3  # ~36/year at steady state
EVENT_RENTALS_PER_MONTH = 3        # kept for backward compat; see ramp below
EVENT_RENTAL_MARGIN = 0.85
# Annual range: $52K-$160K (26×$2K to 40×$4K)

# Year 1 rental ramp: new venue with no reputation, bookings build slowly
# Months 1-3: 0 (still building word-of-mouth), 4-6: 1/mo, 7-9: 2/mo, 10+: 3/mo
EVENT_RENTAL_Y1_RAMP = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1,
                         7: 2, 8: 2, 9: 2, 10: 3, 11: 3, 12: 3}

# Year 1 rental avg check: early bookings are smaller (birthday parties, small groups).
# Later bookings attract corporate clients willing to pay premium.
# Months 4-6: $2,500 avg (small private events), 7-9: $3,000 (mixed),
# 10-12: $3,500 (corporate starting to book). Year 2+: $4,000 (steady state).
EVENT_RENTAL_Y1_AVG = {
    1: 0, 2: 0, 3: 0,                  # no bookings
    4: 2_500, 5: 2_500, 6: 2_500,      # small events
    7: 3_000, 8: 3_000, 9: 3_000,      # mixed
    10: 3_500, 11: 3_500, 12: 3_500,   # corporate starting
}  # Year 2+: $4,000 (steady state)

# --- Digital LED Advertising ---
# 800 sqft LED wall - premium ad real estate visible from FM 812
LED_MONTHLY_REVENUE = 2_500  # conservative: 5 contracts @ $500/mo (steady state)
LED_MARGIN = 0.90

# Year 1 LED ramp: need to actively sell contracts, takes time to build pipeline.
# Months 1-2: 1 contract (launch partner/local business), 3-4: 2 contracts,
# 5-6: 3 contracts, 7-9: 4 contracts, 10+: 5 contracts (steady state)
LED_Y1_RAMP = {
    1: 500,   2: 500,           # 1 contract @ $500
    3: 1_000, 4: 1_000,        # 2 contracts
    5: 1_500, 6: 1_500,        # 3 contracts
    7: 2_000, 8: 2_000, 9: 2_000,  # 4 contracts
    10: 2_500, 11: 2_500, 12: 2_500,  # full 5 contracts
}  # Year 2+: $2,500/mo (steady state)

# --- Food Truck Partnerships ---
FOOD_TRUCK_COUNT = 3             # steady-state (Year 2+)
FOOD_TRUCK_PAD_RENT = 900       # per truck per month
FOOD_TRUCK_REV_SHARE_RATE = 0.12  # 12% of their sales
FOOD_TRUCK_AVG_MONTHLY_SALES = 15_000  # per truck estimate
FOOD_TRUCK_MARGIN = 1.0  # pure profit (no kitchen OpEx)

# Year 1 truck ramp: new venue needs to prove foot traffic before trucks commit.
# Months 1-3: 1 truck (anchor/partner willing to take the risk)
# Months 4-6: 1-2 trucks (second truck tests the waters)
# Months 7-9: 2 trucks (reliable pair, third still evaluating)
# Months 10-12: 2-3 trucks (approaching steady state)
FOOD_TRUCK_Y1_RAMP = {
    1: 1, 2: 1, 3: 1,
    4: 1, 5: 2, 6: 2,
    7: 2, 8: 2, 9: 2,
    10: 2, 11: 3, 12: 3,
}  # Year 2+: 3 trucks (steady state)

# --- Weekday Booster Programs (incremental monthly revenue) ---
# These are additive programs to lift weekday traffic above baseline.
# REVISED: Conservative projections with slow Year 1 ramp.
#
# Tesla: 1-5% of 20K employees visit once/month, $11 avg spend.
#   Year 1 start: 1% = 200 visits × $11 = $2,200/mo
#   Steady state: 3% = 600 visits × $11 = $6,600/mo
#   Optimistic:   5% = 1,000 visits × $11 = $11,000/mo
#
# Trivia: Below-average for new venue in rural area.
#   Avg established bar: $500-$800/week incremental.
#   Year 1 start: ~$300/week = $1,200/mo (building attendance)
#   Steady state: $500/week = $2,000/mo
#
BOOSTER_PROGRAMS = {
    "tesla_partnership": {
        "desc": "Tesla employee happy hour specials (1-5% of 20K workforce × $11/visit)",
        "monthly_low": 2_200,     # 1% penetration (200 visits × $11)
        "monthly_high": 11_000,   # 5% penetration
        "monthly_base": 3_300,    # 1.5% penetration at steady state (conservative)
        "monthly_y1_start": 2_200,  # 1% — new venue, no reputation yet
    },
    "food_truck_hh_combos": {
        "desc": "$15 'Truck + Drink' combo during happy hour",
        "monthly_low": 1_500,
        "monthly_high": 3_200,
        "monthly_base": 2_000,
        "monthly_y1_start": 1_000,
    },
    "industry_night": {
        "desc": "Tues/Wed hospitality/service industry night",
        "monthly_low": 1_500,
        "monthly_high": 3_200,
        "monthly_base": 2_000,
        "monthly_y1_start": 1_000,
    },
    "weekly_trivia": {
        "desc": "Themed trivia night (Wed or Thu) — below avg for new rural venue",
        "monthly_low": 1_200,     # ~$300/week (building attendance)
        "monthly_high": 3_500,    # ~$875/week (strong night)
        "monthly_base": 2_000,    # ~$500/week (steady state)
        "monthly_y1_start": 1_200,  # ~$300/week (starting out)
    },
}
BOOSTER_TOTAL_LOW = sum(p["monthly_low"] for p in BOOSTER_PROGRAMS.values())      # ~$6.4K/mo
BOOSTER_TOTAL_HIGH = sum(p["monthly_high"] for p in BOOSTER_PROGRAMS.values())    # ~$20.9K/mo
BOOSTER_TOTAL_BASE = sum(p["monthly_base"] for p in BOOSTER_PROGRAMS.values())    # ~$9.3K/mo
BOOSTER_TOTAL_Y1_START = sum(p["monthly_y1_start"] for p in BOOSTER_PROGRAMS.values())  # ~$5.4K/mo

# Booster Year 1 ramp: programs don't launch until month 5, then scale to steady state
# Month 5-6: Y1 start level, 7-8: 70% of base, 9-10: 85% of base, 11+: full base
BOOSTER_Y1_RAMP = {
    1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0,       # no boosters during early ramp
    5: 0.0, 6: 0.0,                          # still ramping ops (see extended ramp-up below)
    7: 0.58, 8: 0.58,                        # Y1 start level ($5.4K / $9.3K ≈ 0.58)
    9: 0.70, 10: 0.85, 11: 0.90, 12: 1.0,  # scaling toward steady state
}

# --- Seasonal Event Revenue (annual one-off spikes) ---
SEASONAL_EVENTS = {
    "march_madness": {"month": 3, "rev_low": 16_000, "rev_high": 33_000, "rev_base": 22_000},
    "super_bowl":    {"month": 2, "rev_low": 8_000,  "rev_high": 15_000, "rev_base": 11_000},
    "nye":           {"month": 12, "rev_low": 10_000, "rev_high": 20_000, "rev_base": 14_000},
}
SEASONAL_TOTAL_BASE = sum(e["rev_base"] for e in SEASONAL_EVENTS.values())  # ~$47K/year

# --- Seasonality Multipliers (by month) ---
# Based on sports calendar analysis: Oct peak, Feb low, summer gap
SEASONALITY = {
    1:  0.75,  # Jan - post-holiday lull, NFL playoffs help
    2:  0.60,  # Feb - quietest month (Super Bowl spike but low volume)
    3:  0.80,  # Mar - March Madness, F1 starts, MLS starts
    4:  0.90,  # Apr - highest volume month (MLB + NBA/NHL stretch)
    5:  0.85,  # May - MotoGP at COTA, NBA/NHL playoffs
    6:  0.70,  # Jun - summer gap starts, MLB carries
    7:  0.65,  # Jul - deep summer gap, lowest non-Feb month
    8:  0.70,  # Aug - NFL preseason, college football hype
    9:  0.85,  # Sep - NFL starts, college football peak
    10: 1.00,  # Oct - "Sports Equinox" + F1 USGP (PEAK)
    11: 0.95,  # Nov - NFL + college + NBA/NHL full swing
    12: 0.80,  # Dec - bowl season, holidays slow mid-month
}

# --- COTA Event Tiers ---
# Each tier has its own parking price, occupancy, duration, bar uplift, and costs.
# All figures from the COTA Events Notion analysis (Feb 2026).
# Revenue figures are NET INCREMENTAL (above normal daily ops).
COTA_EVENT_TIERS = {
    "tier1_f1": {
        # F1 US Grand Prix — the undisputed king
        # 400K-440K attendance, $480M-$1B+ regional impact
        # PDF: $155K-$188K total weekend revenue for The Cube
        "name": "F1 US Grand Prix",
        "attendance_range": "400K-440K over 3 days",
        "parking_price": 80,            # $80/space (PDF: 450 × $80)
        "parking_occupancy": 1.00,      # 100% sold out all 3 days
        "parking_days": 3,              # Fri-Sun
        "bar_uplift_per_weekend": 60_000,  # PDF: $45K-$75K midpoint = $60K
        "incremental_cost": 50_000,     # max staffing, security, porta-johns, supplies
    },
    "tier2_motogp": {
        # MotoGP Grand Prix of the Americas — #2 event
        # 100K-150K attendance, $80M-$120M regional impact
        # PDF: $87K-$119K total (~55-65% of F1)
        "name": "MotoGP Grand Prix of the Americas",
        "attendance_range": "100K-150K over 3 days",
        "parking_price": 55,            # PDF: $50-$60/space midpoint
        "parking_occupancy": 0.93,      # PDF: 85-100% utilization midpoint
        "parking_days": 3,              # 3-day event
        "bar_uplift_per_weekend": 27_000,  # PDF: $18K-$36K midpoint
        "incremental_cost": 38_000,
    },
    "tier2_nascar": {
        # NASCAR Cup Series (EchoPark GP) — different crowd, strong spike
        # 80K-120K attendance, $50M-$80M regional impact
        # PDF: $48K-$76K total (~30-40% of F1)
        # Note: strong tailgating demo, favorable for outdoor bar/lot activation
        "name": "NASCAR Cup Series (EchoPark Grand Prix)",
        "attendance_range": "80K-120K over 2-3 days",
        "parking_price": 50,            # PDF: $40-$60/space midpoint
        "parking_occupancy": 0.80,      # PDF: 70-90% utilization midpoint
        "parking_days": 2,              # PDF: 2 days primary
        "bar_uplift_per_weekend": 15_000,  # PDF: $10K-$20K midpoint
        "incremental_cost": 30_000,
    },
    "tier3_wec": {
        # WEC 6 Hours of COTA — niche but valuable
        # 40K-60K attendance, $20M-$40M regional impact
        # PDF: $30K-$48K total (~20-25% of F1)
        "name": "WEC 6 Hours of COTA",
        "attendance_range": "40K-60K over 2 days",
        "parking_price": 35,            # PDF: $30-$40/space midpoint
        "parking_occupancy": 0.70,      # PDF: 60-80% midpoint
        "parking_days": 2,
        "bar_uplift_per_weekend": 9_000,   # PDF: $6K-$12K midpoint
        "incremental_cost": 18_000,
    },
    "tier3_gt_transam": {
        # GT World Challenge / TransAm / smaller races
        # 5K-30K attendance, $3M-$15M regional impact
        # PDF: $8K-$25K total (~5-15% of F1)
        "name": "GT World Challenge / TransAm / Other Races",
        "attendance_range": "5K-30K over 2-3 days",
        "parking_price": 25,            # PDF: $20-$30/space midpoint
        "parking_occupancy": 0.35,      # PDF: 20-50% midpoint
        "parking_days": 2,
        "bar_uplift_per_weekend": 4_500,   # marginal above baseline
        "incremental_cost": 8_000,
    },
    "tier3_concert": {
        # Major Concerts at Germania Insurance Amphitheater
        # 15K-30K per show, 3-6 per year
        # PDF: $5K-$15K per concert night (~5-10% of F1)
        # Underrated bar play — young, social, post-show overflow
        "name": "Major Concert (Germania Amphitheater)",
        "attendance_range": "15K-30K per show, 1 day",
        "parking_price": 30,            # concert-goers pay for convenience
        "parking_occupancy": 0.55,      # PDF: 40-70% midpoint
        "parking_days": 1,              # single night event
        "bar_uplift_per_weekend": 3_000,   # post-show overflow (10pm-2am)
        "incremental_cost": 5_000,
    },
    "tier3_festival": {
        # Festivals (FoodieLand, etc.) — family crowd, moderate impact
        # 20K-50K attendance, $5M-$12M regional impact
        # PDF: $8K-$20K per festival weekend (~5-12% of F1)
        # Parking is main driver, minimal bar spillover during daytime
        "name": "Festival (FoodieLand, etc.)",
        "attendance_range": "20K-50K over 2-3 days",
        "parking_price": 30,            # moderate pricing
        "parking_occupancy": 0.45,      # PDF: 30-60% midpoint
        "parking_days": 2,
        "bar_uplift_per_weekend": 2_500,   # family daytime crowd, low bar impact
        "incremental_cost": 6_000,
    },
    "tier4_trackday": {
        # Track Rentals / Car Clubs / Bike Night — baseline boost
        # 500-5,000 per event, minimal economic impact
        # PDF: $500-$3K per event (<2% of F1)
        "name": "Track Day / Car Club / Bike Night",
        "attendance_range": "500-5K, 1 day",
        "parking_price": 0,             # no meaningful paid parking
        "parking_occupancy": 0.10,      # PDF: 5-15% midpoint
        "parking_days": 1,
        "bar_uplift_per_weekend": 1_500,   # slight bump, baseline boost
        "incremental_cost": 1_000,
    },
}

# --- COTA Event Calendar (month -> list of event tier keys) ---
# Based on PDF "Annual COTA Super Spike Revenue" table (Feb 2026).
# Typical year: ~10-12 major ticketed events.
# PDF annual total: $372K-$581K from COTA events.
COTA_EVENTS_BY_MONTH = {
    1:  [],
    2:  ["tier3_wec"],                       # WEC 6 Hours (Feb/Mar)
    3:  ["tier2_nascar"],                    # NASCAR Cup Series (Late Feb/Early Mar)
    4:  ["tier2_motogp", "tier3_gt_transam"],  # MotoGP (Mar/Apr) + GT World Challenge (Apr)
    5:  ["tier3_concert"],                   # Germania Amp concert #1
    6:  ["tier3_concert", "tier3_festival"], # Concert #2 + FoodieLand/festival
    7:  ["tier3_concert"],                   # Concert #3
    8:  ["tier3_festival"],                  # Festival #2
    9:  ["tier3_concert"],                   # Concert #4
    10: ["tier1_f1", "tier3_gt_transam"],    # F1 USGP + TransAm SpeedTour (Oct/Nov)
    11: [],
    12: [],
}
# Total: 12 events (1×F1 + 1×MotoGP + 1×NASCAR + 1×WEC + 2×GT/TransAm
#                    + 4×Concert + 2×Festival)
# Matches PDF: F1(1) + MotoGP(1) + NASCAR(1) + WEC(1) + GT/TransAm(2)
#              + Concerts(4) + Festivals(2) = 12 events

# Legacy constants kept for reference
COTA_WEEKEND_PARKING_REV = 108_000   # F1: 450 × $80 × 3 days (PDF figure)
COTA_WEEKEND_BAR_REV = 60_000        # F1: $45K-$75K midpoint (PDF figure)
COTA_WEEKEND_INCREMENTAL_COST = 50_000  # F1 scale max staffing/security

# --- Day-of-Week Revenue Pattern (as fraction of weekly total) ---
DAY_WEIGHTS = {
    "Monday":    0.075,   # MNF
    "Tuesday":   0.025,   # slow
    "Wednesday": 0.025,   # slow
    "Thursday":  0.075,   # TNF
    "Friday":    0.110,   # happy hour
    "Saturday":  0.400,   # peak
    "Sunday":    0.290,   # NFL anchor
}

# --- Year 1 Ramp-Up (8-9 month ramp to full capacity) ---
# Conservative ramp for a new bar in a rural area with no existing foot traffic.
# Industry avg for non-urban bar: 6-12 months to steady state. We use ~9 months.
RAMP_UP = {
    1: 0.30,   # Grand opening buzz, but very limited awareness
    2: 0.35,   # Post-opening dip, building regulars
    3: 0.42,   # Slowly growing, March Madness helps
    4: 0.50,   # MotoGP month helps, but still early
    5: 0.58,   # Word-of-mouth building
    6: 0.65,   # Summer gap partially offsets growth
    7: 0.72,   # Boosters launching, food trucks settled in
    8: 0.80,   # NFL preseason hype, approaching steady state
    9: 0.90,   # NFL launch + college football = strong pull
}  # months 10+ = 1.0 (steady state)

# --- Multi-Year Growth ---
# Year 2+: modest organic growth from word-of-mouth, repeat customers, reputation.
# Conservative: 3-5% annual growth in customer volume and check sizes.
ANNUAL_GROWTH_RATE = 0.04   # 4% year-over-year growth (customers + check)
ANNUAL_COST_INFLATION = 0.03  # 3% annual cost inflation (labor, supplies, utilities)

# --- Cash Reserve ---
OPENING_CASH_RESERVE = 186_000  # contingency + operating runway from loan


# =============================================================================
# SECTION 2: REVENUE MODEL FUNCTIONS
# =============================================================================

def calc_scaled_labor_cost(avg_daily_customers):
    """
    Calculate monthly labor cost based on customer volume.
    More customers = more staff needed behind the bar.
    """
    staff_needed = LABOR_BASE_STAFF
    for threshold, staff in LABOR_SCALE_THRESHOLDS:
        if avg_daily_customers >= threshold:
            staff_needed = staff
    additional = max(0, staff_needed - LABOR_BASE_STAFF)
    return LABOR_BASE_COST + (additional * LABOR_COST_PER_STAFF)


def calc_daily_bar_revenue(daily_customers, weekday=True):
    """Revenue from a single day of bar operations."""
    check = AVG_CHECK_WEEKDAY if weekday else AVG_CHECK_WEEKEND
    return daily_customers * check


def calc_weekday_daypart_revenue(hh_customers=None, pt_customers=None,
                                  hh_check=None, pt_check=None):
    """
    Weekday daypart model:
    - Happy Hour (3pm-7pm): ~30 customers × $20 avg check
    - Prime Time (7pm-close): ~42 customers × $27 avg check
    Returns daily weekday revenue and customer count.
    """
    hh_c = hh_customers or WEEKDAY_HH_CUSTOMERS
    pt_c = pt_customers or WEEKDAY_PT_CUSTOMERS
    hh_chk = hh_check or WEEKDAY_HAPPY_HOUR_CHECK
    pt_chk = pt_check or WEEKDAY_PRIME_TIME_CHECK

    hh_rev = hh_c * hh_chk
    pt_rev = pt_c * pt_chk
    return {
        "daily_customers": hh_c + pt_c,
        "daily_revenue": hh_rev + pt_rev,
        "blended_check": (hh_rev + pt_rev) / (hh_c + pt_c),
        "hh_revenue": hh_rev,
        "pt_revenue": pt_rev,
    }


def calc_monthly_bar_revenue(avg_daily_customers, month, year_month=None,
                              weekday_check=None, weekend_check=None):
    """
    Calculate bar-only revenue for a given month.
    Uses weekday daypart model + weekend flat check.
    Applies seasonality and ramp-up multipliers.
    """
    wk_check = weekday_check or AVG_CHECK_WEEKDAY
    we_check = weekend_check or AVG_CHECK_WEEKEND

    season_mult = SEASONALITY.get(month, 0.80)
    ramp_mult = RAMP_UP.get(year_month, 1.0) if year_month else 1.0

    # Monthly day breakdown: ~17.4 Mon-Thu, 4.3 Fri, 4.3 Sat, 4.3 Sun
    weekday_days = 21.7   # Mon-Thu (17.4) + Fri (4.3)
    weekend_days = 8.6    # Sat (4.3) + Sun (4.3)

    # Use blended weighted average across week
    blended_check = (wk_check * 5 + we_check * 2) / 7
    monthly_rev = avg_daily_customers * blended_check * 30.4  # avg days/month

    return monthly_rev * season_mult * ramp_mult


def calc_cota_event_revenue(event_list):
    """
    Revenue from COTA event weekends in a given month, using tiered economics.
    Each tier has its own parking price (from PDF analysis), so no global price needed.

    event_list: list of tier keys, e.g. ["tier1_f1", "tier3_concert"]
                OR an int (legacy: treated as that many tier2_nascar events)

    PDF-sourced per-weekend totals (midpoints):
      Tier 1 F1:         ~$108K parking + ~$60K bar = ~$168K gross
      Tier 2 MotoGP:     ~$74K parking  + ~$27K bar = ~$101K gross
      Tier 2 NASCAR:     ~$36K parking  + ~$15K bar = ~$51K gross
      Tier 3 WEC:        ~$22K parking  + ~$9K bar  = ~$31K gross
      Tier 3 GT/TransAm: ~$8K parking   + ~$4.5K bar = ~$12.5K gross
      Tier 3 Concert:    ~$7.4K parking + ~$3K bar  = ~$10.4K gross
      Tier 3 Festival:   ~$12K parking  + ~$2.5K bar = ~$14.5K gross
      Tier 4 Track Day:  ~$0 parking    + ~$1.5K bar = ~$1.5K gross
    """
    # Legacy support: if caller passes an int, convert to that many tier2_nascar events
    if isinstance(event_list, (int, float)):
        n = int(event_list)
        if n == 0:
            return {"parking": 0, "bar_uplift": 0, "gross": 0,
                    "incremental_cost": 0, "net": 0, "tier_breakdown": {}}
        event_list = ["tier2_nascar"] * n

    if not event_list:
        return {"parking": 0, "bar_uplift": 0, "gross": 0,
                "incremental_cost": 0, "net": 0, "tier_breakdown": {}}

    total_parking = 0
    total_bar_uplift = 0
    total_inc_cost = 0
    tier_breakdown = {}

    for tier_key in event_list:
        tier = COTA_EVENT_TIERS.get(tier_key, COTA_EVENT_TIERS["tier3_gt_transam"])

        cars_per_day = int(PARKING_SPACES * tier["parking_occupancy"])
        parking_rev = cars_per_day * tier["parking_price"] * tier["parking_days"]
        bar_uplift = tier["bar_uplift_per_weekend"]
        inc_cost = tier["incremental_cost"]

        total_parking += parking_rev
        total_bar_uplift += bar_uplift
        total_inc_cost += inc_cost

        # Track per-tier totals
        if tier_key not in tier_breakdown:
            tier_breakdown[tier_key] = {"count": 0, "parking": 0, "bar": 0, "cost": 0}
        tier_breakdown[tier_key]["count"] += 1
        tier_breakdown[tier_key]["parking"] += parking_rev
        tier_breakdown[tier_key]["bar"] += bar_uplift
        tier_breakdown[tier_key]["cost"] += inc_cost

    gross = total_parking + total_bar_uplift

    return {
        "parking": total_parking,
        "bar_uplift": total_bar_uplift,
        "gross": gross,
        "incremental_cost": total_inc_cost,
        "net": gross - total_inc_cost,
        "tier_breakdown": tier_breakdown,
    }


def calc_event_rental_revenue(bookings_per_month=None, avg_booking=None, year_month=None):
    """
    Revenue from private event space rentals.
    Year 1: slow ramp (0 bookings months 1-3, builds to 3/mo by month 10).
    Year 1 avg check: graduated from $2,500 (small events) to $3,500 (corporate).
    Year 2+: 3 bookings/mo at $4,000 avg (steady state).
    """
    if bookings_per_month is not None:
        bookings = bookings_per_month
    elif year_month is not None:
        bookings = EVENT_RENTAL_Y1_RAMP.get(year_month, EVENT_RENTALS_PER_MONTH_STEADY)
    else:
        bookings = EVENT_RENTALS_PER_MONTH_STEADY

    if avg_booking is not None:
        avg = avg_booking
    elif year_month is not None:
        avg = EVENT_RENTAL_Y1_AVG.get(year_month, EVENT_RENTAL_AVG)
    else:
        avg = EVENT_RENTAL_AVG

    gross = bookings * avg
    return {"gross": gross, "net": gross * EVENT_RENTAL_MARGIN}


def calc_led_revenue(monthly_rev=None, year_month=None):
    """
    Revenue from digital LED advertising contracts.
    Year 1: follows LED_Y1_RAMP (1-5 contracts building over 12 months).
    Year 2+: steady state at LED_MONTHLY_REVENUE ($2,500/mo).
    monthly_rev override takes priority if provided (e.g. from Monte Carlo).
    """
    if monthly_rev is not None:
        rev = monthly_rev
    elif year_month is not None:
        rev = LED_Y1_RAMP.get(year_month, LED_MONTHLY_REVENUE)
    else:
        rev = LED_MONTHLY_REVENUE
    return {"gross": rev, "net": rev * LED_MARGIN}


def calc_food_truck_revenue(num_trucks=None, pad_rent=None,
                             avg_truck_sales=None, share_rate=None,
                             year_month=None):
    """
    Revenue from food truck partnerships.
    Year 1: follows FOOD_TRUCK_Y1_RAMP (1-2 trucks, growing to 3).
    Year 2+: steady state at FOOD_TRUCK_COUNT (3).
    num_trucks override takes priority if provided (e.g. from Monte Carlo).
    """
    if num_trucks is not None:
        trucks = num_trucks
    elif year_month is not None:
        trucks = FOOD_TRUCK_Y1_RAMP.get(year_month, FOOD_TRUCK_COUNT)
    else:
        trucks = FOOD_TRUCK_COUNT
    rent = pad_rent or FOOD_TRUCK_PAD_RENT
    sales = avg_truck_sales or FOOD_TRUCK_AVG_MONTHLY_SALES
    share = share_rate or FOOD_TRUCK_REV_SHARE_RATE

    pad_income = trucks * rent
    share_income = trucks * sales * share
    total = pad_income + share_income
    return {"gross": total, "net": total * FOOD_TRUCK_MARGIN,
            "pad_income": pad_income, "share_income": share_income}


def calc_booster_revenue(month, year_month=None, booster_pct=1.0):
    """
    Weekday booster program revenue for a given month.
    booster_pct: 0.0 = no boosters, 1.0 = base case, can go higher.
    Year 1: follows BOOSTER_Y1_RAMP schedule (programs launch month 7).
    Year 2+: full steady-state base.
    """
    if year_month is not None:
        # Year 1: use dedicated booster ramp schedule
        booster_ramp = BOOSTER_Y1_RAMP.get(year_month, 1.0)
        if booster_ramp <= 0:
            return 0
        return BOOSTER_TOTAL_BASE * booster_pct * booster_ramp
    # Year 2+: full base
    return BOOSTER_TOTAL_BASE * booster_pct


def calc_seasonal_event_revenue(month, year_month=None, seasonal_pct=1.0):
    """
    One-off seasonal event revenue (Super Bowl, March Madness, NYE).
    Only fires in the relevant month. Scaled by ramp in Year 1.
    """
    ramp = RAMP_UP.get(year_month, 1.0) if year_month else 1.0
    total = 0
    for event in SEASONAL_EVENTS.values():
        if event["month"] == month:
            total += event["rev_base"] * seasonal_pct
    return total * ramp


def calc_monthly_total(avg_daily_customers, month, year_month=None,
                        weekday_check=None, weekend_check=None,
                        cota_events=None, event_bookings=None,
                        led_rev=None, num_trucks=None,
                        booster_pct=1.0, seasonal_pct=1.0):
    """
    Full monthly revenue calculation across all 8 streams.
    Returns detailed breakdown dict.
    """
    # Stream 1: Daily bar ops
    bar_rev = calc_monthly_bar_revenue(
        avg_daily_customers, month, year_month, weekday_check, weekend_check
    )

    # Stream 2 & 3: COTA event bar + parking (tiered)
    if cota_events is not None:
        event_list = cota_events  # caller override (list of tier keys or int for legacy)
    else:
        event_list = COTA_EVENTS_BY_MONTH.get(month, [])
    ramp = RAMP_UP.get(year_month, 1.0) if year_month else 1.0
    # COTA events are external traffic — they happen regardless of bar ramp.
    # But during very early ramp (months 1-2), operations may not be ready
    # to handle full event logistics. Scale COTA bar uplift by ramp factor
    # in early months, parking revenue unaffected (lot is lot).
    cota = calc_cota_event_revenue(event_list)

    # Stream 4: Event rentals (slow ramp in Year 1)
    rentals = calc_event_rental_revenue(event_bookings, year_month=year_month)

    # Stream 5: LED advertising (Y1 ramp: 1-5 contracts building over 12 months)
    led = calc_led_revenue(led_rev, year_month=year_month)

    # Stream 6: Food trucks (Y1 ramp: 1-2 trucks, growing to 3 by Year 2)
    trucks = calc_food_truck_revenue(num_trucks, year_month=year_month)

    # Stream 7: Weekday booster programs
    booster_rev = calc_booster_revenue(month, year_month, booster_pct)

    # Stream 8: Seasonal events (Super Bowl, March Madness, NYE)
    seasonal_rev = calc_seasonal_event_revenue(month, year_month, seasonal_pct)

    # Totals
    total_gross = (bar_rev + cota["gross"] + rentals["gross"] + led["gross"]
                   + trucks["gross"] + booster_rev + seasonal_rev)

    # Variable costs (COGS + GRT apply to bar revenue + boosters + seasonal, not parking/rentals/LED/trucks)
    bar_like_revenue = bar_rev + cota["bar_uplift"] + booster_rev + seasonal_rev
    bar_variable_costs = bar_like_revenue * VARIABLE_COST_RATE

    # Credit card processing: 2.8% on ~85% of bar-like revenue
    cc_processing = bar_like_revenue * CC_PROCESSING_RATE * CC_CARD_USAGE_RATE

    # Shrinkage (breakage + theft): 2.5% of beverage COGS value
    shrinkage = bar_like_revenue * COGS_RATE * SHRINKAGE_RATE

    # Scaled labor: more staff when busier
    effective_daily = avg_daily_customers * SEASONALITY.get(month, 0.80)
    ramp_adj = RAMP_UP.get(year_month, 1.0) if year_month else 1.0
    effective_daily *= ramp_adj
    labor_cost = calc_scaled_labor_cost(effective_daily)

    # Fixed costs with scaled labor replacing base labor
    fixed_costs = MONTHLY_NUT - FIXED_COSTS["base_labor_5_staff"] + labor_cost
    cota_inc_costs = cota["incremental_cost"]

    # NOI calc
    bar_net = bar_like_revenue * (1 - VARIABLE_COST_RATE) - cc_processing - shrinkage
    parking_net = cota["parking"] * 0.95  # 95% margin
    rental_net = rentals["net"]
    led_net = led["net"]
    truck_net = trucks["net"]

    total_net_before_fixed = bar_net + parking_net + rental_net + led_net + truck_net - cota_inc_costs
    noi = total_net_before_fixed - fixed_costs

    # DSCR
    monthly_ds = MONTHLY_DEBT_SERVICE
    # NOI for DSCR excludes debt service from fixed costs
    noi_for_dscr = total_net_before_fixed - (fixed_costs - FIXED_COSTS["debt_service"])
    dscr = noi_for_dscr / monthly_ds if monthly_ds > 0 else 0

    return {
        "month": month,
        "bar_revenue": bar_rev,
        "cota_bar_uplift": cota["bar_uplift"],
        "cota_parking": cota["parking"],
        "cota_incremental_cost": cota_inc_costs,
        "rental_gross": rentals["gross"],
        "led_gross": led["gross"],
        "truck_gross": trucks["gross"],
        "booster_revenue": booster_rev,
        "seasonal_revenue": seasonal_rev,
        "total_gross_revenue": total_gross,
        "bar_variable_costs": bar_variable_costs,
        "cc_processing": cc_processing,
        "shrinkage": shrinkage,
        "labor_cost": labor_cost,
        "fixed_costs": fixed_costs,
        "total_net_before_fixed": total_net_before_fixed,
        "noi": noi,
        "noi_for_dscr": noi_for_dscr,
        "monthly_dscr": dscr,
        "net_cash_flow": noi,  # after all costs including debt
    }


# =============================================================================
# SECTION 3: ANNUAL P&L AND DSCR
# =============================================================================

def run_annual_projection(avg_daily_customers=100, year=1,
                           weekday_check=None, weekend_check=None,
                           cota_events_override=None,
                           booster_pct=1.0, seasonal_pct=1.0):
    """
    Run a full 12-month projection. Returns list of monthly results + annual summary.
    booster_pct: 0.0 = no boosters, 1.0 = base case boosters
    seasonal_pct: 0.0 = no seasonal events, 1.0 = base case
    cota_events_override: dict of {month: list_of_tier_keys} or {month: int} (legacy)
                          or None to use defaults
    """
    months = []
    for m in range(1, 13):
        year_month = m if year == 1 else None  # ramp-up only applies year 1

        if cota_events_override is not None:
            events = cota_events_override.get(m, COTA_EVENTS_BY_MONTH.get(m, []))
        else:
            events = None  # let calc_monthly_total use defaults

        result = calc_monthly_total(
            avg_daily_customers, m, year_month,
            weekday_check, weekend_check, events,
            booster_pct=booster_pct, seasonal_pct=seasonal_pct
        )
        months.append(result)

    # Annual summary
    annual = {
        "total_gross": sum(m["total_gross_revenue"] for m in months),
        "total_bar": sum(m["bar_revenue"] for m in months),
        "total_cota_bar": sum(m["cota_bar_uplift"] for m in months),
        "total_cota_parking": sum(m["cota_parking"] for m in months),
        "total_cota_cost": sum(m["cota_incremental_cost"] for m in months),
        "total_rentals": sum(m["rental_gross"] for m in months),
        "total_led": sum(m["led_gross"] for m in months),
        "total_trucks": sum(m["truck_gross"] for m in months),
        "total_boosters": sum(m["booster_revenue"] for m in months),
        "total_seasonal": sum(m["seasonal_revenue"] for m in months),
        "total_cc_processing": sum(m["cc_processing"] for m in months),
        "total_shrinkage": sum(m["shrinkage"] for m in months),
        "total_labor": sum(m["labor_cost"] for m in months),
        "total_noi": sum(m["noi"] for m in months),
        "total_net_cash": sum(m["net_cash_flow"] for m in months),
        "avg_monthly_dscr": sum(m["monthly_dscr"] for m in months) / 12,
        "min_monthly_dscr": min(m["monthly_dscr"] for m in months),
        "max_monthly_dscr": max(m["monthly_dscr"] for m in months),
        "annual_debt_service": ANNUAL_DEBT_SERVICE,
        "annual_dscr": (sum(m["noi_for_dscr"] for m in months)) / ANNUAL_DEBT_SERVICE,
    }

    return months, annual


def print_annual_summary(months, annual, label=""):
    """Pretty-print a full annual projection."""
    print(f"\n{'=' * 70}")
    if label:
        print(f"  {label}")
    print(f"{'=' * 70}")
    print(f"{'Month':<8} {'Gross Rev':>12} {'Bar Rev':>12} {'COTA':>10} "
          f"{'NOI':>12} {'DSCR':>8}")
    print("-" * 70)

    for m in months:
        mn = m["month"]
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        cota_total = m["cota_bar_uplift"] + m["cota_parking"]
        print(f"{month_names[mn]:<8} ${m['total_gross_revenue']:>11,.0f} "
              f"${m['bar_revenue']:>11,.0f} ${cota_total:>9,.0f} "
              f"${m['noi']:>11,.0f} {m['monthly_dscr']:>7.2f}x")

    print("-" * 70)
    print(f"{'ANNUAL':<8} ${annual['total_gross']:>11,.0f} "
          f"${annual['total_bar']:>11,.0f} "
          f"${annual['total_cota_bar'] + annual['total_cota_parking']:>9,.0f} "
          f"${annual['total_noi']:>11,.0f} {annual['annual_dscr']:>7.2f}x")
    print(f"\n  Annual Debt Service: ${ANNUAL_DEBT_SERVICE:>12,.0f}")
    print(f"  Annual DSCR:         {annual['annual_dscr']:>11.2f}x")
    print(f"  Min Monthly DSCR:    {annual['min_monthly_dscr']:>11.2f}x")
    print(f"  Free Cash Flow:      ${annual['total_net_cash']:>11,.0f}")
    print(f"\n  Revenue Streams:")
    print(f"    Daily Bar Ops:     ${annual['total_bar']:>11,.0f}  "
          f"({annual['total_bar']/annual['total_gross']*100:.1f}%)")
    print(f"    COTA Bar Uplift:   ${annual['total_cota_bar']:>11,.0f}  "
          f"({annual['total_cota_bar']/annual['total_gross']*100:.1f}%)")
    print(f"    COTA Parking:      ${annual['total_cota_parking']:>11,.0f}  "
          f"({annual['total_cota_parking']/annual['total_gross']*100:.1f}%)")
    print(f"    Event Rentals:     ${annual['total_rentals']:>11,.0f}  "
          f"({annual['total_rentals']/annual['total_gross']*100:.1f}%)")
    print(f"    LED Advertising:   ${annual['total_led']:>11,.0f}  "
          f"({annual['total_led']/annual['total_gross']*100:.1f}%)")
    print(f"    Food Trucks:       ${annual['total_trucks']:>11,.0f}  "
          f"({annual['total_trucks']/annual['total_gross']*100:.1f}%)")
    print(f"    Weekday Boosters:  ${annual['total_boosters']:>11,.0f}  "
          f"({annual['total_boosters']/annual['total_gross']*100:.1f}%)")
    print(f"    Seasonal Events:   ${annual['total_seasonal']:>11,.0f}  "
          f"({annual['total_seasonal']/annual['total_gross']*100:.1f}%)")
    print(f"\n  Cost Breakdown:")
    print(f"    Labor (scaled):    ${annual['total_labor']:>11,.0f}")
    print(f"    CC Processing:     ${annual['total_cc_processing']:>11,.0f}")
    print(f"    Shrinkage:         ${annual['total_shrinkage']:>11,.0f}")
    print(f"    Property Tax:      ${FIXED_COSTS['property_tax'] * 12:>11,.0f}")
    print(f"    COTA Inc. Costs:   ${annual['total_cota_cost']:>11,.0f}")


def run_multi_year_projection(base_customers=100, years=3):
    """
    Run Year 1 through Year N projections.
    Year 1: full ramp-up model with all Y1 constraints.
    Year 2+: steady state with annual growth (customers, checks) and cost inflation.
    Returns list of (year, months, annual) tuples.
    """
    all_years = []

    for yr in range(1, years + 1):
        growth = (1 + ANNUAL_GROWTH_RATE) ** (yr - 1)
        cost_mult = (1 + ANNUAL_COST_INFLATION) ** (yr - 1)

        custs = int(base_customers * growth)
        wk_check = AVG_CHECK_WEEKDAY * growth
        we_check = AVG_CHECK_WEEKEND * growth

        months, annual = run_annual_projection(
            custs, year=yr,
            weekday_check=wk_check, weekend_check=we_check,
        )

        # Adjust fixed costs for inflation in Year 2+ (labor, insurance, etc.)
        # The projection already computed Year 1 costs; for Year 2+ we note the
        # multiplier. Since run_annual_projection uses global FIXED_COSTS, we
        # apply inflation as a post-hoc adjustment to NOI for Years 2+.
        if yr > 1:
            # Extra annual fixed cost from inflation (excluding debt service which is fixed)
            base_non_debt_fixed = (MONTHLY_NUT - FIXED_COSTS["debt_service"]) * 12
            inflation_penalty = base_non_debt_fixed * (cost_mult - 1)
            annual["total_noi"] -= inflation_penalty
            annual["total_net_cash"] -= inflation_penalty
            annual["cost_inflation_adj"] = inflation_penalty
            # Recalc DSCR with inflation-adjusted NOI
            annual["annual_dscr"] = (
                (annual["total_noi"] + ANNUAL_DEBT_SERVICE) / ANNUAL_DEBT_SERVICE
            )
        else:
            annual["cost_inflation_adj"] = 0

        annual["year"] = yr
        annual["growth_mult"] = growth
        annual["cost_mult"] = cost_mult
        all_years.append((yr, months, annual))

    return all_years


def print_multi_year_summary(all_years):
    """Pretty-print a multi-year side-by-side comparison."""
    print(f"\n{'=' * 70}")
    print("  MULTI-YEAR PROJECTION (Year 1-3)")
    print(f"{'=' * 70}")

    # Header
    print(f"\n  {'Metric':<28}", end="")
    for yr, _, ann in all_years:
        print(f"{'Year ' + str(yr):>16}", end="")
    print()
    print("  " + "-" * (28 + 16 * len(all_years)))

    rows = [
        ("Daily Customers (avg)", lambda a: f"{int(100 * a['growth_mult']):>16}"),
        ("Annual Revenue", lambda a: f"${a['total_gross']:>14,.0f}"),
        ("  Bar Operations", lambda a: f"${a['total_bar']:>14,.0f}"),
        ("  COTA Events", lambda a: f"${a['total_cota_bar'] + a['total_cota_parking']:>14,.0f}"),
        ("  Event Rentals", lambda a: f"${a['total_rentals']:>14,.0f}"),
        ("  LED Advertising", lambda a: f"${a['total_led']:>14,.0f}"),
        ("  Food Trucks", lambda a: f"${a['total_trucks']:>14,.0f}"),
        ("  Boosters + Seasonal", lambda a: f"${a['total_boosters'] + a['total_seasonal']:>14,.0f}"),
        ("Cost Inflation Adj.", lambda a: f"${a['cost_inflation_adj']:>14,.0f}"),
        ("Annual NOI", lambda a: f"${a['total_noi']:>14,.0f}"),
        ("Free Cash Flow", lambda a: f"${a['total_net_cash']:>14,.0f}"),
        ("Annual DSCR", lambda a: f"{a['annual_dscr']:>15.2f}x"),
        ("Min Monthly DSCR", lambda a: f"{a['min_monthly_dscr']:>15.2f}x"),
    ]

    for label, fmt in rows:
        print(f"  {label:<28}", end="")
        for _, _, ann in all_years:
            print(fmt(ann), end="")
        print()

    # Growth notes
    print(f"\n  Assumptions:")
    print(f"    Revenue growth:    {ANNUAL_GROWTH_RATE:.0%}/year (customers + check size)")
    print(f"    Cost inflation:    {ANNUAL_COST_INFLATION:.0%}/year (labor, supplies, utilities)")
    print(f"    Debt service:      Fixed at ${MONTHLY_DEBT_SERVICE:,.0f}/mo (25-year term)")
    print(f"    Year 1:            9-month ramp, Y1 truck/LED/rental ramps")
    print(f"    Year 2+:           Steady state (3 trucks, 5 LED contracts, 3 rentals/mo @ $4K)")


def run_cash_reserve_tracker(all_years=None):
    """
    Track cash reserve balance month-by-month starting from OPENING_CASH_RESERVE.
    Shows how close to zero you get during the Year 1 ramp.
    Returns the full monthly cash balance series and key metrics.
    """
    if all_years is None:
        all_years = run_multi_year_projection()

    print(f"\n{'=' * 70}")
    print("  CASH RESERVE TRACKER")
    print(f"{'=' * 70}")
    print(f"\n  Opening Cash Reserve: ${OPENING_CASH_RESERVE:>10,.0f}")
    print(f"  (From contingency + operating runway in loan)")

    balance = OPENING_CASH_RESERVE
    min_balance = balance
    min_balance_month = (1, 1)
    months_negative = 0
    cumulative_cf = 0
    break_even_month = None

    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for yr, months, annual in all_years:
        if yr <= 2:  # Only print detail for Years 1-2
            print(f"\n  Year {yr}:")
            print(f"  {'Month':<8} {'Monthly CF':>12} {'Cumulative':>12} {'Cash Balance':>14}")
            print("  " + "-" * 48)

        for m in months:
            cf = m["net_cash_flow"]
            # Apply cost inflation adjustment evenly across months for Year 2+
            if yr > 1:
                cost_mult = (1 + ANNUAL_COST_INFLATION) ** (yr - 1)
                base_non_debt_fixed = MONTHLY_NUT - FIXED_COSTS["debt_service"]
                monthly_inflation = base_non_debt_fixed * (cost_mult - 1)
                cf -= monthly_inflation

            cumulative_cf += cf
            balance += cf

            if balance < min_balance:
                min_balance = balance
                min_balance_month = (yr, m["month"])

            if cf < 0:
                months_negative += 1

            if break_even_month is None and cumulative_cf > 0:
                break_even_month = (yr, m["month"])

            if yr <= 2:
                print(f"  {month_names[m['month']]:<8} ${cf:>11,.0f} ${cumulative_cf:>11,.0f} "
                      f"${balance:>13,.0f}")

    print(f"\n  {'─' * 50}")
    print(f"  KEY METRICS:")
    yr_min, mo_min = min_balance_month
    print(f"    Lowest cash balance:     ${min_balance:>10,.0f}  "
          f"(Year {yr_min}, {month_names[mo_min]})")
    print(f"    Months with negative CF: {months_negative:>10}")
    if break_even_month:
        yr_be, mo_be = break_even_month
        total_months = (yr_be - 1) * 12 + mo_be
        print(f"    Cumulative break-even:   Month {total_months:>3}    "
              f"(Year {yr_be}, {month_names[mo_be]})")
    else:
        print(f"    Cumulative break-even:   NOT REACHED in {len(all_years)} years")

    if min_balance > 0:
        print(f"\n    Cash reserve NEVER goes negative. Minimum cushion: ${min_balance:,.0f}")
    else:
        print(f"\n    WARNING: Cash reserve goes NEGATIVE. Shortfall: ${abs(min_balance):,.0f}")
        print(f"    Additional capital or credit line needed to bridge the gap.")

    return {"min_balance": min_balance, "min_month": min_balance_month,
            "months_negative": months_negative, "break_even_month": break_even_month,
            "cumulative_cf": cumulative_cf}


def print_cash_flow_waterfall(months=None, annual=None):
    """
    Show Year 1 as a cash flow waterfall:
    Gross Revenue → minus each cost layer → Free Cash Flow.
    """
    if months is None or annual is None:
        months, annual = run_annual_projection(100)

    print(f"\n{'=' * 70}")
    print("  YEAR 1 CASH FLOW WATERFALL")
    print(f"{'=' * 70}")

    gross = annual["total_gross"]
    bar_like = annual["total_bar"] + annual["total_cota_bar"] + annual["total_boosters"] + annual["total_seasonal"]

    # Cost layers
    cogs = bar_like * COGS_RATE
    grt = bar_like * GRT_RATE
    cc = annual["total_cc_processing"]
    shrinkage = annual["total_shrinkage"]
    cota_cost = annual["total_cota_cost"]
    labor = annual["total_labor"]
    # Fixed costs excluding labor and debt (already in NUT)
    fixed_ex_labor_debt = (MONTHLY_NUT - FIXED_COSTS["base_labor_5_staff"]
                           - FIXED_COSTS["debt_service"]) * 12
    debt = ANNUAL_DEBT_SERVICE

    # Waterfall steps
    steps = [
        ("Gross Revenue", gross, None),
        ("  Less: COGS (30%)", cogs, "subtract"),
        ("  Less: TX Gross Receipts Tax (6.7%)", grt, "subtract"),
        ("  Less: CC Processing (2.8% × 85%)", cc, "subtract"),
        ("  Less: Shrinkage (2.5% of COGS)", shrinkage, "subtract"),
        ("  Less: COTA Incremental Costs", cota_cost, "subtract"),
        ("  Less: Labor (scaled)", labor, "subtract"),
        ("  Less: Fixed Costs (excl labor/debt)", fixed_ex_labor_debt, "subtract"),
        ("  Less: Debt Service", debt, "subtract"),
    ]

    running = gross
    print(f"\n  {'':─<45}{'Amount':>14}{'Running':>14}")
    print(f"  {'':─<45}{'':─>14}{'':─>14}")

    for label, amount, action in steps:
        if action is None:
            print(f"  {label:<45}${amount:>13,.0f}${amount:>13,.0f}")
            running = amount
        else:
            running -= amount
            print(f"  {label:<45}$({amount:>12,.0f})${running:>13,.0f}")

    free_cf = running
    print(f"  {'':─<45}{'':─>14}{'':─>14}")
    print(f"  {'FREE CASH FLOW':<45}{'':>14}${free_cf:>13,.0f}")

    # Margin analysis
    print(f"\n  Margin Analysis:")
    print(f"    Gross Margin (after COGS+GRT):  {(1 - COGS_RATE - GRT_RATE) * 100:>6.1f}%")
    total_costs = cogs + grt + cc + shrinkage + cota_cost + labor + fixed_ex_labor_debt + debt
    print(f"    Total Cost Ratio:               {total_costs / gross * 100:>6.1f}%")
    print(f"    Free CF Margin:                 {free_cf / gross * 100:>6.1f}%")
    print(f"    Free CF per Customer/Day:       ${free_cf / 365:>9,.0f}")


# =============================================================================
# SECTION 4: SENSITIVITY ANALYSIS
# =============================================================================

def run_sensitivity_analysis():
    """
    Show how key variables swing DSCR and net cash flow.
    Tests: daily customers, avg check, COGS%, COTA events, seasonality.
    """
    print(f"\n{'=' * 70}")
    print("  SENSITIVITY ANALYSIS")
    print(f"{'=' * 70}")

    # --- Customer Count Sensitivity ---
    print(f"\n  1. Daily Customer Count Impact (Year 1)")
    print(f"  {'Customers/Day':>15} {'Annual Rev':>14} {'Annual NOI':>14} {'DSCR':>8} {'Cash Flow':>12}")
    print("  " + "-" * 65)
    for custs in [60, 70, 80, 90, 100, 113, 130, 150, 175]:
        _, ann = run_annual_projection(custs)
        print(f"  {custs:>15} ${ann['total_gross']:>13,.0f} ${ann['total_noi']:>13,.0f} "
              f"{ann['annual_dscr']:>7.2f}x ${ann['total_net_cash']:>11,.0f}")

    # --- Average Check Sensitivity ---
    print(f"\n  2. Average Check Size Impact (at 100 customers/day)")
    print(f"  {'Wkday/Wkend':>15} {'Annual Rev':>14} {'DSCR':>8} {'Cash Flow':>12}")
    print("  " + "-" * 52)
    for wk, we in [(20, 28), (22, 32), (25, 35), (28, 40), (30, 45), (35, 50)]:
        _, ann = run_annual_projection(100, weekday_check=wk, weekend_check=we)
        print(f"  ${wk}/${we}{'':>8} ${ann['total_gross']:>13,.0f} "
              f"{ann['annual_dscr']:>7.2f}x ${ann['total_net_cash']:>11,.0f}")

    # --- COTA Event Mix Sensitivity (tiered, PDF-sourced) ---
    print(f"\n  3. COTA Event Mix Impact (at 100 customers/day)")
    print(f"  {'Mix':>35} {'Events':>7} {'COTA Rev':>14} {'DSCR':>8} {'Cash Flow':>12}")
    print("  " + "-" * 79)

    # Define realistic event mix scenarios aligned with PDF
    cota_mixes = [
        ("No COTA events", {}),
        ("F1 only", {10: ["tier1_f1"]}),
        ("Big 3 only (F1+MotoGP+NASCAR)", {
            3: ["tier2_nascar"], 4: ["tier2_motogp"], 10: ["tier1_f1"]}),
        ("Big 4 + concerts (8 events)", {
            2: ["tier3_wec"], 3: ["tier2_nascar"], 4: ["tier2_motogp"],
            6: ["tier3_concert"], 7: ["tier3_concert"],
            9: ["tier3_concert"], 10: ["tier1_f1"]}),
        ("Base case (12 events, PDF)", None),  # None = use defaults
        ("Strong year (15 events)", {
            2: ["tier3_wec"], 3: ["tier2_nascar"],
            4: ["tier2_motogp", "tier3_gt_transam"],
            5: ["tier3_concert", "tier3_concert"],
            6: ["tier3_concert", "tier3_festival"],
            7: ["tier3_concert"], 8: ["tier3_festival"],
            9: ["tier3_concert", "tier3_festival"],
            10: ["tier1_f1", "tier3_gt_transam"]}),
    ]
    for label, mix in cota_mixes:
        if mix is not None:
            # Fill missing months with empty lists
            override = {m: mix.get(m, []) for m in range(1, 13)}
            n_total = sum(len(v) for v in override.values())
        else:
            override = None
            n_total = sum(len(v) for v in COTA_EVENTS_BY_MONTH.values())
        _, ann = run_annual_projection(100, cota_events_override=override)
        cota_rev = ann["total_cota_bar"] + ann["total_cota_parking"]
        print(f"  {label:>28} {n_total:>7} ${cota_rev:>13,.0f} "
              f"{ann['annual_dscr']:>7.2f}x ${ann['total_net_cash']:>11,.0f}")

    # --- What-If: COTA goes to 50% (members-only risk) ---
    print(f"\n  4. COTA Decline Stress Test (100 customers/day)")
    print(f"  {'COTA Decline':>15} {'COTA Rev':>14} {'DSCR':>8} {'Still Viable?':>14}")
    print("  " + "-" * 54)
    # Build the full default event list in order, then slice to simulate decline
    full_event_list = []  # list of (month, tier_key) tuples
    for m in range(1, 13):
        for tier_key in COTA_EVENTS_BY_MONTH.get(m, []):
            full_event_list.append((m, tier_key))
    for pct in [0, 25, 50, 75, 100]:
        remaining_count = max(0, int(len(full_event_list) * (1 - pct / 100)))
        kept = full_event_list[:remaining_count]
        override = {m: [] for m in range(1, 13)}
        for month, tier_key in kept:
            override[month].append(tier_key)
        _, ann = run_annual_projection(100, cota_events_override=override)
        cota_rev = ann["total_cota_bar"] + ann["total_cota_parking"]
        viable = "YES" if ann["annual_dscr"] >= 1.25 else "DANGER" if ann["annual_dscr"] >= 1.0 else "NO"
        print(f"  {pct:>14}% ${cota_rev:>13,.0f} {ann['annual_dscr']:>7.2f}x {viable:>14}")


# =============================================================================
# SECTION 5: BREAK-EVEN CALCULATOR
# =============================================================================

def run_breakeven_analysis():
    """
    Calculate exact break-even customer counts at various check sizes
    and DSCR targets.
    """
    print(f"\n{'=' * 70}")
    print("  BREAK-EVEN CALCULATOR")
    print(f"{'=' * 70}")

    # Ancillary monthly income (non-bar, always-on)
    rentals = calc_event_rental_revenue()
    led = calc_led_revenue()
    trucks = calc_food_truck_revenue()
    ancillary_monthly = rentals["net"] + led["net"] + trucks["net"]

    print(f"\n  Fixed Monthly Costs (The Nut): ${MONTHLY_NUT:>10,.0f}")
    print(f"  Ancillary Monthly Income:      ${ancillary_monthly:>10,.0f}")
    print(f"    (Rentals: ${rentals['net']:,.0f} + LED: ${led['net']:,.0f} + Trucks: ${trucks['net']:,.0f})")
    print(f"  Net Monthly Gap to Cover:      ${MONTHLY_NUT - ancillary_monthly:>10,.0f}")

    print(f"\n  Break-Even Customers/Day by DSCR Target")
    print(f"  (Assumes avg seasonality, no COTA events — worst case)")
    print(f"\n  {'DSCR Target':>12} {'Monthly Rev':>14} {'Daily Custs':>13} {'HH Penetration':>16}")
    print("  " + "-" * 58)

    targets = [
        ("Break-even", 1.0),
        ("Lender Min", 1.25),
        ("Comfortable", 1.50),
        ("Strong", 2.0),
        ("Excellent", 2.5),
    ]

    for label, target_dscr in targets:
        # Binary search for customer count
        lo, hi = 10, 500
        while hi - lo > 1:
            mid = (lo + hi) // 2
            _, ann = run_annual_projection(mid, cota_events_override={m: [] for m in range(1, 13)})
            if ann["annual_dscr"] >= target_dscr:
                hi = mid
            else:
                lo = mid
        _, ann = run_annual_projection(hi, cota_events_override={m: [] for m in range(1, 13)})
        monthly_rev = ann["total_gross"] / 12
        # Penetration: customers/day * 30 / local households
        monthly_visits = hi * 30.4
        penetration = (monthly_visits / LOCAL_HOUSEHOLDS) * 100
        print(f"  {label + f' ({target_dscr:.2f}x)':>20} ${monthly_rev:>13,.0f} "
              f"{hi:>13} {penetration:>14.1f}%")

    print(f"\n  Note: 22.8% penetration = 80 customers/day = break-even")
    print(f"  Market has {LOCAL_HOUSEHOLDS:,} households + {TESLA_EMPLOYEES:,} Tesla employees")


# =============================================================================
# SECTION 6: MONTE CARLO SIMULATION
# =============================================================================

def run_monte_carlo(n_simulations=10_000, seed=42):
    """
    Run n randomized annual scenarios varying key inputs within realistic ranges.
    Randomizes: daily customers, check sizes, COTA event mix, booster effectiveness,
    seasonal event performance, event rental bookings, food truck occupancy,
    and LED ad fill rate. COGS is held constant (30%) per user request.
    Reports probability distribution of DSCR, revenue, and cash flow.
    """
    random.seed(seed)
    results = []

    for _ in range(n_simulations):
        # --- 1. Core bar operations ---
        daily_custs = random.gauss(100, 20)       # mean 100, std 20
        daily_custs = max(40, min(200, daily_custs))

        wk_check = random.gauss(25.71, 3)          # $25.71 +/- $3
        wk_check = max(18, min(35, wk_check))

        we_check = random.gauss(36.63, 5)          # $36.63 +/- $5
        we_check = max(25, min(50, we_check))

        # --- 2. COTA event mix ---
        # Core 4 motorsport events always happen (F1 + MotoGP + NASCAR + WEC)
        # Then randomize: 2-6 concerts, 1-3 festivals, 0-2 GT/TransAm
        n_concerts = random.choice([2, 3, 3, 4, 4, 4, 5, 6])
        n_festivals = random.choice([1, 2, 2, 2, 3])
        n_gt = random.choice([0, 1, 1, 2, 2])
        override = {m: [] for m in range(1, 13)}
        override[10].append("tier1_f1")
        override[4].append("tier2_motogp")
        override[3].append("tier2_nascar")
        override[2].append("tier3_wec")
        flexible = (["tier3_concert"] * n_concerts
                     + ["tier3_festival"] * n_festivals
                     + ["tier3_gt_transam"] * n_gt)
        flex_months = [4, 5, 6, 7, 8, 9, 10, 11]
        random.shuffle(flexible)
        for i, tier_key in enumerate(flexible):
            month = flex_months[i % len(flex_months)]
            override[month].append(tier_key)

        # --- 3. Booster program effectiveness ---
        # 0.5 = half of base projections, 1.0 = base, 1.5 = 50% above
        booster_pct = random.gauss(1.0, 0.25)
        booster_pct = max(0.3, min(1.8, booster_pct))

        # --- 4. Seasonal event performance ---
        seasonal_pct = random.gauss(1.0, 0.2)
        seasonal_pct = max(0.4, min(1.5, seasonal_pct))

        # --- 5. Run the projection with randomized inputs ---
        # (event rentals and food trucks are randomized per-month below)
        months_data = []
        for m in range(1, 13):
            year_month = m  # Year 1

            # Randomize event rental bookings for this month
            # Base ramp: EVENT_RENTAL_Y1_RAMP gives expected bookings
            base_bookings = EVENT_RENTAL_Y1_RAMP.get(m, EVENT_RENTALS_PER_MONTH_STEADY)
            if base_bookings > 0:
                # Can be 0 to base+1 bookings (uncertainty in corporate demand)
                rental_bookings = max(0, int(random.gauss(base_bookings, 1.0) + 0.5))
            else:
                rental_bookings = 0

            # Randomize food truck pad occupancy around Y1 ramp
            # Base from ramp schedule, then +/- 1 truck with floor of 1
            base_trucks = FOOD_TRUCK_Y1_RAMP.get(m, FOOD_TRUCK_COUNT)
            truck_options = [max(1, base_trucks - 1), base_trucks, base_trucks,
                             min(3, base_trucks + 1)]
            trucks_active = random.choice(truck_options)

            # Randomize LED ad revenue around Y1 ramp base
            base_led = LED_Y1_RAMP.get(m, LED_MONTHLY_REVENUE)
            led_rev = random.gauss(base_led, 300)
            led_rev = max(0, min(base_led + 500, led_rev))

            events = override.get(m, [])

            result = calc_monthly_total(
                int(daily_custs), m, year_month,
                wk_check, we_check, events,
                event_bookings=rental_bookings,
                led_rev=led_rev,
                num_trucks=trucks_active,
                booster_pct=booster_pct, seasonal_pct=seasonal_pct
            )
            months_data.append(result)

        # Build annual summary (same as run_annual_projection)
        ann = {
            "total_gross": sum(m["total_gross_revenue"] for m in months_data),
            "total_bar": sum(m["bar_revenue"] for m in months_data),
            "total_cota_bar": sum(m["cota_bar_uplift"] for m in months_data),
            "total_cota_parking": sum(m["cota_parking"] for m in months_data),
            "total_cota_cost": sum(m["cota_incremental_cost"] for m in months_data),
            "total_rentals": sum(m["rental_gross"] for m in months_data),
            "total_led": sum(m["led_gross"] for m in months_data),
            "total_trucks": sum(m["truck_gross"] for m in months_data),
            "total_boosters": sum(m["booster_revenue"] for m in months_data),
            "total_seasonal": sum(m["seasonal_revenue"] for m in months_data),
            "total_noi": sum(m["noi"] for m in months_data),
            "total_net_cash": sum(m["net_cash_flow"] for m in months_data),
            "avg_monthly_dscr": sum(m["monthly_dscr"] for m in months_data) / 12,
            "min_monthly_dscr": min(m["monthly_dscr"] for m in months_data),
            "max_monthly_dscr": max(m["monthly_dscr"] for m in months_data),
            "annual_debt_service": ANNUAL_DEBT_SERVICE,
            "annual_dscr": (sum(m["noi_for_dscr"] for m in months_data)) / ANNUAL_DEBT_SERVICE,
        }

        results.append({
            "revenue": ann["total_gross"],
            "noi": ann["total_noi"],
            "dscr": ann["annual_dscr"],
            "cash_flow": ann["total_net_cash"],
            "daily_custs": daily_custs,
        })

    # Sort by DSCR
    results.sort(key=lambda x: x["dscr"])

    # Statistics
    revenues = [r["revenue"] for r in results]
    dscrs = [r["dscr"] for r in results]
    cfs = [r["cash_flow"] for r in results]

    def percentile(data, pct):
        idx = int(len(data) * pct / 100)
        return data[min(idx, len(data) - 1)]

    def avg(data):
        return sum(data) / len(data)

    print(f"\n{'=' * 70}")
    print(f"  MONTE CARLO SIMULATION ({n_simulations:,} scenarios)")
    print(f"{'=' * 70}")
    print(f"\n  Randomized Variables (COGS held constant at {COGS_RATE:.0%}):")
    print(f"    Daily Customers:   40-200 (mean 100, std 20)")
    print(f"    Weekday Check:     $18-$35 (mean $25.71)")
    print(f"    Weekend Check:     $25-$50 (mean $36.63)")
    print(f"    COTA Events:       8-15/year (Big 4 fixed + variable concerts/festivals)")
    print(f"    Booster Programs:  30%-180% of base (mean 100%, std 25%)")
    print(f"    Seasonal Events:   40%-150% of base (mean 100%, std 20%)")
    print(f"    Event Rentals:     0-4/mo (based on Y1 ramp +/- 1 booking)")
    print(f"    Food Trucks:       1-3 active (Y1 ramp: 1→2→3)")
    print(f"    LED Advertising:   Y1 ramp $500→$2,500/mo (1→5 contracts)")

    print(f"\n  {'Metric':<25} {'P5':>12} {'P25':>12} {'Median':>12} {'P75':>12} {'P95':>12}")
    print("  " + "-" * 78)

    rev_sorted = sorted(revenues)
    dscr_sorted = sorted(dscrs)
    cf_sorted = sorted(cfs)

    print(f"  {'Annual Revenue':<25} ${percentile(rev_sorted, 5):>11,.0f} "
          f"${percentile(rev_sorted, 25):>11,.0f} ${percentile(rev_sorted, 50):>11,.0f} "
          f"${percentile(rev_sorted, 75):>11,.0f} ${percentile(rev_sorted, 95):>11,.0f}")

    print(f"  {'Annual DSCR':<25} {percentile(dscr_sorted, 5):>12.2f}x"
          f"{percentile(dscr_sorted, 25):>12.2f}x{percentile(dscr_sorted, 50):>12.2f}x"
          f"{percentile(dscr_sorted, 75):>12.2f}x{percentile(dscr_sorted, 95):>12.2f}x")

    print(f"  {'Free Cash Flow':<25} ${percentile(cf_sorted, 5):>11,.0f} "
          f"${percentile(cf_sorted, 25):>11,.0f} ${percentile(cf_sorted, 50):>11,.0f} "
          f"${percentile(cf_sorted, 75):>11,.0f} ${percentile(cf_sorted, 95):>11,.0f}")

    # Probability metrics
    pct_above_1 = sum(1 for d in dscrs if d >= 1.0) / len(dscrs) * 100
    pct_above_125 = sum(1 for d in dscrs if d >= 1.25) / len(dscrs) * 100
    pct_above_15 = sum(1 for d in dscrs if d >= 1.5) / len(dscrs) * 100
    pct_above_2 = sum(1 for d in dscrs if d >= 2.0) / len(dscrs) * 100
    pct_positive_cf = sum(1 for c in cfs if c > 0) / len(cfs) * 100

    print(f"\n  Probability Analysis:")
    print(f"    P(DSCR >= 1.00x):  {pct_above_1:>6.1f}%  (covers debt)")
    print(f"    P(DSCR >= 1.25x):  {pct_above_125:>6.1f}%  (lender minimum)")
    print(f"    P(DSCR >= 1.50x):  {pct_above_15:>6.1f}%  (comfortable)")
    print(f"    P(DSCR >= 2.00x):  {pct_above_2:>6.1f}%  (strong)")
    print(f"    P(Cash Flow > 0):  {pct_positive_cf:>6.1f}%")

    print(f"\n  Average Annual Revenue: ${avg(revenues):>12,.0f}")
    print(f"  Average Annual DSCR:    {avg(dscrs):>12.2f}x")
    print(f"  Average Free Cash Flow: ${avg(cfs):>12,.0f}")

    # Worst case
    worst = results[0]
    best = results[-1]
    print(f"\n  Worst Scenario: Revenue ${worst['revenue']:,.0f} | "
          f"DSCR {worst['dscr']:.2f}x | CF ${worst['cash_flow']:,.0f}")
    print(f"  Best Scenario:  Revenue ${best['revenue']:,.0f} | "
          f"DSCR {best['dscr']:.2f}x | CF ${best['cash_flow']:,.0f}")

    return results


# =============================================================================
# SECTION 7: SCENARIO COMPARISON + LENDER OUTPUT
# =============================================================================

SCENARIOS = {
    "Worst Case": {
        "desc": "No COTA events, slow ramp, construction overruns, no boosters",
        "daily_customers": 65,
        "weekday_check": 22,
        "weekend_check": 30,
        "cota_events": {m: [] for m in range(1, 13)},  # zero COTA
        "booster_pct": 0.0,
        "seasonal_pct": 0.5,
    },
    "Stress Test": {
        "desc": "Big 3 + 2 concerts, zero boosters, reduced seasonal (6 COTA events)",
        "daily_customers": 80,
        "weekday_check": 25.71,
        "weekend_check": 36.63,
        "cota_events": {m: [] for m in range(1, 13)},  # start empty, fill below
        "booster_pct": 0.0,
        "seasonal_pct": 0.75,
    },
    "Conservative": {
        "desc": "90 custs/day, full 12 COTA events, modest boosters at 50%",
        "daily_customers": 90,
        "weekday_check": 25.71,
        "weekend_check": 36.63,
        "cota_events": None,  # full PDF calendar (COTA events happen regardless)
        "booster_pct": 0.5,
        "seasonal_pct": 0.75,
    },
    "Base Case": {
        "desc": "Full PDF calendar: 12 tiered events ($372K-$581K COTA range)",
        "daily_customers": 100,
        "weekday_check": 25.71,
        "weekend_check": 36.63,
        "cota_events": None,  # use defaults (tiered calendar from PDF)
        "booster_pct": 1.0,
        "seasonal_pct": 1.0,
    },
    "Upside": {
        "desc": "Strong year: 15 events (extra concerts/festivals), aggressive boosters",
        "daily_customers": 135,
        "weekday_check": 28,
        "weekend_check": 42,
        "cota_events": None,  # filled below
        "booster_pct": 1.5,
        "seasonal_pct": 1.25,
    },
}
# Populate Stress Test: Big 3 motorsport + 2 concerts only (6 events)
_stress_cota = {3: ["tier2_nascar"], 4: ["tier2_motogp"],
                6: ["tier3_concert"], 9: ["tier3_concert"], 10: ["tier1_f1"]}
SCENARIOS["Stress Test"]["cota_events"].update(_stress_cota)
# Populate Upside: 15 events (add extra concerts + extra festival + WEC)
SCENARIOS["Upside"]["cota_events"] = {
    1:  [],
    2:  ["tier3_wec"],
    3:  ["tier2_nascar"],
    4:  ["tier2_motogp", "tier3_gt_transam"],
    5:  ["tier3_concert", "tier3_concert"],       # 2 concerts
    6:  ["tier3_concert", "tier3_festival"],
    7:  ["tier3_concert"],
    8:  ["tier3_festival", "tier3_concert"],
    9:  ["tier3_concert", "tier3_festival"],
    10: ["tier1_f1", "tier3_gt_transam"],
    11: [],
    12: [],
}


def run_scenario_comparison():
    """Run all five scenarios side by side."""
    print(f"\n{'=' * 86}")
    print("  SCENARIO COMPARISON")
    print(f"{'=' * 86}")

    scenario_results = {}
    for name, params in SCENARIOS.items():
        _, ann = run_annual_projection(
            params["daily_customers"],
            weekday_check=params["weekday_check"],
            weekend_check=params["weekend_check"],
            cota_events_override=params["cota_events"],
            booster_pct=params.get("booster_pct", 1.0),
            seasonal_pct=params.get("seasonal_pct", 1.0),
        )
        scenario_results[name] = ann

    # Side-by-side comparison
    print(f"\n  {'':>20} ", end="")
    for name in SCENARIOS:
        print(f"{name:>16}", end="")
    print()
    print("  " + "-" * (20 + 16 * len(SCENARIOS)))

    metrics = [
        ("Daily Customers", lambda n: f"{SCENARIOS[n]['daily_customers']:>16}"),
        ("Annual Revenue", lambda n: f"${scenario_results[n]['total_gross']:>14,.0f}"),
        ("Annual NOI", lambda n: f"${scenario_results[n]['total_noi']:>14,.0f}"),
        ("Free Cash Flow", lambda n: f"${scenario_results[n]['total_net_cash']:>14,.0f}"),
        ("Annual DSCR", lambda n: f"{scenario_results[n]['annual_dscr']:>15.2f}x"),
        ("Min Month DSCR", lambda n: f"{scenario_results[n]['min_monthly_dscr']:>15.2f}x"),
        ("Bar Revenue", lambda n: f"${scenario_results[n]['total_bar']:>14,.0f}"),
        ("COTA Revenue", lambda n: f"${scenario_results[n]['total_cota_bar'] + scenario_results[n]['total_cota_parking']:>14,.0f}"),
    ]

    for label, fmt in metrics:
        print(f"  {label:>20} ", end="")
        for name in SCENARIOS:
            print(fmt(name), end="")
        print()

    # Descriptions
    print()
    for name, params in SCENARIOS.items():
        print(f"  {name}: {params['desc']}")

    return scenario_results


def print_lender_summary():
    """Generate a clean lender-ready summary table."""
    print(f"\n{'=' * 70}")
    print("  LENDER-READY SUMMARY")
    print("  The Cube | Del Valle Sports Bar & Event Center")
    print("  SBA 7(a) Loan Application Support")
    print(f"{'=' * 70}")

    print(f"\n  LOAN TERMS")
    print(f"  {'Loan Amount:':<30} ${TOTAL_LOAN:>14,.0f}")
    print(f"  {'Interest Rate:':<30} {INTEREST_RATE:>14.2%}")
    print(f"  {'Term:':<30} {'25 years':>14}")
    print(f"  {'Monthly P&I:':<30} ${MONTHLY_DEBT_SERVICE:>14,.2f}")
    print(f"  {'Annual Debt Service:':<30} ${ANNUAL_DEBT_SERVICE:>14,.0f}")
    print(f"  {'Post-Construction Value:':<30} ${POST_CONSTRUCTION_VALUE:>14,.0f}")
    print(f"  {'LTV:':<30} {LTV:>14.0%}")

    print(f"\n  USE OF FUNDS")
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
    for label, amt in uses:
        print(f"  {label:<35} ${amt:>12,.0f}")
    print(f"  {'TOTAL':<35} ${sum(a for _, a in uses):>12,.0f}")

    print(f"\n  COLLATERAL")
    print(f"  {'Land (4.5 acres):':<30} ${1_200_000:>14,.0f}")
    print(f"  {'New-build (5,000 sqft):':<30} ${575_000:>14,.0f}")
    print(f"  {'Sewage infrastructure:':<30} ${350_000:>14,.0f}")
    print(f"  {'Improvements & FF&E:':<30} ${375_000:>14,.0f}")
    print(f"  {'Total Collateral Value:':<30} ${POST_CONSTRUCTION_VALUE:>14,.0f}")

    print(f"\n  MONTHLY FIXED EXPENSES (The Nut)")
    for label, amt in FIXED_COSTS.items():
        clean_label = label.replace("_", " ").title()
        print(f"  {clean_label:<35} ${amt:>10,.0f}")
    print(f"  {'─' * 47}")
    print(f"  {'Total Monthly Nut':<35} ${MONTHLY_NUT:>10,.0f}")
    print(f"  {'Annual Fixed Costs':<35} ${MONTHLY_NUT * 12:>10,.0f}")

    # Run conservative (90 custs, full COTA, modest boosters) and base projections
    _, conservative = run_annual_projection(
        90, weekday_check=25.71, weekend_check=36.63,
        booster_pct=0.5, seasonal_pct=0.75
    )
    _, base = run_annual_projection(100)

    print(f"\n  PROJECTED PERFORMANCE (Year 1)")
    print(f"  {'':>25} {'Conservative':>16} {'Base Case':>16}")
    print("  " + "-" * 58)
    print(f"  {'Annual Revenue':<25} ${conservative['total_gross']:>15,.0f} ${base['total_gross']:>15,.0f}")
    print(f"  {'Annual NOI':<25} ${conservative['total_noi']:>15,.0f} ${base['total_noi']:>15,.0f}")
    print(f"  {'Free Cash Flow':<25} ${conservative['total_net_cash']:>15,.0f} ${base['total_net_cash']:>15,.0f}")
    print(f"  {'Annual DSCR':<25} {conservative['annual_dscr']:>15.2f}x {base['annual_dscr']:>15.2f}x")
    print(f"  {'Min Monthly DSCR':<25} {conservative['min_monthly_dscr']:>15.2f}x {base['min_monthly_dscr']:>15.2f}x")

    # Multi-year trajectory (base case)
    all_years = run_multi_year_projection()
    print(f"\n  PROJECTED TRAJECTORY (Base Case)")
    print(f"  {'':>25} ", end="")
    for yr, _, ann in all_years:
        print(f"{'Year ' + str(yr):>16}", end="")
    print()
    print("  " + "-" * (25 + 16 * len(all_years)))
    for yr, _, ann in all_years:
        pass  # just need the data
    row_data = [(yr, ann) for yr, _, ann in all_years]
    print(f"  {'Annual Revenue':<25} ", end="")
    for yr, ann in row_data:
        print(f"${ann['total_gross']:>14,.0f}", end="")
    print()
    print(f"  {'Free Cash Flow':<25} ", end="")
    for yr, ann in row_data:
        print(f"${ann['total_net_cash']:>14,.0f}", end="")
    print()
    print(f"  {'Annual DSCR':<25} ", end="")
    for yr, ann in row_data:
        print(f"{ann['annual_dscr']:>15.2f}x", end="")
    print()

    print(f"\n  REVENUE STREAMS (Base Case)")
    print(f"  {'Daily Bar Operations':<30} ${base['total_bar']:>14,.0f}")
    print(f"  {'COTA Events (bar + parking)':<30} ${base['total_cota_bar'] + base['total_cota_parking']:>14,.0f}")
    print(f"  {'Private Event Rentals':<30} ${base['total_rentals']:>14,.0f}")
    print(f"  {'LED Advertising':<30} ${base['total_led']:>14,.0f}")
    print(f"  {'Food Truck Partnerships':<30} ${base['total_trucks']:>14,.0f}")
    print(f"  {'Weekday Booster Programs':<30} ${base['total_boosters']:>14,.0f}")
    print(f"  {'Seasonal Events':<30} ${base['total_seasonal']:>14,.0f}")

    print(f"\n  BREAK-EVEN ANALYSIS")
    # Dynamically calculate break-even
    lo, hi = 10, 300
    while hi - lo > 1:
        mid = (lo + hi) // 2
        _, test = run_annual_projection(mid, cota_events_override={m: [] for m in range(1, 13)},
                                         booster_pct=0.0, seasonal_pct=0.0)
        if test["annual_dscr"] >= 1.0:
            hi = mid
        else:
            lo = mid
    be_monthly = hi * BLENDED_DAILY_CHECK * 30.4
    print(f"  {'Monthly break-even revenue:':<35} ${be_monthly:>10,.0f}")
    print(f"  {'Daily customers needed:':<35} {'~' + str(hi):>10}")
    penetration = (hi * 30.4 / LOCAL_HOUSEHOLDS) * 100
    print(f"  {'Household penetration required:':<35} {penetration:>9.1f}%")
    print(f"  {'Local households (ZIP 78617):':<35} {LOCAL_HOUSEHOLDS:>10,}")
    print(f"  {'Tesla employees nearby:':<35} {TESLA_EMPLOYEES:>10,}")
    print(f"  {'Annual COTA visitors:':<35} {ANNUAL_COTA_VISITORS:>10,}")

    print(f"\n  DANGER ZONE (from Expense Projection)")
    danger_monthly = 76_744
    print(f"  {'Monthly danger-zone revenue:':<35} ${danger_monthly:>10,}")
    print(f"  {'Below this = negative cash flow after all costs'}")

    print(f"\n  RISK MITIGANTS")
    print(f"  - Zero direct competition within 10-mile radius")
    print(f"  - 3-5 year first-mover advantage (below chain threshold)")
    print(f"  - Beverage-only model: $0 kitchen OpEx, 28-30% COGS")
    print(f"  - 4.5 acres with on-site septic = infrastructure moat")
    print(f"  - Outside COTA PUD = no square-footage caps on liquor")
    print(f"  - $580K post-construction equity cushion")
    print(f"  - 800 sqft LED wall = premium ad revenue asset")
    print(f"  - Weekday booster programs add $12K-$26K/mo incremental")


# =============================================================================
# SECTION 8: CUSTOM SCENARIO BUILDER
# =============================================================================

def run_custom_scenario():
    """Let the user input their own assumptions and see the result."""
    print(f"\n{'=' * 70}")
    print("  CUSTOM SCENARIO BUILDER")
    print("  (Press Enter to use default values)")
    print(f"{'=' * 70}")

    def get_input(prompt, default, cast=float):
        try:
            val = input(f"  {prompt} [{default}]: ").strip()
            return cast(val) if val else default
        except ValueError:
            print(f"    Invalid input, using default: {default}")
            return default

    custs = get_input("Daily customers", 100, int)
    wk = get_input("Weekday avg check ($)", 25.71)
    we = get_input("Weekend avg check ($)", 36.63)

    print(f"\n  COTA Event Counts (enter number of each type):")
    print(f"  (PDF defaults: 1×F1, 1×MotoGP, 1×NASCAR, 1×WEC, 2×GT/TransAm, 4×Concert, 2×Festival)")
    n_f1 = get_input("  F1 USGP", 1, int)
    n_motogp = get_input("  MotoGP", 1, int)
    n_nascar = get_input("  NASCAR", 1, int)
    n_wec = get_input("  WEC 6 Hours", 1, int)
    n_gt = get_input("  GT World / TransAm", 2, int)
    n_concert = get_input("  Major Concerts (Germania Amp)", 4, int)
    n_festival = get_input("  Festivals (FoodieLand, etc.)", 2, int)
    n_cota = n_f1 + n_motogp + n_nascar + n_wec + n_gt + n_concert + n_festival

    # Build event pool and distribute across calendar
    event_pool = (["tier1_f1"] * n_f1 + ["tier2_motogp"] * n_motogp
                  + ["tier2_nascar"] * n_nascar + ["tier3_wec"] * n_wec
                  + ["tier3_gt_transam"] * n_gt + ["tier3_concert"] * n_concert
                  + ["tier3_festival"] * n_festival)
    override = {m: [] for m in range(1, 13)}
    # Place fixed-month events first
    for tier_key in event_pool:
        if tier_key == "tier1_f1":
            override[10].append(tier_key)
        elif tier_key == "tier2_motogp":
            override[4].append(tier_key)
        elif tier_key == "tier2_nascar":
            override[3].append(tier_key)
        elif tier_key == "tier3_wec":
            override[2].append(tier_key)
    # Spread remaining events across available months
    flex_events = [t for t in event_pool if t in ("tier3_gt_transam", "tier3_concert", "tier3_festival")]
    flex_months = [4, 5, 6, 7, 8, 9, 10, 11]
    for i, tier_key in enumerate(flex_events):
        month = flex_months[i % len(flex_months)]
        override[month].append(tier_key)

    months, ann = run_annual_projection(
        custs, weekday_check=wk, weekend_check=we,
        cota_events_override=override
    )
    tier_desc = (f"{n_f1}×F1 + {n_motogp}×MotoGP + {n_nascar}×NASCAR + {n_wec}×WEC"
                 f" + {n_gt}×GT + {n_concert}×Concert + {n_festival}×Festival")
    print_annual_summary(months, ann, f"Custom: {custs} custs/day, ${wk}/${we} checks, {n_cota} COTA ({tier_desc})")


# =============================================================================
# SECTION 9: INTERACTIVE MENU
# =============================================================================

def print_menu():
    print(f"\n{'=' * 50}")
    print("  THE CUBE | Interactive Financial Model")
    print(f"{'=' * 50}")
    print("  1.  Full Annual Projection (Base Case)")
    print("  2.  Sensitivity Analysis")
    print("  3.  Break-Even Calculator")
    print("  4.  Monte Carlo Simulation (10K scenarios)")
    print("  5.  Scenario Comparison (5 scenarios)")
    print("  6.  Lender-Ready Summary")
    print("  7.  Custom Scenario Builder")
    print("  8.  Multi-Year Projection (Years 1-3)")
    print("  9.  Cash Reserve Tracker")
    print("  10. Cash Flow Waterfall (Year 1)")
    print("  11. Run ALL Reports")
    print("  0.  Exit")
    print(f"{'=' * 50}")


def main():
    while True:
        print_menu()
        try:
            choice = input("\n  Select option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if choice == "1":
            months, ann = run_annual_projection(100)
            print_annual_summary(months, ann, "BASE CASE: 100 customers/day, Year 1")
        elif choice == "2":
            run_sensitivity_analysis()
        elif choice == "3":
            run_breakeven_analysis()
        elif choice == "4":
            run_monte_carlo()
        elif choice == "5":
            run_scenario_comparison()
        elif choice == "6":
            print_lender_summary()
        elif choice == "7":
            run_custom_scenario()
        elif choice == "8":
            all_years = run_multi_year_projection()
            print_multi_year_summary(all_years)
        elif choice == "9":
            all_years = run_multi_year_projection()
            run_cash_reserve_tracker(all_years)
        elif choice == "10":
            months, ann = run_annual_projection(100)
            print_cash_flow_waterfall(months, ann)
        elif choice == "11":
            print("\n  Running ALL reports...\n")
            months, ann = run_annual_projection(100)
            print_annual_summary(months, ann, "BASE CASE: 100 customers/day, Year 1")
            print_cash_flow_waterfall(months, ann)
            run_sensitivity_analysis()
            run_breakeven_analysis()
            run_monte_carlo()
            run_scenario_comparison()
            all_years = run_multi_year_projection()
            print_multi_year_summary(all_years)
            run_cash_reserve_tracker(all_years)
            print_lender_summary()
            print(f"\n{'=' * 50}")
            print("  ALL REPORTS COMPLETE")
            print(f"{'=' * 50}")
        elif choice == "0":
            print("\n  Goodbye!")
            break
        else:
            print("  Invalid choice. Try again.")


if __name__ == "__main__":
    main()
