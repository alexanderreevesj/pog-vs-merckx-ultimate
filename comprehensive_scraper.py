import requests
from bs4 import BeautifulSoup
import re
import json
import os
from typing import Dict, List, Tuple, Optional

class CyclingStatsScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
    def generate_rider_urls(self, rider_name: str) -> Dict[str, str]:
        """Generate all necessary URLs for a rider"""
        rider_slug = rider_name.lower().replace(" ", "-")
        base_url = f"https://www.procyclingstats.com/rider/{rider_slug}"
        
        return {
            "rider_slug": rider_slug,
            "base_url": base_url,
            "wins_url": f"{base_url}/statistics/wins",
            "monument_results_url": f"{base_url}/statistics/top-classic-results",
            "grand_tour_results_url": f"{base_url}/statistics/grand-tour-starts",
            "leader_jerseys_url": f"{base_url}/statistics/grandtour-leader-jerseys",
            "world_championships_url": f"https://www.procyclingstats.com/rider.php?xseason=&zxseason=&pxseason=equal&sort=date&race=1021&km1=&zkm1=&pkm1=equal&limit=100&xoffset=0&topx=&ztopx=&ptopx=smallerorequal&znation=&type=&continent=&pnts=&zpnts=&ppnts=largerorequal&level=&rnk=&zrnk=&prnk=equal&exclude_tt=0&racedate=&zracedate=&pracedate=equal&name=&pname=contains&category=&profile_score=&zprofile_score=&pprofile_score=largerorequal&exclude_gcs=0&vert_meters=&zvert_meters=&pvert_meters=largerorequal&uci_pnt=&zuci_pnt=&puci_pnt=largerorequal&filter=Filter&id={rider_slug}&p=results",
            "season_statistics_url": f"https://www.procyclingstats.com/rider.php?proresults=0&proresults=1&pproresults=largerorequal&stage_type=&filter=Filter&id={rider_slug}&p=statistics&s=season-statistics"
        }

    def scrape_rider_info(self, rider_slug: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Scrape basic rider information"""
        url = f"https://www.procyclingstats.com/rider/{rider_slug}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return None, None, None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        info_section = soup.find('div', {'class': 'rdr-info-cont'})
        
        if not info_section:
            return None, None, None
            
        full_text = info_section.get_text(separator=' ', strip=True)
        
        # Extract Date of Birth
        dob_match = re.search(r'\b\d{1,2}\s*(?:st|nd|rd|th)?\s+\w+\s+\d{4}\b', full_text)
        date_of_birth = dob_match.group(0) if dob_match else None
        
        # Extract Nationality
        nationality_match = re.search(r'Nationality:\s*([A-Za-z\s]+?)(?=\s+Weight:)', full_text)
        nationality = nationality_match.group(1).strip() if nationality_match else None
        
        # Extract Place of Birth
        place_of_birth_match = re.search(r'Place of birth:\s*([A-Za-z\s\-,]+)(?=\s+Points per specialty)', full_text)
        place_of_birth = place_of_birth_match.group(1).strip() if place_of_birth_match else None
        
        return date_of_birth, nationality, place_of_birth

    def scrape_total_wins(self, rider_slug: str) -> List[Dict]:
        """Scrape all wins with details"""
        url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/wins"
        response = requests.get(url, headers=self.headers)
        
        wins_list = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            wins_table = soup.find('table', {'class': 'basic'})
            
            if wins_table:
                rows = wins_table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) >= 5:
                        wins_list.append({
                            'nr': columns[0].text.strip(),
                            'race': columns[1].text.strip(),
                            'class': columns[2].text.strip(),
                            'date': columns[3].text.strip(),
                            'category': columns[4].text.strip()
                        })
        
        return wins_list

    def scrape_monument_results(self, rider_slug: str) -> List[Dict]:
        """Scrape monument results"""
        url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/top-classic-results"
        response = requests.get(url, headers=self.headers)
        
        monument_results = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            monument_table = soup.find('table', {'class': 'basic'})
            
            if monument_table:
                rows = monument_table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) >= 4:
                        classic = self.standardize_race_name(columns[2].text.strip())
                        monument_results.append({
                            'nr': columns[0].text.strip(),
                            'season': columns[1].text.strip(),
                            'classic': classic,
                            'result': columns[3].text.strip()
                        })
        
        return monument_results

    def scrape_grand_tour_results(self, rider_slug: str) -> List[Dict]:
        """Scrape Grand Tour participations"""
        url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/grand-tour-starts"
        response = requests.get(url, headers=self.headers)
        
        grand_tour_results = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            grand_tour_table = soup.find('table', {'class': 'basic'})
            
            if grand_tour_table:
                rows = grand_tour_table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) >= 7:
                        grand_tour = self.standardize_grand_tour_name(columns[2].text.strip())
                        grand_tour_results.append({
                            'nr': columns[0].text.strip(),
                            'season': columns[1].text.strip(),
                            'grand_tour': grand_tour,
                            'gc': columns[3].text.strip(),
                            'points': columns[4].text.strip(),
                            'mountains': columns[5].text.strip(),
                            'youth': columns[6].text.strip(),
                            'best_stage': columns[7].text.strip() if len(columns) > 7 else ""
                        })
        
        return grand_tour_results

    def scrape_world_championships_results(self, rider_slug: str) -> List[Dict]:
        """Scrape World Championships results"""
        url = f"https://www.procyclingstats.com/rider.php?xseason=&zxseason=&pxseason=equal&sort=date&race=1021&km1=&zkm1=&pkm1=equal&limit=100&xoffset=0&topx=&ztopx=&ptopx=smallerorequal&znation=&type=&continent=&pnts=&zpnts=&ppnts=largerorequal&level=&rnk=&zrnk=&prnk=equal&exclude_tt=0&racedate=&zracedate=&pracedate=equal&name=&pname=contains&category=&profile_score=&zprofile_score=&pprofile_score=largerorequal&exclude_gcs=0&vert_meters=&zvert_meters=&pvert_meters=largerorequal&uci_pnt=&zuci_pnt=&puci_pnt=largerorequal&filter=Filter&id={rider_slug}&p=results"
        response = requests.get(url, headers=self.headers)
        
        wc_results = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            wc_table = soup.find('table', {'class': 'basic'})
            
            if wc_table:
                rows = wc_table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) >= 9 and columns[0].text.strip().isdigit():
                        wc_results.append({
                            'nr': columns[0].text.strip(),
                            'date': columns[1].text.strip(),
                            'result': columns[2].text.strip(),
                            'race': columns[3].text.strip(),
                            'class': columns[4].text.strip(),
                            'kms': columns[5].text.strip(),
                            'pcs_points': columns[6].text.strip(),
                            'uci_points': columns[7].text.strip(),
                            'vert_mtr': columns[8].text.strip()
                        })
        
        return wc_results

    def scrape_season_statistics(self, rider_slug: str) -> List[Dict]:
        """Scrape season statistics"""
        url = f"https://www.procyclingstats.com/rider.php?proresults=0&proresults=1&pproresults=largerorequal&stage_type=&filter=Filter&id={rider_slug}&p=statistics&s=season-statistics"
        response = requests.get(url, headers=self.headers)
        
        season_statistics = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            season_table = soup.find('table', {'class': 'basic'})
            
            if season_table:
                rows = season_table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) >= 7 and columns[0].text.strip():
                        season_statistics.append({
                            'season': columns[0].text.strip(),
                            'points': columns[1].text.strip(),
                            'racedays': columns[2].text.strip(),
                            'kms': columns[3].text.strip(),
                            'wins': columns[4].text.strip(),
                            'top_3s': columns[5].text.strip(),
                            'top_10s': columns[6].text.strip()
                        })
        
        return season_statistics

    def scrape_leader_jerseys(self, rider_slug: str) -> List[Dict]:
        """Scrape Grand Tour leader jerseys"""
        url = f"https://www.procyclingstats.com/rider/{rider_slug}/statistics/grandtour-leader-jerseys"
        response = requests.get(url, headers=self.headers)
        
        leader_jersey_data = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            jersey_table = soup.find('table', {'class': 'basic'})
            
            if jersey_table:
                rows = jersey_table.find_all('tr')[1:-1]  # Skip header and total row
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) >= 3:
                        leader_jersey_data.append({
                            'year': columns[0].text.strip(),
                            'race': columns[1].text.strip(),
                            'total': int(columns[2].text.strip()) if columns[2].text.strip().isdigit() else 0,
                            'gc': int(columns[3].text.strip()) if len(columns) > 3 and columns[3].text.strip().isdigit() else 0,
                            'points': int(columns[4].text.strip()) if len(columns) > 4 and columns[4].text.strip().isdigit() else 0,
                            'kom': int(columns[5].text.strip()) if len(columns) > 5 and columns[5].text.strip().isdigit() else 0,
                            'youth': int(columns[6].text.strip()) if len(columns) > 6 and columns[6].text.strip().isdigit() else 0
                        })
        
        return leader_jersey_data

    def standardize_race_name(self, race_name: str) -> str:
        """Standardize Monument names"""
        monument_name_mapping = {
            'Milano-Sanremo': ['Milano-Sanremo', 'Milan-San Remo'],
            'Ronde van Vlaanderen - Tour des Flandres': ['Ronde van Vlaanderen - Tour des Flandres', 'Ronde van Vlaanderen / Tour des Flandres', 'Tour of Flanders', 'Ronde van Vlaanderen - Tour des Flandres ME'],
            'Paris-Roubaix': ['Paris-Roubaix', 'Paris - Roubaix'],
            'Liège-Bastogne-Liège': ['Liège-Bastogne-Liège', 'Liège - Bastogne - Liège'],
            'Il Lombardia': ['Il Lombardia', 'Giro di Lombardia']
        }
        
        for standard_name, variations in monument_name_mapping.items():
            if race_name in variations:
                return standard_name
        return race_name

    def standardize_grand_tour_name(self, tour_name: str) -> str:
        """Standardize Grand Tour names"""
        grand_tour_name_mapping = {
            'Vuelta a España': ['Vuelta a España', 'La Vuelta ciclista a España'],
            'Tour de France': ['Tour de France'],
            'Giro d\'Italia': ['Giro d\'Italia']
        }
        
        for standard_name, variations in grand_tour_name_mapping.items():
            if tour_name in variations:
                return standard_name
        return tour_name

    def safe_int(self, value: str) -> int:
        """Safely convert string to int"""
        try:
            return int(value) if value.isdigit() else 0
        except:
            return 0

    def safe_float(self, value: str) -> float:
        """Safely convert string to float"""
        try:
            return float(value)
        except:
            return 0.0

    def calculate_career_metrics(self, wins_list: List[Dict], season_statistics: List[Dict], 
                               grand_tour_results: List[Dict], monument_results: List[Dict], 
                               leader_jersey_data: List[Dict]) -> Dict:
        """Calculate comprehensive career metrics without pandas"""
        
        # Basic career metrics
        races_participated = sum(self.safe_int(stat['racedays']) for stat in season_statistics)
        races_won = len(wins_list)
        win_percentage = (races_won / races_participated) * 100 if races_participated > 0 else 0
        
        races_podiumed = sum(self.safe_int(stat['top_3s']) for stat in season_statistics)
        podium_percentage = (races_podiumed / races_participated) * 100 if races_participated > 0 else 0
        
        races_top_10 = sum(self.safe_int(stat['top_10s']) for stat in season_statistics)
        top_10_percentage = (races_top_10 / races_participated) * 100 if races_participated > 0 else 0
        
        pro_seasons = len(set(stat['season'] for stat in season_statistics if stat['season']))

        # Grand Tour metrics
        grand_tours_started = len(grand_tour_results)
        grand_tours_won = len([gt for gt in grand_tour_results if gt['gc'] == '1'])
        grand_tours_win_percentage = (grand_tours_won / grand_tours_started) * 100 if grand_tours_started > 0 else 0
        
        grand_tours_podiums = len([gt for gt in grand_tour_results if gt['gc'] in ['1', '2', '3']])
        grand_tours_podium_percentage = (grand_tours_podiums / grand_tours_started) * 100 if grand_tours_started > 0 else 0
        
        grand_tours_top_10s = len([gt for gt in grand_tour_results if gt['gc'].isdigit() and int(gt['gc']) <= 10])
        grand_tours_top_10_percentage = (grand_tours_top_10s / grand_tours_started) * 100 if grand_tours_started > 0 else 0
        
        # Extract stage wins
        def extract_stage_wins(text):
            if not text:
                return 0
            match = re.search(r'1\s*\((\d+)x\)', text)
            if match:
                return int(match.group(1))
            elif '1' in text:
                return 1
            return 0

        stage_wins_in_grand_tours = sum(extract_stage_wins(gt['best_stage']) for gt in grand_tour_results)
        total_gc_days_in_leader_jersey = sum(jersey['gc'] for jersey in leader_jersey_data)

        # Monument metrics
        monuments_started = len(monument_results)
        monuments_won = len([m for m in monument_results if m['result'] == '1'])
        monuments_win_percentage = (monuments_won / monuments_started) * 100 if monuments_started > 0 else 0
        
        monuments_podiums = len([m for m in monument_results if m['result'] in ['1', '2', '3']])
        monuments_podium_percentage = (monuments_podiums / monuments_started) * 100 if monuments_started > 0 else 0
        
        monuments_top_10s = len([m for m in monument_results if m['result'].isdigit() and int(m['result']) <= 10])
        monuments_top_10_percentage = (monuments_top_10s / monuments_started) * 100 if monuments_started > 0 else 0

        return {
            'races_participated': races_participated,
            'races_won': races_won,
            'win_percentage': round(win_percentage, 2),
            'races_podiumed': races_podiumed,
            'podium_percentage': round(podium_percentage, 2),
            'races_top_10': races_top_10,
            'top_10_percentage': round(top_10_percentage, 2),
            'pro_seasons': pro_seasons,
            'grand_tours_started': grand_tours_started,
            'grand_tours_won': grand_tours_won,
            'grand_tours_win_percentage': round(grand_tours_win_percentage, 2),
            'grand_tours_podiums': grand_tours_podiums,
            'grand_tours_podium_percentage': round(grand_tours_podium_percentage, 2),
            'grand_tours_top_10s': grand_tours_top_10s,
            'grand_tours_top_10_percentage': round(grand_tours_top_10_percentage, 2),
            'stage_wins_in_grand_tours': stage_wins_in_grand_tours,
            'total_gc_days_in_leader_jersey': total_gc_days_in_leader_jersey,
            'monuments_started': monuments_started,
            'monuments_won': monuments_won,
            'monuments_win_percentage': round(monuments_win_percentage, 2),
            'monuments_podiums': monuments_podiums,
            'monuments_podium_percentage': round(monuments_podium_percentage, 2),
            'monuments_top_10s': monuments_top_10s,
            'monuments_top_10_percentage': round(monuments_top_10_percentage, 2)
        }

    def scrape_complete_rider_data(self, rider_name: str) -> Dict:
        """Scrape all data for a rider and return comprehensive results"""
        print(f"Starting comprehensive scrape for {rider_name}...")
        
        urls = self.generate_rider_urls(rider_name)
        rider_slug = urls['rider_slug']
        
        # Scrape all data
        rider_dob, rider_nationality, rider_place_of_birth = self.scrape_rider_info(rider_slug)
        wins_list = self.scrape_total_wins(rider_slug)
        monument_results = self.scrape_monument_results(rider_slug)
        grand_tour_results = self.scrape_grand_tour_results(rider_slug)
        world_championships_results = self.scrape_world_championships_results(rider_slug)
        season_statistics = self.scrape_season_statistics(rider_slug)
        leader_jersey_data = self.scrape_leader_jerseys(rider_slug)
        
        # Calculate metrics
        career_metrics = self.calculate_career_metrics(
            wins_list, season_statistics, grand_tour_results, 
            monument_results, leader_jersey_data
        )
        
        # Compile complete data
        complete_data = {
            'rider_info': {
                'name': rider_name,
                'date_of_birth': rider_dob,
                'nationality': rider_nationality,
                'place_of_birth': rider_place_of_birth
            },
            'career_metrics': career_metrics,
            'detailed_data': {
                'total_wins': wins_list,
                'monument_results': monument_results,
                'grand_tour_results': grand_tour_results,
                'world_championships_results': world_championships_results,
                'season_statistics': season_statistics,
                'leader_jersey_data': leader_jersey_data
            }
        }
        
        print(f"Completed comprehensive scrape for {rider_name}")
        return complete_data
