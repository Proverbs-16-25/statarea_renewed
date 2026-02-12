from base import *
from pprint import pprint


class MatchPage:
	def __init__(self, soup):
		self.soup = soup

	def basic_data(self):
		...
		
	def next_match(self):
		"""Parse the next match for home and away teams."""
		result = {
			"status": "not_available",
			"home": None,
			"away": None
		}

		try:
			root = self.soup.select_one('div.teamsnextmatches')
			if not root:
				return result  # no next match section

			halves = root.select('.teamsnextmatches > .halfcontainer')
			if len(halves) != 2:
				return {"status": "error", "home": None, "away": None}

			home_half, away_half = halves
		except Exception as e:
			print(f"[next_match] Error selecting match halves: --- {e}")
			return {"status": "error", "home": None, "away": None}

		def parse_half(half):
			# Check if next match exists
			if half.select_one('.noitems'):
				return None  # explicitly mark as not available

			# Parse date/time
			try:
				dt = text(half.select_one('[itemprop="startDate"]'))
				date, time = dt.split(' ', 1)
			except Exception:
				date = time = None

			# Parse host and guest
			try:
				teams = half.select('div.halfcontainer')
				host_block, guest_block = teams
				host_name = text(host_block.select_one('[itemprop="homeTeam"]'))
				guest_name = text(guest_block.select_one('[itemprop="awayTeam"]'))
			except Exception:
				host_name = guest_name = None

			return {
				"date": date,
				"time": time,
				"host": host_name,
				"guest": guest_name
			}

		# Parse home and away halves
		result["home"] = parse_half(home_half)
		result["away"] = parse_half(away_half)

		# Determine final status
		if result["home"] or result["away"]:
			result["status"] = "ok"
		elif result["home"] is None and result["away"] is None:
			result["status"] = "not_available"
		else:
			result["status"] = "error"

		return result

	def parse_match_row(self, row):
		"""Parse a single match row for team names, goals, halftime scores, and actions."""
		match_data = {
			'date': text(row.select_one('.date')),
			'league': text(row.select_one('.competition')),
			'hostteam_name': text(row.select_one('.hostteam a')),
			'hostteam_goals': text(row.select_one('.hostteam > .goals')),
			'guestteam_name': text(row.select_one('.guestteam a')),
			'guestteam_goals': text(row.select_one('.guestteam > .goals')),
			'hostteam_ht_goals': None,
			'guestteam_ht_goals': None,
			'actions': []
		}

		details = row.select_one('.details')
		if details:
			# Halftime goals
			halftime_goals = details.select('div.goals')
			if len(halftime_goals) == 2:
				# order: home (left), away (right)
				hostteam_ht_goals_raw, guestteam_ht_goals_raw = halftime_goals
				match_data['hostteam_ht_goals'] = text(hostteam_ht_goals_raw)
				match_data['guestteam_ht_goals'] = text(guestteam_ht_goals_raw)
			elif len(halftime_goals) > 2:
				# ignore penalties — just get the first two
				match_data['hostteam_ht_goals'] = text(halftime_goals[0])
				match_data['guestteam_ht_goals'] = text(halftime_goals[1])

			# Match actions
			acts = details.select('.action')
			for act in acts:
				side_container = act.select_one('div')
				side_list = attr(side_container, "class")
				side = side_list[0] if side_list else None

				matchaction = act.select_one('.matchaction div')
				action_list = attr(matchaction, "class")
				action = action_list[0] if action_list else None

				time_player = text(act.select_one('.player'))
				parts = time_player.split("'", 1)
				time = parts[0].strip()
				player = parts[1].strip() if len(parts) > 1 else ''

				match_data['actions'].append({
					'side': side,
					'action': action,
					'time': time,
					'player': player,
				})

		return match_data



	def matches_btw_teams(self):
		"""Extract 'matches between teams' data from the page."""
		matches_btw_teams_par = self.soup.select_one('.matchbtwteams > .matches')
		if not matches_btw_teams_par:
			return []

		rows = matches_btw_teams_par.select('.matchitem')
		matches = []

		for row in rows:
			data = self.parse_match_row(row)
			matches.append({
				'date': data['date'],
				'league': data['league'],
				'home_name': data['hostteam_name'],
				'away_name': data['guestteam_name'],
				'home_ft_goals': data['hostteam_goals'],
				'away_ft_goals': data['guestteam_goals'],
				'home_ht_goals': data['hostteam_ht_goals'],
				'away_ht_goals': data['guestteam_ht_goals'],
				'actions': data['actions'],
			})

		return matches

	def last_10(self):
		last_10_par = self.soup.select_one('.lastteamsmatches')
		if not last_10_par:
			return {"home_last_10": [], "away_last_10": []}

		home_half, away_half = last_10_par.select('.halfcontainer')

		# Home
		home_rows = home_half.select('.matchitem')
		home_last_10 = [self.parse_match_row(row) for row in home_rows]

		# Away
		away_rows = away_half.select('.matchitem')
		away_last_10 = [self.parse_match_row(row) for row in away_rows]

		return {
			"home_last_10": home_last_10,
			"away_last_10": away_last_10
		}

	def stat_facts(self):
		halves = self.soup.select_one('.teamsstatistics').select('.halfcontainer')
		
		def parse_half(half):
			return [
				{"label": h.select_one('.label').get_text(strip=True),
				"value": h.select_one('.value').get_text(strip=True)}
				for h in half.select('.factitem')
			] if half else []

		return {
			"home_stat_facts": parse_half(halves[0] if len(halves) > 0 else None),
			"away_stat_facts": parse_half(halves[1] if len(halves) > 1 else None)
		}

	def standings(self):
		def parse_sect(section):
			if not section:
				return {"wins": None, "draws": None, "loses": None, "scored": None, "conceded": None}
			return {
				"wins": text(section.select_one('.wins')),
				"draws": text(section.select_one('.draws')),
				"loses": text(section.select_one('.loses')),
				"scored": text(section.select_one('[class*="host"]')),
				"conceded": text(section.select_one('[class*="guest"]'))
			}
		
		def parse_row(row):
			return {
				"position": text(row.select_one('.pos')),
				"name": text(row.select_one('.name a')),
				"matches_played": text(row.select_one('.matches')),
				"points": text(row.select_one('.common2')),
				"home_stats": parse_sect(row.select_one('.home')),
				"away_stats": parse_sect(row.select_one('.away')),
				"overall_stats": parse_sect(row.select_one('.overall'))
			}

		standings = []
		standings_table = self.soup.select_one('.teamstandings')
		if not standings_table:
			return []

		rows = standings_table.select('.standingrow:not(.legend)')

		for row in rows:
			try:
				standings.append(parse_row(row))
			except Exception:
				continue  # ignore the empty or malformed row

		return standings
	
	def league_name(self):
		standings_table = self.soup.select_one('.teamstandings')
		if not standings_table:
			return None
		league_name =  text(standings_table.select_one('.competition'))
		return league_name

	def team_bet_stats(self):
		"""Parses team betting statistics into structured JSON."""
		stats_root = self.soup.select_one('.teamsbetstatistics')
		if not stats_root:
			return {"home_bet_stats": [], "away_bet_stats": []}

		halves = stats_root.select('.halfcontainer')
		if len(halves) < 2:
			# In case statarea ever forgets the second half or breaks layout
			halves.append(None)
		home_half, away_half = halves[:2]

		def parse_half(half):
			if not half:
				return []

			def parse_barrow(barrow):
				return {
					"name": text(barrow.select_one('.name')),
					"value": text(barrow.select_one('.value'))
				}

			def parse_barchart(barchart):
				barrows = barchart.select('.barrow')
				return {
					"title": text(barchart.select_one('.title')),
					"barrows": [parse_barrow(b) for b in barrows]
				}

			barcharts_css = half.select('.barchart')
			return [parse_barchart(barchart) for barchart in barcharts_css]

		return {
			"home_bet_stats": parse_half(home_half),
			"away_bet_stats": parse_half(away_half)
		}
	
	def parse_all(self, parallel=True):
		# define tasks
		tasks = {
			"matches_btw_teams": lambda: self.matches_btw_teams(),
			"next_match": lambda: self.next_match(),
			"last_10": lambda: self.last_10(),
			"stat_facts": lambda: self.stat_facts(),
			"standings": lambda: self.standings(),
			"team_bet_stats": lambda: self.team_bet_stats(),
			"league_name": lambda: self.league_name()
		}


		results = {}

		if parallel:
			# Run in parallel threads
			with ThreadPoolExecutor(max_workers=3) as executor:
				futures = {executor.submit(func): name for name, func in tasks.items()}
				for future in as_completed(futures):
					name = futures[future]
					try:
						results[name] = future.result()
					except Exception as e:
						results[name] = {"error": str(e)}
		else:
			# Sequential fallback
			for name, func in tasks.items():
				try:
					results[name] = func()
				except Exception as e:
					print(e)
					results[name] = {"error": str(e)}

		return results


if __name__ == '__main__':
	soup = fetch('https://www.statarea.com/compare/teams/Lazio%20(Italy)/Genoa%20(Italy)')
	mp = MatchPage(soup)
	matches_btw_teams = mp.matches_btw_teams()
	next_match = mp.next_match()
	last_10  = mp.last_10()
	stat_facts = mp.stat_facts()
	standings = mp.standings()
	teams_bet_stats = mp.team_bet_stats()

	#pprint(matches_btw_teams)
	#input("continue")
	#pprint(next_match)
	#input("continue")
	#pprint(last_10)
	#input("continue")
	#pprint(stat_facts)
	#input("continue")
	#pprint(standings)
	#input("continue")
	#pprint(teams_bet_stats)

	#all = mp.parse_all()
	#pprint(all)

