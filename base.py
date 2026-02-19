import sqlite3
import requests
from urllib.parse import urljoin, quote, urlparse
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor 
from concurrent.futures import as_completed
from itertools import zip_longest
import sys
import re
from DatabaseManager import DatabaseManager, DB_PATH
sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------
# GLOBAL SETTINGS
# ---------------------------------------------------------
BASE_URL = "https://www.statarea.com"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/120.0 Safari/537.36"
    )
}

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.statarea.com/",
    "Connection": "keep-alive",
})


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def clean_url(url: str):
    """Safely quote and join relative links."""
    if not url:
        return None
    return quote(url, safe='/:()')

def db_row_to_match_dict(row):
    """
    Converts a raw_matches row tuple into the dict format
    expected by StatareaSimplifier.simp_whole_match_row
    """
    match_dict = {}

    # Simple scalar fields
    match_dict['date'] = row['date']  # might need conversion later
    match_dict['home_team_id'] = row['home_team_id']
    match_dict['away_team_id'] = row['away_team_id']
    match_dict['league_id'] = row['league_id']
    match_dict['home_ht_goals'] = row['home_ht_goals']
    match_dict['away_ht_goals'] = row['away_ht_goals']
    match_dict['home_ft_goals'] = row['home_ft_goals']
    match_dict['away_ft_goals'] = row['away_ft_goals']

    # JSON/dict fields
    for field in ['home_next_match', 'away_next_match', 'h2h', 'last10',
                  'stat_facts', 'standings', 'team_bet_stats']:
        raw_val = row[field]
        if raw_val is None:
            match_dict[field] = {}
        else:
            match_dict[field] = json.loads(raw_val)

    return match_dict
def extract_date_from_link(link):
    # example link: /predictions/date/2026-01-31/competition
    parts = urlparse(link).path.split("/")
    for part in parts:
        if part.count("-") == 2:  # crude YYYY-MM-DD
            return part
    return None

def parse_league_name(raw: str):
    if not raw:
        return {
            "region": None,
            "competition": None,
            "season": None
        }

    region = None
    competition = None
    season = None

    if " - " in raw:
        region, rest = raw.split(" - ", 1)
    else:
        rest = raw

    m = re.search(r"(20\d{2}/20\d{2})$", rest)
    if m:
        season = m.group(1)
        competition = rest.replace(season, "").strip()
    else:
        competition = rest.strip()

    return {
        "region": region,
        "competition": competition,
        "season": season
    }

def fetch(url, retries=3, delay=1.5, min_size=100000):
    """
    Fetch HTML with retries, polite backoff, and human-like session behavior.
    min_size = minimal content size for full page detection
    """
    
    # Soft pre-visit to homepage if first call in session
    if not hasattr(fetch, "_visited_home"):
        session.get("https://www.statarea.com/")
        time.sleep(random.uniform(2.0, 4.0))
        fetch._visited_home = True

    for attempt in range(1, retries + 1):
        try:
            # Fetch page
            resp = session.get(url, timeout=15, headers={"Referer": "https://www.statarea.com/"})
            resp.raise_for_status()
            
            # Check for "lite" page
            if len(resp.text) < min_size:
                raise ValueError(f"Lite page detected ({len(resp.text)} bytes)")

            # Return parsed soup
            return BeautifulSoup(resp.text, "lxml")

        except Exception as e:
            print(f"[Fetch Error] {url} | {type(e).__name__}: {e}")
            if attempt < retries:
                sleep_time = delay * random.uniform(1.0, 2.0)
                print(f"  retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
    
    print(f"[FAIL] Could not fetch full page: {url}")
    return BeautifulSoup("", "lxml")



def text(el, default=""):
    """Extract element text or return default."""
    try:
        return el.get_text(strip=True)
    except:
        return default

def attr(el, name, default=None):
    """Extract attribute or return default."""
    try:
        return el.get(name, default)
    except:
        return default


