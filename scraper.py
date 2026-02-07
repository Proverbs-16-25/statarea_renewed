from base import DatabaseManager, fetch, time, random, parse_league_name
from PredictionsPage import PredictionsPage
from MatchPage import MatchPage
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# =========================================================
# PRODUCTION-READY TEST SCRAPER
# =========================================================

class StatareaScraper:

    def __init__(self, base_url="https://www.statarea.com"):
        self.base_url = base_url
        self.db = DatabaseManager()

    # ------------------------------------------------------------
    def collect_date_links(self, days):
        soup = fetch(f"{self.base_url}/predictions")
        pp = PredictionsPage(soup)
        links = pp.navigate_to(days)
        if isinstance(links, str):
            return [links]
        return links or []

    # ------------------------------------------------------------
    def collect_match_rows(self, date_links_with_dates):
        rows = []
        for link, date_str in date_links_with_dates:
            soup = fetch(link)
            pp = PredictionsPage(soup)
            day_rows = pp.days_matches(soup)
            # assign date to every row
            for r in day_rows:
                r["date"] = date_str
            rows.extend(day_rows)
        return rows

    # ------------------------------------------------------------
    def enrich(self, rows, parallel=True, max_workers=5):
        def worker(row):
            if not row.get("link"):
                row["details"] = None
                return row
            try:
                soup = fetch(row["link"])
                row["details"] = MatchPage(soup).parse_all()
                league = row["details"].get("league_name")
                row["league"] = league 
                if league:
                    row["league_meta"] = parse_league_name(row["league"])
                else: row["league_meta"] = None
            except Exception as e:
                print(f"[Worker Error] {row.get('link')} | {type(e).__name__}: {e}")
                row["details"] = None
                row["league"] = None
                row["league_meta"] = None
            return row

        if not parallel:
            return [worker(r) for r in rows]

        out = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(worker, r): r for r in rows}
            for f in as_completed(futures):
                out.append(f.result())
        return out

    # ------------------------------------------------------------
    def add_to_database(self, enriched_rows):
        for row in enriched_rows:
            self.db.insert_raw_match(row)
        print(f"✅ Inserted {len(enriched_rows)} matches into database.")

    # ------------------------------------------------------------
    def scrape(self, days=3, parallel=True, limit=None):
        print("[1] Collecting date links...")
        links = self.collect_date_links(days)

        print("[2] Collecting match rows...")
        rows = self.collect_match_rows(links)

        if limit:
            print(f"[DEBUG] Limiting rows to first {limit}")
            rows = rows[:limit]
    

        print("[3] Enriching rows with match pages...")
        enriched = self.enrich(rows, parallel=parallel)

        return enriched


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    print(">>> Running scraper...\n")

    scraper = StatareaScraper()
    enriched = scraper.scrape(days=3, parallel=True, limit=None)

    print(f"\n>>> Scraped {len(enriched)} matches.")
    print(">>> Inserting into database...\n")

    scraper.add_to_database(enriched)
    scraper.db.close()  # <--- clean close
    # -------------------------
    # INSPECT SCRAPED DATA (PRE-DB)
    # -------------------------
