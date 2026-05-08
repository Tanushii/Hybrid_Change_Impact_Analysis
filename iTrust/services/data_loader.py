"""
services/data_loader.py
Cached loaders for all heavy data assets: traceability links, call graph, file index.
All functions use @st.cache_resource so data is loaded once per Streamlit session.
"""
import json
import os
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LINKS_FILE = BASE_DIR / "itrust_solution_links.txt"
CALLGRAPH_FILE = BASE_DIR / "itrust_method_callgraph.json"
CODE_DIR = BASE_DIR / "code"
REQ_DIR = BASE_DIR / "req"


@st.cache_resource
def load_traceability_links():
    """Parse solution links file into bidirectional dicts."""
    req_to_code = {}
    code_to_req = {}
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                req = parts[0].strip()
                code = parts[1].strip()
                req_to_code.setdefault(req, []).append(code)
                code_to_req.setdefault(code, []).append(req)
    return req_to_code, code_to_req


@st.cache_resource
def load_callgraph():
    """Load the JSON method call graph."""
    with open(CALLGRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource
def build_file_index():
    """
    Recursively walk code/ and build a filename→absolute_path index.
    Handles Java files spread across subdirectories (beans/, dao/, action/, etc.)
    """
    index = {}
    for root, _, files in os.walk(CODE_DIR):
        for fname in files:
            if fname.endswith(".java"):
                index[fname] = os.path.join(root, fname)
    return index
