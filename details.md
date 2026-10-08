# Qualifying or Race Strategy? Where a Midfield F1 Team Should Spend Its Next Dollar

> A data science and business analytics study of Formula 1 race results from 2018 to 2025, framed as a resource allocation decision under a hard budget cap.

**Author:** Harshita Wattal
**Status:** v2 in progress (v1 was a single-season correlation study in Tableau; see section 4)
**Companion document:** [`implementation.md`](implementation.md) covers the repository structure, phases, build steps, research background and citations.

---

## Contents

1. [The project in one paragraph](#1-the-project-in-one-paragraph)
2. [Formula 1 in ten minutes (for people who don't watch it)](#2-formula-1-in-ten-minutes)
3. [The business question](#3-the-business-question)
4. [What version 1 found, and why it isn't enough](#4-what-version-1-found-and-why-it-isnt-enough)
5. [The version 2 approach](#5-the-version-2-approach)
6. [The analyses, one by one](#6-the-analyses-one-by-one)
7. [Key technical decisions and why we made them](#7-key-technical-decisions-and-why-we-made-them)
8. [Statistical ideas used, explained simply](#8-statistical-ideas-used-explained-simply)
9. [What this project can and cannot claim](#9-what-this-project-can-and-cannot-claim)
10. [Glossary](#10-glossary)

---

## 1. The project in one paragraph

Every Formula 1 team has to decide where to put its limited money and engineering hours. One option is making the car faster over a single lap, which improves where it starts the race. The other is getting better at race-day decisions and execution: when to change tyres, how fast the pit crew works, and how the team reacts to incidents. Since 2021 every team spends under a **cost cap** ($135M a year from 2023 to 2025, raised to $215M with a wider scope from 2026), so this is a real trade-off. This project measures, for **midfield teams** (the ones fighting over the last points places, not for wins), how many championship points each lever is worth. It then converts those points into **constructors' championship position and estimated prize money**, with honest uncertainty intervals. The output is a recommendation a team's head of strategy could act on, supported by reproducible code.

---

## 2. Formula 1 in ten minutes

You don't need to follow the sport to follow this project. These are the pieces of the sport that matter here.

### 2.1 Teams, cars and drivers

- F1 has **10 teams** (called **constructors**) from 2018 to 2025, and an 11th from 2026. Each team builds its own car and enters **two drivers**, so about 20 cars start each race.
- The **car matters more than in most motorsports.** A top car can be more than a second per lap faster than a backmarker. This is the central difficulty of F1 analytics, because a driver's result is mostly the car's result. Separating the two is a research problem in its own right (see `implementation.md`, section 7).

### 2.2 A race weekend

1. **Practice:** teams test set-ups. These sessions are not used in this project.
2. **Qualifying (Saturday):** each car sets its fastest single lap. The fastest car starts at the front ("pole position", grid slot 1), the slowest at the back. Penalties, such as for replacing engine parts, can push a car further back. The final starting order is called the **grid**.
3. **The race (Sunday):** about 300 km, usually 50 to 70 laps, lasting around 90 minutes. Cars finish in an order, and that order earns points.

Some weekends also have a short **sprint race**. This project uses **Grand Prix races only**, so that every data point is the same kind of event.

### 2.3 Points and the championships

- Only the **top 10 finishers score points**: 25, 18, 15, 12, 10, 8, 6, 4, 2, 1.
- From 2019 to 2024, one extra point went to whoever set the fastest lap. **We remove that point** so every season is scored on the same scale.
- There are two championships. The **Drivers'** is for individual drivers. The **Constructors'** adds up both drivers' points for each team. **Prize money is paid by constructors' position**, so this is the one that matters to the business.

**Why the points structure matters for this project:** the difference between 10th place (1 point) and 11th place (0 points) is a cliff. For a midfield team, most of the season's points are won or lost around that 10th-place boundary. Gaining one place at the front (2nd to 1st) is worth 7 points to a top team. Gaining one place at the boundary (11th to 10th) is worth 1 point, but for a team that scores rarely, that point can decide its championship position.

### 2.4 Pit stops, tyres and strategy

- Tyres wear out as the race goes on, and worn tyres are slower. Cars stop in the **pit lane** for fresh tyres. A stop costs around 20 seconds in total, depending on the circuit (driving through the pit lane at a speed limit, plus 2 to 3 seconds stationary while the tyres are changed).
- Tyres come in different **compounds**: softer ones are faster but wear quickly, harder ones are slower but last longer. In a dry race each car must use at least two different compounds, so **every car must stop at least once**.
- **Strategy** is the plan of when to stop, how many times, and which tyres to fit. Two classic moves:
  - **Undercut:** stop *before* the car ahead. Your fresh tyres are faster for a lap or two, and if you gain more time than the gap, you pass them when they stop.
  - **Overcut:** stay out *longer* than the car ahead, if your old tyres are still holding up and you can use the clear track.
- **Safety Car (SC) / Virtual Safety Car (VSC):** after a crash, the field slows down. A pit stop during this period costs much less time, so a well-timed safety car can make or ruin a race. **Teams can't control when it happens**, which matters statistically (section 8.5).

### 2.5 Retirements (DNFs)

A car that crashes or breaks down **Did Not Finish (DNF)**. Around 10 to 15% of starts end this way. DNFs are part of the outcome: a team that retires scores zero. Throwing them out of the data, as v1 did, makes the sport look more predictable than it is (section 4).

### 2.6 The cost cap and prize money

- **Cost cap:** a limit on most team spending. It was $135M per year from 2023 to 2025 (plus inflation adjustments) and is $215M from 2026, because more items now count toward it ([Formula1.com](https://www.formula1.com/en/latest/article/explained-what-is-the-f1-cost-cap-and-why-has-it-gone-up.2tYtDIe5SbE5utjThctBT3)). Every engineering hour spent on qualifying pace is an hour not spent somewhere else.
- **Prize money:** F1 pays teams from a central fund, mostly by constructors' championship position. The exact formula is confidential (it's part of the Concorde Agreement). Published estimates put the gap between adjacent positions at roughly **$8–9M** ([The Race, 2025](https://www.the-race.com/formula-1/f1-2025-prize-money-split-revealed-mclaren-only-fourth/)). We use that as an **explicitly labelled assumption** and show how the conclusion changes if it's wrong.

### 2.7 What "midfield" means

The top three or four teams fight for wins and podiums. The bottom one or two struggle to score at all. The **midfield** is the group in between, and their season is decided by fights over 7th to 12th place. Midfield teams are the most interesting case because they can't simply out-qualify the top cars, and **race strategy is where an underdog can most plausibly steal points**.

---

## 3. The business question

> **For a midfield team operating under a cost cap, does a marginal improvement in qualifying (grid position) or in race-day strategy and pit execution return more championship points, and therefore more prize money?**

This is a **resource allocation problem**, the same shape as:

- a marketing team deciding between search ads and brand campaigns (marketing mix modelling),
- a product team deciding between acquisition and retention spend,
- an operations team deciding between buying faster machines and improving scheduling.

In each case the steps are the same: (1) measure the return of each lever in a **common currency**, (2) account for **uncertainty**, and (3) recommend under **constraints**. Here the currency is championship points, converted to money.

### Why this framing helps a portfolio

- It shows **data science** skills: modelling, causal care, uncertainty quantification and validation.
- It shows **business analytics** skills: translating a model into a decision, an ROI comparison and an executive memo.
- It is understandable to non-fans, because the question underneath is universal.

---

## 4. What version 1 found, and why it isn't enough

**v1 (2023 season, 22 races, Python and Tableau):** Pearson correlation between grid and finishing position was r = 0.661. Between number of pit stops and finishing position it was r = −0.005. The conclusion was that qualifying matters much more than pit stops.

The direction is plausible, but the method has six problems. Each one has a fix in v2:

| # | Problem in v1 | Why it matters | v2 fix |
|---|---|---|---|
| 1 | **DNFs dropped** (440 rows down to 304, 31% of data) | Survivorship bias. A car that qualified 2nd and crashed disappears, so the sport looks more orderly than it is and r is inflated. | Keep every starter. The outcome is **points** (DNF = 0) and the official classified order. |
| 2 | **Pit-lane starters coded as grid 0** | The API stores "started from pit lane" as 0, so in the correlation they look like pole position. | Recode to the back of the grid. Run sensitivity checks with them excluded. |
| 3 | **Confounding by car quality** | Fast cars qualify well *and* finish well. Part of r = 0.661 is the car, not the qualifying "lever". | Control for **constructor and season** (fixed or random effects), and compare drivers within the same team and race. |
| 4 | **Pit-stop count has almost no variation** | Nearly everyone stops 1 to 3 times, and the count is chosen in response to the race. A near-zero correlation is almost guaranteed and doesn't measure "strategy". | Measure strategy properly: stop **timing** relative to rivals, **pit-lane time** relative to the race median, and stop count relative to the race's typical count. |
| 5 | **Pearson correlation on ranks** | Positions are ordinal (1st, 2nd, 3rd), not measurements. Pearson assumes linear, interval-scale data. | **Spearman** rank correlation for descriptives. Points-based and ordinal-aware models for inference. |
| 6 | **One season, no uncertainty** | 22 races of one regulation era, with no confidence intervals. We can't tell signal from noise. | **2018–2025** (8 seasons, about 173 races, about 3,500 car-starts), **race-clustered bootstrap** intervals, and out-of-sample validation on 2025. |

v1 also had a **security issue**: a GitHub access token was hard-coded in a notebook cell of a public repo. In v2 it is revoked and removed (see `implementation.md`, Phase 0). This is worth knowing as a lesson in professional practice.

v1 stays in the repo under `v1/` as the baseline. Showing "this is what I did first, this is what was wrong with it, this is how I fixed it" is stronger evidence of skill than a polished project with no history.

---

## 5. The version 2 approach

### 5.1 The unit of analysis

One row is **one car in one race** (a car-start). Columns include the driver, team, season, round, circuit, grid slot, finishing position, points, finish status, laps completed, the pit stops (lap and pit-lane time of each), and derived features.

### 5.2 The decision-maker: a midfield team

A team is **midfield for a given race** if its constructors' ranking, based on points scored in the **previous 5 races only**, is between **4th and 8th**. Two consequences:

- A team can move in and out of the midfield during a season, as happens in reality when a car improves or falls back.
- We never use information from the future. Using the final championship table to decide who was "midfield" would leak the outcome into the sample.

At the start of a season, the window reaches back into the previous season. We also check the conclusions with alternative definitions (ranks 3–8, 4–9, a 3-race window) to make sure they don't depend on one arbitrary choice.

### 5.3 The two levers

| Lever | What a team would invest in | How we measure it in the data |
|---|---|---|
| **A. Qualifying / grid** | One-lap aerodynamic and set-up performance, qualifying run planning, tyre preparation | Grid slot, and the expected points value of each slot |
| **B. Race strategy and execution** | Strategy software and simulation, pit crew training, pit equipment, real-time decision support | Pit-lane time relative to the race median, first-stop timing relative to rivals, stop count relative to the race norm, and positions gained beyond what grid and car predict |

### 5.4 The common currency

```
lever improvement  ->  change in expected points per race
                   ->  change in expected points per season (x ~22 races x 2 cars)
                   ->  change in expected constructors' championship position
                   ->  change in estimated prize money ($8–9M per place, assumption)
```

Points are the right currency because they are what the championship, and therefore the money, is decided on. Finishing position treats 15th to 14th the same as 11th to 10th, which is wrong for business purposes. Section 7 has the full reasoning.

---

## 6. The analyses, one by one

The phases are listed here in plain language. `implementation.md` has the exact steps, code layout and timeline.

### A1. Corrected replication of v1

Recompute grid vs finish with all starters included, pit-lane starts fixed, Spearman correlation, for 2018–2025, by season and for midfield cars only. Then compute the **partial** association after controlling for constructor-season. This shows how much of v1's r = 0.661 was really "car quality".

*What we learn:* how strong the grid effect is once v1's bias is removed, and whether it is weaker or stronger in the midfield.

### A2. The value of a grid slot (lever A)

For midfield cars, estimate the **probability of scoring points** and the **expected points** for each grid slot (1 to 20), using:

1. empirical averages with bootstrap intervals (transparent and assumption-free), and
2. a **logistic regression** of "scored points (yes/no)" on grid slot, with constructor-season effects so that the car's underlying pace is held constant.

The key output is the **marginal value of one grid place** at each slot. We expect it to be steepest around **grid 8 to 13**, close to the points boundary.

*Business translation:* "Moving a midfield car from P12 to P11 on the grid is worth X points per race on average. Doing that consistently for both cars over a season is worth Y points, which is Z constructors' places."

### A3. The value of strategy and pit execution (lever B)

Within each race, compare cars on:

- **Pit-lane time delta:** the car's average pit-lane time minus the race median. This captures pit crew execution.
- **Stop count delta:** the car's number of stops minus the most common number in that race. Did the team gamble on a different strategy from the field?
- **First-stop timing:** the lap of the car's first stop relative to the race median (early means attempting an undercut, late means attempting an overcut).

Then regress **points scored** (and **positions gained versus expected**) on these features, controlling for grid slot, constructor-season and race. Race effects matter because some races are chaotic for everyone.

*Business translation:* "Cutting average pit-lane time by 0.5 s relative to the field is associated with X more points per season for a midfield team."

*Important caveat:* strategy choices respond to events in the race. A team pits early *because* something happened. These results are **associations, not causal effects**. Section 9 explains this, and Phase 4 in `implementation.md` uses the safety car natural experiment to get closer to causality.

### A4. Lever comparison: points to position to money

Take the effect sizes from A2 and A3 for a **realistic improvement** in each lever:

- Lever A: +1 grid place on average for both cars.
- Lever B: −0.5 s average pit-lane time, plus better-timed first stops.

Then **re-simulate past seasons**: add the expected points gain to each midfield team's races, recompute the constructors' standings, and count how many positions, and how many dollars, each lever would have been worth. Repeat this inside the bootstrap so that the answer comes with an interval: "Lever A is worth 0.8 places (90% interval 0.3–1.4)".

### A5. Validation

Fit everything on **2018–2024**, then test on **2025**, a season the model has never seen. We check:

- Does the grid-slot value curve predict 2025 midfield points better than a naive baseline (the overall average points per grid slot ignoring the car)?
- Is the model calibrated? When it says "30% chance of points", do about 30% of those cars actually score?

### A6. Robustness checks

The conclusions should hold with:

- alternative midfield definitions (section 5.2),
- excluding 2020, the shortened COVID season with an unusual calendar,
- splitting by regulation era (2018–2021 vs 2022–2025; the 2022 rules changed the cars substantially to make overtaking easier),
- pit-lane starters excluded rather than recoded.

### Later phases (after the first deadline)

- **Phase 4, safety car natural experiment:** use FastF1 track-status data to find which cars happened to have a stop "discounted" by a safety car. Because teams can't schedule safety cars, this measures the value of a cheap pit stop **causally**, and it separates strategy *luck* from strategy *skill*.
- **Phase 5, tyre degradation and a Monte Carlo race simulator:** fit lap time as a function of tyre age and compound for midfield cars, then simulate thousands of races comparing one-stop and two-stop strategies, with random safety cars. The output is expected points and their spread (risk) for each strategy.
- **Phase 6, circuit segmentation and dashboard:** cluster circuits by how easy overtaking is, and give a lever recommendation per circuit cluster in a Streamlit or Tableau dashboard.

---

## 7. Key technical decisions and why we made them

| Decision | Choice | Alternatives considered | Why |
|---|---|---|---|
| Data source | **F1DB** (open F1 database, CC BY 4.0, published as CSV releases on GitHub) | Jolpica-F1 API (Ergast successor), Kaggle dumps, OpenF1, FastF1 | Covers results, starting grid, pit stops and qualifying for every season, already joined and versioned. The planned Jolpica API was blocked from the build environment; F1DB holds the same Ergast-lineage data as one download, with no rate limits. FastF1 is added in Phase 4 for lap-level and track-status data. |
| Seasons | **2018–2025** | 2011–2025; only 2022–2025 | 2018 onward overlaps with FastF1's detailed timing coverage, so later phases join cleanly. Eight seasons give about 3,500 car-starts. 2026 is excluded: it's in progress under new rules. |
| Race type | **Grand Prix only, no sprints** | Include sprints | Sprints have different points and no mandatory pit stops, so they aren't comparable. |
| Points scale | **25-18-15-12-10-8-6-4-2-1 for every season**, no fastest-lap point | Use actual points awarded | Puts every season on the same scale. The fastest-lap point is a separate mini-game that would add noise. |
| DNFs | **Kept, scored as 0 points** | Drop them (v1) | Dropping them creates survivorship bias. Reliability is part of reality. |
| Grid source | **Actual starting grid** (after penalties) | Qualifying classification | The grid is what the race actually starts from. Penalties are noise we can't model as "qualifying pace" and note as a limitation. |
| Pit-lane starters | **Recoded to the last grid slot** | Drop, or treat as 0 | They do start last. Coding them as 0 put them at pole in v1. |
| Outcome variable | **Points**, plus a **points-finish yes/no** | Finishing position | The business value is points. Position treats all gaps as equal, which is wrong for a midfield team living at the 10th-place cliff. |
| Correlation | **Spearman** | Pearson (v1) | Positions are ranks, and Spearman makes no linearity or interval assumptions. |
| Controlling for the car | **Constructor-season fixed effects** (one intercept per team per season) | Mixed or random effects; Bayesian hierarchical model | Fixed effects are simple, transparent and fast to fit. A Bayesian version following van Kesteren & Bergkamp (2023) is a planned extension. |
| Midfield definition | **Rolling 5-race constructor rank 4–8, past races only** | Final-season standings | Avoids look-ahead leakage and adapts within a season. |
| Uncertainty | **Race-clustered bootstrap** (resample whole races) | Standard errors that assume independent rows | Cars in the same race aren't independent: if one car gains a place, another loses one. Resampling whole races respects that. |
| Validation | **Train 2018–2024, test 2025** | Random k-fold | Random splits leak information across time. Time-based splits mimic real use: a team in 2025 only has the past. |
| Model complexity | **Interpretable regression first**, gradient boosting only as a benchmark | Deep learning | About 3,500 rows is small. The goal is a *decision* that has to be explained to non-technical leadership, and every coefficient here has a business meaning. |
| Prize money | **$8.5M per constructors' place (published estimate)**, with sensitivity from $5M to $12M | Ignore money | The real split is confidential. We state the assumption and show that the *ranking of levers* doesn't depend on it, only the dollar size does. |
| Storage | **CSV/Parquet files queried with DuckDB (SQL)** | A database server | Zero setup and reproducible. It also shows SQL skills without infrastructure. |
| Data download | **One cached download of the F1DB CSV release** | Live API calls per race | Reproducible (a fixed versioned release), fast, and no rate limits. `run_pipeline.py --refresh` pulls the latest release. |

---

## 8. Statistical ideas used, explained simply

### 8.1 Correlation is not causation, and confounding

Ice cream sales and drownings rise together because both are driven by summer. In F1, a good grid slot and a good finish rise together partly because both are driven by **a fast car**. The car is a **confounder**. If we don't control for it, we credit the grid with the car's effect.

### 8.2 Fixed effects

A fixed effect gives each group its own baseline. With **constructor-season fixed effects**, the model asks: *for the same car in the same season, does starting one place higher lead to more points?* That compares like with like, which is much closer to the question a team actually faces.

### 8.3 Logistic regression

This models the **probability** of a yes/no outcome (here, "scored points"). It keeps probabilities between 0 and 1 and naturally produces an S-shaped curve: little change far from the points boundary, a steep change near it. That's exactly the shape F1's points system creates for the midfield.

### 8.4 The bootstrap

We don't know the "true" value of a grid slot. We only have one history of races. The **bootstrap** resamples that history many times (here, 1,000 times, drawing whole races with replacement), recomputes the answer each time, and reports the range in the middle 90% of those answers. It's a general way to get honest uncertainty without strong distribution assumptions.

### 8.5 Natural experiments (Phase 4)

The gold standard for cause and effect is a randomised experiment, but nobody randomises F1 pit stops. Sometimes the world randomises for us: **safety cars are triggered by crashes, not by team strategy**. Whether a car's planned stop happened to fall under a safety car is close to random. Comparing those cars to similar cars that weren't lucky estimates the causal value of a "cheap" pit stop. Economists call this a **natural experiment**.

### 8.6 Out-of-sample validation

A model that only explains the data it was trained on may have memorised noise. Testing on a **future season it has never seen** is the honest check that the findings generalise.

### 8.7 Monte Carlo simulation (Phase 5)

When a system is too complicated to solve with a formula (20 cars, tyre wear, random crashes, pit stops), we **simulate it thousands of times with randomness** and look at the distribution of outcomes. This gives both the *expected* result of a strategy and its *risk*. Real F1 teams work this way, and the method is documented in the research literature (`implementation.md`, section 7).

---

## 9. What this project can and cannot claim

**It can claim:**

- The historical association between grid slot and points for midfield cars, controlling for car quality, with uncertainty intervals.
- The historical association between pit execution and timing measures and points, under the same controls.
- An evidence-based **ranking** of the two levers for a midfield team, and an approximate money value under stated assumptions.
- (After Phase 4) a causal estimate of the value of a safety-car-discounted pit stop.

**It cannot claim:**

- **Exact causal effects of strategy from observational data.** Strategy decisions respond to the race as it unfolds. A3 is associational, and we say so wherever the results appear.
- **The cost side of the ROI.** We don't know what it costs a team to gain one grid place versus 0.5 s of pit time. Those are internal engineering figures. We estimate the **return** per unit of improvement, and a team would bring its own cost figures. The memo states the **break-even cost**: "lever A is worth it if one grid place costs less than $X".
- **Anything that depends on proprietary data**, such as telemetry, fuel loads or real-time gaps. Teams have far richer data. Our simulator is a simplified public-data version.
- **Exact prize money.** The split is confidential. We use published estimates with sensitivity analysis.
- **Transfer to 2026 rules.** The 2026 cars are new, and the conclusions are for 2018–2025-style racing.

These limitations are also written into the README.

---

## 10. Glossary

| Term | Meaning |
|---|---|
| **Constructor** | A team that builds and races its own car (e.g. McLaren, Williams). |
| **Grid / grid slot** | Starting position for the race, decided mainly by qualifying, plus penalties. |
| **Pole position** | Grid slot 1. |
| **Qualifying** | The Saturday session where the fastest single lap sets the grid order. |
| **DNF** | Did Not Finish: the car retired from the race. |
| **Classified** | Officially given a finishing position, usually requires completing 90% of the race distance. |
| **Pit stop / pit-lane time** | Stopping for tyres. Pit-lane time is entry to exit (about 20 s), and the stationary part is about 2–3 s. |
| **Compound** | Tyre type (soft, medium, hard). Softer is faster but wears out sooner. |
| **Stint** | The laps driven on one set of tyres. |
| **Undercut / overcut** | Gaining a position by stopping earlier / later than a rival. |
| **Safety Car / VSC** | Neutralised racing after an incident. Pit stops cost less during it. |
| **Midfield** | Teams ranked roughly 4th–8th, fighting for the lower points places. |
| **Cost cap** | The FIA limit on most team spending ($135M for 2023–2025, $215M from 2026 with a wider scope). |
| **Constructors' Championship** | Team standings. Prize money is paid by this position. |
| **Spearman correlation** | Correlation computed on ranks rather than raw values. |
| **Fixed effect** | A separate baseline per group (here, per team per season). |
| **Bootstrap** | Resampling the data to estimate uncertainty. |
| **Natural experiment** | A situation where chance, not choice, decides who gets a "treatment". |
| **Monte Carlo** | Repeated random simulation to estimate outcomes and risk. |
