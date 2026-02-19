import json
import sqlite3
from datetime import datetime, timedelta
DB_PATH = "statarea_ml_accumulator.db"


class DatabaseManager:
	def __init__(self, db_path=DB_PATH):
		self.conn = sqlite3.connect(db_path)
		self.cur = self.conn.cursor()
		self._ensure_tables()

	def _ensure_tables(self):
		# ----------------- TEAMS -----------------
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS teams (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE
			)
		""")

		# ----------------- LEAGUES -----------------
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS leagues (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE
			)
		""")

		# --------------- ACCUMULATION LOG ---------------
		self.cur.execute("""
		CREATE TABLE IF NOT EXISTS accumulation_log (
			date TEXT PRIMARY KEY,
			scraped INTEGER DEFAULT 0,
			updated INTEGER DEFAULT 0
		);
		""")

		# ----------------- MATCHES -----------------
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS raw_matches (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				date INTEGER NOT NULL,
				match_url TEXT,
				home_team_id INTEGER NOT NULL,
				away_team_id INTEGER NOT NULL,
				league_id INTEGER,
				league_meta TEXT,
				home_ht_goals INTEGER,
				away_ht_goals INTEGER,
				home_ft_goals INTEGER,
				away_ft_goals INTEGER,
				statarea_tip TEXT,
				statarea_odds TEXT,
				home_next_match TEXT,
				away_next_match TEXT,
				h2h TEXT,
				last10 TEXT,
				stat_facts TEXT,
				standings TEXT,
				team_bet_stats TEXT,
				UNIQUE(home_team_id, date, away_team_id),
				FOREIGN KEY(home_team_id) REFERENCES teams(id),
				FOREIGN KEY(away_team_id) REFERENCES teams(id),
				FOREIGN KEY(league_id) REFERENCES leagues(id)
			)
		""")
		self.conn.commit()

	# ---------------- HELPERS ----------------
	def get_or_create_team(self, name):
		if not name:
			return None
		self.cur.execute("SELECT id FROM teams WHERE name=?", (name,))
		row = self.cur.fetchone()
		if row:
			return row[0]
		self.cur.execute("INSERT INTO teams (name) VALUES (?)", (name,))
		self.conn.commit()
		return self.cur.lastrowid

	def get_or_create_league(self, name):
		if not name:
			return None
		self.cur.execute("SELECT id FROM leagues WHERE name=?", (name,))
		row = self.cur.fetchone()
		if row:
			return row[0]
		self.cur.execute("INSERT INTO leagues (name) VALUES (?)", (name,))
		self.conn.commit()
		return self.cur.lastrowid

	# ---------------- INSERT ----------------
	def insert_matches(self, row):
		home_id = self.get_or_create_team(row.get("home_name"))
		away_id = self.get_or_create_team(row.get("away_name"))
		league_id = self.get_or_create_league(row.get("league"))
		date_val = row.get("date")

		if not home_id or not away_id or not date_val:
			return  # integrity guard

		details = row.get("details") or {}

		self.cur.execute("""
			INSERT OR IGNORE INTO raw_matches
			(date, match_url, home_team_id, away_team_id, league_id, league_meta,
			 statarea_tip, statarea_odds,
			 home_next_match, away_next_match,
			 h2h, last10, stat_facts, standings, team_bet_stats)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""", (
			date_val,
			row.get("link"),
			home_id,
			away_id,
			league_id,
			json.dumps(row.get("league_meta")),
			row.get("statarea_tip"),
			json.dumps(row.get("statarea_odds")),
			json.dumps(details.get("next_match", {}).get("home")),
			json.dumps(details.get("next_match", {}).get("away")),
			json.dumps(details.get("matches_btw_teams")),
			json.dumps(details.get("last_10")),
			json.dumps(details.get("stat_facts")),
			json.dumps(details.get("standings")),
			json.dumps(details.get("team_bet_stats"))
		))
		self.conn.commit()

	# ---------------- UPDATE SCORES ----------------
	def update_scores(self, updates):
		for update in updates:
			self.cur.execute("""
				UPDATE raw_matches
				SET home_ht_goals=?, away_ht_goals=?, home_ft_goals=?, away_ft_goals=?
				WHERE match_url=? AND home_ht_goals IS NULL
			""", (
				update.get("home_ht"),
				update.get("away_ht"),
				update.get("home_ft"),
				update.get("away_ft"),
				update.get("link")
			))
		self.conn.commit()

	# ---------------- PENDING MATCHES ----------------
	def get_pending_matches(self, days=None):
		"""
		Fetch matches where scores are not updated yet or links failed.
		Optionally filter by 'days' in the future.
		"""
		query = "SELECT * FROM raw_matches WHERE home_ft_goals IS NULL OR away_ft_goals IS NULL"
		params = ()
		if days is not None:
			query += " AND date <= ?"
			params = (days,)
		self.cur.execute(query, params)
		return self.cur.fetchall()
	
	def log_accumulation(self, scraped=True, updated=True):
		today = datetime.now().strftime("%Y-%m-%d")

		query = """
		INSERT OR REPLACE INTO accumulation_log (date, scraped, updated)
		VALUES (?, ?, ?);
		"""
		self.conn.execute(query, (today, int(scraped), int(updated)))
		self.conn.commit()

	def was_accumulated_today(self):
		today = datetime.now().strftime("%Y-%m-%d")

		query = "SELECT 1 FROM accumulation_log WHERE date = ?;"
		cursor = self.conn.execute(query, (today,))
		return cursor.fetchone() is not None	
	
	def get_last_accumulation_date(self):
		query = """
		SELECT date FROM accumulation_log
		ORDER BY date DESC
		LIMIT 1;
		"""
		cursor = self.conn.execute(query)
		row = cursor.fetchone()
		return row[0] if row else None

	def get_missed_days(self, limit_days=3):

		last_date = self.get_last_accumulation_date()
		if not last_date:
			return []

		last = datetime.strptime(last_date, "%Y-%m-%d")
		today = datetime.now()

		missed = []
		delta = (today - last).days

		if delta <= 1:
			return []

		for i in range(1, delta):
			missed_date = last + timedelta(days=i)
			if (today - missed_date).days <= limit_days:
				missed.append(missed_date.strftime("%Y-%m-%d"))

		return missed
	
	# ---------------- CLOSE ----------------
	def close(self):
		self.conn.commit()
		self.conn.close()
