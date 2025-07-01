import requests
from bs4 import BeautifulSoup

def scrape_total_wins(rider_slug):
    url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/wins"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", class_="basic")
    wins = len(table.find_all("tr")) - 1 if table else 0
    return wins

def scrape_grand_tours(rider_slug):
    url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/grand-tour-starts"
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

def scrape_monuments(rider_slug):
    url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/top-classic-results"
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

def get_comparison_data():
    pogacar = {
        "total_wins": scrape_total_wins("tadej-pogacar"),
        "grand_tours": scrape_grand_tours("tadej-pogacar"),
        "monuments": scrape_monuments("tadej-pogacar"),
        "worlds": scrape_worlds("tadej-pogacar"),
    }
    merckx = {
        "total_wins": scrape_total_wins("eddy-merckx"),
        "grand_tours": scrape_grand_tours("eddy-merckx"),
        "monuments": scrape_monuments("eddy-merckx"),
        "worlds": scrape_worlds("eddy-merckx"),
    }
    return {
        "pogacar": pogacar,
        "merckx": merckx
    }
