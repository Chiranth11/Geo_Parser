import time
import requests
from typing import Dict, Optional

from agents.cache_agent import (
    generate_address_hash,
    insert_cache
)

# -----------------------------
# Configuration
# -----------------------------
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "AgenticGeoIntelligence/1.0 (contact: nlchiranth11@gmail.com)"
DEFAULT_CONFIDENCE = 0.80
REQUEST_DELAY_SEC = 1


# -----------------------------
# Query Builders (Fallback Strategy)
# -----------------------------
def build_primary_query(parsed: Dict) -> str:
    """
    Coarse query – highest success rate for Indian addresses
    """
    c = parsed["components"]
    parts = [
        c.get("building_name"),
        c.get("area"),
        c.get("city"),
        c.get("state")
    ]
    return ", ".join(str(p) for p in parts if p)


def build_fallback_query(parsed: Dict) -> str:
    """
    Fallback query – broader, less specific
    """
    c = parsed["components"]
    parts = [
        c.get("area"),
        c.get("city"),
        c.get("state"),
        str(c.get("pincode")) if c.get("pincode") else None
    ]
    return ", ".join(str(p) for p in parts if p)


# -----------------------------
# External API Call
# -----------------------------
def call_nominatim(query: str) -> Optional[Dict]:
    params = {
        "q": query,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(NOMINATIM_URL, params=params, headers=headers)
    time.sleep(REQUEST_DELAY_SEC)

    if response.status_code != 200:
        return None

    data = response.json()
    if not data:
        return None

    return {
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"]),
        "confidence": DEFAULT_CONFIDENCE,
        "source": "external"
    }


# -----------------------------
# External Geo Resolution Agent
# -----------------------------
def resolve_geo_externally(parsed: Dict) -> Optional[Dict]:
    """
    Two-step fallback strategy:
    1. Primary (building + area + city + state)
    2. Fallback (area + city + state + pincode)
    """

    # Step 1: Primary query
    primary_query = build_primary_query(parsed)
    if primary_query:
        result = call_nominatim(primary_query)
        if result:
            return result

    # Step 2: Fallback query
    fallback_query = build_fallback_query(parsed)
    if fallback_query:
        result = call_nominatim(fallback_query)
        if result:
            return result

    return None


# -----------------------------
# Persist External Result
# -----------------------------
def save_external_result(conn, parsed: Dict, geo: Dict):
    record = {
        "address_hash": generate_address_hash(parsed["components"]),
        "normalized_address": parsed["normalized_address"],
        "city": parsed["components"].get("city"),
        "state": parsed["components"].get("state"),
        "pincode": str(parsed["components"].get("pincode"))
        if parsed["components"].get("pincode") else None,
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "confidence": geo["confidence"],
        "source": geo["source"]
    }

    insert_cache(conn, record)


# -----------------------------
# End-to-End External Resolution
# -----------------------------
def external_geo_resolution(conn, parsed: Dict) -> Dict:
    """
    Called ONLY when cache returns MISS
    """
    geo = resolve_geo_externally(parsed)

    if not geo:
        return {
            "decision": "external_failed"
        }

    save_external_result(conn, parsed, geo)

    return {
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "confidence": geo["confidence"],
        "source": "external",
        "decision": "accepted"
    }
