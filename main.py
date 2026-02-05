# main.py

import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel

from graph.geo_flow import run_geo_flow

app = FastAPI(title="Agentic Geo Parser")

conn = sqlite3.connect("geo_cache.db", check_same_thread=False)


class AddressRequest(BaseModel):
    address: str


@app.post("/geocode")
def geocode_address(request: AddressRequest):
    return run_geo_flow(conn, request.address)
