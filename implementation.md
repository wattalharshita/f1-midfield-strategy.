# Implementation Plan: F1 Midfield Lever Analysis (v2)

**Companion to:** [`details.md`](details.md) (what the project is and why each decision was made).
**This document covers:** repository structure, phases, step-by-step build instructions, the timeline to the deadline, research background with citations, data sources, expected outcomes and resume bullets.

---

## Build status (8 Oct 2026): Phases 0–3 complete

Phases 0–3 below were built and run. Results are in [`reports/results.md`](reports/results.md). Where the build departed from the plan, the plan text below is kept as written and the differences are listed here:

| Planned | Built | Why |
|---|---|---|
| Jolpica-F1 API, ~265 rate-limited calls | **F1DB CSV release** (one cached download from GitHub) | The API was blocked from the build environment. F1DB carries the same Ergast-lineage data, already joined, versioned and CC BY 4.0. |
| `fetch.py`, `clean.py`, `features.py`, `models.py`, `value.py`, `validate.py`, `bootstrap.py`, `plots.py` | `data.py` (fetch, clean, features), `analysis.py` (A1–A6, bootstrap, re-simulation, validation), `report.py` (figures, results.md) | Fewer, larger modules to fit the deadline; same logic |
| DuckDB layer | Not used | pandas was sufficient; listed as optional |
| 1,000 bootstrap replicates | 500 | Runtime (~6 min end to end) |
| Pit outliers: >2.5× race median | Also a hard cap: >60 s is always an outlier | Red-flag races made the race median itself unreliable |
| v1 replication filter "finishers only" | **Lead-lap finishers only** | Re-reading v1 showed its filter also dropped every lapped car (the API labels them "Lapped", not "+1 Lap") |
| Fig 2 model: spline logit with fixed effects | Linear-in-grid logit with fixed effects | The spline version produced a non-monotonic artefact |
| Hypothesis H2 | **Not supported in points terms** | The 25-18-15 scale makes front-of-grid places worth most, even for midfield cars. The 10th-place drop does show in probability terms. |
| A5 "grid + form" model | Added a **grid-only** model; it wins | Team form overfit; reported as found |

The **filled-in resume bullets** are in section 10.

---

## Contents

1. [Goal and definition of done](#1-goal-and-definition-of-done)
2. [Timeline to the deadline](#2-timeline-to-the-deadline)
3. [Repository structure](#3-repository-structure)
4. [Environment setup](#4-environment-setup)
5. [Phases 0–3: the deadline build (today)](#5-phases-03-the-deadline-build)
6. [Phases 4–7: extensions (after the deadline)](#6-phases-47-extensions-after-the-deadline)
7. [Research background: where the idea comes from](#7-research-background-where-the-idea-comes-from)
8. [Data sources](#8-data-sources)
9. [Expected outcomes and what we get at the end](#9-expected-outcomes-and-what-we-get-at-the-end)
10. [Resume bullets](#10-resume-bullets)
11. [Risks and mitigations](#11-risks-and-mitigations)
12. [References](#12-references)

---

## 1. Goal and definition of done

### Today's goal (hard deadline)

| Time (IST) | Milestone |
|---|---|
| **16:00** | Working pipeline and core analysis (A1–A4) run end to end from one command and produce figures and a results file |
| **16:30** | Pushed to GitHub with a clean README, the token issue fixed, and resume bullets filled with real numbers |
| **17:00** | Resume submitted |

### Definition of done for today

- [ ] The GitHub token from v1 is **revoked** and no longer appears in the current files.
- [ ] `python run_pipeline.py` downloads (or loads from cache) 2018–2025 data, cleans it, and writes `data/processed/car_starts.csv`.
- [ ] `python run_analysis.py` produces `reports/results.md` and at least 4 figures in `reports/figures/`.
- [ ] Results include **bootstrap intervals**, not just point estimates.
- [ ] The README states the question, headline findings, method, limitations and how to reproduce.
- [ ] v1 is preserved under `v1/` with the token cell removed.
- [ ] Resume bullets use **real numbers from `reports/results.md`**, not placeholders.

### Explicitly out of scope today

These are designed for later and listed in section 6: FastF1 lap and tyre data, the safety car natural experiment, the Monte Carlo simulator, the dashboard and a Bayesian model. The README will list them as **"Roadmap"**. A well-scoped v2 with a credible roadmap is better than a rushed v3.

---

## 2. Timeline to the deadline

| Slot (IST) | Phase | Output | Cut line if behind |
|---|---|---|---|
| 14:00–14:15 | Docs (this file and `details.md`) | Plan agreed | — |
| 14:15–14:25 | **Phase 0:** security and repo hygiene | Token revoked, `v1/` folder, `.gitignore` | Never skip this |
| 14:25–14:50 | **Phase 1:** data pipeline | `car_starts.csv`, `pit_stops.csv`, DuckDB file | If the API is slow, cut to 2019–2025 |
| 14:50–15:40 | **Phase 2:** core analyses A1–A4 | Effect sizes with CIs | At **15:15**, if A3 isn't done, ship A1, A2 and A4 with lever A only, and move A3 to tomorrow |
| 15:40–15:55 | **Phase 3a:** A5 validation and A6 one robustness check | Validation metrics | Drop A6 first, then A5 |
| 15:55–16:15 | **Phase 3b:** figures, `results.md`, README, decision memo | Publishable repo | The memo can be half a page |
| 16:15–16:30 | **Phase 3c:** fresh-clone test, push, resume bullets | Live repo and final bullets | — |

**Where code runs:** the Jolpica API is **not reachable from the cloud workspace** (the request is blocked by its network allowlist), so **Phase 1 runs on your laptop**, either through Claude Code connected to your environment or by running the script yourself. After that, every phase can run anywhere, because the data is cached locally.

---

## 3. Repository structure

```
f1-strategy-analysis/
├── README.md                    # question, headline findings, how to run, limitations, roadmap
├── details.md                   # full explanation (non-F1 readers welcome)
├── implementation.md            # this file
├── requirements.txt
├── .gitignore                   # data/raw/, __pycache__/, .ipynb_checkpoints/, *.duckdb
├── run_pipeline.py              # Phase 1 entry point: fetch -> clean -> features
├── run_analysis.py              # Phase 2-3 entry point: A1-A6 -> figures + results.md
├── src/
│   └── f1lever/
│       ├── __init__.py
│       ├── config.py            # seasons, midfield ranks, window, points scale, $/place, seeds
│       ├── fetch.py             # Jolpica client: pagination, rate limit, JSON cache
│       ├── clean.py             # parse JSON -> tidy tables; grid recode; status classes
│       ├── features.py          # midfield flag (no look-ahead), pit deltas, standings
│       ├── models.py            # A1-A3 models
│       ├── value.py             # A4 points -> standings -> $ re-simulation
│       ├── validate.py          # A5 time-split validation, calibration
│       ├── bootstrap.py         # race-clustered bootstrap helper
│       └── plots.py             # all figures, consistent style
├── data/
│   ├── raw/                     # cached API JSON (git-ignored; reproducible)
│   └── processed/               # car_starts.csv, pit_stops.csv (committed: small)
├── reports/
│   ├── results.md               # auto-generated numbers + tables
│   ├── decision_memo.md         # one-page recommendation for a team principal
│   └── figures/                 # fig1...fig6 .png
├── tests/
│   └── test_clean_features.py   # grid recode, points scale, no look-ahead, DNF retention
└── v1/
    ├── f1_2023_analysis.ipynb   # original notebook, token cell removed
    ├── sheet1_positions_gained.png
    └── sheet2_grid_vs_finish.png
```

**Why this layout:**

- `src/` as a package keeps logic out of notebooks, so it's testable and importable. Reviewers and admissions committees look for this.
- Two entry scripts mean anyone can reproduce everything with two commands.
- `data/raw` is ignored but `data/processed` is committed, so people can rerun the analysis without hitting the API.
- `reports/results.md` is **generated by code**, so the numbers in the README and on the resume trace back to code.

---

## 4. Environment setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt`:

```
pandas>=2.0
numpy>=1.24
requests>=2.31
statsmodels>=0.14
scipy>=1.10
matplotlib>=3.7
duckdb>=0.10
pytest>=7.0
# Phase 4+ (later):
# fastf1>=3.4
# streamlit>=1.30
```

`config.py` holds every assumption in one place:

```python
SEASONS = list(range(2018, 2026))        # 2018-2025 inclusive
TRAIN_SEASONS = list(range(2018, 2025))  # 2018-2024
TEST_SEASON = 2025
POINTS = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}  # no fastest-lap point
MIDFIELD_RANKS = (4, 8)                  # inclusive
MIDFIELD_WINDOW = 5                      # previous races used for rolling rank
USD_PER_CONSTRUCTOR_PLACE = 8.5e6        # published estimate (The Race, 2025); sensitivity 5-12M
N_BOOT = 1000
SEED = 42
API_BASE = "https://api.jolpi.ca/ergast/f1"
REQUEST_SLEEP_S = 0.35                   # stay under 4 req/s burst
```

---

## 5. Phases 0–3: the deadline build

### Phase 0 — Security and repo hygiene (14:15–14:25)

**Why first:** a live credential in a public repo is the one problem that can't wait, and it's the first thing a technical reviewer will spot.

1. **Revoke the token.** GitHub → Settings → Developer settings → Personal access tokens → delete the token that was pasted into the v1 notebook. Once it's revoked, the copy in git history is **inert**: it no longer grants access.
2. **Remove it from current files.** Copy the notebook to `v1/f1_2023_analysis.ipynb`, delete cells 10–16 (the git and push cells, including the token), and delete the original file from the repo root.
3. **(Optional, later)** Purge it from history with `git filter-repo` or BFG. This isn't necessary once the token is revoked. Skip it today.
4. Move the two PNGs into `v1/` with clean filenames (no spaces).
5. Add `.gitignore`.
6. **Authenticate safely from now on:** `gh auth login`, or a credential manager. Never put a token in a URL.

### Phase 1 — Data pipeline (14:25–14:50)

**Goal:** one tidy table where each row is a car-start, plus a pit stop table.

#### 1.1 Fetch (`fetch.py`)

| Data | Endpoint (relative to `API_BASE`) | Calls |
|---|---|---|
| Race calendar | `/{season}/races/?limit=100` | 8 |
| Results (grid, finish, status, laps, points) | `/{season}/results/?limit=100&offset={k}` | about 5 per season → about 40 |
| Qualifying (for sensitivity checks) | `/{season}/qualifying/?limit=100&offset={k}` | about 40 |
| Pit stops | `/{season}/{round}/pitstops/?limit=100` | about 175 |
| **Total** | | **about 265 calls**, under the 500/hour limit |

Implementation rules:

- **Cache first:** the path is `data/raw/{endpoint}/{season}_{round}_{offset}.json`. If the file exists, read it and make no request. Reruns cost zero API calls.
- **Pagination:** read `MRData.total` and loop offset in steps of 100. Results pages can **split one race across two pages**, so merge race entries by `(season, round)` after fetching.
- **Rate limiting:** sleep 0.35 s between calls. On HTTP 429, back off exponentially (2, 4, 8 s) up to 5 retries.
- **Logging:** print one line per season so progress is visible. Expect about 2–4 minutes for the full run.

#### 1.2 Clean (`clean.py`)

The output is `car_starts` with these columns:

`season, round, race_id, circuit_id, race_name, date, driver_id, constructor_id, grid_raw, grid, pit_lane_start, finish_pos, position_text, status, status_class, laps, race_laps, points_std, scored`

Cleaning rules (each one is covered by a unit test):

| Rule | Implementation | Why |
|---|---|---|
| Pit-lane start | `grid_raw == 0` → `grid = n_starters`, `pit_lane_start = True` | v1 treated these cars as pole position |
| Did not start | Drop rows where status is "Did not start", "Withdrew" or "Did not qualify" | Never raced, so not part of the population |
| DNFs | **Keep.** `finish_pos` is the official classified order, which already ranks retirements by laps completed | Fixes v1's survivorship bias |
| Status classes | Map raw status into `finished`, `lapped`, `mechanical`, `accident`, `other` (lookup dict) | Used for robustness checks, e.g. excluding mechanical DNFs |
| Standard points | `points_std = POINTS.get(finish_pos, 0)` if classified, else 0 | Same scale every season, no fastest-lap point |
| `scored` | `points_std > 0` | Outcome for the logistic model |
| Sprints | Not fetched (the `/results` endpoint is Grand Prix only) | Comparability |

`pit_stops` has these columns: `season, round, driver_id, stop, lap, duration_s`.

- `duration_s` parsing: Jolpica reports **pit-lane time** (entry to exit) as a string. Values with ":" (over a minute, e.g. under a red flag) → NaN.
- Flag outliers where a stop is more than 2.5× that race's median stop. These are usually repairs or penalties. Exclude them from execution metrics but keep them in the stop count.

#### 1.3 Store

- Write `data/processed/car_starts.csv` and `pit_stops.csv`.
- Load both into DuckDB (`data/f1.duckdb`, git-ignored) so the analysis can use SQL for aggregations. This also shows SQL skills in the repo.

```sql
-- example used in features.py: per-race pit benchmarks
CREATE TABLE race_pit_bench AS
SELECT season, round,
       median(duration_s)                         AS race_median_pit_s,
       mode(n_stops)                              AS race_modal_stops,
       median(first_stop_lap::DOUBLE / race_laps) AS race_median_first_stop_frac
FROM car_pit_summary
GROUP BY season, round;
```

#### 1.4 Features (`features.py`)

1. **Rolling constructor rank (midfield flag, no look-ahead):**
   - Sum `points_std` per constructor per race. Order all races from 2017 to 2025 chronologically. Fetch the 2017 tail (the last 5 races) so that the early 2018 races have history.
   - For race *r*, sum each constructor's points over races *r−5 … r−1*, which **excludes race *r***, and rank them.
   - `midfield = MIDFIELD_RANKS[0] <= rank <= MIDFIELD_RANKS[1]`.
   - Unit test: changing race *r*'s results must not change race *r*'s midfield flag.
2. **Per-car pit summary:** `n_stops`, `mean_pit_s` (outliers excluded), `first_stop_lap`, `first_stop_frac = first_stop_lap / race_laps`.
3. **Within-race deltas** (relative to the race's benchmark):
   - `pit_time_delta = mean_pit_s − race_median_pit_s` (negative means faster than the field)
   - `stop_delta = n_stops − race_modal_stops`
   - `first_stop_rel = first_stop_frac − race_median_first_stop_frac` (negative means an earlier stop, an undercut attempt)
4. **Team-season key:** `team_season = constructor_id + "_" + season`, used for fixed effects.

### Phase 2 — Core analyses (14:50–15:40)

All analyses use `bootstrap.py`, which resamples **whole races** with replacement (`N_BOOT = 1000`, seed 42). Every estimate is reported as **point estimate [5th, 95th percentile]**.

#### A1 — Corrected replication of v1

1. Reproduce the v1 number on 2023 finishers only, using Pearson, as a sanity check. It should be close to 0.661.
2. Correct it step by step and record each value in a table, so readers see **how each fix changes the answer**:
   - (a) Spearman instead of Pearson
   - (b) add DNFs back
   - (c) recode pit-lane starts
   - (d) expand to 2018–2025
   - (e) midfield cars only
   - (f) **partial** Spearman controlling for constructor-season: rank-transform `grid` and `finish_pos`, residualise each on `team_season` dummies, then correlate the residuals.
3. Figure: `fig1_v1_to_v2_correlation.png` (a bar or step chart of the six values with CIs).

#### A2 — Value of a grid slot (lever A)

Sample: midfield car-starts in the training seasons.

1. **Empirical curve:** for each grid slot *g* from 1 to 20, compute `P(scored)` and `E[points_std]`, with bootstrap CIs.
2. **Model:**
   ```
   logit P(scored_i = 1) = α_team_season(i) + f(grid_i)
   ```
   `f` is a natural cubic spline with 4 degrees of freedom: `statsmodels.formula.api.glm("scored ~ C(team_season) + cr(grid, df=4)", family=Binomial())`. A companion OLS for `points_std` has the same right-hand side.
3. **Marginal value:** for each midfield car-start, predict at grid *g* and at *g−1* (one place better) and average the difference, giving Δpoints per race for +1 grid place, overall and by slot. This is the **average marginal effect**.
4. **Season value:** Δpoints per race × races in a season × 2 cars = **Δpoints per team-season for +1 average grid place**.
5. Figures: `fig2_grid_value_curve.png` (P(points) by grid slot with CI band, empirical points and model line) and `fig3_marginal_value_by_slot.png`.

#### A3 — Value of strategy and pit execution (lever B)

Sample: midfield car-starts that completed at least 50% of race laps and made at least one stop. Cars that retire early have no meaningful strategy, and keeping them would create reverse causality.

1. **Model:**
   ```
   points_std_i = β1·pit_time_delta_i + β2·stop_delta_i + β3·first_stop_rel_i
                  + f(grid_i) + α_team_season(i) + γ_race(i) + ε_i
   ```
   Fit with OLS and **cluster-robust standard errors by race**, then bootstrap β1–β3 as well.
2. **Companion outcome:** `positions_gained_vs_expected = expected_finish(grid, team_season) − finish_pos`, from an auxiliary model, to see where strategy moves the car even outside the points.
3. **Translate to realistic improvements:**
   - pit execution: `β1 × (−0.5 s)` per stop, times the average number of stops,
   - timing: the effect of moving `first_stop_rel` by one interquartile range earlier.
4. Figure: `fig4_strategy_effects.png` (forest plot of β with 90% CIs, in points per season).
5. **Label clearly:** "associational. Strategy responds to race events (see details.md §9)."

#### A4 — Lever comparison: points → position → money

1. For each training season and each constructor that was midfield in at least 50% of races:
   - add `Δpoints_A` (A2's per-race effect) to each of its midfield races, then recompute **final constructors' standings** with every other team unchanged,
   - record the change in championship position (e.g. 7th → 6th = +1),
   - repeat for `Δpoints_B` (A3's realistic improvement).
2. Average over team-seasons → **expected places gained per season** for each lever. Wrap it in the bootstrap to get CIs.
3. Money: places × `USD_PER_CONSTRUCTOR_PLACE`, with a sensitivity table at $5M, $8.5M and $12M.
4. **Break-even statement:** "Lever A is worth funding if one average grid place costs less than $X per season."
5. Figure: `fig5_lever_comparison.png` (two bars with intervals: places per season and $M per season).

### Phase 3 — Validation, outputs and push (15:40–16:30)

#### 3a. A5 — Out-of-sample validation (2025)

1. Refit A2 on 2018–2024. Predict `P(scored)` for 2025 midfield car-starts. 2025's team-season effects aren't in training, so use the **rolling 5-race team form** as a continuous covariate in place of the fixed effect for prediction. Note this in results.
2. Compare against baselines:
   - **B0:** global P(scored | grid) curve (all teams, no car information)
   - **B1:** team's rolling points rate only
3. Metrics: **Brier score**, **log loss**, and a **calibration plot** (10 bins), saved as `fig6_calibration_2025.png`.
4. **A6 (if there's time):** rerun A2 and A4 with midfield ranks 3–8 and excluding 2020. Report whether the lever ranking changes.

#### 3b. Outputs

- `run_analysis.py` writes **`reports/results.md`** automatically. It contains all headline numbers, CI tables and figure links, so nothing is typed by hand.
- **`reports/decision_memo.md`** (one page, for a team principal):
  1. Recommendation (one sentence)
  2. Expected gain per lever (places, $) with intervals
  3. Break-even cost
  4. Confidence and caveats (three bullets)
  5. Next analyses (safety car experiment, simulator)
- **README.md**: the question, a three-bullet headline finding, the lever comparison figure, how to run (two commands), method summary, limitations, roadmap, and links to `details.md` and `implementation.md`.

#### 3c. Test and push

```bash
pytest -q                                   # 4 tests pass
rm -rf /tmp/f1check && git clone <repo> /tmp/f1check && cd /tmp/f1check
pip install -r requirements.txt && python run_analysis.py   # uses committed processed data
git add -A && git commit -m "v2: midfield lever analysis 2018-2025 (pipeline, models, bootstrap, validation)"
git push origin main
```

Then fill in the resume bullets (section 10) from `reports/results.md`.

---

## 6. Phases 4–7: extensions (after the deadline)

These turn a solid analytics project into a standout one. Each is self-contained, so the repo improves one phase at a time.

### Phase 4 — Safety car natural experiment (causal) · about 1 day

**Why:** A3 is associational. This phase gets a **causal** estimate of the value of a cheap pit stop, and separates strategy **luck** from **skill**.

1. Install FastF1 (`pip install fastf1`). Enable its cache. Load sessions for 2018–2025 races with `session.load(laps=True, telemetry=False, weather=False)`.
2. From `session.track_status`, extract SC and VSC periods (status codes 4 = SC, 6/7 = VSC).
3. From `session.laps`, get each car's pit-in laps (`PitInTime` not null) and tyre compound and age per stint.
4. **Treatment:** a car's stop happened during an SC or VSC that started *after* the car's planned pit window opened. Define the window using the car's stint length on that compound relative to the race median.
5. **Comparison:** similar cars (same race, adjacent grid, same team tier) that pitted under green flag. Match on grid, tyre age and gap. Estimate the effect on points and positions gained.
6. Output: "a safety-car-discounted stop is worth X points for a midfield car". Then decompose A3's strategy delta into **SC luck vs residual skill**.
7. Reference design: natural experiments (Angrist & Pischke, 2009).

### Phase 5 — Tyre degradation and Monte Carlo race simulator · 2–3 days

**Why:** answers "which strategy should we run?" before the race, the way real strategy engineers do (Heilmeier et al., 2018, 2020a; Bekker & Lotz, 2009).

1. **Degradation model:** for midfield cars on green-flag laps (excluding in/out laps, SC laps and lap 1), fit
   `lap_time = base_race + fuel_effect·lap + deg_compound·tyre_age + driver/car effect + ε`
   per circuit, either as a mixed model or a per-compound linear fit.
2. **Pit loss per circuit:** median pit-lane time minus the time to drive the same section at racing speed (estimated from FastF1 sector times).
3. **Simulator:** a lap-by-lap loop for 20 cars, with overtaking modelled as a probability based on the pace gap and a circuit "overtaking difficulty" index. SC events are drawn from historical per-circuit SC rates. Pit decisions follow the candidate strategies.
4. **Monte Carlo:** 5,000 runs per strategy, giving the distribution of finishing positions and points: **expected value and spread** (risk-return).
5. **Validation:** check that the simulator's best strategy matches what the top-performing midfield cars actually ran in held-out races.

### Phase 6 — Circuit segmentation and dashboard · 1 day

1. Build circuit features: overtakes per race (positions changed between lap 1 and the finish, excluding DNFs), SC frequency, pit loss and degradation.
2. Run k-means (k = 3–4) on standardised features to get circuit clusters ("processional", "strategic", "chaotic").
3. Rerun A2–A4 per cluster to get a **lever recommendation per circuit type**.
4. Build a Streamlit app: choose a cluster and team tier to see the recommended lever, expected points and interval. Refresh the Tableau sheets from `data/processed/*.csv` for the Tableau portfolio.

### Phase 7 — Bayesian hierarchical model and write-up · 2 days

1. Refit A2 as a Bayesian hierarchical model (PyMC) with driver and constructor random effects, following van Kesteren & Bergkamp (2023). This handles small team-season samples better than fixed effects.
2. Write a 6–8 page paper-style report (in `reports/paper.pdf`) for master's applications: introduction, related work (section 7 here), data, methods, results, limitations.

---

## 7. Research background: where the idea comes from

The project sits at the intersection of four established bodies of work.

### 7.1 Separating car from driver (why we control for constructor)

- **Bell, Smith, Sabel & Jones (2016)** applied cross-classified multilevel models to F1 results from 1950 to 2014 and found that **team (constructor) effects dominate** driver effects in explaining results. This is the statistical basis for treating "car quality" as the main confounder.
- **van Kesteren & Bergkamp (2023)** built a Bayesian multilevel rank-ordered logit model of results in the hybrid era and estimated that **about 88% of the variance in race results is explained by the constructor**.
- **Implication for us:** v1's grid–finish correlation was mostly measuring the car. A2 controls for constructor-season, and Phase 7 adopts their Bayesian approach.

### 7.2 Race strategy simulation (why Phases 4–5 exist)

- **Bekker & Lotz (2009)** modelled F1 race strategy with **discrete-event simulation** to choose the number of stops and fuel loads. It's an early operations research treatment of F1 strategy as a decision problem.
- **Heilmeier, Graf & Lienkamp (2018)** published a lap-wise race simulation for strategy decisions in circuit motorsport, with tyre degradation, fuel mass, pit losses and overtaking.
- **Heilmeier, Graf, Betz & Lienkamp (2020a)** added **Monte Carlo** methods to account for probabilistic events (accidents, failures, safety cars). This is the direct template for our Phase 5.
- **Heilmeier, Thomaser, Graf & Betz (2020b)** trained neural networks as a **"virtual strategy engineer"** that makes pit decisions inside the simulation, showing that teams treat strategy as a learnable decision policy.

### 7.3 Pit decisions under uncertainty (why strategy is hard to measure)

- **Tulabandhula & Rudin (2014)** studied predictive analytics for pit-stop decisions in professional racing (NASCAR), covering tyre changes and caution (yellow flag) periods. They highlight that **race events and decisions are entangled**, which is exactly why our A3 is labelled associational and why Phase 4 uses safety cars as an external shock.

### 7.4 Economics of F1 competition and incentives (why points and money matter)

- **Judde, Booth & Brooks (2013)** analysed competitive balance in F1 and how points and race outcomes are distributed among teams. This is background for why the 10th-place points boundary creates the steep, nonlinear value curve we expect in A2.
- **Cost cap and prize money:** the FIA financial regulations ($135M for 2023–2025, $215M from 2026 with a wider scope; Formula1.com) make this a **constrained allocation** problem. Published prize money estimates (The Race, 2025) give about $8–9M between adjacent constructors' positions.

### 7.5 Methods borrowed from other fields

- **Marketing mix modelling** (e.g. Jin et al., 2017, Google) answers "which channel returns most per dollar?" with regression plus uncertainty. Our lever comparison has the same structure.
- **Natural experiments** (Angrist & Pischke, 2009) underpin Phase 4.
- **Bootstrap** (Efron, 1979) and **cluster bootstrap / cluster-robust inference** (Cameron, Gelbach & Miller, 2008) underpin all of our intervals.
- **Fixed-effects and multilevel regression** (Gelman & Hill, 2007).
- **Rank correlation** (Spearman, 1904).

### 7.6 What's new in this project

Prior work either **explains results** (who is the best driver or car?) or **optimises strategy for one car** (which stop plan is fastest?). This project asks a **portfolio question that sits between them**: *given a budget cap, which capability should a midfield team build?* It answers that in championship points and money, with the uncertainty attached. As far as our search found, this specific framing (midfield-only, points to standings to prize money, both levers in one currency) isn't covered by the papers above, so we present it as an applied synthesis rather than a claim of novelty in methods.

---

## 8. Data sources

| Source | What we use | Coverage | Access | Notes |
|---|---|---|---|---|
| **F1DB** ([github.com/f1db/f1db](https://github.com/f1db/f1db)), **used in the build** | Race results, starting grid (incl. pit-lane starts), classification, retirement reasons, pit stops (pit-lane time) | 1950–present | Versioned CSV release, CC BY 4.0 | One download, cached in `data/raw/` |
| **Jolpica-F1 API** ([github.com/jolpica/jolpica-f1](https://github.com/jolpica/jolpica-f1)) | Results, grid, status, laps, qualifying, pit stops | Results 1950+, pit stops 2011+ | Free, no key. 4 req/s burst, 500 req/hour | Successor to the Ergast API, which shut down. Same response schema. Also used through FastF1 (docs.fastf1.dev/api_reference/jolpica.html) |
| **FastF1** ([docs.fastf1.dev](https://docs.fastf1.dev)) | Lap times, tyre compound and age, stints, track status (SC/VSC) | Detailed timing 2018+ | Python library with local cache | Phases 4–5 |
| **OpenF1** ([openf1.org](https://openf1.org)) | Alternative live and historical timing | 2023+ | Free REST API | Backup source and cross-check |
| **Formula1.com cost cap explainer** | Cap figures and scope | 2021–2026 | Public | $135M (2023–2025), $215M (2026) |
| **The Race (2025), prize money estimate** | $ per constructors' place | 2024 payouts | Public, estimate | Concorde Agreement is confidential, so it's used only as a labelled assumption with sensitivity |
| **FIA Sporting Regulations** | Points system, tyre rules | Annual | Public PDFs | Justifies the standardised points scale and the "at least one stop" rule |

**Data quality notes:**

- `grid = 0` means a pit-lane start (recoded in Phase 1).
- Jolpica pit `duration` is **pit-lane time** (entry to exit), not stationary time. It includes the speed-limited drive, which varies by circuit, which is why we use **within-race deltas**.
- Red-flag tyre changes may not appear as pit stops, and some stops are over a minute (red flags, repairs). Both are handled by parsing and outlier rules.
- Data is community-maintained, so we spot-check a few races against official F1 classifications.

---

## 9. Expected outcomes and what we get at the end

### 9.1 Hypotheses (stated before seeing the results)

Writing these down before running the analysis keeps it honest. Whatever we find gets reported, including if a hypothesis fails.

| # | Hypothesis | What would support it |
|---|---|---|
| H1 | v1's r = 0.661 shrinks substantially once constructor-season is controlled for | The partial Spearman in A1 is clearly lower than the raw value |
| H2 | For midfield cars, grid value is **nonlinear** and steepest around grid 8–13 (the points boundary) | A2 marginal effects peak in that range |
| H3 | Grid remains the stronger lever per unit for midfield teams | A4: places per season for lever A > lever B, with CIs mostly separated |
| H4 | Pit execution has a small but nonzero positive effect | A3: β1 < 0 (faster than the field means more points), CI excluding 0 or close |
| H5 | Stop-count deviations add variance rather than mean | A3: β2 near 0, while the spread of outcomes is wider for off-strategy cars (descriptive) |
| H6 | The lever ranking holds out of sample and across definitions | A5 beats baselines, and A6 doesn't flip the ranking |

**If H3 fails** (strategy turns out to be the stronger lever for the midfield), that's an *interesting* result. The memo would recommend strategy investment, and Phases 4–5 become the priority.

### 9.2 Deliverables

**Today (v2.0):**

1. A reproducible pipeline: API → cache → tidy data → DuckDB.
2. A corrected replication showing step by step how each bias changed v1's conclusion.
3. A grid-value curve for midfield cars with uncertainty.
4. Strategy and execution effect estimates with clear causal caveats.
5. A lever comparison in **points, constructors' places and dollars**, with break-even costs.
6. Out-of-sample validation on 2025.
7. Six figures, an auto-generated `results.md`, a one-page decision memo, and a README.
8. Unit tests for the cleaning and no-look-ahead logic.

**After the extensions (v3):** a causal safety car estimate, a Monte Carlo strategy simulator, circuit-cluster recommendations, a Streamlit dashboard, a Bayesian model, and a paper-style report.

### 9.3 Skills demonstrated (for the portfolio list)

| Area | Evidence in the repo |
|---|---|
| Data engineering | Paginated, rate-limited, cached API client; DuckDB/SQL; tidy schemas |
| Statistics | Fixed effects, logistic regression, splines, cluster-robust SEs, cluster bootstrap, partial correlation |
| Causal thinking | Confounder control, look-ahead prevention, associational vs causal labelling, natural experiment (Phase 4) |
| ML practice | Time-based train/test split, baselines, Brier score and log loss, calibration |
| Business analytics | ROI framing under a budget cap, break-even analysis, sensitivity, decision memo |
| Engineering practice | Package layout, tests, config file, reproducible entry points, secret handling |
| Communication | Non-specialist explainer (`details.md`), executive memo, figures |

---

## 10. Resume bullets

### Final bullets (numbers from `reports/results.md`, run of 8 Oct 2026)

**F1 Midfield Strategy Analytics** | Python, pandas, statsmodels, matplotlib | github.com/wattalharshita/…

*Data science version*
- Built a reproducible Python pipeline over **8 F1 seasons (3,441 car-starts, 173 races)** and corrected four biases in my earlier single-season study (dropped DNFs and lapped cars, pit-lane starts coded as pole, no control for car quality). The grid–finish correlation fell from **0.60 to 0.40** once the car was held constant.
- Quantified the points value of qualifying vs pit execution for midfield teams using **fixed-effects regression with splines and race-clustered bootstrap CIs**: +1 grid place ≈ **15.8 pts/season** vs **3.1** for 0.5 s faster stops (**~5x**). The result held across **8 robustness checks**, and the model was **validated out of sample on 2025**.
- Translated the results into a **cost-cap ROI memo**: pit crews would need to be **~2.5 s per stop faster** to match one grid place. Lever value was expressed in constructors' places and prize money (~$2.8M vs ~$0.5M per season, with $5–12M/place sensitivity).

*Business analytics version*
- Framed a budget-capped F1 team's choice between qualifying pace and race-day pit execution as an **ROI problem**, and valued both in a common currency (points → championship position → prize money) across 3,441 race starts.
- Found qualifying improvements return **~5x** the points of faster pit stops (15.8 vs 3.1 per season, ~$2.8M vs ~$0.5M). The ranking held under all 8 robustness checks and every prize-money assumption tested.
- Delivered a one-page **decision memo** with break-even thresholds, confidence levels and a roadmap (causal safety-car analysis, race simulator).

*One line*
- Modelled 8 F1 seasons (3,441 car-starts) to compare qualifying vs pit-stop investment for midfield teams. Qualifying is worth ~5x more championship points (fixed-effects regression, cluster bootstrap, 2025 out-of-sample validation).

### Original templates

**Fill the [brackets] only with numbers from `reports/results.md`.** Every number needs to be defensible in an interview.

### Version A — Data science roles

**F1 Midfield Strategy Analytics** | Python, statsmodels, DuckDB/SQL, Tableau | [GitHub link]
- Built a reproducible, rate-limited data pipeline over **8 F1 seasons (2018–2025; ~3,500 car-starts across ~173 races)** from the Jolpica-F1 API, fixing survivorship and coding biases in an earlier single-season study that had **overstated** the grid–finish correlation ([0.66 → X after controls]).
- Quantified the points value of qualifying vs race strategy for midfield teams using **fixed-effects logistic regression with splines and race-clustered bootstrap CIs**: +1 grid place ≈ **[X] points/season [CI]** vs **[Y]** for 0.5 s faster pit execution. **Validated out-of-sample on 2025** (Brier [Z] vs [W] baseline).
- Converted model output into a **cost-cap ROI recommendation**: [lever] worth ~**[N] constructors' places (~$[M]M prize money)**, with break-even investment thresholds and sensitivity analysis.

### Version B — Business analytics / strategy roles

**Resource Allocation Under a Budget Cap: Formula 1 Midfield Teams**
- Framed a $135M-cost-cap team's choice between qualifying pace and race-day strategy as an **ROI problem**, and measured both levers in a common currency (points → championship position → prize money).
- Found that [lever] returns **~[N] championship places (~$[M]M) per season** for midfield teams, with uncertainty ranges and break-even cost thresholds, using 8 seasons of race data and bootstrap analysis.
- Delivered a **one-page decision memo**, reproducible analysis and dashboards in Tableau, showing that [one-line insight, e.g. "grid gains near the 10th-place points boundary are worth ~3x gains elsewhere"].

### One-line version (for tight spaces)

- Modelled 8 seasons of F1 data (~3,500 car-starts) to compare the championship and prize-money value of qualifying vs pit strategy for midfield teams (fixed-effects logistic regression, cluster bootstrap, 2025 out-of-sample validation). [Lever] worth ~[N] places/season (~$[M]M).

**If something isn't finished by 16:30,** leave it out of the bullet. Don't put in a number that isn't in `results.md`.

---

## 11. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| API slow or rate-limited | Medium | Delays Phase 1 | Cache JSON; 0.35 s sleep with backoff; cut to 2019–2025 if needed |
| Pagination splits a race across pages | High | Duplicate or missing rows | Merge by `(season, round)`; assert about 20 rows per race |
| Too few midfield rows per team-season for fixed-effects logit | Medium | Unstable estimates | Use OLS linear probability model as backup; report both; Phase 7 Bayesian |
| A3 effects too noisy | High | Weak lever B estimate | Report honestly with CIs; it motivates Phase 4–5 (that's a finding too) |
| Prize money figure challenged | Medium | Credibility | Labelled assumption with $5–12M sensitivity; the ranking doesn't depend on it |
| Running out of time | Medium | Incomplete push | Cut lines in section 2; push whatever passes tests by 16:15 |
| Token still active | — | Security | Phase 0 first, not optional |

---

## 12. References

**Academic**

1. Bell, A., Smith, J., Sabel, C. E., & Jones, K. (2016). Formula for success: Multilevel modelling of Formula One driver and constructor performance, 1950–2014. *Journal of Quantitative Analysis in Sports, 12*(2), 99–112. https://ideas.repec.org/a/bpj/jqsprt/v12y2016i2p99-112n3.html
2. van Kesteren, E.-J., & Bergkamp, T. (2023). Bayesian analysis of Formula One race results: Disentangling driver skill and constructor advantage. *Journal of Quantitative Analysis in Sports, 19*(4), 273–293. https://arxiv.org/abs/2203.08489
3. Bekker, J., & Lotz, W. (2009). Planning Formula One race strategies using discrete-event simulation. *Journal of the Operational Research Society, 60*(7), 952–961. https://iaorifors.com/paper/64724
4. Heilmeier, A., Graf, M., & Lienkamp, M. (2018). A race simulation for strategy decisions in circuit motorsports. *21st IEEE International Conference on Intelligent Transportation Systems (ITSC)*, 2986–2993. https://mediatum.ub.tum.de/node?id=1462798
5. Heilmeier, A., Graf, M., Betz, J., & Lienkamp, M. (2020a). Application of Monte Carlo methods to consider probabilistic effects in a race simulation for circuit motorsport. *Applied Sciences, 10*(12), 4229. https://www.mdpi.com/2076-3417/10/12/4229
6. Heilmeier, A., Thomaser, A., Graf, M., & Betz, J. (2020b). Virtual strategy engineer: Using artificial neural networks for making race strategy decisions in circuit motorsport. *Applied Sciences, 10*(21), 7805. https://portal.fis.tum.de/en/publications/virtual-strategy-engineer-using-artificial-neural-networks-for-ma/
7. Tulabandhula, T., & Rudin, C. (2014). Tire changes, fresh air, and yellow flags: Challenges in predictive analytics for professional racing. *Big Data, 2*(2), 97–112. https://doi.org/10.1089/big.2014.0018
8. Judde, C., Booth, R., & Brooks, R. (2013). Second place is first of the losers: An analysis of competitive balance in Formula One. *Journal of Sports Economics, 14*(4), 411–439. https://ideas.repec.org/a/sae/jospec/v14y2013i4p411-439.html

**Methods**

9. Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *The Annals of Statistics, 7*(1), 1–26.
10. Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). Bootstrap-based improvements for inference with clustered errors. *The Review of Economics and Statistics, 90*(3), 414–427.
11. Gelman, A., & Hill, J. (2007). *Data Analysis Using Regression and Multilevel/Hierarchical Models.* Cambridge University Press.
12. Angrist, J. D., & Pischke, J.-S. (2009). *Mostly Harmless Econometrics: An Empiricist's Companion.* Princeton University Press.
13. Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology, 15*(1), 72–101.
14. Jin, Y., Wang, Y., Sun, Y., Chan, D., & Koehler, J. (2017). *Bayesian methods for media mix modeling with carryover and shape effects.* Google Inc. technical report.

**Data and industry**

15a. F1DB: The open-source Formula 1 database. https://github.com/f1db/f1db (CC BY 4.0)
15. Jolpica-F1 API. https://github.com/jolpica/jolpica-f1 (rate limits: `docs/rate_limits.md`)
16. FastF1 documentation. https://docs.fastf1.dev
17. OpenF1 API. https://openf1.org
18. Formula 1 (2025). *Explained: What is the F1 cost cap and why has it gone up?* https://www.formula1.com/en/latest/article/explained-what-is-the-f1-cost-cap-and-why-has-it-gone-up.2tYtDIe5SbE5utjThctBT3
19. The Race (2025). *F1 2025 prize money split revealed.* https://www.the-race.com/formula-1/f1-2025-prize-money-split-revealed-mclaren-only-fourth/
