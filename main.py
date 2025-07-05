from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from comprehensive_scraper import CyclingStatsScraper
import json
import os
import time
from typing import Dict, Any

app = FastAPI(title="Pogacar vs Merckx API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper
scraper = CyclingStatsScraper()

# Cache configuration
MERCKX_CACHE_FILE = "merckx_complete_data.json"
POGACAR_CACHE_FILE = "pogacar_complete_data.json"
POGACAR_CACHE_DURATION = 60 * 60 * 24 * 7

# Global cache variables
cached_merckx_data = None
cached_pogacar_data = None
last_pogacar_fetch_time = 0

def load_merckx_data():
    """Load Merckx data from cache or scrape if not available"""
    global cached_merckx_data
    
    if os.path.exists(MERCKX_CACHE_FILE):
        print("Loading Merckx data from cache...")
        with open(MERCKX_CACHE_FILE, "r") as f:
            cached_merckx_data = json.load(f)
    else:
        print("Scraping Merckx data (first time)...")
        cached_merckx_data = scraper.scrape_complete_rider_data("Eddy Merckx")
        with open(MERCKX_CACHE_FILE, "w") as f:
            json.dump(cached_merckx_data, f, indent=2)
    
    return cached_merckx_data

def get_pogacar_data():
    """Get Pogacar data with caching"""
    global cached_pogacar_data, last_pogacar_fetch_time
    
    current_time = time.time()
    
    # Check if we need to refresh Pogacar data
    if (cached_pogacar_data is None or 
        (current_time - last_pogacar_fetch_time) > POGACAR_CACHE_DURATION):
        
        try:
            print("Scraping fresh Pogacar data...")
            cached_pogacar_data = scraper.scrape_complete_rider_data("Tadej Pogacar")
            last_pogacar_fetch_time = current_time
            
            # Save to cache file
            with open(POGACAR_CACHE_FILE, "w") as f:
                json.dump(cached_pogacar_data, f, indent=2)
                
        except Exception as e:
            print(f"Error scraping Pogacar data: {e}")
            # Try to load from cache file if scraping fails
            if os.path.exists(POGACAR_CACHE_FILE):
                print("Loading Pogacar data from cache due to scraping error...")
                with open(POGACAR_CACHE_FILE, "r") as f:
                    cached_pogacar_data = json.load(f)
            elif cached_pogacar_data is None:
                raise HTTPException(status_code=500, detail="Failed to load Pogacar data")
    
    return cached_pogacar_data

# Load Merckx data on startup
print("Initializing data...")
load_merckx_data()

@app.get("/")
def read_root():
    return {"message": "Pogacar vs Merckx API - Comprehensive Cycling Statistics"}

@app.get("/api/pog-vs-merckx")
def get_pog_merckx_comparison():
    """Get complete comparison data between Pogacar and Merckx"""
    try:
        pogacar_data = get_pogacar_data()
        merckx_data = cached_merckx_data
        
        return {
            "pogacar": pogacar_data,
            "merckx": merckx_data,
            "last_updated": {
                "pogacar": time.ctime(last_pogacar_fetch_time),
                "merckx": "Cached permanently"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating comparison: {str(e)}")

@app.get("/api/rider/{rider_name}")
def get_rider_data(rider_name: str):
    """Get complete data for a specific rider"""
    try:
        if rider_name.lower() in ["eddy-merckx", "eddy merckx"]:
            return cached_merckx_data
        elif rider_name.lower() in ["tadej-pogacar", "tadej pogacar"]:
            return get_pogacar_data()
        else:
            # For other riders, scrape fresh data (no caching)
            return scraper.scrape_complete_rider_data(rider_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rider data: {str(e)}")

@app.get("/api/simplified-comparison")
def get_simplified_comparison():
    """Get simplified comparison data (compatible with current iOS app)"""
    try:
        pogacar_data = get_pogacar_data()
        merckx_data = cached_merckx_data
        
        def extract_simplified_stats(rider_data):
            metrics = rider_data['career_metrics']
            return {
                "total_wins": metrics['races_won'],
                "grand_tours": {
                    "starts": metrics['grand_tours_started'],
                    "wins": metrics['grand_tours_won'],
                    "podiums": metrics['grand_tours_podiums'],
                    "top_10s": metrics['grand_tours_top_10s'],
                    "win_%": metrics['grand_tours_win_percentage'],
                    "podium_%": metrics['grand_tours_podium_percentage'],
                    "top10_%": metrics['grand_tours_top_10_percentage']
                },
                "monuments": {
                    "starts": metrics['monuments_started'],
                    "wins": metrics['monuments_won'],
                    "podiums": metrics['monuments_podiums'],
                    "top_10s": metrics['monuments_top_10s'],
                    "win_%": metrics['monuments_win_percentage'],
                    "podium_%": metrics['monuments_podium_percentage'],
                    "top10_%": metrics['monuments_top_10_percentage']
                },
                "worlds": {
                    "starts": len([r for r in rider_data['detailed_data']['world_championships_results']]),
                    "wins": len([r for r in rider_data['detailed_data']['world_championships_results'] if r['result'] == '1']),
                    "podiums": len([r for r in rider_data['detailed_data']['world_championships_results'] if r['result'] in ['1', '2', '3']]),
                    "top_10s": len([r for r in rider_data['detailed_data']['world_championships_results'] if r['result'].isdigit() and int(r['result']) <= 10]),
                    "win_%": 0,
                    "podium_%": 0,
                    "top10_%": 0
                }
            }
        
        pogacar_simplified = extract_simplified_stats(pogacar_data)
        merckx_simplified = extract_simplified_stats(merckx_data)
        
        # Calculate World Championships percentages
        for rider_stats in [pogacar_simplified, merckx_simplified]:
            worlds = rider_stats["worlds"]
            if worlds["starts"] > 0:
                worlds["win_%"] = round((worlds["wins"] / worlds["starts"]) * 100, 1)
                worlds["podium_%"] = round((worlds["podiums"] / worlds["starts"]) * 100, 1)
                worlds["top10_%"] = round((worlds["top_10s"] / worlds["starts"]) * 100, 1)
        
        return {
            "pogacar": pogacar_simplified,
            "merckx": merckx_simplified
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating simplified comparison: {str(e)}")

@app.get("/api/career-metrics/{rider_name}")
def get_career_metrics(rider_name: str):
    """Get just the career metrics for a rider"""
    try:
        if rider_name.lower() in ["eddy-merckx", "eddy merckx"]:
            return cached_merckx_data['career_metrics']
        elif rider_name.lower() in ["tadej-pogacar", "tadej pogacar"]:
            return get_pogacar_data()['career_metrics']
        else:
            rider_data = scraper.scrape_complete_rider_data(rider_name)
            return rider_data['career_metrics']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting career metrics: {str(e)}")

@app.get("/api/detailed-data/{rider_name}")
def get_detailed_data(rider_name: str):
    """Get detailed race data for a rider"""
    try:
        if rider_name.lower() in ["eddy-merckx", "eddy merckx"]:
            return cached_merckx_data['detailed_data']
        elif rider_name.lower() in ["tadej-pogacar", "tadej pogacar"]:
            return get_pogacar_data()['detailed_data']
        else:
            rider_data = scraper.scrape_complete_rider_data(rider_name)
            return rider_data['detailed_data']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting detailed data: {str(e)}")

@app.get("/api/refresh-pogacar")
def refresh_pogacar_data():
    """Force refresh Pogacar data"""
    global cached_pogacar_data, last_pogacar_fetch_time
    
    try:
        print("Force refreshing Pogacar data...")
        cached_pogacar_data = scraper.scrape_complete_rider_data("Tadej Pogacar")
        last_pogacar_fetch_time = time.time()
        
        with open(POGACAR_CACHE_FILE, "w") as f:
            json.dump(cached_pogacar_data, f, indent=2)
        
        return {
            "message": "Pogacar data refreshed successfully",
            "updated_at": time.ctime(last_pogacar_fetch_time)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing Pogacar data: {str(e)}")

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "merckx_data_loaded": cached_merckx_data is not None,
        "pogacar_data_loaded": cached_pogacar_data is not None,
        "last_pogacar_update": time.ctime(last_pogacar_fetch_time) if last_pogacar_fetch_time > 0 else "Never"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Add this endpoint to main.py after the existing endpoints

@app.get("/api/keep-alive")
def keep_alive():
    """Keep the service warm and prevent cold starts"""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "message": "Service is warm and ready"
    }

# Also modify the warmup endpoint to be more comprehensive:
@app.get("/api/warmup")
def warmup():
    """Pre-warm all data to prevent cold starts"""
    try:
        # Ensure both datasets are loaded
        pogacar_data = get_pogacar_data()
        merckx_data = cached_merckx_data
        
        # Test the comparison endpoint functionality
        comparison_ready = pogacar_data is not None and merckx_data is not None
        
        return {
            "status": "warmed" if comparison_ready else "partial",
            "pogacar_loaded": pogacar_data is not None,
            "merckx_loaded": merckx_data is not None,
            "comparison_ready": comparison_ready,
            "last_update": time.ctime(last_pogacar_fetch_time) if last_pogacar_fetch_time > 0 else "Never"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
