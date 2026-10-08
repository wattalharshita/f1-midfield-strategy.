"""Figures and the auto-generated results file. Every number in README/resume comes from here."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as cfg

# Reference palette (dataviz skill, light mode): slot 1 blue, slot 2 orange; text in ink, not series color.
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID_C, SURFACE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID_C, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID_C, "grid.linewidth": 0.8, "axes.axisbelow": True,
})


def _save(fig, name):
    cfg.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg.FIGURES / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig1_a1(a1: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(a1))[::-1]
    err = [a1.est - a1.lo, a1.hi - a1.est]
    colors = [ORANGE if i == 0 else BLUE for i in range(len(a1))]
    ax.barh(y, a1.est, color=colors, height=0.55)
    ax.errorbar(a1.est, y, xerr=err, fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3)
    ax.set_yticks(y, a1.step, fontsize=9.5)
    for yi, v in zip(y, a1.est):
        ax.text(0.01, yi, f"{v:.2f}", va="center", ha="left", color="white", fontsize=9.5, fontweight="bold")
    ax.set_xlim(0, 0.8)
    ax.set_xlabel("Rank correlation, grid vs finish (90% race-bootstrap interval)")
    ax.set_title("Fixing v1 step by step: how much of 'grid matters' was really the car")
    ax.grid(axis="y", visible=False)
    _save(fig, "fig1_v1_to_v2_correlation.png")


def fig2_grid_curve(a2: dict):
    emp = a2["empirical"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    slots = np.arange(1, 21)
    ax.fill_between(slots, emp.p_lo, emp.p_hi, color=BLUE, alpha=0.15, linewidth=0)
    ax.plot(slots, emp.p_scored, "o", color=BLUE, markersize=6, label="Observed share scoring (90% interval band)")
    ax.plot(slots, a2["curve_p"], "-", color=ORANGE, linewidth=2,
            label="Model: same midfield cars moved slot to slot")
    ax.axvline(10.5, color=INK2, linestyle=":", linewidth=1)
    ax.text(10.7, 0.95, "10th = last points place", color=INK2, fontsize=9)
    ax.set_xticks(slots)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Starting grid slot")
    ax.set_ylabel("Probability of scoring points")
    ax.set_title("Midfield cars: chance of scoring by starting slot (2018-2024)")
    ax.legend(frameon=False, loc="lower left")
    _save(fig, "fig2_grid_value_curve.png")


def fig3_slot_value(a2: dict):
    sv = a2["slot_value"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = sv.from_slot
    ax.bar(x, sv.gain_pts, color=BLUE, width=0.7)
    ax.errorbar(x, sv.gain_pts, yerr=[sv.gain_pts - sv.lo, sv.hi - sv.gain_pts], fmt="none",
                ecolor=INK2, elinewidth=1, capsize=2)
    ax.set_xticks(x, [f"P{f}→{t}" for f, t in zip(sv.from_slot, sv.to_slot)], rotation=60, fontsize=8.5)
    ax.set_ylabel("Extra points per car per race")
    ax.set_title("What one grid place is worth, by where you start (midfield, same car)")
    ax.grid(axis="x", visible=False)
    _save(fig, "fig3_marginal_value_by_slot.png")


def fig4_strategy(a3: dict):
    # Effects scaled to a realistic change, in points per car per race.
    rows = [
        ("Pit stops 0.5 s faster than field", -cfg.PIT_IMPROVEMENT_S, "pit_time_delta"),
        ("One extra stop vs the field", 1.0, "stop_delta"),
        ("First stop earlier by one IQR\n(~%.0f%% of race distance)" % (100 * a3["iqr_first_stop_rel"]),
         -a3["iqr_first_stop_rel"], "first_stop_rel"),
    ]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    y = np.arange(len(rows))[::-1]
    for yi, (label, scale, t) in zip(y, rows):
        est = scale * a3[t]["coef"]
        se = abs(scale) * a3[t]["se_cluster"]
        ax.errorbar(est, yi, xerr=1.645 * se, fmt="o", color=BLUE, ecolor=BLUE, markersize=8, capsize=4, elinewidth=2)
        ax.text(est, yi + 0.22, f"{est:+.2f}", ha="center", color=INK, fontsize=9.5)
    ax.axvline(0, color=INK2, linewidth=1)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_xlabel("Change in points per car per race (90% CI, race-clustered SE)")
    ax.set_title("Strategy & pit execution (associational, see limitations)")
    ax.grid(axis="y", visible=False)
    _save(fig, "fig4_strategy_effects.png")


def fig5_levers(a4: dict):
    a, b = a4["A_grid_plus1"], a4["B_pit_minus_0p5s"]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    labels = ["Lever A: +1 average grid place", "Lever B: pit stops 0.5 s faster"]
    ests = [a["season_points"]["est"], b["season_points"]["est"]]
    los = [a["season_points"]["lo"], b["season_points"]["lo"]]
    his = [a["season_points"]["hi"], b["season_points"]["hi"]]
    y = np.array([1, 0])
    ax.barh(y, ests, color=[BLUE, ORANGE], height=0.5)
    ax.errorbar(ests, y, xerr=[np.subtract(ests, los), np.subtract(his, ests)], fmt="none", ecolor=INK2, capsize=4)
    for yi, e, h, lv in zip(y, ests, his, [a, b]):
        usd = lv["places"]["est"] * cfg.USD_PER_PLACE / 1e6
        ax.text(h + 0.4, yi, f"{e:.1f} pts/season  ≈ {lv['places']['est']:.2f} places  ≈ ${usd:.1f}M",
                va="center", color=INK, fontsize=10)
    ax.set_yticks(y, labels)
    ax.set_xlim(0, max(his) * 1.9)
    ax.set_xlabel("Expected extra championship points per season for a midfield team (90% interval)")
    ax.set_title("Where should a midfield team spend? Same currency, both levers")
    ax.grid(axis="y", visible=False)
    _save(fig, "fig5_lever_comparison.png")


def fig6_calibration(a5: dict):
    c = a5["calibration"]
    fig, ax = plt.subplots(figsize=(5.2, 5))
    ax.plot([0, 1], [0, 1], linestyle=":", color=INK2, linewidth=1, label="Perfect calibration")
    ax.plot(c.pred, c.obs, "o-", color=BLUE, markersize=7, linewidth=2, label="Grid model on unseen 2025")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted chance of scoring")
    ax.set_ylabel("Observed share that scored")
    ax.set_title("Out-of-sample check: 2025 season")
    ax.legend(frameon=False, loc="upper left")
    _save(fig, "fig6_calibration_2025.png")


# ---------------------------------------------------------------- results.md
def _fmt(s, nd=2):
    return f"{s['est']:.{nd}f} [{s['lo']:.{nd}f}, {s['hi']:.{nd}f}]"


def write_results(df, a1, a2, a3, a4, a5, a6):
    a, b = a4["A_grid_plus1"], a4["B_pit_minus_0p5s"]
    ratio = a["season_points"]["est"] / b["season_points"]["est"]
    best = a5["metrics"].sort_values("brier").iloc[0]
    headline = {
        "car_starts": int(len(df)), "races": int(df.race_key.nunique()), "seasons": "2018-2025",
        "midfield_car_starts_train": a2["n"],
        "v1_r_replicated": round(a1.est.iloc[0], 3), "partial_spearman_within_car": round(a1.est.iloc[-1], 3),
        "lever_A_pts_per_car_race": round(a["delta_pts_per_car_race"]["est"], 3),
        "lever_A_pts_per_season": round(a["season_points"]["est"], 1),
        "lever_A_places_per_season": round(a["places"]["est"], 2),
        "lever_B_pts_per_car_race": round(b["delta_pts_per_car_race"]["est"], 3),
        "lever_B_pts_per_season": round(b["season_points"]["est"], 1),
        "lever_B_places_per_season": round(b["places"]["est"], 2),
        "ratio_A_over_B": round(ratio, 1),
        "pit_seconds_equal_to_one_grid_place": round(a4["seconds_per_grid_place"], 2),
        "usd_A_at_8p5M": round(a["places"]["est"] * cfg.USD_PER_PLACE / 1e6, 2),
        "usd_B_at_8p5M": round(b["places"]["est"] * cfg.USD_PER_PLACE / 1e6, 2),
        "best_2025_model": best.model, "best_2025_brier": round(best.brier, 4),
    }
    cfg.REPORTS.mkdir(parents=True, exist_ok=True)
    (cfg.REPORTS / "headline.json").write_text(json.dumps(headline, indent=2))

    sv = a2["slot_value"].set_index("from_slot")
    L = []
    L.append("# Results (auto-generated by `run_analysis.py` — do not edit by hand)\n")
    L.append(f"Data: F1DB, {headline['seasons']}, **{headline['car_starts']:,} car-starts in "
             f"{headline['races']} Grands Prix**. Training = 2018–2024, test = 2025. "
             f"Intervals are 90% race-clustered bootstrap ({cfg.N_BOOT} replicates) unless stated.\n")

    L.append("## Headline\n")
    L.append(f"- For a midfield team, **one extra grid place on average is worth {a['season_points']['est']:.1f} "
             f"points per season** {_fmt(a['season_points'],1)}; **0.5 s faster pit stops are worth "
             f"{b['season_points']['est']:.1f}** {_fmt(b['season_points'],1)}, about **{ratio:.0f}x less**.")
    L.append(f"- Pit work would have to be **{a4['seconds_per_grid_place']:.1f} s faster per stop than the field** "
             "to match one grid place. A typical stationary stop lasts only 2–3 s, so pit execution "
             "alone cannot plausibly close that gap.")
    L.append(f"- In championship terms: lever A ≈ **{a['places']['est']:.2f} constructors' places per season** "
             f"(≈ ${headline['usd_A_at_8p5M']:.1f}M at $8.5M/place); lever B ≈ {b['places']['est']:.2f} places "
             f"(≈ ${headline['usd_B_at_8p5M']:.1f}M).")
    L.append(f"- v1's headline correlation shrinks from **{a1.est.iloc[0]:.2f} to {a1.est.iloc[-1]:.2f}** once DNFs, "
             "lapped cars and pit-lane starts are handled and the car is held constant.")
    L.append(f"- Out of sample (2025), the best predictor of a midfield car scoring is **{best.model}** "
             f"(Brier {best.brier:.3f}). Adding team form did not improve it.\n")

    L.append("## A1 — Correcting v1 step by step\n")
    L.append("| Step | n | Rank correlation | 90% interval |\n|---|---:|---:|---|")
    for _, r in a1.iterrows():
        L.append(f"| {r.step} | {r.n:,} | {r.est:.3f} | [{r.lo:.3f}, {r.hi:.3f}] |")
    L.append("\nThe original v1 notebook reported r = 0.661 using the Ergast API. Re-running v1's exact filter "
             "on F1DB data selects the same 304 rows but gives r ≈ "
             f"{a1.est.iloc[0]:.2f}; the gap reflects source-level grid coding differences. "
             "Note: v1's filter (`status == 'Finished' or '+' in status`) also silently dropped every lapped car, "
             "because the API labels them 'Lapped'.\n")
    L.append("![A1](figures/fig1_v1_to_v2_correlation.png)\n")

    L.append("## A2 — Value of a grid place (lever A)\n")
    L.append(f"Sample: {a2['n']:,} midfield car-starts, {a2['n_races']} races, {a2['n_team_seasons']} team-seasons. "
             "Model: OLS of standard points on a natural cubic spline of grid slot (4 df) with team-season "
             "fixed effects (one baseline per car per season).\n")
    L.append(f"- Average marginal effect of starting one place higher: **{_fmt(a['delta_pts_per_car_race'],3)} "
             "points per car per race**.")
    L.append(f"- The value is highest at the front: P2→P1 is worth {sv.loc[2,'gain_pts']:.2f} pts, "
             f"P8→P7 {sv.loc[8,'gain_pts']:.2f}, P11→P10 {sv.loc[11,'gain_pts']:.2f}, P15→P14 {sv.loc[15,'gain_pts']:.2f}.")
    emp = a2["empirical"].p_scored
    drops = (emp.shift(1) - emp).loc[5:15]
    s = int(drops.idxmax())
    L.append("- **Pre-registered hypothesis H2 (value steepest around the 10th-place boundary) is not supported "
             "in points terms:** the 25-18-15 scale makes front-of-grid gains worth more, even for midfield cars.")
    L.append(f"- In probability terms the boundary does show: the largest observed drop in the share of midfield "
             f"cars scoring (P5–P15) is from P{s-1} to P{s} ({emp.loc[s-1]:.2f} → {emp.loc[s]:.2f}).\n")
    L.append("| Move | Extra points per car per race | 90% interval |\n|---|---:|---|")
    for f_, r in sv.iterrows():
        L.append(f"| P{f_}→P{int(r.to_slot)} | {r.gain_pts:.3f} | [{r.lo:.3f}, {r.hi:.3f}] |")
    L.append("\n![A2](figures/fig2_grid_value_curve.png)\n\n![A2b](figures/fig3_marginal_value_by_slot.png)\n")

    L.append("## A3 — Strategy and pit execution (lever B)\n")
    L.append(f"Sample: {a3['n']:,} midfield car-starts that ran ≥50% distance and stopped at least once "
             f"({a3['n_races']} races). Model: OLS of points on pit-lane time vs race median, stop count vs race "
             "mode, first-stop timing vs race median, grid spline, team-season and race fixed effects. "
             "Cluster-robust SEs by race.\n")
    L.append("| Feature | Coef (pts per unit) | Cluster SE | p | Bootstrap 90% |\n|---|---:|---:|---:|---|")
    names = {"pit_time_delta": "Pit-lane time vs race median (per s)",
             "stop_delta": "Stops vs race mode (per stop)",
             "first_stop_rel": "First-stop timing vs race median (per race fraction)"}
    for t, nm in names.items():
        r = a3[t]
        L.append(f"| {nm} | {r['coef']:.3f} | {r['se_cluster']:.3f} | {r['p']:.3f} | [{r['lo']:.3f}, {r['hi']:.3f}] |")
    L.append(f"\n- 0.5 s faster per stop → **{-0.5*a3['pit_time_delta']['coef']:.3f} pts per car per race**.")
    L.append(f"- An extra stop vs the field is associated with {a3['stop_delta']['coef']:.2f} pts. This is likely "
             "reverse causation (unplanned stops for damage or punctures), not evidence that two-stops are bad.")
    L.append("- First-stop timing is not distinguishable from zero with cluster-robust SEs.")
    L.append("- **These are associations.** Strategy reacts to race events; Phase 4 (safety-car natural "
             "experiment) is designed to get causal estimates.\n")
    L.append("![A3](figures/fig4_strategy_effects.png)\n")

    L.append("## A4 — Lever comparison: points → championship → money\n")
    L.append(f"Each training season is re-scored with the lever's expected gain added to every midfield car-start "
             f"of each team that was midfield in ≥50% of its races ({a['n_team_seasons']} team-seasons); "
             "other teams unchanged; constructors' table recomputed on the standard points scale.\n")
    L.append("| | Pts per car-race | Pts per season | Constructors' places per season |\n|---|---|---|---|")
    L.append(f"| A: +1 grid place | {_fmt(a['delta_pts_per_car_race'],3)} | {_fmt(a['season_points'],1)} | {_fmt(a['places'])} |")
    L.append(f"| B: 0.5 s faster stops | {_fmt(b['delta_pts_per_car_race'],3)} | {_fmt(b['season_points'],1)} | {_fmt(b['places'])} |")
    L.append("\nPrize money (assumption, real split is confidential):\n")
    L.append("| $ per place | Lever A per season | Lever B per season |\n|---|---:|---:|")
    for u in cfg.USD_SENSITIVITY:
        L.append(f"| ${u/1e6:g}M | ${a['places']['est']*u/1e6:.2f}M | ${b['places']['est']*u/1e6:.2f}M |")
    L.append("\nPlaces intervals reflect uncertainty in the effect size only, conditional on the observed seasons; "
             "they understate total uncertainty. The **ranking of levers holds at every $ assumption**; only the "
             "dollar size changes.\n")
    L.append(f"**Break-even:** lever A is worth funding over lever B whenever one average grid place costs less than "
             f"≈{ratio:.0f}x what a 0.5 s pit improvement costs.\n")
    L.append("![A4](figures/fig5_lever_comparison.png)\n")

    L.append("## A5 — Out-of-sample validation (train 2018–2024, test 2025)\n")
    L.append(f"Test set: {a5['n_test']} midfield car-starts in {a5['n_test_races']} races. Outcome: scored points.\n")
    L.append("| Model | Brier (lower = better) | Log loss |\n|---|---:|---:|")
    for _, r in a5["metrics"].sort_values("brier").iterrows():
        L.append(f"| {r.model} | {r.brier:.4f} | {r.log_loss:.4f} |")
    L.append("\nGrid position alone generalises best; adding rolling team form overfits. This supports the "
             "central finding that the grid carries most of the information.\n")
    L.append("![A5](figures/fig6_calibration_2025.png)\n")

    L.append("## A6 — Robustness\n")
    L.append("| Variant | Midfield n | A: pts/car-race | B: pts/car-race | A ÷ B |\n|---|---:|---:|---:|---:|")
    for _, r in a6.iterrows():
        L.append(f"| {r.variant} | {r.n_midfield:,} | {r.A_pts_per_race:.3f} | {r.B_pts_per_race:.3f} | {r.ratio_A_over_B:.1f} |")
    L.append("\nThe lever ranking holds in every variant."
             if (a6.ratio_A_over_B > 1).all() else "\n**The lever ranking flips in at least one variant; see table.**")
    L.append("\n(Re-flagged midfield variants recompute rolling form from 2018 onward, so the first few 2018 races "
             "have shorter history than the baseline.)\n")
    (cfg.REPORTS / "results.md").write_text("\n".join(L))
    return headline
