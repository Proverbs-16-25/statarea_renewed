import sqlite3
import json
import numpy as np
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score


DB_PATH = "statarea_lean.db"
LAST_N = 10
RANDOM_STATE = 42


# =========================
# DATABASE LOAD
# =========================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT
        date,
        last10,
        home_ft_goals,
        away_ft_goals
    FROM raw_matches
    WHERE home_ft_goals IS NOT NULL
      AND away_ft_goals IS NOT NULL
""")

rows = cursor.fetchall()
conn.close()

print("Total DB rows:", len(rows))


# =========================
# HELPERS
# =========================

def safe_float(x):
    try:
        if x is None or x == "":
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def parse_date(d):
    return datetime.strptime(d, "%Y-%m-%d")


def filter_past_matches(matches, current_date):
    """Remove matches played on or after the current match date"""
    out = []
    for m in matches:
        try:
            m_date = parse_date(m["date"])
            if m_date < current_date:
                out.append(m)
        except Exception:
            continue
    return out


def parse_team_last10(matches, current_date):
    """
    Returns 40 floats:
    10 × [ht_scored, ht_conceded, ft_scored, ft_conceded]
    """

    matches = filter_past_matches(matches, current_date)

    matches = sorted(
        matches,
        key=lambda x: parse_date(x["date"])
    )[-LAST_N:]

    features = []

    for m in matches:
        features.extend([
            safe_float(m.get("hostteam_ht_goals")),
            safe_float(m.get("guestteam_ht_goals")),
            safe_float(m.get("hostteam_goals")),
            safe_float(m.get("guestteam_goals"))
        ])

    # left-pad if fewer than LAST_N
    missing = LAST_N - len(matches)
    if missing > 0:
        features = ([0.0] * 4 * missing) + features

    return features


def build_feature_vector(last10_json, current_date):
    home_vec = parse_team_last10(
        last10_json["home_last_10"], current_date
    )
    away_vec = parse_team_last10(
        last10_json["away_last_10"], current_date
    )
    return home_vec + away_vec  # 80 features


def encode_ft_result(home_goals, away_goals):
    home_goals = safe_float(home_goals)
    away_goals = safe_float(away_goals)

    if home_goals > away_goals:
        return 2
    elif home_goals < away_goals:
        return 0
    else:
        return 1


# =========================
# BUILD DATASET
# =========================

X, y = [], []
skipped = 0

for match_date, last10_raw, h_ft, a_ft in rows:

    if not last10_raw or last10_raw.strip() == "":
        skipped += 1
        continue

    try:
        last10_json = json.loads(last10_raw)
    except Exception:
        skipped += 1
        continue

    if not isinstance(last10_json, dict):
        skipped += 1
        continue

    if "home_last_10" not in last10_json or "away_last_10" not in last10_json:
        skipped += 1
        continue

    try:
        current_date = parse_date(match_date)
        features = build_feature_vector(last10_json, current_date)
    except Exception:
        skipped += 1
        continue

    # skip if literally no history left
    if np.count_nonzero(features) == 0:
        skipped += 1
        continue

    X.append(features)
    y.append(encode_ft_result(h_ft, a_ft))


X = np.array(X)
y = np.array(y)


# =========================
# SANITY CHECKS
# =========================

print("Samples:", X.shape[0])
print("Skipped rows:", skipped)
print("Feature vector length:", X.shape[1])
print("Non-zero ratio:", np.count_nonzero(X) / X.size)


# =========================
# TRAIN / TEST
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y
)


models = {
    "LogReg": LogisticRegression(max_iter=2000),
    "RF": RandomForestClassifier(n_estimators=400, n_jobs=-1, random_state=42),
    "GB": GradientBoostingClassifier(random_state=42)
}

print("\nModel performance (LEAKAGE-FREE):\n")

for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"{name}: {acc:.4f}")
