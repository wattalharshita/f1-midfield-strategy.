"""Analyses A1-A6. Every function returns plain dicts/DataFrames; report.py turns them into prose.

Inference: race-clustered bootstrap (resample whole races with replacement), because cars in
the same race are not independent - if one car gains a place, another loses one.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy import stats

from . import config as cfg

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(cfg.SEED)


# ---------------------------------------------------------------- helpers
def boot_samples(df: pd.DataFrame, n: int = cfg.N_BOOT, seed: int = cfg.SEED):
    """Yield race-clustered bootstrap resamples."""
    rng = np.random.default_rng(seed)
    races = df.race_key.unique()
    groups = {k: g for k, g in df.groupby("race_key")}
    for _ in range(n):
        pick = rng.choice(races, size=len(races), replace=True)
        parts = []
        for i, k in enumerate(pick):
            g = groups[k].copy()
            g["race_key"] = f"{k}_b{i}"          # duplicates become distinct races
            parts.append(g)
        yield pd.concat(parts, ignore_index=True)


def ci(values, lo=5, hi=95):
    v = np.asarray([x for x in values if np.isfinite(x)])
    return float(np.percentile(v, lo)), float(np.percentile(v, hi))


def summarise(point, draws):
    lo, hi = ci(draws)
    return {"est": float(point), "lo": lo, "hi": hi}


def train(df):
    return df[df.year.isin(cfg.TRAIN_SEASONS)]


def midfield_train(df):
    d = train(df)
    return d[d.midfield].copy()


# ---------------------------------------------------------------- A1
def _spearman(x, y):
    return stats.spearmanr(x, y).statistic


def _partial_spearman(d, x="grid", y="finish_order", group="team_season"):
    rx = d.groupby("race_key")[x].rank()
    ry = d.groupby("race_key")[y].rank()
    rx = rx - rx.groupby(d[group]).transform("mean")
    ry = ry - ry.groupby(d[group]).transform("mean")
    return np.corrcoef(rx, ry)[0, 1]


def a1_steps(df: pd.DataFrame, n_boot: int = cfg.N_BOOT) -> pd.DataFrame:
    """How each v1 -> v2 correction changes the grid-finish association."""
    v1_grid = df.grid_raw.fillna(0)                          # v1 coded pit-lane starts as 0
    d23 = df[df.year == 2023].assign(grid_v1=v1_grid[df.year == 2023])
    # v1 kept rows with status 'Finished' or containing '+'. The API labels lapped cars
    # 'Lapped', so v1 actually kept only lead-lap finishers.
    lead_lap = d23.finished_classified & (d23.laps == d23.groupby("raceId").laps.transform("max"))
    v1_rows = d23[lead_lap]

    steps = [
        ("v1 replication: 2023, lead-lap finishers only, Pearson, pit-lane = 0",
         v1_rows, lambda d: np.corrcoef(d.grid_v1, d.classified_pos)[0, 1]),
        ("Spearman instead of Pearson",
         v1_rows, lambda d: _spearman(d.grid_v1, d.classified_pos)),
        ("+ keep lapped finishers",
         d23[d23.finished_classified], lambda d: _spearman(d.grid_v1, d.classified_pos)),
        ("+ keep DNFs (official finishing order)",
         d23, lambda d: _spearman(d.grid_v1, d.finish_order)),
        ("+ pit-lane starts moved to back of grid",
         d23, lambda d: _spearman(d.grid, d.finish_order)),
        ("+ all seasons 2018-2025",
         df, lambda d: _spearman(d.grid, d.finish_order)),
        ("+ midfield cars only",
         df[df.midfield], lambda d: _spearman(d.grid, d.finish_order)),
        ("+ within the same car (team-season controlled)",
         df[df.midfield], lambda d: _partial_spearman(d)),
    ]
    rows = []
    for label, d, f in steps:
        point = f(d)
        draws = [f(b) for b in boot_samples(d, n=n_boot, seed=cfg.SEED + len(rows))]
        s = summarise(point, draws)
        rows.append({"step": label, "n": len(d), **s})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- A2
GRID_TERMS = "cr(grid, df=4)"


def _a2_fit(d):
    ols = smf.ols(f"points_std ~ {GRID_TERMS} + C(team_season)", data=d).fit()
    return ols


def _marginal_points(model, d):
    """Average change in points per race if each car started one place higher."""
    better = d.assign(grid=(d.grid - 1).clip(lower=1))
    return float((model.predict(better) - model.predict(d)).mean())


def _curve(model, d, slots=range(1, 21)):
    """Model expected points per slot, averaged over the cars actually observed (their cars held fixed)."""
    return np.array([model.predict(d.assign(grid=g)).mean() for g in slots])


def a2_grid_value(df: pd.DataFrame, n_boot: int = cfg.N_BOOT) -> dict:
    d = midfield_train(df)
    m = _a2_fit(d)
    # Linear-in-grid logit for the probability curve: a spline + ~50 fixed effects in a logit
    # produced a non-monotonic artefact (dip at P9-10), so the plotted curve stays monotone.
    logit = smf.glm("scored ~ grid + C(team_season)", data=d, family=sm.families.Binomial()).fit()

    me = _marginal_points(m, d)
    curve = _curve(m, d)
    p_curve = np.array([logit.predict(d.assign(grid=g)).mean() for g in range(1, 21)])

    me_draws, curve_draws, p_draws = [], [], []
    for b in boot_samples(d, n=n_boot):
        try:
            mb = _a2_fit(b)
            me_draws.append(_marginal_points(mb, b))
            curve_draws.append(_curve(mb, b))
        except Exception:
            continue
    curve_draws = np.vstack(curve_draws)

    emp = d.groupby("grid").agg(n=("scored", "size"), p_scored=("scored", "mean"), pts=("points_std", "mean"))
    emp_draws = []
    for b in boot_samples(d, n=n_boot, seed=cfg.SEED + 7):
        emp_draws.append(b.groupby("grid").scored.mean().reindex(range(1, 21)).values)
    emp_draws = np.vstack(emp_draws)
    emp = emp.reindex(range(1, 21))
    emp["p_lo"] = np.nanpercentile(emp_draws, 5, axis=0)
    emp["p_hi"] = np.nanpercentile(emp_draws, 95, axis=0)

    slot_value = pd.DataFrame({
        "from_slot": range(2, 21), "to_slot": range(1, 20),
        "gain_pts": curve[:-1] - curve[1:],
        "lo": np.percentile(curve_draws[:, :-1] - curve_draws[:, 1:], 5, axis=0),
        "hi": np.percentile(curve_draws[:, :-1] - curve_draws[:, 1:], 95, axis=0),
    })
    return {
        "n": len(d), "n_races": d.race_key.nunique(), "n_team_seasons": d.team_season.nunique(),
        "me_points_per_race": summarise(me, me_draws), "me_draws": np.array(me_draws),
        "curve_pts": curve, "curve_p": p_curve, "empirical": emp, "slot_value": slot_value,
    }


# ---------------------------------------------------------------- A3
A3_FORMULA = (f"points_std ~ pit_time_delta + stop_delta + first_stop_rel + {GRID_TERMS}"
              " + C(team_season) + C(race_key)")


def a3_sample(df):
    d = midfield_train(df)
    d = d[(d.laps >= cfg.MIN_LAP_SHARE_A3 * d.race_laps) & (d.n_stops > 0)]
    return d.dropna(subset=["pit_time_delta", "stop_delta", "first_stop_rel"]).copy()


def a3_strategy(df: pd.DataFrame, n_boot: int = cfg.N_BOOT) -> dict:
    d = a3_sample(df)
    m = smf.ols(A3_FORMULA, data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.race_key)[0]})
    terms = ["pit_time_delta", "stop_delta", "first_stop_rel"]
    draws = {t: [] for t in terms}
    for b in boot_samples(d, n=n_boot, seed=cfg.SEED + 3):
        try:
            mb = smf.ols(A3_FORMULA, data=b).fit()
            for t in terms:
                draws[t].append(mb.params[t])
        except Exception:
            continue
    out = {"n": len(d), "n_races": d.race_key.nunique(), "model": m}
    for t in terms:
        out[t] = {"coef": float(m.params[t]), "se_cluster": float(m.bse[t]), "p": float(m.pvalues[t]),
                  **{k: v for k, v in summarise(m.params[t], draws[t]).items() if k != "est"},
                  "draws": np.array(draws[t])}
    out["sd"] = {t: float(d[t].std()) for t in terms}
    out["iqr_first_stop_rel"] = float(d.first_stop_rel.quantile(.75) - d.first_stop_rel.quantile(.25))
    out["mean_stops"] = float(d.n_stops.mean())
    return out


# ---------------------------------------------------------------- A4
def _standings(team_pts: pd.Series) -> pd.Series:
    return team_pts.rank(ascending=False, method="min")


def resimulate(df: pd.DataFrame, delta_per_car_race: float) -> dict:
    """Add `delta` expected points to every midfield car-start of each midfield team-season,
    recompute that season's constructors' table (others unchanged), count places gained."""
    d = train(df)
    gains, pts_gains = [], []
    for year, season in d.groupby("year"):
        totals = season.groupby("constructor_id").points_std.sum()
        base_rank = _standings(totals)
        mid_share = season.groupby("constructor_id").midfield.mean()
        for team in mid_share[mid_share >= 0.5].index:
            n_mid = int(season[(season.constructor_id == team) & season.midfield].shape[0])
            new = totals.copy()
            new[team] += delta_per_car_race * n_mid
            gains.append(base_rank[team] - _standings(new)[team])
            pts_gains.append(delta_per_car_race * n_mid)
    return {"places": float(np.mean(gains)), "points": float(np.mean(pts_gains)), "n_team_seasons": len(gains)}


def a4_compare(df: pd.DataFrame, a2: dict, a3: dict) -> dict:
    lever_a = a2["me_points_per_race"]["est"]
    lever_b = -cfg.PIT_IMPROVEMENT_S * a3["pit_time_delta"]["coef"]
    res = {}
    for name, point, draws in [
        ("A_grid_plus1", lever_a, a2["me_draws"]),
        ("B_pit_minus_0p5s", lever_b, -cfg.PIT_IMPROVEMENT_S * a3["pit_time_delta"]["draws"]),
    ]:
        base = resimulate(df, point)
        sims = [resimulate(df, x) for x in draws[: min(len(draws), 200)]]
        res[name] = {
            "delta_pts_per_car_race": summarise(point, draws),
            "season_points": summarise(base["points"], [s["points"] for s in sims]),
            "places": summarise(base["places"], [s["places"] for s in sims]),
            "n_team_seasons": base["n_team_seasons"],
        }
        res[name]["usd"] = {f"{int(u/1e6) if u % 1e6 == 0 else u/1e6}M": base["places"] * u for u in cfg.USD_SENSITIVITY}
    # How much faster pit work would match one grid place?
    beta = a3["pit_time_delta"]["coef"]
    res["seconds_per_grid_place"] = float(lever_a / -beta) if beta < 0 else float("nan")
    return res


# ---------------------------------------------------------------- A5
def _logloss(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def a5_validate(df: pd.DataFrame) -> dict:
    tr = midfield_train(df)
    te = df[(df.year == cfg.TEST_SEASON) & df.midfield].copy()
    full = smf.glm(f"scored ~ {GRID_TERMS} + form_per_race", data=tr, family=sm.families.Binomial()).fit()
    form_only = smf.glm("scored ~ form_per_race", data=tr, family=sm.families.Binomial()).fit()
    grid_mid = smf.glm(f"scored ~ {GRID_TERMS}", data=tr, family=sm.families.Binomial()).fit()
    all_train = train(df)
    grid_only_rate = all_train.groupby("grid").scored.mean()

    preds = {
        "Model: grid + team form": full.predict(te).values,
        "Model: grid only (midfield-trained)": grid_mid.predict(te).values,
        "Baseline 1: team form only": form_only.predict(te).values,
        "Baseline 0: grid only, all teams": te.grid.map(grid_only_rate).fillna(all_train.scored.mean()).values,
        "Baseline -1: midfield base rate": np.full(len(te), tr.scored.mean()),
    }
    y = te.scored.values
    metrics = pd.DataFrame([
        {"model": k, "brier": float(np.mean((p - y) ** 2)), "log_loss": _logloss(y, p)} for k, p in preds.items()
    ])
    p = preds["Model: grid only (midfield-trained)"]
    bins = pd.qcut(p, 10, duplicates="drop")
    calib = pd.DataFrame({"p": p, "y": y, "bin": bins}).groupby("bin", observed=True).agg(
        pred=("p", "mean"), obs=("y", "mean"), n=("y", "size")).reset_index(drop=True)
    return {"n_test": len(te), "n_test_races": te.race_key.nunique(), "metrics": metrics, "calibration": calib}


# ---------------------------------------------------------------- A6
def a6_robustness(df: pd.DataFrame) -> pd.DataFrame:
    from .data import add_midfield_flag
    rows = []

    def run(label, d_all):
        d = midfield_train(d_all)
        me = _marginal_points(_a2_fit(d), d)
        s = a3_sample(d_all)
        b = smf.ols(A3_FORMULA, data=s).fit().params["pit_time_delta"]
        lever_b = -cfg.PIT_IMPROVEMENT_S * b
        rows.append({"variant": label, "n_midfield": len(d), "A_pts_per_race": me, "B_pts_per_race": lever_b,
                     "ratio_A_over_B": me / lever_b if lever_b > 0 else np.nan})

    run("Baseline (ranks 4-8, 5-race window)", df)
    run("Midfield = ranks 3-8", add_midfield_flag(df.drop(columns=["race_idx", "form_pts", "team_rank", "midfield", "form_per_race"]), ranks=(3, 8)))
    run("Midfield = ranks 4-9", add_midfield_flag(df.drop(columns=["race_idx", "form_pts", "team_rank", "midfield", "form_per_race"]), ranks=(4, 9)))
    run("Excluding 2020 (COVID season)", df[df.year != 2020])
    run("2018-2021 era only", df[df.year <= 2021])
    run("2022-2024 era only (new car rules)", df[df.year >= 2022])
    run("Pit-lane starters excluded", df[~df.pit_lane_start])
    run("Mechanical DNFs excluded", df[df.status_class != "mechanical_other"])
    return pd.DataFrame(rows)
