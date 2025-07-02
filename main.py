from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pog_merckx_scraper_full import (
    get_pogacar_data,
    get_merckx_data,
    combine_data,
)
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_merckx = get_merckx_data()

cached_pogacar = None
last_fetch_time = 0
POGACAR_CACHE_DURATION = 60 * 60 * 12  # 12 hours

@app.get("/api/pog-vs-merckx")
def get_pog_merckx():
    global cached_pogacar, last_fetch_time

    current_time = time.time()

    if cached_pogacar is None or (current_time - last_fetch_time) > POGACAR_CACHE_DURATION:
        try:
            cached_pogacar = get_pogacar_data()
            last_fetch_time = current_time
        except Exception:
            if cached_pogacar is None:
                return {"error": "Failed to load Pogacar data and no cache available"}

    return combine_data(cached_pogacar, cached_merckx)


