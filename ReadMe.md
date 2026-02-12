**Football Edge Research Platform**
*Overview*

This project is a modular football analytics platform designed to systematically build, test, and validate betting edges using controlled data collection and transparent feature engineering.
It emphasizes temporal correctness, reproducibility, and flexibility across multiple data sources, ensuring that predictive signals are based on accurate and auditable data.

*Philosophy*

No post-match leakage – all statistics are derived without seeing future outcomes.

Traceable inputs – every statistic, match, and feature is linked back to raw scraped data.

Flexible feature engineering – easily extendable to incorporate new metrics, teams, leagues, and sources.

Transparent validation – supports backtesting and edge evaluation before deploying predictive strategies.

*Components*
1. Scrapers

Extract match predictions, fixtures, and statistics from multiple sources (e.g., Statarea).

Handles retries, timeouts, and failed link tracking.

2. Accumulators

Maintain time-aware datasets separating future fixtures from historical updates.

Includes StatareaAccumulator (formerly StatareaCompounder) to deep-scrape upcoming matches and shallow-scrape prior matches for score updates.

3. Databases

Stores raw and derived data for auditability.

Enforces integrity with unique constraints and temporal separation between datasets.

4. Feature Generation & Modeling

Builds rolling statistics, last-10 form, head-to-head records, and team bet stats.

Enables downstream ML pipelines or heuristic signal generation.

5. Dashboard (planned)

Color-coded calendar to visualize update status and failed scrapes.

Quick follow-up for incomplete data and automatic daily update logic.

Current Status

Data ingestion: ✔

Accumulators: ✔

Feature derivation: ⏳

Modeling / Signal generation: ⏳

Evaluation dashboard: ⏳


*Roadmap*

Add additional data sources for more comprehensive coverage.

Expand derived feature tables with advanced statistical metrics.

Implement predictive signals and ML pipelines.

Build interactive dashboards to monitor scraping, accumulation, and signal performance.

Automate daily scraping, accumulation, and feature updates.


*Getting Started*

Clone the repository:

git clone <repo-url>
cd football-edge-platform


Install dependencies:

pip install -r requirements.txt


Run scrapers:

python scraper.py


Use the accumulator to gather future matches and update historical scores:

from StatareaAccumulator import StatareaAccumulator

acc = StatareaAccumulator(future_days=5, update_scores_days=3)
acc.accumulate_daily()
