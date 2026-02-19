from statarea_utilities import *
from pprint import pprint

conn = sqlite3.connect('statarea_ml_accumulator.db')
cur = conn.cursor()

cur.execute('select standings from raw_matches where home_ft_goals is not null')
rows = cur.fetchall()
my_rows = rows[:5]
conn.close()

ss = []
for row in my_rows:
    standings = json.loads(row[0])
    for standing in standings:
        simplified_standings = simplify_standing(standing)
        ss.append(simplified_standings)

print(ss)
