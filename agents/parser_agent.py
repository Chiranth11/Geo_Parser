import json
import re
from typing import Dict, Any
from agents import cache_agent, external_geo_agent
import ollama

# -----------------------------
# Configuration
# -----------------------------
MODEL_NAME = "qwen2.5:7b-instruct"

# -----------------------------
# Internal Rich Schema
# -----------------------------
EMPTY_COMPONENTS = {
    "house_number": None,
    "building_name": None,
    "street": None,
    "landmark": None,
    "area": None,
    "village": None,
    "taluk": None,
    "city": None,
    "district": None,
    "state": None,
    "pincode": None
}

# -----------------------------
# Normalization Maps
# -----------------------------
NORMALIZATION_MAP = {
    "blr": "Bengaluru",
    "bangalore": "Bengaluru",
    "govt": "Government",
    "schl": "School",
    "opp": "Opposite",
    "nr": "Near"
}

STATE_MAP = {
    "ka": "Karnataka",
    "karnataka": "Karnataka"
}

# -----------------------------
# Prompt Builder
# -----------------------------
def build_prompt(raw_address: str) -> str:
    return f"""
You are an address parsing and normalization engine for Indian addresses.

Your tasks:
- Extract structured address components.
- Expand abbreviations (e.g., blr → Bengaluru, govt → Government, schl → School).
- Split concatenated words into meaningful address parts.
- Normalize city and state names to official names.
- Do NOT guess missing fields.
- Use null if a field is missing.
- Return valid JSON only. No explanations.

Address:
"{raw_address}"

Return JSON exactly in this format:
{{
  "components": {json.dumps(EMPTY_COMPONENTS, indent=2)},
  "normalized_address": "string",
  "confidence": 0.0
}}
""".strip()

# -----------------------------
# LLM Call
# -----------------------------
def call_llm(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

# -----------------------------
# JSON Extraction
# -----------------------------
def extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM output")
    return json.loads(match.group())

# -----------------------------
# Confidence Normalization
# -----------------------------
def normalize_confidence(value: Any) -> float:
    try:
        value = float(value)
        return max(0.0, min(1.0, value))
    except Exception:
        return 0.0

# -----------------------------
# Text Normalization
# -----------------------------
def normalize_text(text: str) -> str:
    if not text:
        return text

    words = text.split()
    normalized_words = []

    for w in words:
        key = w.lower()
        if key in NORMALIZATION_MAP:
            normalized_words.append(NORMALIZATION_MAP[key])
        elif key in STATE_MAP:
            normalized_words.append(STATE_MAP[key])
        else:
            normalized_words.append(w)

    return " ".join(normalized_words)

# -----------------------------
# Post Processing
# -----------------------------
def post_process(parsed: Dict[str, Any]) -> Dict[str, Any]:
    components = parsed.get("components", {})

    # Ensure all expected keys exist
    for key in EMPTY_COMPONENTS:
        components.setdefault(key, None)

    # Normalize text fields
    for key, value in components.items():
        if isinstance(value, str):
            components[key] = normalize_text(value)

    if isinstance(parsed.get("normalized_address"), str):
        parsed["normalized_address"] = normalize_text(parsed["normalized_address"])

    parsed["confidence"] = normalize_confidence(parsed.get("confidence", 0.0))
    parsed["components"] = components

    return parsed

# -----------------------------
# Main Public Function (Day-2 Deliverable)
# -----------------------------
def parse_address(raw_address: str) -> Dict[str, Any]:
    """
    Parses a noisy Indian address into structured components.

    Returns:
    {
        "components": {...},
        "normalized_address": "...",
        "confidence": float
    }
    """
    prompt = build_prompt(raw_address)
    llm_output = call_llm(prompt)
    parsed_json = extract_json(llm_output)
    final_output = post_process(parsed_json)

    return {
        "components": final_output["components"],
        "normalized_address": final_output.get("normalized_address", ""),
        "confidence": final_output["confidence"]
    }


# -----------------------------
# Optional Local Test
# -----------------------------
# if __name__ == "__main__":
#     test_address = "Near govt schl Yelhanka blr 560064"
#     test_address = "Door Number 14, 5th cross, N R Mohalla, Mysore, Karnataka, 570007"
#     # result_1 = parse_address(test_address)
#     # print(json.dumps(result_1, indent=2))

#     # test_address = "Flat302PrestigeSunriseWhitefieldBlr560066"
#     # test_address = "Opposite Temple, K R Puram Village, Tumkur District, Karnataka"

#     result_2 = parse_address(test_address)
#     print(json.dumps(result_2, indent=2))

#     from agents import cache_agent

# # def run_cache(parsed_output):
#     conn = cache_agent.get_connection()
#     # cache_result = cache_agent.check_cache(conn, result_1)
#     # print(cache_result)
#     cache_result_2 = cache_agent.check_cache(conn, result_2)
#     print(cache_result_2)

#     if  cache_result_2.get("decision") == "external_required":
#         geo = external_geo_agent.external_geo_resolution(conn, result_2)

#         if geo:
#             print("EXTERNAL HIT", geo)
#         else:
#             print("EXTERNAL FAILED")
