from ml_base import load_dataset, train_models, sanity_check
from sklearn.preprocessing import StandardScaler
import numpy as np

# =========================
# LOAD DATA
# =========================

X, y_ht, y_ft = load_dataset()

# Sanity check
sanity_check(X, y_ft, n=5)

# =========================
# FEATURE SCALING EXAMPLE
# =========================

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================
# TRAIN FT MODELS
# =========================

print("\n--- Full-Time Outcome Models ---")
models_ft, results_ft = train_models(X_scaled, y_ft)

# =========================
# TRAIN HT MODELS
# =========================

print("\n--- Half-Time Outcome Models ---")
models_ht, results_ht = train_models(X_scaled, y_ht)

# =========================
# EXPLORATION
# You can now safely manipulate X_scaled, add new features,
# try new ML algorithms, or test alternative targets without
# touching ml_base.py
