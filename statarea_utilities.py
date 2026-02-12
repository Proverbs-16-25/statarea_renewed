from base import *
from DatabaseManager import DatabaseManager

def parse_statarea_tip(tip):
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
	
def standardize_date(date):
	"""Takes the date format we scrape and changes standardizes it"""
	...

def parse_next_match(next_match, team_id, current_date):
	"""
	Take the next_match Json from the scraper and returns:
	is_host_team and match in x days
	param:
		next_match dict, team string: the team being considered, date string to calculate match in x days
	"""
	db = DatabaseManager()
	host_id = db.get_or_create_team(next_match["host"])

	if team_id == host_id:
		is_home_team = 1
	else:
		is_home_team = 0

	next_match_date = standardize_date(next_match["date"])
	current_date = standardize_date(current_date["date"])
	next_match_in = next_match_date - current_date

	return is_home_team, next_match_in 	