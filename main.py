from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pog_merckx_scraper_full import (
    scrape_total_wins,
    scrape_grand_tours,
    scrape_monuments,
    scrape_worlds,
)
import time

app = FastAPI()

# CORS for frontend app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cached Merckx data (scraped only once)
merckx_data = {
    "total_wins": scrape_total_wins("eddy-merckx"),
    "grand_tours": scrape_grand_tours("eddy-merckx"),
    "monuments": scrape_monuments("eddy-merckx"),
    "worlds": scrape_worlds("eddy-merckx"),
}

# Cached Pogacar data (refreshed once per day)
cached_pogacar = None
last_pogacar_fetch = 0
CACHE_DURATION = 60 * 60 * 24  # 1 day

@app.get("/api/pog-vs-merckx")
def get_pog_vs_merckx():
    global cached_pogacar, last_pogacar_fetch

    now = time.time()
    if cached_pogacar is None or (now - last_pogacar_fetch) > CACHE_DURATION:
        cached_pogacar = {
            "total_wins": scrape_total_wins("tadej-pogacar"),
            "grand_tours": scrape_grand_tours("tadej-pogacar"),
            "monuments": scrape_monuments("tadej-pogacar"),
            "worlds": scrape_worlds("tadej-pogacar"),
        }
        last_pogacar_fetch = now

    return {
        "pogacar": cached_pogacar,
        "merckx": merckx_data
    }
