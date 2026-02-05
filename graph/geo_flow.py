# graph/geo_flow.py

from agents.parser_agent import parse_address
from agents.cache_agent import check_cache
from agents.external_geo_agent import external_geo_resolution


def run_geo_flow(conn, raw_address: str) -> dict:
    """
    End-to-end orchestration:
    Parse → Cache → External (if needed)
    """

    # 1. Parse
    parsed = parse_address(raw_address)

    # 2. Cache lookup
    cache_result = check_cache(conn, parsed)

    if cache_result.get("decision") != "external_required":
        return {
            "input_address": raw_address,
            "parsed": parsed,
            "result": cache_result
        }

    # 3. External resolution (Day-4)
    external_result = external_geo_resolution(conn, parsed)

    return {
        "input_address": raw_address,
        "parsed": parsed,
        "result": external_result
    }
