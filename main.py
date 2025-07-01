from fastapi import FastAPI
from pog_merckx_scraper_full import get_comparison_data

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Pog vs Merckx API is live!"}

@app.get("/api/pog-vs-merckx")
def compare():
    return get_comparison_data()
