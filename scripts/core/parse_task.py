#!/usr/bin/env python3
"""Natural Language Task Intake — parse a plain-English GIS task into a project brief.

Reads methodology templates from templates/methodologies/, pattern-matches the task
description to the best template, extracts geography + question type, performs a
FIPS lookup, and outputs a populated project_brief.json ready for the lead analyst
to review before spawning agents.

Usage:
    python parse_task.py --task "Map healthcare access gaps in rural Kansas counties" \\
                         --output analyses/my-project/project_brief.json

    python parse_task.py --task "..." --interactive   # asks one clarifying question if ambiguous
    python parse_task.py --task "..." --output /path/to/brief.json --interactive
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METHODOLOGIES_DIR = PROJECT_ROOT / "templates" / "methodologies"
BRIEF_TEMPLATE_PATH = PROJECT_ROOT / "templates" / "project_brief.json"
ANALYSES_DIR = PROJECT_ROOT / "analyses"

# ---------------------------------------------------------------------------
# FIPS reference tables (no external deps — embedded for offline use)
# ---------------------------------------------------------------------------

# State name / abbreviation → FIPS code
STATE_FIPS: dict[str, str] = {
    "alabama": "01", "alaska": "02", "arizona": "04", "arkansas": "05",
    "california": "06", "colorado": "08", "connecticut": "09", "delaware": "10",
    "district of columbia": "11", "dc": "11", "florida": "12", "georgia": "13",
    "hawaii": "15", "idaho": "16", "illinois": "17", "indiana": "18",
    "iowa": "19", "kansas": "20", "kentucky": "21", "louisiana": "22",
    "maine": "23", "maryland": "24", "massachusetts": "25", "michigan": "26",
    "minnesota": "27", "mississippi": "28", "missouri": "29", "montana": "30",
    "nebraska": "31", "nevada": "32", "new hampshire": "33", "new jersey": "34",
    "new mexico": "35", "new york": "36", "north carolina": "37",
    "north dakota": "38", "ohio": "39", "oklahoma": "40", "oregon": "41",
    "pennsylvania": "42", "rhode island": "44", "south carolina": "45",
    "south dakota": "46", "tennessee": "47", "texas": "48", "utah": "49",
    "vermont": "50", "virginia": "51", "washington": "53",
    "west virginia": "54", "wisconsin": "55", "wyoming": "56",
    # abbreviations
    "al": "01", "ak": "02", "az": "04", "ar": "05", "ca": "06", "co": "08",
    "ct": "09", "de": "10", "fl": "12", "ga": "13", "hi": "15", "id": "16",
    "il": "17", "in": "18", "ia": "19", "ks": "20", "ky": "21", "la": "22",
    "me": "23", "md": "24", "ma": "25", "mi": "26", "mn": "27", "ms": "28",
    "mo": "29", "mt": "30", "ne": "31", "nv": "32", "nh": "33", "nj": "34",
    "nm": "35", "ny": "36", "nc": "37", "nd": "38", "oh": "39", "ok": "40",
    "or": "41", "pa": "42", "ri": "44", "sc": "45", "sd": "46", "tn": "47",
    "tx": "48", "ut": "49", "vt": "50", "va": "51", "wa": "53",
    "wv": "54", "wi": "55", "wy": "56",
}

STATE_NAME_CANONICAL: dict[str, str] = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
    "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
    "11": "District of Columbia", "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa", "20": "Kansas",
    "21": "Kentucky", "22": "Louisiana", "23": "Maine", "24": "Maryland",
    "25": "Massachusetts", "26": "Michigan", "27": "Minnesota", "28": "Mississippi",
    "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada",
    "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico", "36": "New York",
    "37": "North Carolina", "38": "North Dakota", "39": "Ohio", "40": "Oklahoma",
    "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island",
    "45": "South Carolina", "46": "South Dakota", "47": "Tennessee", "48": "Texas",
    "49": "Utah", "50": "Vermont", "51": "Virginia", "53": "Washington",
    "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming",
}

# A small county→FIPS lookup for common metros (expandable)
COUNTY_FIPS: dict[str, str] = {
    "cook county": "17031",
    "los angeles county": "06037",
    "harris county": "48201",
    "maricopa county": "04013",
    "san diego county": "06073",
    "orange county": "06059",
    "kings county": "36047",
    "miami-dade county": "12086",
    "dallas county": "48113",
    "tarrant county": "48439",
    "king county": "53033",
    "wayne county": "26163",
    "franklin county": "39049",
    "bexar county": "48029",
    "travis county": "48453",
}

# City → county FIPS (representative county) for common cities
CITY_TO_COUNTY_FIPS: dict[str, str] = {
    "chicago": "17031",
    "los angeles": "06037",
    "houston": "48201",
    "phoenix": "04013",
    "san antonio": "48029",
    "san diego": "06073",
    "dallas": "48113",
    "san jose": "06085",
    "austin": "48453",
    "jacksonville": "12031",
    "fort worth": "48439",
    "columbus": "39049",
    "charlotte": "37119",
    "indianapolis": "18097",
    "seattle": "53033",
    "denver": "08031",
    "washington": "11001",
    "nashville": "47037",
    "oklahoma city": "40109",
    "el paso": "48141",
    "boston": "25025",
    "portland": "41051",
    "las vegas": "32003",
    "memphis": "47157",
    "louisville": "21111",
    "baltimore": "24510",
    "milwaukee": "55079",
    "albuquerque": "35001",
    "tucson": "04019",
    "fresno": "06019",
    "sacramento": "06067",
    "kansas city": "29095",
    "mesa": "04013",
    "atlanta": "13121",
    "omaha": "31055",
    "colorado springs": "08041",
    "raleigh": "37183",
    "minneapolis": "27053",
    "new orleans": "22071",
    "cleveland": "39035",
    "detroit": "26163",
    "miami": "12086",
    "new york": "36061",
    "brooklyn": "36047",
    "bronx": "36005",
    "queens": "36081",
    "manhattan": "36061",
    "philadelphia": "42101",
    "pittsburgh": "42003",
    "cincinnati": "39061",
    "st. louis": "29510",
    "saint louis": "29510",
}

# ---------------------------------------------------------------------------
# Question type / methodology patterns
# ---------------------------------------------------------------------------

QUESTION_TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    # (canonical_question_type, [keyword patterns])
    ("healthcare_access_gap", [
        r"\bhealthcare?\b", r"\bhealth\s+access\b", r"\bhospital\b", r"\bclinic\b",
        r"\bfqhc\b", r"\bmedical\b", r"\binsur(ed|ance|ance\s+gap)\b",
        r"\buninsur\b", r"\bprimary\s+care\b", r"\bphysician\b",
        r"\bhpsa\b", r"\bmedically\s+underserved\b",
    ]),
    ("food_access_gap", [
        r"\bfood\s+(access|deserts?|insecurity|gap)\b", r"\bgrocery\b",
        r"\bsupermarket\b", r"\bfood\s+pantry\b", r"\bhunger\b",
        r"\bnutrition\b", r"\bsnap\b", r"\busda\s+food\b",
    ]),
    ("environmental_justice", [
        r"\benvironmental\s+justice\b", r"\bej\b", r"\bejscreen\b",
        r"\bpollution\b", r"\btoxic\b", r"\bsuperfund\b", r"\bair\s+quality\b",
        r"\bnoise\b", r"\bhazardous\b", r"\bcontaminat\b", r"\bexposure\b",
    ]),
    ("poverty_socioeconomic", [
        r"\bpoverty\b", r"\bpoor\b", r"\blow[- ]income\b", r"\bsocioeconomic\b",
        r"\bmedian\s+income\b", r"\bhousehold\s+income\b", r"\bsnap\b",
        r"\bunemployment\b", r"\bwages?\b",
    ]),
    ("hazard_risk", [
        r"\bhazard\b", r"\bflood\b", r"\bfema\b", r"\bwildfire\b",
        r"\bearthquake\b", r"\bhurricane\b", r"\btornado\b", r"\brisk\b",
        r"\bdisaster\b", r"\bemergency\b", r"\bevacuation\b",
    ]),
    ("demographic_change", [
        r"\bpopulation\s+change\b", r"\bgentrification\b", r"\bdemographic\b",
        r"\bmigration\b", r"\bgrowth\b", r"\bdecline\b", r"\baging\b",
        r"\brace\b", r"\bethnic\b",
    ]),
    ("transit_mobility", [
        r"\btransit\b", r"\btransportation\b", r"\bcommute\b", r"\bbike\b",
        r"\bwalk\b", r"\bbus\b", r"\btrain\b", r"\bpublic\s+transport\b",
        r"\bcar[- ]free\b", r"\bno[\s-]vehicle\b",
    ]),
    ("education_access", [
        r"\beducat\b", r"\bschool\b", r"\bcollege\b", r"\buniversity\b",
        r"\bliteracy\b", r"\bgraduat\b", r"\bdropout\b",
    ]),
]

# Methodology template file → question types it serves
METHODOLOGY_COVERAGE: dict[str, list[str]] = {
    "healthcare-access-gap": ["healthcare_access_gap"],
    # These don't exist yet but parse_task will fall back gracefully
    "food-access-gap": ["food_access_gap"],
    "environmental-justice": ["environmental_justice"],
    "poverty-analysis": ["poverty_socioeconomic"],
    "hazard-risk": ["hazard_risk"],
    "demographic-change": ["demographic_change"],
    "transit-mobility": ["transit_mobility"],
    "education-access": ["education_access"],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert arbitrary text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:64].strip("-")


def score_question_type(task_lower: str) -> list[tuple[str, int]]:
    """Return (question_type, match_count) sorted by descending match count."""
    scores: dict[str, int] = {}
    for qtype, patterns in QUESTION_TYPE_PATTERNS:
        count = sum(1 for p in patterns if re.search(p, task_lower))
        if count:
            scores[qtype] = count
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def extract_geography(task: str) -> dict[str, Any]:
    """
    Pull geographic signal from the task string.

    Returns:
        {
          "study_area": str,         # human-readable label
          "geo_level": str,          # "city" | "county" | "state" | "national" | "unknown"
          "state_fips": str | None,
          "county_fips": str | None,
          "geographic_unit": str,    # recommended unit of analysis
          "ambiguous": bool,
        }
    """
    task_lower = task.lower()
    result: dict[str, Any] = {
        "study_area": "",
        "geo_level": "unknown",
        "state_fips": None,
        "county_fips": None,
        "geographic_unit": "tract",
        "ambiguous": False,
    }

    # Check city names first (most specific)
    for city, county_fips in sorted(CITY_TO_COUNTY_FIPS.items(), key=lambda x: -len(x[0])):
        if city in task_lower:
            state_fips = county_fips[:2]
            state_name = STATE_NAME_CANONICAL.get(state_fips, "")
            result.update({
                "study_area": f"{city.title()}, {state_name}",
                "geo_level": "city",
                "state_fips": state_fips,
                "county_fips": county_fips,
                "geographic_unit": "tract",
            })
            return result

    # Check county names
    for county, county_fips in sorted(COUNTY_FIPS.items(), key=lambda x: -len(x[0])):
        if county in task_lower:
            state_fips = county_fips[:2]
            state_name = STATE_NAME_CANONICAL.get(state_fips, "")
            result.update({
                "study_area": f"{county.title()}, {state_name}",
                "geo_level": "county",
                "state_fips": state_fips,
                "county_fips": county_fips,
                "geographic_unit": "tract",
            })
            return result

    # Check for "X County" pattern in task
    county_pattern = re.search(
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County\b', task
    )
    if county_pattern:
        county_raw = county_pattern.group(0).lower()
        # Try to find state nearby
        state_fips_found = None
        state_name_found = ""
        for state_name_key, fips in STATE_FIPS.items():
            if len(state_name_key) > 2 and state_name_key in task_lower:
                state_fips_found = fips
                state_name_found = STATE_NAME_CANONICAL.get(fips, state_name_key.title())
                break
        result.update({
            "study_area": county_raw.title() + (f", {state_name_found}" if state_name_found else ""),
            "geo_level": "county",
            "state_fips": state_fips_found,
            "county_fips": None,   # unknown without full FIPS DB
            "geographic_unit": "tract",
        })
        if not state_fips_found:
            result["ambiguous"] = True
        return result

    # Check for "statewide" / "across X" / state names
    for state_name_key in sorted(STATE_FIPS.keys(), key=lambda x: -len(x)):
        if len(state_name_key) <= 2:
            # Only match abbreviations as standalone words to avoid false positives
            if re.search(rf'\b{re.escape(state_name_key.upper())}\b', task):
                fips = STATE_FIPS[state_name_key]
                result.update({
                    "study_area": STATE_NAME_CANONICAL.get(fips, state_name_key.title()),
                    "geo_level": "state",
                    "state_fips": fips,
                    "county_fips": None,
                    "geographic_unit": "tract",
                })
                return result
        else:
            if state_name_key in task_lower:
                fips = STATE_FIPS[state_name_key]
                result.update({
                    "study_area": STATE_NAME_CANONICAL.get(fips, state_name_key.title()),
                    "geo_level": "state",
                    "state_fips": fips,
                    "county_fips": None,
                    "geographic_unit": "tract",
                })
                return result

    # National / no specific geography
    if any(kw in task_lower for kw in ["national", "nationwide", "united states", "u.s.", "usa"]):
        result.update({
            "study_area": "United States (national)",
            "geo_level": "national",
            "geographic_unit": "county",
        })
        return result

    result["ambiguous"] = True
    return result


def detect_geo_unit_override(task_lower: str, default: str) -> str:
    """Override geographic unit based on explicit task mentions."""
    if re.search(r'\bcounty\b|\bcounties\b', task_lower) and "tract" in default:
        return "county"
    if re.search(r'\bblock\s+group\b', task_lower):
        return "block_group"
    if re.search(r'\bzip\b|\bzip\s+code\b|\bzcta\b', task_lower):
        return "zip"
    if re.search(r'\btract\b|\bcensus\s+tract\b', task_lower):
        return "tract"
    return default


def load_methodology_template(methodology_id: str) -> dict[str, Any] | None:
    """Load a methodology template JSON if it exists."""
    path = METHODOLOGIES_DIR / f"{methodology_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None
    return None


def load_base_template() -> dict[str, Any]:
    """Load the base project_brief.json template."""
    if BRIEF_TEMPLATE_PATH.exists():
        return json.loads(BRIEF_TEMPLATE_PATH.read_text())
    # Minimal fallback if template file is missing
    return {
        "_version": "1.0",
        "project_id": "",
        "project_title": "",
        "created_at": "",
        "created_by": "parse_task.py",
        "client": {"name": "", "type": "", "notes": ""},
        "audience": {"primary_reader": "", "role": "", "technical_level": "medium",
                     "what_they_are_deciding": "", "what_they_already_believe": "",
                     "political_or_institutional_context": ""},
        "engagement": {"hero_question": "", "deliverable_type": "external",
                       "deadline": "", "budget_tier": "standard",
                       "sensitive_findings_to_handle_carefully": []},
        "geography": {"study_area": "", "geographic_unit": "tract",
                      "crs_epsg": "4326", "bounding_box": None,
                      "known_spatial_issues": []},
        "data": {"primary_sources": [], "vintage": "",
                 "known_data_quality_issues": [], "institutional_areas_to_flag": [],
                 "join_key": "GEOID"},
        "analysis": {"dependent_variable": "", "independent_variables": [],
                     "analysis_types_requested": [], "spatial_weights": "queen",
                     "classification_scheme": "natural_breaks", "k_classes": 5},
        "outputs": {"required_maps": [], "required_statistics": [],
                    "required_formats": ["markdown", "html"],
                    "executive_brief_required": True, "technical_appendix_required": False,
                    "web_map_required": False, "qgis_package_required": True,
                    "print_pdf_required": False},
        "report": {"tone": "plain", "pyramid_lead": "", "scqa": {
            "situation": "", "complication": "", "question": "", "answer": ""}},
        "qa": {"max_null_pct": 15, "min_join_rate": 0.85,
               "require_morans_gate": True, "flag_institutions": True},
        "handoff_log": [],
    }


def extract_client_context(task: str) -> dict[str, str]:
    """Heuristically pull client / audience signals from task text."""
    task_lower = task.lower()
    client_type = ""
    primary_reader = ""

    if any(k in task_lower for k in ["grant", "foundation", "nonprofit", "ngo"]):
        client_type = "nonprofit"
        primary_reader = "Grant writer or program officer"
    elif any(k in task_lower for k in ["county", "city", "municipality", "planning department"]):
        client_type = "government"
        primary_reader = "Local government planner"
    elif any(k in task_lower for k in ["health department", "public health", "dhhs", "dph"]):
        client_type = "public_health"
        primary_reader = "Public health official"
    elif any(k in task_lower for k in ["hospital", "health system", "fqhc", "clinic"]):
        client_type = "health_system"
        primary_reader = "Health system administrator"
    elif any(k in task_lower for k in ["developer", "real estate", "investment"]):
        client_type = "private"
        primary_reader = "Real estate developer or investor"
    elif any(k in task_lower for k in ["internal", "benchmark", "test"]):
        client_type = "internal"
        primary_reader = "Internal analyst"
    else:
        client_type = "unknown"
        primary_reader = ""

    return {"client_type": client_type, "primary_reader": primary_reader}


def build_analysis_recommendations(
    question_type: str,
    methodology_template: dict[str, Any] | None,
    geo: dict[str, Any],
    task_lower: str,
) -> dict[str, Any]:
    """
    Merge methodology template analysis section with task-specific overrides.
    Returns analysis dict + data sources + output requirements.
    """
    if methodology_template and "analysis" in methodology_template:
        analysis = dict(methodology_template["analysis"])
        data_sources = methodology_template.get("data", {}).get("primary_sources", [])
        required_maps = methodology_template.get("outputs", {}).get("required_maps", [])
    else:
        # Generic fallbacks by question type
        analysis, data_sources, required_maps = _generic_analysis(question_type, task_lower)

    return {"analysis": analysis, "data": data_sources, "required_maps": required_maps}


def _generic_analysis(question_type: str, task_lower: str) -> tuple[dict, list, list]:
    """Return generic analysis/data/maps for question types without a template."""
    base_analysis = {
        "spatial_weights": "queen",
        "classification_scheme": "natural_breaks",
        "k_classes": 5,
        "analysis_types_requested": [],
        "independent_variables": [],
    }

    if question_type == "food_access_gap":
        base_analysis.update({
            "dependent_variable": "food_desert_flag or low_access_pct",
            "independent_variables": ["poverty_rate", "pct_no_vehicle", "median_income"],
            "analysis_types_requested": [
                "Choropleth: food desert flag by tract",
                "Drive-time service areas: 10/20/30 min from grocery stores",
                "Hotspot analysis: food desert clustering (Gi*)",
                "Dot density: population in food desert tracts",
            ],
        })
        data_sources = [
            {"name": "USDA Food Access Research Atlas", "url": "https://www.ers.usda.gov/data-products/food-access-research-atlas/"},
            {"name": "ACS 5-Year Estimates (poverty, vehicles)", "url": "https://data.census.gov"},
            {"name": "TIGER/Line Tracts", "fetch_script": "retrieve_tiger.py"},
            {"name": "OSM Grocery Stores (via Overpass)", "url": "https://overpass-api.de"},
        ]
        required_maps = ["food_desert_choropleth", "grocery_service_areas", "population_dot_density"]

    elif question_type == "environmental_justice":
        base_analysis.update({
            "dependent_variable": "ejscreen_score or pollution_percentile",
            "independent_variables": ["pct_minority", "poverty_rate", "proximity_to_facility"],
            "analysis_types_requested": [
                "Choropleth: EJScreen composite index by tract",
                "Bivariate: pollution burden vs demographic vulnerability",
                "Hotspot analysis: cumulative burden clustering",
                "Proportional symbols: facility proximity",
            ],
        })
        data_sources = [
            {"name": "EPA EJScreen", "url": "https://ejscreen.epa.gov/mapper/"},
            {"name": "EPA ECHO Facility Data", "url": "https://echo.epa.gov/"},
            {"name": "ACS 5-Year Estimates (demographics)", "url": "https://data.census.gov"},
            {"name": "TIGER/Line Tracts", "fetch_script": "retrieve_tiger.py"},
        ]
        required_maps = ["ejscreen_choropleth", "bivariate_burden_vulnerability", "facility_overlay"]

    elif question_type == "poverty_socioeconomic":
        base_analysis.update({
            "dependent_variable": "poverty_rate",
            "independent_variables": ["median_income", "unemployment_rate", "pct_no_hs_diploma"],
            "analysis_types_requested": [
                "Choropleth: poverty rate by tract",
                "Hotspot analysis: poverty clustering (Gi*)",
                "Bivariate: poverty vs unemployment",
                "Change detection: poverty rate vs prior ACS vintage",
            ],
        })
        data_sources = [
            {"name": "ACS 5-Year Estimates (B17001 poverty, S1901 income)", "url": "https://data.census.gov", "fetch_script": "fetch_acs_data.py"},
            {"name": "TIGER/Line Tracts", "fetch_script": "retrieve_tiger.py"},
        ]
        required_maps = ["poverty_rate_choropleth", "poverty_hotspots", "bivariate_poverty_unemployment"]

    elif question_type == "hazard_risk":
        base_analysis.update({
            "dependent_variable": "risk_score or flood_zone_flag",
            "independent_variables": ["poverty_rate", "pct_elderly", "housing_age"],
            "analysis_types_requested": [
                "Choropleth: hazard risk by tract",
                "Overlay: hazard zones + vulnerable population",
                "Hotspot analysis: risk clustering",
            ],
        })
        data_sources = [
            {"name": "FEMA National Flood Hazard Layer", "url": "https://msc.fema.gov/portal/"},
            {"name": "ACS 5-Year Estimates (demographics)", "url": "https://data.census.gov"},
            {"name": "TIGER/Line Tracts", "fetch_script": "retrieve_tiger.py"},
        ]
        required_maps = ["hazard_zone_choropleth", "vulnerable_population_overlay"]

    elif question_type == "transit_mobility":
        base_analysis.update({
            "dependent_variable": "pct_no_vehicle or transit_score",
            "independent_variables": ["poverty_rate", "employment_rate", "distance_to_transit"],
            "analysis_types_requested": [
                "Choropleth: vehicle access by tract",
                "Service areas: transit stop coverage",
                "Bivariate: vehicle access vs poverty",
            ],
        })
        data_sources = [
            {"name": "ACS 5-Year Estimates (B08201 vehicles)", "url": "https://data.census.gov", "fetch_script": "fetch_acs_data.py"},
            {"name": "GTFS Transit Feeds", "url": "https://transitfeeds.com"},
            {"name": "TIGER/Line Tracts", "fetch_script": "retrieve_tiger.py"},
        ]
        required_maps = ["vehicle_access_choropleth", "transit_service_areas"]

    else:
        # Generic demographic / unknown
        base_analysis.update({
            "dependent_variable": "key_indicator (to be determined)",
            "analysis_types_requested": [
                "Choropleth: primary indicator by unit",
                "Hotspot analysis (pending Moran's I gate)",
                "Summary statistics by jurisdiction",
            ],
        })
        data_sources = [
            {"name": "ACS 5-Year Estimates", "url": "https://data.census.gov", "fetch_script": "fetch_acs_data.py"},
            {"name": "TIGER/Line Boundaries", "fetch_script": "retrieve_tiger.py"},
        ]
        required_maps = ["primary_indicator_choropleth"]

    return base_analysis, data_sources, required_maps


def generate_clarifying_question(
    question_types: list[tuple[str, int]],
    geo: dict[str, Any],
) -> str:
    """
    Generate ONE focused clarifying question for the most ambiguous dimension.
    Priority: geography ambiguity > question type ambiguity.
    """
    if geo["ambiguous"] and not geo["state_fips"]:
        return (
            "What is the geographic scope? "
            "(e.g., a specific state, county, or city — I need a place name to proceed)"
        )

    if geo["ambiguous"] and geo["county_fips"] is None and geo["state_fips"]:
        return (
            f"Should this analysis cover the entire state of "
            f"{STATE_NAME_CANONICAL.get(geo['state_fips'], geo['state_fips'])}, "
            f"or are you focused on a specific county or city within it?"
        )

    if len(question_types) >= 2:
        top_two = [q[0].replace("_", " ") for q in question_types[:2]]
        return (
            f"Is the primary question about {top_two[0]} or {top_two[1]}? "
            f"That will determine which data sources and methods I recommend."
        )

    if not question_types:
        return (
            "What is the core analytic question? For example: "
            "access gap, environmental justice, poverty change, hazard risk, or demographic shift?"
        )

    return (
        "Who is the primary audience and what decision will this analysis support? "
        "(e.g., siting a facility, targeting outreach, making a policy case)"
    )


# ---------------------------------------------------------------------------
# Brief assembly
# ---------------------------------------------------------------------------

def build_project_brief(
    task: str,
    question_type: str,
    geo: dict[str, Any],
    methodology_template: dict[str, Any] | None,
    client_ctx: dict[str, str],
) -> dict[str, Any]:
    """Assemble a populated project_brief.json from all extracted signals."""
    base = load_base_template()
    recs = build_analysis_recommendations(question_type, methodology_template, geo, task.lower())

    now = datetime.now(UTC).isoformat()

    # Build hero question: trim filler, capitalize properly
    hero = task.strip()
    hero = re.sub(r'^(please\s+|can\s+you\s+|i\s+need\s+(you\s+to\s+)?|we\s+need\s+to\s+)',
                  '', hero, flags=re.IGNORECASE).strip()
    hero = hero[0].upper() + hero[1:] if hero else task

    # Project ID
    geo_slug = slugify(geo["study_area"].split(",")[0]) if geo["study_area"] else "unknown-geography"
    type_slug = question_type.replace("_", "-")
    project_id = f"{geo_slug}-{type_slug}"

    # Geographic unit: allow task-level override
    geo_unit = detect_geo_unit_override(task.lower(), geo["geographic_unit"])

    # Build SCQA skeleton
    study_area = geo["study_area"] or "[study area]"
    scqa = {
        "situation": f"{study_area} has variable patterns in {question_type.replace('_', ' ')}.",
        "complication": "Simple counts or averages miss the spatial concentration of need.",
        "question": hero,
        "answer": "TBD — to be filled in by report-writer after analysis.",
    }
    if methodology_template and "report" in methodology_template:
        tmpl_scqa = methodology_template["report"].get("scqa", {})
        for k in ["situation", "complication"]:
            if tmpl_scqa.get(k):
                scqa[k] = tmpl_scqa[k]

    brief = {
        **base,
        "_generated_by": "parse_task.py",
        "_parse_confidence": "review-required",
        "project_id": project_id,
        "project_title": f"{question_type.replace('_', ' ').title()} — {study_area}",
        "created_at": now,
        "created_by": "parse_task.py (lead-analyst review required)",
        "client": {
            "name": "",
            "type": client_ctx.get("client_type", ""),
            "contact": "",
            "notes": "Auto-parsed from natural language task. Verify with client before proceeding.",
        },
        "audience": {
            **base.get("audience", {}),
            "primary_reader": client_ctx.get("primary_reader", ""),
            "role": client_ctx.get("primary_reader", ""),
            "technical_level": "medium",
            "what_they_are_deciding": "TBD — review with client",
            "what_they_already_believe": "TBD — review with client",
            "political_or_institutional_context": "",
        },
        "engagement": {
            "hero_question": hero,
            "deliverable_type": "external",
            "deadline": "",
            "budget_tier": "standard",
            "sensitive_findings_to_handle_carefully": [],
        },
        "geography": {
            "study_area": study_area,
            "geographic_unit": geo_unit,
            "crs_epsg": "4326",
            "bounding_box": None,
            "state_fips": geo.get("state_fips"),
            "county_fips": geo.get("county_fips"),
            "geo_level": geo.get("geo_level", "unknown"),
            "known_spatial_issues": (
                methodology_template.get("geography", {}).get("known_spatial_issues", [])
                if methodology_template else []
            ),
        },
        "data": {
            "primary_sources": recs["data"],
            "vintage": "Use most recent available ACS 5-year vintage",
            "known_data_quality_issues": (
                methodology_template.get("data", {}).get("known_data_quality_issues", [])
                if methodology_template else []
            ),
            "institutional_areas_to_flag": (
                methodology_template.get("data", {}).get("institutional_areas_to_flag", [])
                if methodology_template else []
            ),
            "join_key": "GEOID",
        },
        "analysis": recs["analysis"],
        "outputs": {
            **base.get("outputs", {}),
            "required_maps": recs["required_maps"],
            "executive_brief_required": True,
            "qgis_package_required": True,
            "web_map_required": False,
        },
        "report": {
            "tone": "plain",
            "pyramid_lead": f"TBD — fill in after analysis of {study_area}.",
            "scqa": scqa,
            "key_findings_draft": [],
        },
        "qa": {
            "max_null_pct": 15,
            "min_join_rate": 0.85,
            "require_morans_gate": True,
            "flag_institutions": True,
        },
        "handoff_log": [],
        "_methodology_matched": (
            methodology_template.get("_methodology_id", "none")
            if methodology_template else "none — generic template used"
        ),
        "_question_type_detected": question_type,
        "_parse_notes": (
            "Auto-generated by parse_task.py. Lead analyst MUST review before spawning agents. "
            "Pay special attention to: geography (FIPS), hero question phrasing, "
            "analysis types, and audience fields."
        ),
    }

    return brief


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a natural language GIS task into a structured project brief.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Natural language task description (quote the whole string)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write project_brief.json. Defaults to analyses/<project_id>/project_brief.json",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="If ambiguous, ask ONE clarifying question before writing the brief",
    )
    args = parser.parse_args()

    task = args.task.strip()
    task_lower = task.lower()

    print("=" * 60)
    print("parse_task.py — GIS Natural Language Task Intake")
    print("=" * 60)
    print(f"\nTask: {task}\n")

    # 1. Score question types
    question_type_scores = score_question_type(task_lower)
    top_question_type = question_type_scores[0][0] if question_type_scores else "unknown"
    is_question_type_ambiguous = (
        len(question_type_scores) >= 2
        and question_type_scores[0][1] == question_type_scores[1][1]
    ) or not question_type_scores

    # 2. Extract geography
    geo = extract_geography(task)

    # 3. Determine overall ambiguity
    is_ambiguous = geo["ambiguous"] or is_question_type_ambiguous

    # 4. Interactive clarification
    if args.interactive and is_ambiguous:
        clarifying_q = generate_clarifying_question(question_type_scores, geo)
        print("─" * 60)
        print("CLARIFYING QUESTION:")
        print(f"  {clarifying_q}")
        print("─" * 60)
        answer = input("Your answer (press Enter to skip): ").strip()
        if answer:
            # Re-parse with the additional context appended
            combined = f"{task}. {answer}"
            task_lower = combined.lower()
            question_type_scores = score_question_type(task_lower)
            top_question_type = question_type_scores[0][0] if question_type_scores else "unknown"
            geo = extract_geography(combined)
            is_ambiguous = geo["ambiguous"] or (not question_type_scores)
            print()

    # 5. Load best methodology template
    methodology_template: dict[str, Any] | None = None
    matched_methodology = "none"
    for meth_id, covered_types in METHODOLOGY_COVERAGE.items():
        if top_question_type in covered_types:
            methodology_template = load_methodology_template(meth_id)
            if methodology_template:
                matched_methodology = meth_id
                break

    # 6. Extract client context
    client_ctx = extract_client_context(task)

    # 7. Build the brief
    brief = build_project_brief(task, top_question_type, geo, methodology_template, client_ctx)

    # 8. Resolve output path
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_path = ANALYSES_DIR / brief["project_id"] / "project_brief.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(brief, indent=2))

    # 9. Print inference summary
    print("INFERENCE SUMMARY")
    print("─" * 60)
    print(f"  Project ID       : {brief['project_id']}")
    print(f"  Question type    : {top_question_type}")
    if question_type_scores:
        score_str = ", ".join(f"{q}({s})" for q, s in question_type_scores[:3])
        print(f"  Type scores      : {score_str}")
    print(f"  Geography        : {geo['study_area'] or '(not detected)'}")
    print(f"  Geo level        : {geo['geo_level']}")
    print(f"  State FIPS       : {geo['state_fips'] or '(not found)'}")
    print(f"  County FIPS      : {geo['county_fips'] or '(not found)'}")
    print(f"  Unit of analysis : {brief['geography']['geographic_unit']}")
    print(f"  Methodology tmpl : {matched_methodology}")
    print(f"  Client type      : {client_ctx['client_type'] or '(not detected)'}")
    print(f"  Ambiguous        : {'YES — review carefully' if is_ambiguous else 'no'}")
    print()
    print("HERO QUESTION")
    print(f"  {brief['engagement']['hero_question']}")
    print()
    print("RECOMMENDED ANALYSES")
    for a in brief["analysis"].get("analysis_types_requested", []):
        print(f"  • {a}")
    print()
    print("SUGGESTED DATA SOURCES")
    for src in brief["data"]["primary_sources"]:
        name = src.get("name", src) if isinstance(src, dict) else src
        print(f"  • {name}")
    print()
    print(f"OUTPUT → {out_path}")
    print()

    if is_ambiguous:
        print("⚠  AMBIGUITY WARNING: One or more fields could not be confidently inferred.")
        print("   Review the brief carefully before spawning agents.")
        print("   Fields to check: geography.study_area, geography.county_fips,")
        print("   engagement.hero_question, analysis.dependent_variable")
        print()

    print("✓ Done. Review the project brief, then start the pipeline with your agent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
