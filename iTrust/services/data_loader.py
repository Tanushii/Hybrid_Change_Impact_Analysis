"""
services/data_loader.py
Cached loaders for all heavy data assets: traceability links, call graph, file index,
and artifact texts.
All functions use @st.cache_resource when available so data is loaded once per session.
"""
import json
import os
from pathlib import Path
from typing import Dict, Tuple

try:
    import streamlit as st
    cache_decorator = st.cache_resource
except Exception:
    def cache_decorator(func):
        cache = {}
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key not in cache:
                cache[key] = func(*args, **kwargs)
            return cache[key]
        return wrapper

BASE_DIR = Path(__file__).resolve().parent.parent
LINKS_FILE = BASE_DIR / "itrust_solution_links.txt"
CALLGRAPH_FILE = BASE_DIR / "itrust_method_callgraph.json"
CODE_DIR = BASE_DIR / "code"
REQ_DIR = BASE_DIR / "req"


@cache_decorator
def load_traceability_links() -> Tuple[Dict[str, list], Dict[str, list]]:
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


@cache_decorator
def load_callgraph() -> Dict[str, dict]:
    """Load the JSON method call graph."""
    with open(CALLGRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@cache_decorator
def build_file_index() -> Dict[str, str]:
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


@cache_decorator
def load_all_requirements() -> Dict[str, str]:
    """Load all requirement texts mapped by filename."""
    req_data = {}
    if REQ_DIR.exists():
        for fname in os.listdir(REQ_DIR):
            if fname.endswith(".txt"):
                fpath = REQ_DIR / fname
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    req_data[fname] = f.read()
    return req_data


@cache_decorator
def load_all_code_texts() -> Dict[str, str]:
    """Load all Java source code texts mapped by filename."""
    code_data = {}
    file_index = build_file_index()
    for fname, fpath in file_index.items():
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                code_data[fname] = f.read()
        except Exception:
            code_data[fname] = ""
    return code_data
