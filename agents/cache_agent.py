import sqlite3
import hashlib
from typing import Dict, Optional


# -----------------------------
# Database Connection
# -----------------------------
def get_connection(db_path: str = "geo_cache.db"):
    return sqlite3.connect(db_path)


# -----------------------------
# Address Hashing
# -----------------------------
def generate_address_hash(components: Dict) -> str:
    key_parts = [
        components.get("house_number"),
        components.get("street"),
        components.get("landmark"),
        components.get("village"),
        components.get("taluk"),
        components.get("city"),
        components.get("district"),
        components.get("state"),
        components.get("pincode")
    ]

    key = "|".join([str(p).lower() for p in key_parts if p])
    return hashlib.sha256(key.encode()).hexdigest()


# -----------------------------
# Cache Insert
# -----------------------------
def insert_cache(conn, record: Dict):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO geo_cache (
            address_hash,
            normalized_address,
            city,
            state,
            pincode,
            latitude,
            longitude,
            confidence,
            source,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        record["address_hash"],
        record["normalized_address"],
        record["city"],
        record["state"],
        record["pincode"],
        record["latitude"],
        record["longitude"],
        record["confidence"],
        record["source"]
    ))
    conn.commit()


# -----------------------------
# Cache Lookup
# -----------------------------
def lookup_cache(
    conn,
    address_hash: str,
    min_confidence: float = 0.75
) -> Optional[Dict]:

    cursor = conn.cursor()
    cursor.execute("""
        SELECT latitude, longitude, confidence, source
        FROM geo_cache
        WHERE address_hash = ?
    """, (address_hash,))

    row = cursor.fetchone()

    if row and row[2] >= min_confidence:
        return {
            "latitude": row[0],
            "longitude": row[1],
            "confidence": row[2],
            "source": "cache",
            "decision": "accepted"
        }

    return None


# -----------------------------
# End-to-End Cache Check
# -----------------------------
def check_cache(conn, parsed_output: Dict) -> Dict:
    address_hash = generate_address_hash(parsed_output["components"])
    result = lookup_cache(conn, address_hash)

    if result:
        print("CACHE HIT → Returning cached geo-coordinates")
        return result

    print("CACHE MISS → External resolution required")
    return {
        "decision": "external_required"
    }
