import os
import time
import json
from pog_v_merckx_ultimate import (
    scrape_total_wins,
    scrape_grand_tours,
    scrape_monuments,
    scrape_worlds,
)

MERCKX_CACHE = "merckx_data.json"
POGACAR_CACHE = "pogacar_data.json"
POGACAR_CACHE_TTL = 60 * 60 * 12  # 12 hours

def load_cache(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def save_cache(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

def get_merckx_data():
    cached = load_cache(MERCKX_CACHE)
    if cached:
        return cached

    data = {
        "total_wins": scrape_total_wins("eddy-merckx"),
        "grand_tours": scrape_grand_tours("eddy-merckx"),
        "monuments": scrape_monuments("eddy-merckx"),
        "worlds": scrape_worlds("eddy-merckx"),
    }
    save_cache(MERCKX_CACHE, data)
    return data

def get_pogacar_data():
    if os.path.exists(POGACAR_CACHE):
        mtime = os.path.getmtime(POGACAR_CACHE)
        if time.time() - mtime < POGACAR_CACHE_TTL:
            return load_cache(POGACAR_CACHE)

    data = {
        "total_wins": scrape_total_wins("tadej-pogacar"),
        "grand_tours": scrape_grand_tours("tadej-pogacar"),
        "monuments": scrape_monuments("tadej-pogacar"),
        "worlds": scrape_worlds("tadej-pogacar"),
    }
    save_cache(POGACAR_CACHE, data)
    return data

def get_comparison_data():
    return {
        "pogacar": get_pogacar_data(),
        "merckx": get_merckx_data()
    }
