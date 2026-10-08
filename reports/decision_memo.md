# Decision memo: qualifying pace vs pit execution for a midfield team

**To:** Team Principal / Head of Strategy · **From:** Harshita Wattal · **Basis:** 3,441 car-starts, 173 Grands Prix, 2018–2025 (numbers from `results.md`)

## Recommendation

**Prioritise one-lap (qualifying) performance over pit-stop execution.** For a midfield team, an average gain of one grid place returns about **5x** the championship points of pit stops that are 0.5 s faster than the field.

## Expected return per season (midfield team, both cars)

| Lever | Extra points | Constructors' places | Prize money at $8.5M/place |
|---|---:|---:|---:|
| **A. +1 average grid place** | **~15.8** (90% CI 13.3–18.2) | ~0.33 | **~$2.8M** |
| B. Pit stops 0.5 s faster | ~3.1 (90% CI 2.1–4.2) | ~0.06 | ~$0.5M |

## Break-even

- Fund lever A ahead of lever B whenever **one grid place costs less than ~5x** what a 0.5 s pit improvement costs.
- To match one grid place through pit work alone, the crew would need to be **~2.5 s per stop faster** than the field. That's about the whole stationary time of a modern stop, so it isn't achievable.

## Where the value sits

- Grid gains are worth most **near the front**: P8→P7 ≈ 0.77 pts per car per race, P11→P10 ≈ 0.28, beyond P13 ≈ 0.10. Qualifying upgrades that move a car from the lower midfield into the top 8 pay most.
- The **10th-place boundary** is where midfield scoring probability drops most sharply. Fewer Q2 exits is a concrete operating target.

## Confidence

- **High** on the ranking: it holds in all 8 robustness checks (lever A 4.5–6x lever B), across both regulation eras, and at prize-money assumptions from $5M to $12M per place.
- **Medium** on the dollar figures: the prize-money split is confidential (published estimate used).
- **Low on strategy beyond pit execution:** extra stops and stop timing are confounded by race events, so these effects are not causal.

## What not to conclude

- Not "strategy doesn't matter". Strategy *timing* (undercuts, safety-car calls) isn't fully captured by public data. The next analysis (safety-car natural experiment and race simulator) is designed to measure it causally.
- Not a cost estimate. Engineering costs per grid place are internal data; plug them into the break-even ratio above.
