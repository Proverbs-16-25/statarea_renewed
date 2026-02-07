import sqlite3
import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score

# =========================
# FEATURE DEFINITIONS
# =========================

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

# =========================
# PARSERS
# =========================

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

def build_feature_vector(match_json):
    if not match_json or "home_stat_facts" not in match_json or "away_stat_facts" not in match_json:
        return None
    home_stats = parse_stat_block(match_json["home_stat_facts"])
    away_stats = parse_stat_block(match_json["away_stat_facts"])

    features = []
    # Home
    for key in FEATURE_KEYS:
        features.append(home_stats[key])
    # Away
    for key in FEATURE_KEYS:
        features.append(away_stats[key])
    # Differences
    for key in FEATURE_KEYS:
        features.append(home_stats[key] - away_stats[key])

    return features

# =========================
# TARGET ENCODING
# =========================

def encode_result(home_goals, away_goals):
    if home_goals > away_goals:
        return 1
    elif home_goals < away_goals:
        return -1
    else:
        return 0

def remap_labels(y):
    # -1 → 0, 0 → 1, 1 → 2
    return y + 1

# =========================
# DATA LOADING
# =========================

def load_dataset(db_path="statarea_lean.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            stat_facts,
            home_ht_goals,
            away_ht_goals,
            home_ft_goals,
            away_ft_goals
        FROM raw_matches
        WHERE home_ht_goals IS NOT NULL
    """)

    rows = cursor.fetchall()
    conn.close()

    X, y_ht, y_ft = [], [], []

    for stat_facts_raw, h_ht, a_ht, h_ft, a_ft in rows:
        try:
            match_json = json.loads(stat_facts_raw)
        except json.JSONDecodeError:
            print("Skipping row, invalid JSON")
            continue

        if "error" in match_json:
            print("Skipping row, unexpected JSON keys:", match_json.keys())
            continue

        vec = build_feature_vector(match_json)
        if vec is None:
            continue

        X.append(vec)
        y_ht.append(encode_result(h_ht, a_ht))
        y_ft.append(encode_result(h_ft, a_ft))

    X = np.array(X)
    y_ht = remap_labels(np.array(y_ht))
    y_ft = remap_labels(np.array(y_ft))

    return X, y_ht, y_ft

# =========================
# MODEL TRAINING
# =========================

def train_models(X, y, test_size=0.2, random_state=42, stratify=True):
    stratify_arr = y if stratify else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify_arr
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, multi_class="auto"),
        "Random Forest": RandomForestClassifier(n_estimators=300, random_state=random_state, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(random_state=random_state),
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        results[name] = acc
        print(f"{name} accuracy: {acc:.4f}")

    return models, results

# =========================
# SANITY CHECK FUNCTION
# =========================

def sanity_check(X, y, n=5):
    print("Samples:", X.shape[0])
    print("Feature vector length:", X.shape[1])
    print("\nFirst", n, "rows:\n")
    for i in range(n):
        print("X:", X[i])
        print("Label:", y[i])
        print("-" * 50)
