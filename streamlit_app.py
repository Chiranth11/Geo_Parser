import sqlite3
import streamlit as st

from graph.geo_flow import run_geo_flow

st.set_page_config(page_title="Agentic Geo Parser")

conn = sqlite3.connect("geo_cache.db", check_same_thread=False)

st.title("Agentic Geo-Parser")

address = st.text_input("Enter address")

if st.button("Resolve Location"):
    if address.strip():
        result = run_geo_flow(conn, address)
        st.json(result)
    else:
        st.warning("Please enter an address")
