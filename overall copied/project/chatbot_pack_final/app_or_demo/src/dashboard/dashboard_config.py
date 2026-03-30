"""Configuration constants for the Phase 6 dashboard package."""

from __future__ import annotations

from dataclasses import dataclass


PAGE_BACKGROUND = "#F7F8FA"
CARD_BACKGROUND = "#FFFFFF"
CARD_BORDER = "#D9E0EA"
TEXT_PRIMARY = "#1F2937"
TEXT_SECONDARY = "#667085"
MUTED_NEUTRAL = "#B7C2D6"
DARK_NEUTRAL = "#344054"
GRIDLINE = "#E5E7EB"
CANADA_HIGHLIGHT = "#D52B1E"
CANADA_LIGHT_FILL = "#FDECEC"

RECOMMENDATION_STYLE = {
    "R1": {
        "label": "Build Career Moats for Talent",
        "scenario": "rec1_only",
        "dark": "#183B66",
        "core": "#4F7CCB",
        "light": "#AFC6F2",
        "tint": "#EEF4FF",
    },
    "R2": {
        "label": "Build the Conditions to Scale AI in Canada",
        "scenario": "rec2_only",
        "dark": "#7A4614",
        "core": "#D4832E",
        "light": "#F2BE84",
        "tint": "#FFF4E8",
    },
    "R3": {
        "label": "Stimulate B2B Demand via Adoption Credits",
        "scenario": "rec3_only",
        "dark": "#0F5C55",
        "core": "#2E9C8F",
        "light": "#98D9CF",
        "tint": "#EAF8F5",
    },
}

SCENARIO_LABELS = {
    "baseline": "Baseline",
    "rec1_only": "Rec 1 Only",
    "rec2_only": "Rec 2 Only",
    "rec3_only": "Rec 3 Only",
    "all_recommendations": "All Recs",
}

RECOMMENDATION_SCENARIO_CROSSWALK = {
    "Build Career Moats for Talent": "rec1_only",
    "Build the Conditions to Scale AI in Canada": "rec2_only",
    "Stimulate B2B Demand via Adoption Credits": "rec3_only",
}

DASHBOARD_A_TEXT = {
    "title": "Canada's AI competitiveness problem is conversion, not strategy",
    "subtitle": "Three federal-style actions to retain talent, scale firms, and create domestic demand",
    "success_title": "How we will know each recommendation is working",
    "success_subtitle": "Operational success metrics, separate from competitiveness KPIs",
    "gap_title": "Where each recommendation closes Canada's KPI gap by 2029Q4",
    "gap_subtitle": "Stand-alone impact vs peer-cluster best benchmark",
}

DASHBOARD_B_TEXT = {
    "title": "Policy timeline simulation: Canada's competitiveness path quarter by quarter",
    "subtitle": "Quarterly policy rollout, KPI movement, and rank position under the selected scenario",
    "timeline_title": "When the policy levers start to bite",
    "kpi_title": "Selected KPI trajectories",
    "kpi_subtitle": "Median path with optional p10-p90 band",
    "rank_title": "Canada's position versus the field",
}

PROBLEM_CARDS = [
    {
        "id": "R1",
        "title": "Canada's AI Talent Paradox",
        "diagnosis": "High acquisition, weak retention; Canada trains and attracts talent but leaks senior value creation south.",
        "evidence": ["20% attrition baseline"],
    },
    {
        "id": "R2",
        "title": "The Commercialization Valley of Death",
        "diagnosis": "Canada produces research and technical feasibility, but scale-up and domestic commercial capture remain weak.",
        "evidence": ["Commercial Ecosystem score = 10.27", "R2 contract conversion baseline proxy = 25%"],
    },
    {
        "id": "R3",
        "title": "Weak Market Validation / First-Customer Gap",
        "diagnosis": "Risk-averse adoption and weak first-buyer pathways stop domestic firms from proving market value.",
        "evidence": ["R3 conversion baseline proxy = 25%", "Launch-registry baseline proxy = 44 firms"],
    },
]

RECOMMENDATION_CARDS = [
    {
        "id": "R1",
        "title": "Build Career Moats for Talent",
        "objective": "Retain and attract senior AI builders so value creation compounds domestically.",
        "bullets": [
            "Elite equity tax exemption",
            "1:1 salary-matching tax credit",
            "AI Elite fast-track visa and PR mechanism",
        ],
        "horizon": "1-3 years",
    },
    {
        "id": "R2",
        "title": "Build the Conditions to Scale AI in Canada",
        "objective": "Close the commercialization valley so scale-ups can survive and grow in Canada.",
        "bullets": [
            "Compute utilization and access support",
            "Procurement and pilot-to-contract conversion",
            "Growth-stage co-investment and later-stage capital",
        ],
        "horizon": "1-3 years",
    },
    {
        "id": "R3",
        "title": "Stimulate B2B Demand via Adoption Credits",
        "objective": "Create first-customer pull that converts pilots into durable commercial traction.",
        "bullets": [
            "Refundable first-customer AI adoption credit",
            "Canadian-owned and Canadian-IP eligibility rules",
            "Conversion mandate with clawback logic",
        ],
        "horizon": "1-3 years",
    },
]

DEFAULT_KPI_WATCHLIST = [
    "Tortoise Talent Score",
    "Tortoise Commercial Score",
    "AI Investment Activity",
    "AI Adoption (%)",
    "Tortoise Development Score",
]

A4_DEFAULT_KPIS = {
    "rec1_only": [
        "Tortoise Talent Score",
        "Relative AI Skill Penetration",
        "Net Migration Flow of AI Skills",
    ],
    "rec2_only": [
        "Tortoise Commercial Score",
        "AI Investment Activity",
        "AI Adoption (%)",
    ],
    "rec3_only": [
        "AI Adoption (%)",
        "Tortoise Commercial Score",
        "AI Investment Activity",
    ],
}

COUNTRY_STYLE_MAP = {
    "Canada": {"color": "#D52B1E", "flag": "🇨🇦", "short": "Canada"},
    "United States of America": {"color": "#1F3B73", "flag": "🇺🇸", "short": "USA"},
    "China": {"color": "#DE2910", "flag": "🇨🇳", "short": "China"},
    "South Korea": {"color": "#0A4EA3", "flag": "🇰🇷", "short": "South Korea"},
    "Singapore": {"color": "#D50032", "flag": "🇸🇬", "short": "Singapore"},
    "United Kingdom": {"color": "#012169", "flag": "🇬🇧", "short": "UK"},
    "Germany": {"color": "#1A1A1A", "flag": "🇩🇪", "short": "Germany"},
    "India": {"color": "#138808", "flag": "🇮🇳", "short": "India"},
    "Israel": {"color": "#0038B8", "flag": "🇮🇱", "short": "Israel"},
    "France": {"color": "#0055A4", "flag": "🇫🇷", "short": "France"},
    "UAE": {"color": "#00732F", "flag": "🇦🇪", "short": "UAE"},
    "Japan": {"color": "#BC002D", "flag": "🇯🇵", "short": "Japan"},
    "Spain": {"color": "#AA151B", "flag": "🇪🇸", "short": "Spain"},
}


@dataclass(frozen=True, slots=True)
class DashboardExportPaths:
    """Static export paths for dashboard deliverables."""

    html: str = "outputs/dashboard/final_dashboard.html"
    dashboard_a_png: str = "outputs/dashboard/dashboard_a_snapshot.png"
    dashboard_b_png: str = "outputs/dashboard/dashboard_b_snapshot.png"
    build_notes: str = "outputs/reports/dashboard_build_notes.md"
    inventory: str = "outputs/reports/dashboard_data_inventory.md"
    unresolved: str = "outputs/reports/dashboard_unresolved_dependencies.md"
