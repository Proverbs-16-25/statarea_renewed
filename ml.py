import json
import sqlite3
from ml_base import *
from base import *
from pprint import pprint
from DatabaseManager import *
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import datetime
from statarea_utilities import StatareaSimplifier

#Fetch data
conn = sqlite3.connect('statarea_ml_accumulator.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('select * from raw_matches where home_ft_goals is not null')
rows = cur.fetchall()


ft_outcs, ht_outcs, matches = [], [], []
parser = StatareaSimplifier()
for row in rows:
    try:
        parsed_row = db_row_to_match_dict(row)
        home_tbs, away_tbs = parsed_row['last10']['home_last_10'], parsed_row['last10']['away_last_10']
        flat_row = parser.ultimate_flattener([
            parser.simp_last10(home_tbs, DatabaseManager().get_or_create_team(parsed_row['home_team_id']), parsed_row['date']),
            parser.simp_last10(away_tbs, DatabaseManager().get_or_create_team(parsed_row['away_team_id']), parsed_row['date'])
        ])
        print(len(flat_row))
        if len(flat_row) == 176:
            matches.append(flat_row)
            ht_outc, ft_outc = parser.parse_match_outc(
            int(row['home_ht_goals']),
            int(row['away_ht_goals']),
            int(row['home_ft_goals']),
            int(row['away_ft_goals'])
            )
            ft_outcs.append(ft_outc)
            ht_outcs.append(ht_outc)
    except Exception as e:
        continue

if len(ft_outcs) == len(ht_outcs) == len(matches):
    X = np.array(matches)
    y_ht = np.array(ht_outcs)
    y_ft = np.array(ft_outcs)

    print("\n--- Dataset Summary ---")
    print("X shape:", X.shape)
    print("HT shape:", y_ht.shape)
    print("FT shape:", y_ft.shape)
    print("NaNs in X:", np.isnan(X).sum())
    print("Max value in X:", np.max(X))
    print("Min value in X:", np.min(X))

    print("\nHT class distribution:")
    print(np.bincount(y_ht))

    print("\nFT class distribution:")
    print(np.bincount(y_ft))

    print("half_time")
    train_models(X, ht_outcs)

    print("full_time")
    train_models(X, ft_outcs)
