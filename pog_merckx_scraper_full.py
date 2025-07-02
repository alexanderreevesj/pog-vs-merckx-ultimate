import os
import json
import requests
from bs4 import BeautifulSoup

MERCKX_CACHE_FILE = "merckx_data.json"

def scrape_total_wins(rider_slug):
    url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/wins"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", class_="basic")
    wins = len(table.find_all("tr")) - 1 if table else 0
    return wins

def scrape_category(url):
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", class_="basic")

    starts = wins = podiums = top10s = 0
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:
                result = cols[3].text.strip()
                starts += 1
                if result == '1':
                    wins += 1
                if result in ['1', '2', '3']:
                    podiums += 1
                if result.isdigit() and int(result) <= 10:
                    top10s += 1

    return {
        "starts": starts,
        "wins": wins,
        "podiums": podiums,
        "top_10s": top10s,
        "win_%": round(wins / starts * 100, 1) if starts else 0,
        "podium_%": round(podiums / starts * 100, 1) if starts else 0,
        "top10_%": round(top10s / starts * 100, 1) if starts else 0,
    }

def scrape_worlds(rider_slug):
    url = f"https://www.procyclingstats.com/rider/{rider_slug}?season=&race=1021&filter=Filter&p=results"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", class_="basic")

    starts = wins = podiums = top10s = 0
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                result = cols[2].text.strip()
                starts += 1
                if result == '1':
                    wins += 1
                if result in ['1', '2', '3']:
                    podiums += 1
                if result.isdigit() and int(result) <= 10:
                    top10s += 1

    return {
        "starts": starts,
        "wins": wins,
        "podiums": podiums,
        "top_10s": top10s,
        "win_%": round(wins / starts * 100, 1) if starts else 0,
        "podium_%": round(podiums / starts * 100, 1) if starts else 0,
        "top10_%": round(top10s / starts * 100, 1) if starts else 0,
    }

def get_merckx_data():
    if os.path.exists(MERCKX_CACHE_FILE):
        with open(MERCKX_CACHE_FILE, "r") as f:
            return json.load(f)
    else:
        data = {
            "total_wins": scrape_total_wins("eddy-merckx"),
            "grand_tours": scrape_category("https://www.procyclingstats.com/rider/eddy-merckx/statistics/grand-tour-starts"),
            "monuments": scrape_category("https://www.procyclingstats.com/rider/eddy-merckx/statistics/top-classic-results"),
            "worlds": scrape_worlds("eddy-merckx"),
        }
        with open(MERCKX_CACHE_FILE, "w") as f:
            json.dump(data, f)
        return data

def get_pogacar_data():
    return {
        "total_wins": scrape_total_wins("tadej-pogacar"),
        "grand_tours": scrape_category("https://www.procyclingstats.com/rider/tadej-pogacar/statistics/grand-tour-starts"),
        "monuments": scrape_category("https://www.procyclingstats.com/rider/tadej-pogacar/statistics/top-classic-results"),
        "worlds": scrape_worlds("tadej-pogacar"),
    }

def combine_data(pogacar_data, merckx_data):
    return {
        "pogacar": pogacar_data,
        "merckx": merckx_data
    }

