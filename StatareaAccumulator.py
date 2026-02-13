from base import *
from MatchPage import *
from PredictionsPage import *
from scraper import *
from DatabaseManager import DatabaseManager  

class StatareaAccumulator:
	def __init__(self, future_days=5, update_scores_days=3, db_path="statarea_ml_accumulator.db"):
		self.scraper = StatareaScraper()  
		self.db = DatabaseManager(db_path=db_path)
		self.future_days = future_days
		self.update_scores_days = update_scores_days

	# ---------------- FUTURE MATCHES ----------------
	def gather_future_matches(self):
		"""
		Deep scrape upcoming matches for the next `future_days` days and insert into DB.
		"""
		print(f"Gathering future matches for day {self.future_days}. ")
		future_rows = self.scraper.scrape(days=self.future_days, parallel=True)
		for row in future_rows:
			self.db.insert_matches(row)
		print(f"Inserted {len(future_rows)} future matches.")

	# ---------------- UPDATE SCORES ----------------
	def update_scores(self):
		"""
		Shallow scrape for past matches to update scores without fetching full match pages.
		"""
		print(f"Updating scores for day {self.update_scores_days}.")
		rows = self.scraper.collect_match_rows(date_links_with_dates=self.scraper.collect_date_links(self.update_scores_days))
		updates = []
		for row in rows:
			updates.append({
				"link": row.get("link"),
				"home_ht": row.get("home_ht_goals"),
				"away_ht": row.get("away_ht_goals"),
				"home_ft": row.get("home_ft_goals"),
				"away_ft": row.get("away_ft_goals")
			})
		self.db.update_scores(updates)
		print(f"Updated scores for {len(updates)} matches.")

	# ---------------- PENDING MATCHES ----------------
	def pending_matches(self, days=None):
		"""
		Fetch matches that still need scores or failed scraping.
		"""
		return self.db.get_pending_matches(days=days)
	
	def accumulate_daily(self):
		"""
		One-click daily Accumulation:
		1. Update scores for previous day(s)
		2. Scrape future matches for next day(s)
		"""
		print("=== Daily Accumulation Started ===\n\n")
		
		# 1️⃣ Update scores for past matches
		try:
			print("Step 1: Updating past scores...\n")
			self.update_scores()
		except Exception as e:
			print(f"[Accumulate Daily] Error updating past scores: {e}")

		# 2️⃣ Gather future matches
		try:
			print("Step 2: Gathering future matches...\n")
			self.gather_future_matches()
		except Exception as e:
			print(f"[Accumulate Daily] Error gathering future matches: {e}")

		print("\n\n=== Daily Accumulating Finished ===")
	# ---------------- CLOSE ----------------
	def close(self):
		"""
		Safely close the DB connection.
		"""
		self.db.close()

if __name__ == "__main__":
	StatareaAccumulator().accumulate_daily()
	








































































