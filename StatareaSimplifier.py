from base import *
from ml_base import *
from datetime import date
from DatabaseManager import DatabaseManager


class StatareaSimplifier:
	def __init__(self):
		self.db = DatabaseManager()

	def parse_statarea_tip(self, tip):
		"""
		Take the raw Data being scraped from statarea and turn into information ML can use.
		param: tip = A single tip	
		"""
		
		tip_map = {
			"1": 1,
			"2": 2,
			"X": 0,
			"12": 3,
			"1X": 1.5,
			"X2": 2.5
		}
		if tip in tip_map.keys():	
			parsed_tip = tip_map[tip]
			return parsed_tip
		else:
			print(f"[Parse_statarea_tip]: ERROR: Provided tip is not in tip map || provided tip: {tip}")
			return None
		
	def standardize_date(self, date_input):
		if isinstance(date_input, date):
			return date_input
		return datetime.strptime(date_input, "%Y-%m-%d").date()

	def date_obj_to_int(self, date_obj):
		date_int = date_obj.year * 10000 + date_obj.month * 100 + date_obj.day
		return date_int

	def days_in_between(self, past_date, future_date):
		"""
		Calculates number of days between two YYYY-MM-DD strings.
		Assumes future_date >= past_date.
		"""

		past = self.standardize_date(past_date)
		future = self.standardize_date(future_date)

		delta = future - past

		return delta.days

	def parse_next_match(self, next_match, team_id, current_match_date):
		"""
		Returns:
			is_home (1 or 0)
			days_until_next_match (int)
		"""

		host_id = self.db.get_or_create_team(next_match["host"])
		guest_id = self.db.get_or_create_team(next_match["guest"])
		is_home = 1 if team_id == host_id else 0

		next_match_date = self.standardize_date(next_match["date"])

		days_until = self.days_in_between(current_match_date, next_match_date)

		if is_home: 
			opponent = self.simp_standings[guest_id]
		else:
			opponent = self.simp_standings[host_id]

		return [is_home, days_until, opponent]

	def parse_match_outc(self, hhtg, ahtg, hftg, aftg):
		def _parse_half(hg, ag):
			if hg == ag:
				return 0
			elif hg > ag:
				return 1
			else:
				return 2
			
		ht_outc = _parse_half(hhtg, ahtg)
		ft_outc = _parse_half(hftg, aftg)

		return ht_outc, ft_outc

	def calc_statarea_tip_accu(self):
		"""
		Calculate the accuracy of statarea's tips when and only when they tip on one outcome.
		"""
		conn = sqlite3.connect('statarea_ml_accumulator.db')
		cur = conn.cursor()

		cur.execute('SELECT statarea_tip, home_ht_goals, away_ht_goals, home_ft_goals, away_ft_goals FROM raw_matches WHERE home_ft_goals IS NOT NULL;')
		rows = cur.fetchall()
		conn.close()

		cor_pred = []
		incor_pred = []
		print(F'Rows with outc: {len(rows)}')
		for row in rows:
			tip, hhtg, ahtg, hftg, aftg = row
			if tip in ["12", "1X", "X2"]:
				continue
			parsed_tip = self.parse_statarea_tip(tip)
			_, ft_outc = self.parse_match_outc(hhtg, ahtg, hftg, aftg)

			if parsed_tip == ft_outc:
				cor_pred.append(f'{parsed_tip} > {ft_outc}') 
			else:
				incor_pred.append(f'{parsed_tip} > {ft_outc}')
		
		accu = (len(cor_pred) / (len(incor_pred) + len(cor_pred))) * 100

		return cor_pred, incor_pred, accu

	def statarea_odds_model(self):
		conn = sqlite3.connect('statarea_ml_accumulator.db')
		cur = conn.cursor()

		cur.execute('SELECT statarea_odds, home_ht_goals, away_ht_goals, home_ft_goals, away_ft_goals FROM raw_matches')
		rows = cur.fetchall()
		conn.close()

		odds_outc = []
		for row in rows:
			odds, hhtg, ahtg, hftg, aftg = row
			odds_dict = json.loads(odds)
			odds = [int(v) for v in odds_dict.values()]
			ht_outc, ft_outc = self.parse_match_outc(hhtg, ahtg, hftg, aftg)
			odds_outc.append({
				"ht_outc": ht_outc, 
				"ft_outc": ft_outc,
				"odds": odds
			})
		row = odds_outc[0]
		print(row["odds"])

		X, y_ht, y_ft = [], [], []
		for odd_outc in odds_outc:
			y_ht.append(odd_outc["ht_outc"])
			y_ft.append(odd_outc["ft_outc"])
			X.append(
				odd_outc["odds"]
			)

		from ml_base import train_models 
		X = np.array(X)
		y_ht = np.array(y_ht)
		y_ft = np.array(y_ft)

		print("HT model:")
		train_models(X, y_ht)

		print("FT model:")
		train_models(X, y_ft)

		print("HT baseline:", self.baseline(y_ht))
		print("FT baseline:", self.baseline(y_ft))

	def baseline(self, y):
		from collections import Counter
		c = Counter(y)
		return max(c.values()) / len(y)

	def simp_standing(self, team_standing):
		"""
		This function takes a single team from the standings json
		and turns it into a dictionary with flat values.
		"""

		# The list map is a map that shows what each value 
		# represents in the final flat_list for each team in the standings table
		list_map = {
			1: "position",
			2: "matches_played",
			3: "points",
			4: "home_wins",
			5: "home_draws",
			6: "home_losses",
			7: "home_goals_scored",
			8: "home_goals_conceded",
			9: "away_wins",
			10: "away_draws",
			11: "away_losses",
			12: "away_goals_scored",
			13: "away_goals_conceded",
			14: "overall_wins",
			15: "overall_draws",
			16: "overall_losses", 
			17: "overall_goals_scored",
			18: "overall_goals_conceded"
		}
		
		position = team_standing["position"]
		team_name = team_standing["name"]
		matches_played = team_standing["matches_played"]
		points = team_standing['points']
		home_stats, away_stats, overall_stats = team_standing['home_stats'], team_standing['away_stats'], team_standing['overall_stats']

		standings_flat_list = [int(position), int(matches_played), int(points)]

		def _individual_stats_to_flat_list(home_stats, away_stats, overall_stats):
			"""
			This function turns three groups of stat_dictionaries into a flat list
			Parameters:
				home_stats, away_stats, overall_stats
			Returns:
				flat_list of 15 elements
			"""
			def _parse_individual_stats_dict(standings_stats_dict):
				"""
				This function turns a single stat_dictionary into a flar list.
				"""
				values = []
				for value in standings_stats_dict.values():
					values.append(int(value))
				return values
			
			home_list = _parse_individual_stats_dict(home_stats)
			away_list = _parse_individual_stats_dict(away_stats)
			overall_list = _parse_individual_stats_dict(overall_stats)

			flat_list = []
			for section in [home_list, away_list, overall_list]:
				for item in section:
					flat_list.append(item)
			
			return flat_list
		
		#Check if the flat list has the required amount of stats
		stats_flat_list = _individual_stats_to_flat_list(home_stats, away_stats, overall_stats)
		if len(stats_flat_list) == 15:
			for item in stats_flat_list:
				standings_flat_list.append(item)
			return {
				self.db.get_or_create_team(team_name):	standings_flat_list
			}
		else:
			print('[json_standings_to_flat_list_error]: stats_flat_list is not the required size')
			print(f'expected size was 15, size got was {len(stats_flat_list)}')
		
	def simp_tbs(self, tbs_list):
		flat = []

		for barchart in tbs_list:
			for barrow in barchart["barrows"]:
				val = barrow["value"]

				if val.endswith("%"):
					val = val[:-1]

				flat.append(float(val) / 100.0)


		if len(flat) != 88:
			raise ValueError("TBS structure changed")

		return flat

	def initialize_standings(self, standings):
		self.simp_standings = {}
		for team in standings:
			self.simp_standings.update(self.simp_standing(team))

		self.standings_vector_length = len(next(iter(self.simp_standings.values())))
		self.zero_standing_vector = [0] * self.standings_vector_length

	def simp_action(self, action):
		"""Simplify a match action dict"""
		if action['side'] == 'hostteam':
			is_home = 1
		else:
			is_home = 0
		time = int(action['time'])
		act_map = {
			None: 0,
			'goal': 1,
			'ycard': 2,
			'rcard': 3,
			'own': 4,
			'penalty': 5,
			'dycard': 6
		}
		act = act_map[action['actions']]
		return {
			'is_home': is_home,
			'time': time,
			'act': act
		}

	def check_goal_integrity(self, ht, ft):
		"""Validate goal arrangement"""
		if ft >= ht:
			return True
		elif ft == ht == None:
			return None
		else:
			return False

	def iterate_last10(self, teams_last_10_json, spotlight_team_str, current_match_date, add_actions=False):
		"""This function gets a last10 json and converts it into a list"""

		iterated_last10 = []
		db = DatabaseManager()
		dates = []
		for match_summary in teams_last_10_json:

			#Append all the dates in a list for later processing
			match_date = self.standardize_date(match_summary['date'])

			if match_date >= current_match_date:
				# This match is in the future or same day → leakage
				continue

			dates.append(match_summary['date'])


			#League
			league = match_summary['league']
			league_id = db.get_or_create_league(league)
			
			#Team Names
			hostteam_name = match_summary['hostteam_name']		
			guestteam_name = match_summary['guestteam_name']		
			
			# Goals
			# Note: 'htg' -> half_time_goals
			#		'ftg' -> full_time_goals
			
			# === HOME ===
			hostteam_htg = int(match_summary['hostteam_ht_goals'])
			hostteam_ftg = int(match_summary['hostteam_goals'])

			#statarea soup can be messy and sometimes the goals can be swapped, so we add a check
			if self.check_goal_integrity(hostteam_htg, hostteam_ftg) is True:
				pass
			elif self.check_goal_integrity(hostteam_htg, hostteam_ftg) is None:
				print('[Last10 Error]: No goals found in last10 json, skipping match in last 10')
				print(f'[Match_skipped]: {hostteam_name} vs {guestteam_name}')
				continue
			else:
				hostteam_htg = int(match_summary['hostteam_goals'])
				hostteam_ftg = int(match_summary['hostteam_ht_goals'])

			# === AWAY ===
			guestteam_htg = int(match_summary['guestteam_ht_goals'])
			guestteam_ftg = int(match_summary['guestteam_goals'])

			#the same goal integrity check for away
			if self.check_goal_integrity(guestteam_htg, guestteam_ftg) is True:
				pass
			elif self.check_goal_integrity(guestteam_htg, guestteam_ftg) is None:
				print('[Last10 Error]: No goals found in last10 json, skipping match in last 10')
				print(f'[Match_skipped]: {hostteam_name} vs {guestteam_name}')
				continue			
			else:
				guestteam_htg = int(match_summary['guestteam_goals'])
				guestteam_ftg = int(match_summary['guestteam_ht_goals'])

			#Process outcomes
			ht_outc, ft_outc = self.parse_match_outc(hostteam_htg, guestteam_htg, hostteam_ftg, guestteam_ftg)

			actions = match_summary['actions']

			if spotlight_team_str == hostteam_name:
				is_home = 1
				opponent_id = self.db.get_or_create_team(guestteam_name)
			else:
				is_home = 0
				opponent_id = self.db.get_or_create_team(hostteam_name)

			if opponent_id in self.simp_standings:
				opponent_standing = [1] + self.simp_standings[opponent_id]
			else:
				opponent_standing = [0] + self.zero_standing_vector


			match = [
				league_id,
				is_home,
				opponent_standing,
				ht_outc,
				ft_outc,
				hostteam_htg,
				guestteam_htg,
				hostteam_ftg,
				guestteam_ftg,
			]
			
			if add_actions:
				match.append([self.simp_action(act) for act in actions])

			iterated_last10.append(match)
		return iterated_last10, dates

	def simp_last10(self, last10_json, spotlight_team_str, current_match_date):
		"""
		Takes the result of the 'iterate_last10' method and turns it into a flat list 
		and then appends a temporal feature of the dates to it.
		"""

		iterated_last10, dates = self.iterate_last10(
			last10_json,
			spotlight_team_str,
			current_match_date
		)

		parsed_dates = self.last10_dates_parser(dates)
		assert len(iterated_last10) == 10
		assert len(parsed_dates) == 9

		flat_list = []

		for match in iterated_last10:
			flat_list.extend(match)

		flat_list.extend(parsed_dates)

		return flat_list

	def simp_stat_facts(self, stat_facts, flat_mode=True):
		FEATURE_KEYS = [
			"wins",
			"draws",
			"losses",
			"avg_scored",
			"avg_conceded",
			"score_chance",
			"concede_chance",
			"clean_sheets",
			"fail_to_score",
			"over25",
			"under25",
			"time_no_score",
			"time_no_concede",
		]

		LABEL_MAP = {
			"Average scored goals per match": "avg_scored",
			"Average conceded goals per match": "avg_conceded",
			"Chance to score goal next match": "score_chance",
			"Chance to conceded goal next match": "concede_chance",
			"Number of clean sheet matches": "clean_sheets",
			"Failure to score matches": "fail_to_score",
			"Matches over 2.5 goals in": "over25",
			"Matches under 2.5 goals in": "under25",
			"Time without scored goal": "time_no_score",
			"Time without conceded goal": "time_no_concede",
		}

		def parse_value(raw):
			raw = raw.strip()
			if "%" in raw:
				return float(raw.replace("%", "")) / 100.0
			if "min" in raw:
				return float(raw.replace("min.", "").replace("min", "").strip())
			return float(raw)

		def parse_stat_block(stat_facts):
			stats = {key: 0.0 for key in FEATURE_KEYS}
			for item in stat_facts:
				label = item.get("label", "")
				value = item.get("value", "0")
				if label.startswith("Number of"):
					if "wins" in label:
						stats["wins"] = parse_value(value)
					elif "draws" in label:
						stats["draws"] = parse_value(value)
					elif "loses" in label:
						stats["losses"] = parse_value(value)
					continue
				if label in LABEL_MAP:
					stats[LABEL_MAP[label]] = parse_value(value)
			return stats
		parsed_stats = parse_stat_block(stat_facts)
		
		if not flat_mode:
			return parsed_stats
		else:
			return [parsed_stats[key] for key in FEATURE_KEYS]

	def last10_dates_parser(self, dates_list):
		"""
		Takes 10 date strings (newest first, YYYY-MM-DD)
		and returns 9 integers representing the number of
		days between consecutive matches.
		"""

		assert len(dates_list) == 10

		date_objects = [
			datetime.strptime(date, "%Y-%m-%d")
			for date in dates_list
		]

		return [
			(date_objects[i] - date_objects[i + 1]).days
			for i in range(9)
		]

	def simp_h2h(self, h2h):
		return self.simp_last10(h2h)

	def safe_load_json(self, object):
		if isinstance(object, dict):
			return object
		elif isinstance (object, None):
			print('[safe_load_json]: error: Receieved None')
			raise ValueError
		elif isinstance(object, list):
			print('[safe_load_json]: error: Recieved list')
		elif isinstance(object, str):
			return json.loads(object)
		else:
			print(f'[safe_load_json]: error: Recieved unprescribed type: {type(object)}')
			raise ValueError
		
	def ultimate_flattener(self, obj):
		flat = []

		if isinstance(obj, list):
			for item in obj:
				flat.extend(self.ultimate_flattener(item))
		else:
			flat.append(obj)

		return flat

	def simp_whole_match_row(self, match, ultimate_flat_list=True):
		"""Simplify / De soup an entire match row"""
		#basic data
		date = self.standardize_date(match['date'])
		home = match['home_team_id']
		away = match['away_team_id']
		league = match['league_id']

		#goals
		home_htg = match['home_ht_goals']
		away_htg = match['away_ht_goals']
		home_ftg = match['home_ft_goals']
		away_ftg = match['away_ft_goals']
		
		# Start by initializing the standings table
		self.initialize_standings(match['standings'])

		#tbs -> team_bet_statistics
		tbs = match['team_bet_stats']
		home_tbs, away_tbs = tbs['home_bet_stats'], tbs['away_bet_stats']
		simp_home_tbs, simp_away_tbs = self.simp_tbs(home_tbs), self.simp_tbs(away_tbs)

		#last10
		last10 = match['last10']
		home_last10, away_last10 = last10['home_last_10'], last10['away_last_10']
		simp_home_last10 = self.simp_last10(
			home_last10,
			self.db.get_or_create_team(home),
			date
		)

		simp_away_last10 = self.simp_last10(
			away_last10,
			self.db.get_or_create_team(away),
			date
		)


		#Stat Facts
		stat_facts = match['stat_facts']
		home_stat_facts, away_stat_facts = stat_facts['home_stat_facts'], stat_facts['away_stat_facts']
		simp_home_stat_facts, simp_away_stat_facts = self.simp_stat_facts(home_stat_facts), self.simp_stat_facts(away_stat_facts)

		#Next Matches
		home_next_match = self.parse_next_match(match['home_next_match'], home, date)
		away_next_match = self.parse_next_match(match['away_next_match'], away, date)

		#h2h
		h2h = match['h2h']
		#simp_h2h = self.simp_h2h(h2h)

		if ultimate_flat_list:
			return self.ultimate_flattener([
				self.date_obj_to_int(date), 
				home,
				away,
				league,
				home_next_match,
				away_next_match,
				#simp_h2h,
				simp_home_last10,
				simp_away_last10, 
				simp_home_stat_facts,
				simp_away_stat_facts,
				simp_home_tbs,
				simp_away_tbs
			])

	def close(self):
		self.db.close()

