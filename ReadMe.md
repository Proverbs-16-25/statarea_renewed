# Statarea Research Suite

A modular football (soccer) data research framework focused on **data integrity**, **temporal correctness**, and **long-horizon modeling**.

This project exists to solve a single hard problem:

> **How do you build predictive systems when the data source itself quietly leaks the future?**

Rather than relying on opaque datasets or monolithic scrapers, this suite is built from small, explicit tools that give full control over:
- What data is scraped
- When it is scraped
- How it is stored
- And what information is allowed to exist at any point in time

---

## 🧠 Philosophy

Most football datasets look clean — until you inspect *when* the data was available.

Statistics like:
- last 10 matches
- stat facts
- team trends
- head-to-head

often include the **match that was just played**.

If those stats are used to predict that same match (or matches before it), the model is cheating — even if unintentionally.

This project is built around **temporal discipline**:
- No future data in past rows
- No silent re-writes
- No convenience shortcuts

If a feature exists, it existed *at that time*.

---

## 🧱 Project Components

### 1. **StatareaAccumulater**
A controlled data compounding engine.

- Deep-scrapes **future matches** with full statistical context
- Shallow-updates **past matches** for score completion only
- Prevents statistical self-injection
- Enforces strict database integrity

This is the backbone of dataset creation.

---

### 2. **Scrapers**
Low-level, explicit scrapers for:
- Match listings
- Predictions
- Match details
- Team and league context

No giant files.  
No “magic” parsers.  
Every field is accounted for.

---

### 3. **Database Layer**
SQLite-based, normalized storage with:
- Hard uniqueness constraints
- Referential integrity
- JSON-encoded complex structures
- Explicit update paths (no silent overwrites)

Designed for:
- ML training
- Feature engineering
- Post-hoc analysis

---

### 4. **(Planned) Signal Generators**
Future modules will sit *on top* of the accumulated data:
- Rule-based signals
- Statistical edges
- ML inference layers

These will **never** scrape data themselves — they consume only validated, time-correct datasets.

---

## 🧪 Intended Use

- Machine learning research
- Betting model development
- Dataset auditing
- Feature leakage detection
- Long-term compounding experiments

This is not a prediction bot.  
It is a **truth-preserving data factory**.

---

## ⚠️ Why This Exists

Many systems fail silently.

They look profitable.
They backtest beautifully.
They collapse in the real world.

This project was built to answer the uncomfortable question:

> *“What if the data itself is lying to me?”*

---

## 🚧 Status

- Core scraping: stable
- Accumulation logic: stable
- Data integrity: verified
- Dashboards / monitoring: planned
- Betting edge layer: upcoming

---

## 🧑‍💻 Final Note

This project favors:
- correctness over speed
- clarity over cleverness
- control over convenience

It took longer than expected.

It was worth it.
