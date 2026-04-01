# Geo_Parser — Agentic Address & Geocoordinate Retrieval

> Built as part of a self-directed GenAI learning programme alongside an MBA at HHL Leipzig, this project addresses a real logistics problem: resolving noisy Indian addresses into reliable geocoordinates while minimising cost, latency, and external API dependency.

---

## The Problem

Indian addresses are highly variable — mixed scripts, non-standard abbreviations, missing pincodes, inconsistent formatting. Third-party geocoding APIs are expensive at scale and often fail on non-standard formats. In a high-volume logistics network, address resolution failures directly impact first-attempt delivery rates.

This system resolves addresses using a **confidence-based routing strategy**: cheap and fast paths first, escalating to external tools only when confidence is insufficient.

---

## How It Works

```
Raw Address (free-form text)
        ↓
Parser Agent  ←── Qwen2.5:7b-instruct via Ollama
        │         Extracts structured components + confidence score
        │         Expands abbreviations (blr → Bengaluru, govt → Government)
        ↓
Cache Agent
        │
        ├── SHA-256 hash of address components
        ├── Lookup in SQLite (geo_cache.db)
        ├── Confidence threshold: 0.75
        │
        ├── CACHE HIT  ──► Return coordinates immediately
        │
        └── CACHE MISS ──► External Geo Agent
                                │
                                ├── Primary query: building + area + city + state
                                │   → OpenStreetMap Nominatim API
                                │
                                ├── Fallback query: area + city + state + pincode
                                │   → OpenStreetMap Nominatim API
                                │
                                ├── Save result to SQLite cache
                                │
                                └── Return coordinates + source + decision
```

**Output schema:**
```json
{
  "input_address": "string",
  "parsed": {
    "components": { "city": "...", "state": "...", "pincode": "...", ... },
    "normalized_address": "string",
    "confidence": 0.0
  },
  "result": {
    "latitude": 12.9716,
    "longitude": 77.5946,
    "confidence": 0.80,
    "source": "cache | external",
    "decision": "accepted | external_failed"
  }
}
```

---

## Architecture Decisions

**Why Qwen2.5:7b-instruct via Ollama (default) instead of a cloud LLM API?**
Indian addresses often contain personally identifiable information. Running the LLM locally means zero data egress — no address ever leaves the machine. It also eliminates per-call API cost at high query volume. The system supports OpenAI, Groq, and Google Gemini as optional alternatives via LangChain connectors — configurable via `.env` — for teams that prefer managed APIs and accept the data-sharing trade-off.

**Why SHA-256 hashing on address components for cache lookup?**
Hashing on the structured components (city, state, pincode, street, landmark) rather than the raw address string means semantically identical addresses with different formatting (`Bengaluru` vs `Bangalore` vs `BLR`) resolve to the same hash after normalisation — dramatically improving cache hit rate.

**Why OpenStreetMap Nominatim instead of Google Maps API?**
Nominatim is free and open — no API key, no per-call cost. For a prototype validating the architecture, this is the right default. A production deployment at scale would evaluate Google Maps or HERE for higher accuracy, particularly on tier-2 and tier-3 Indian cities.

**Why two-query fallback in the external agent?**
Primary query (building + area + city + state) is precise but fails on non-standard or incomplete addresses. Fallback query (area + city + state + pincode) is coarser but has a much higher success rate. Trying both before failing means fewer unresolved addresses without sacrificing precision on the majority of inputs.

**Why SQLite for the cache?**
Local, zero-dependency, zero-cost. The cache persists validated coordinates so repeated queries for the same address or nearby addresses are resolved instantly without any API call. A production deployment would replace this with PostgreSQL or a managed database for concurrent access and durability.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Agent Orchestration | LangChain (custom flow in `graph/geo_flow.py`) |
| LLM (default) | Qwen2.5:7b-instruct via Ollama (local, no API cost) |
| LLM (optional) | OpenAI, Groq, Google Gemini — via LangChain connectors |
| External Geocoding | OpenStreetMap Nominatim API |
| Cache | SQLite (`geo_cache.db`) with SHA-256 address hashing |
| API | FastAPI (`/geocode` POST endpoint) |
| UI | Streamlit (`streamlit_app.py`) |

---

## Project Structure

```
Geo_Parser/
│
├── agents/
│   ├── parser_agent.py        # LLM-based address normalisation + confidence scoring
│   ├── cache_agent.py         # SQLite cache lookup, insert, SHA-256 hashing
│   └── external_geo_agent.py  # OpenStreetMap Nominatim with two-query fallback
│
├── graph/
│   └── geo_flow.py            # End-to-end orchestration: Parse → Cache → External
│
├── notebooks/
│   ├── parser_agent.ipynb     # Parser agent development and testing
│   ├── cache_lookup.ipynb     # Cache logic development and testing
│   └── external_geo_resolution.ipynb  # External agent development and testing
│
├── schema.py                  # Input/output data models
├── main.py                    # FastAPI app entry point
├── streamlit_app.py           # Streamlit UI
├── geo_cache.db               # SQLite geocoordinate cache
└── requirements.txt
```

---

## Running the Project

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.ai) installed with Qwen2.5:7b-instruct pulled.

```bash
# Pull the local LLM
ollama pull qwen2.5:7b-instruct

# Install dependencies
pip install -r requirements.txt

# Run Streamlit UI
streamlit run streamlit_app.py

# Or run FastAPI server
uvicorn main:app --reload
# POST to http://localhost:8000/geocode
# Body: { "address": "Near govt schl Yelhanka blr 560064" }
```

**Using a cloud LLM instead of Ollama:** Set your preferred provider key in `.env` and update `MODEL_NAME` in `parser_agent.py` to use the appropriate LangChain connector (langchain-openai, langchain-groq, or langchain-google-genai).

---

## Limitations (Honest Assessment)

This is a proof-of-concept, not a production system.

- **Orchestration is sequential, not graph-based:** The current `geo_flow.py` runs Parse → Cache → External as a fixed sequence. A LangGraph implementation would make the routing stateful and conditional — enabling human-in-the-loop review for low-confidence addresses, parallel tool calls, and resumable flows after external API failures.
- **FAISS not yet integrated:** The README references FAISS for semantic similarity lookup between cached and incoming addresses. This is a planned enhancement — the current cache uses exact hash matching only.
- **Non-determinism:** Qwen2.5 introduces slight variation in output across runs. Addresses near the 0.75 confidence threshold may route differently on repeated calls.
- **Coverage:** Optimised and tested on Indian addresses. Performance on other regional formats is untested.
- **No automated evaluation:** There is no test set with ground-truth coordinates to measure system accuracy. This is the most significant gap for production readiness.

---

## What I Would Add With More Time

- **LangGraph migration:** Replace `geo_flow.py` with a proper LangGraph state graph — TypedDict state holding raw address, parsed components, confidence score, cache decision, and final coordinates. Add interrupt nodes for human review on low-confidence results. Add conditional edges that route based on confidence rather than a fixed sequence.
- **FAISS semantic cache:** Embed normalised address strings and retrieve the nearest cached address by vector similarity. This would improve cache hit rate significantly for paraphrased or partially matching addresses that fail exact hash lookup.
- **Evaluation module:** A labelled test set of Indian addresses with verified coordinates, measuring accuracy by routing path (cache hit vs. primary external vs. fallback external vs. failed).
- **QLoRA fine-tuning:** Fine-tune Qwen2.5 on labelled Indian address pairs (raw → structured components) to improve accuracy on long-tail edge cases where the base model currently underperforms.

---

## Context

This project was built independently alongside an MBA at HHL Leipzig Graduate School of Management. The business context — address resolution in Indian logistics — draws directly from professional experience building ML systems at XpressBees (BusyBees Logistics Solutions), where address parsing accuracy had a measurable impact on delivery success rates and reverse logistics costs.

The notebooks in `/notebooks` document the development process day by day — useful for understanding how each component was built and tested incrementally before being integrated.
