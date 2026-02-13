# ⚽ Football Edge Research Platform

A modular football analytics system designed to systematically build, test, and validate betting edges using controlled data collection and transparent feature engineering.

---

## 🎯 Core Principles

- **No post-match leakage**  
  All statistics are derived without seeing future outcomes.

- **Traceable inputs**  
  Every statistic, match, and feature is linked back to raw scraped data.

- **Flexible feature engineering**  
  Easily extendable to incorporate new metrics, teams, leagues, and sources.

- **Transparent validation**  
  Supports backtesting and edge evaluation before deploying predictive strategies.

---

## 🧱 System Architecture

The platform is built around modular components:

### 1️⃣ Scrapers
- Extract match predictions, fixtures, and statistics from multiple sources (e.g., Statarea).
- Handles retries, timeouts, and failed link tracking.
- Designed for robustness and long-term automation.

### 2️⃣ Accumulators
- Maintain time-aware datasets separating:
  - Future fixtures
  - Historical score updates
- Includes `StatareaAccumulator` (formerly `StatareaCompounder`)
  - Deep-scrapes upcoming matches
  - Shallow-scrapes prior matches for score updates
  - Preserves temporal correctness

### 3️⃣ Databases
- Stores raw and derived data for auditability.
- Enforces integrity using:
  - Unique constraints
  - Temporal separation
  - Controlled update logic

### 4️⃣ Feature Generation & Modeling
- Rolling statistics
- Last-10 match form
- Head-to-head records
- Team betting statistics
- Designed for ML pipelines or heuristic signal generation.

### 5️⃣ Dashboard (Planned)
- Color-coded update calendar
- Failed scrape monitoring
- Automated daily update tracking

---

## 📊 Current Status

| Component | Status |
|-----------|--------|
| Data Ingestion | ✅ Complete |
| Accumulators | ✅ Complete |
| Feature Derivation | ⏳ In Progress |
| Modeling / Signals | ⏳ Planned |
| Evaluation Dashboard | ⏳ Planned |

---

## 🗺 Roadmap

- Add additional data sources
- Expand derived feature tables
- Implement predictive signals / ML models
- Build interactive dashboards
- Automate full daily pipeline (scrape → accumulate → features)

---

## 🚀 Getting Started

### Clone the repository

```bash
git clone <repo-url>
cd football-edge-platform
Install dependencies
pip install -r requirements.txt
Run scrapers
python scraper.py
Use the Accumulator
from StatareaAccumulator import StatareaAccumulator

acc = StatareaAccumulator(future_days=5, update_scores_days=3)
acc.accumulate_daily()
🧠 Design Philosophy
This platform prioritizes:

Reproducibility

Temporal integrity

Modular extensibility

Transparent evaluation

It is structured as a long-term research framework rather than a one-off scraping script.