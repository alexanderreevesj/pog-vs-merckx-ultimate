from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pog_merckx_scraper_full import (
    get_pogacar_stats,
    get_merckx_stats,
    combine_data,
)
import time

app = FastAPI()

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Merckx is static – only scrape once ever
cached_merckx = get_merckx_stats()

# Pogacar is cached once every 12 hours
cached_pogacar = None
last_pogacar_fetch = 0
POGACAR_CACHE_DURATION = 60 * 60 * 12  # 12 hours

@app.get("/api/pog-vs-merckx")
def get_comparison():
    global cached_pogacar, last_pogacar_fetch

    now = time.time()
    if cached_pogacar is None or (now - last_pogacar_fetch) > POGACAR_CACHE_DURATION:
        try:
            cached_pogacar = get_pogacar_stats()
            last_pogacar_fetch = now
        except Exception as e:
            print(f"Error fetching Pogacar stats: {e}")
            # fallback to last cached_pogacar (can be None)

    if cached_pogacar is None:
        return {"error": "Failed to fetch Pogacar data and no cached data available."}

    return combine_data(cached_pogacar, cached_merckx)

