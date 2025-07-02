from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pog_merckx_scraper_full import (
    get_pogacar_data,
    get_merckx_stats,
    combine_data,
)
import time

app = FastAPI()

# Enable CORS for frontend app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Merckx data (scraped only once)
cached_merckx = get_merckx_stats()

# Pogacar cache setup (refreshed daily)
cached_pogacar = None
last_fetch_time = 0
POGACAR_CACHE_DURATION = 60 * 60 * 24  # 24 hours in seconds

@app.get("/api/pog-vs-merckx")
def get_pog_merckx():
    global cached_pogacar, last_fetch_time

    current_time = time.time()

    # Refresh Pogacar if cache is empty or outdated
    if cached_pogacar is None or (current_time - last_fetch_time) > POGACAR_CACHE_DURATION:
        try:
            cached_pogacar = get_pogacar_data()
            last_fetch_time = current_time
        except Exception:
            # Keep using the last successful scrape if available
            if cached_pogacar is None:
                return {"error": "Failed to load Pogacar data and no cache available"}
            # else: just return existing cached_pogacar below

    return combine_data(cached_pogacar, cached_merckx)
