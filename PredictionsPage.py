from base import *


class PredictionsPage:
    def __init__(self, soup):
        self.soup = soup

    # -------------------------
    def days_matches(self, soup):
        matches = soup.find_all('div', class_="match")
        return [self.parse_row(m) for m in matches]

    # -------------------------
    def parse_row(self, match):
        """Parse the prediction page match row."""

        time = text(match.select_one('div.date'))

        link_tag = attr(match.select_one('.name').select_one('a'), 'href')
        raw_link = link_tag
        link = clean_url(link_tag)

        home_name_el, away_name_el = match.select('div.name')
        home_name = text(home_name_el)
        away_name = text(away_name_el)

        # ----------------- halftime score -----------------
        halftime_el = match.select_one('div.htres')
        halftime_text = text(halftime_el).replace('HT', '').strip() if halftime_el else ""
        try:
            home_ht, away_ht = map(int, halftime_text.split(':'))
        except:
            home_ht = away_ht = None

        # ----------------- fulltime score -----------------
        try:
            home_ft = int(text(match.select_one('.hostteam a.goals')))
        except:
            home_ft = None

        try:
            away_ft = int(text(match.select_one('.guestteam a.goals')))
        except:
            away_ft = None

        # ----------------- type / tip ---------------------
        tip = text(match.select_one('[class^="type"]'))

        # ----------------- odds ---------------------------
        coefrow = match.select_one('div.coefrow')
        odds = self.extract_odds(coefrow) if coefrow else {}

        # ----------------- row dict -----------------------
        row = {
            "time": time,
            "link": link,
            "home_name": home_name,
            "away_name": away_name,
            "home_ht_goals": home_ht,
            "away_ht_goals": away_ht,
            "home_ft_goals": home_ft,
            "away_ft_goals": away_ft,
            "statarea_tip": tip,
            "statarea_odds": odds
        }

        for k, v in odds.items():
            row[f"odd_{k}"] = v

        return row

    # -------------------------
    def extract_odds(self, coefrow):
        labels = ['1', 'X', '2', 'HT1', 'HTX', 'HT2', '1.5', '2.5', '3.5', 'BTS', 'OTS']
        elems = coefrow.select('[class*="value"]')
        odds = [el.get_text(strip=True) for el in elems]

        return {
            label: odds[i] if i < len(odds) else None
            for i, label in enumerate(labels)
        }

    # -------------------------
    def navigate_to(self, days):
        nav_par = self.soup.select_one('#cdate + .buttons')
        if not nav_par:
            return []

        links = [btn['href'] for btn in nav_par.select('a[href]')]
        mapping = dict(zip_longest(range(1, 8), links))

        day_links = []
        if isinstance(days, int):
            l = mapping.get(days)
            if l:
                day_links.append((l, extract_date_from_link(l)))
        elif isinstance(days, list):
            for d in days:
                l = mapping.get(d)
                if l:
                    day_links.append((l, extract_date_from_link(l)))
        else:
            raise TypeError("days must be int or list")

        return day_links


    def all_days_matches(self):
        all_days_links = {
            "Day_1": None, 
            "Day_2": None,
            "Day_3": None,
            "Day_4": None,
            "Day_5": None,
            "Day_6": None,
            "Day_7": None
        }
        all_days_matches = {
            "Day_1": None, 
            "Day_2": None,
            "Day_3": None,
            "Day_4": None,
            "Day_5": None,
            "Day_6": None,
            "Day_7": None
        }
        
        for day in range(1, 8):
            all_days_links[f"Day_{day}"] = self.navigate_to(day)

        for day_key, link in all_days_links:
            if link:
                soup = fetch(link)
                all_days_matches[day_key] = self.days_matches(soup) 

        return all_days_matches
    
# -------------------------------
# TEST BLOCK
# -------------------------------
if __name__ == "__main__":
    base_url = "https://www.statarea.com/predictions"
    print(f"Fetching predictions page: {base_url}")
    soup = fetch(base_url)

    pp = PredictionsPage(soup)
    day_link = pp.navigate_to(days=1)  # pick any day
    print(f"\n[DEBUG] Day 1 raw link from navigate_to(): {day_link}")

    if day_link:
        print(f"Fetching matches for Day 1: {day_link}")
        day_soup = fetch(day_link)
        rows = pp.days_matches(day_soup)
        print(f"\n[DEBUG] Scraped {len(rows)} match rows:\n")
        for r in rows:
            print(f"Home: {r['home_name']}, Away: {r['away_name']}")
            print(f"Raw link: {r['raw_link']}")
            print(f"Cleaned link: {r['link']}")
            print("--------------------------------------------------")
