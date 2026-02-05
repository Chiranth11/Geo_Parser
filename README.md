Build an Agentic GenAI system that resolves noisy Indian addresses into reliable geo-coordinates by intelligently choosing between cached knowledge and external resolution, optimizing cost, latency, and accuracy.

Future Enhancements: We can also extend further by adding more agents like Annotation agent to label or annotate the addresses to handle different types of addresses or more complex addresses in case need of training the model with new address with annotations.

This project is complete as a production-ready agentic geocoding system. Future improvements include RAG-based abbreviation handling, which I’m exploring in a separate project. Apart from this we can work on fine tuning the models being used to handle more complex addresses.

Geo_Parser/
│
├── agents/
│   ├── parser_agent.py
│   ├── validation_agent.py
│   └── decision_agent.py
│
├── storage/
│   └── cache.db
│
├── graph/
│   └── flow.py
│
├── schema.py
├── main.py
└── README.md

Tech Stack:
- Python
- LangGraph
- LLM (OpenAI / Azure OpenAI; open-source optional)
- FAISS (later)
- SQLite
- Excel export (read-only)

Architecture Flow:
Input Address
   ↓
LLM Normalizer
   ↓
Decision Agent
   ↓
Cache Lookup ──► External Fetch
   ↓
Validation Agent
   ↓
Final Output
