import sqlite3

conn = sqlite3.connect("statarea_lean.db")
cursor = conn.cursor()

cursor.execute("SELECT stat_facts FROM raw_matches")
rows = cursor.fetchall()

conn.close()