"""
Data Loader — loads all CSV datasets into memory for agent use.
"""
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

_cache = {}

TABLES = [
    "hospitals", "departments", "doctors", "services",
    "contacts", "documents", "embeddings_metadata",
    "lead_scores", "search_history",
]


def load_all():
    """Load all CSVs. Returns dict of DataFrames."""
    global _cache
    for table in TABLES:
        path = os.path.join(DATA_DIR, f"{table}.csv")
        if os.path.exists(path):
            _cache[table] = pd.read_csv(path)
        else:
            _cache[table] = pd.DataFrame()
    return _cache


def get(table: str) -> pd.DataFrame:
    if not _cache:
        load_all()
    return _cache.get(table, pd.DataFrame())


def data_ready() -> bool:
    return all(
        os.path.exists(os.path.join(DATA_DIR, f"{t}.csv"))
        for t in ["hospitals", "doctors", "services"]
    )


def summary() -> dict:
    dfs = load_all()
    return {k: len(v) for k, v in dfs.items()}
