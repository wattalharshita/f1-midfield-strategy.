"""Fetch (once), clean and feature-engineer the F1DB CSV export.

Output tables
-------------
car_starts : one row per car per Grand Prix start, 2017-2025 (2017 only used for rolling form)
pit_stops  : one row per pit stop, 2018-2025
"""
from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd

from . import config as C

NEVER_STARTED = {"DNS", "DNQ", "DNPQ", "EX", "DNP"}


# ---------------------------------------------------------------- fetch
def fetch(force: bool = False) -> None:
    """Download the F1DB CSV release once; later runs read the local copy."""
    if (C.RAW / "f1db-races-race-results.csv").exists() and not force:
        return
    import requests

    C.RAW.mkdir(parents=True, exist_ok=True)
    resp = requests.get(C.F1DB_CSV_URL, timeout=120)
    resp.raise_for_status()
    zipfile.ZipFile(io.BytesIO(resp.content)).extractall(C.RAW)


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(C.RAW / f"f1db-{name}.csv", low_memory=False)


# ---------------------------------------------------------------- clean
def standard_points(pos: pd.Series) -> pd.Series:
    return pos.map(C.POINTS).fillna(0).astype(float)


def build_car_starts() -> pd.DataFrame:
    races = _read("races")[["id", "year", "round", "date", "circuitId", "grandPrixId", "laps"]]
    races = races.rename(columns={"id": "raceId", "laps": "race_laps"})

    rr = _read("races-race-results")
    rr = rr[(rr.year >= C.HISTORY_START) & (rr.year <= max(C.SEASONS))]
    rr = rr[~rr.positionText.isin(NEVER_STARTED)].copy()

    df = rr.merge(races[["raceId", "date", "circuitId", "grandPrixId", "race_laps"]], on="raceId")
    df = df.rename(columns={
        "driverId": "driver_id", "constructorId": "constructor_id",
        "positionNumber": "classified_pos", "positionDisplayOrder": "finish_order",
        "gridPositionNumber": "grid_raw", "positionText": "position_text",
        "reasonRetired": "reason_retired", "points": "points_actual",
    })

    # Pit-lane starters: F1DB leaves the grid number empty with text "PL".
    # v1 (Ergast) coded them as 0 = pole. Here: back of the grid.
    n_starters = df.groupby("raceId").driver_id.transform("size")
    df["pit_lane_start"] = df.gridPositionText.eq("PL") | df.grid_raw.isna()
    df["grid"] = np.where(df.pit_lane_start, n_starters, df.grid_raw).astype(int)

    df["finished_classified"] = df.classified_pos.notna()
    df["points_std"] = standard_points(df.classified_pos)
    df["scored"] = (df.points_std > 0).astype(int)
    df["status_class"] = np.select(
        [df.finished_classified,
         df.reason_retired.str.contains("Collision|Accident|Spun|Puncture|Damage", case=False, na=False),
         df.position_text.eq("DSQ")],
        ["classified", "incident", "disqualified"], default="mechanical_other")
    df["team_season"] = df.constructor_id + "_" + df.year.astype(str)
    df["race_key"] = df.year.astype(str) + "_" + df["round"].astype(str).str.zfill(2)
    df["date"] = pd.to_datetime(df.date)

    keep = ["raceId", "race_key", "year", "round", "date", "circuitId", "grandPrixId", "race_laps",
            "driver_id", "constructor_id", "team_season", "grid_raw", "grid", "pit_lane_start",
            "finish_order", "classified_pos", "position_text", "finished_classified", "status_class",
            "reason_retired", "laps", "points_actual", "points_std", "scored", "pitStops"]
    return df[keep].sort_values(["date", "finish_order"]).reset_index(drop=True)


def build_pit_stops() -> pd.DataFrame:
    ps = _read("races-pit-stops")
    ps = ps[(ps.year >= min(C.SEASONS)) & (ps.year <= max(C.SEASONS))].copy()
    ps = ps.rename(columns={"driverId": "driver_id", "constructorId": "constructor_id"})
    ps["pit_s"] = ps.timeMillis / 1000.0          # pit-lane time, entry to exit
    # Red-flag "stops" and garage repairs run to minutes; drop anything over 60 s first,
    # then flag stops far above the race's normal stop (penalties, slow repairs).
    hard = ps.pit_s > 60
    med = ps.pit_s.where(~hard).groupby(ps.raceId).transform("median")
    ps["pit_outlier"] = hard | (ps.pit_s > C.PIT_OUTLIER_MULT * med)
    return ps[["raceId", "year", "round", "driver_id", "constructor_id", "stop", "lap", "pit_s", "pit_outlier"]]


# ---------------------------------------------------------------- features
def add_midfield_flag(df: pd.DataFrame, ranks=C.MIDFIELD_RANKS, window=C.MIDFIELD_WINDOW) -> pd.DataFrame:
    """Rolling constructor rank using ONLY races before race r (no look-ahead)."""
    team_race = (df.groupby(["raceId", "date", "constructor_id"], as_index=False).points_std.sum()
                   .sort_values("date"))
    race_order = team_race[["raceId", "date"]].drop_duplicates().sort_values("date").reset_index(drop=True)
    race_order["race_idx"] = np.arange(len(race_order))
    team_race = team_race.merge(race_order[["raceId", "race_idx"]], on="raceId")
    wide = team_race.pivot_table(index="race_idx", columns="constructor_id", values="points_std", aggfunc="sum")
    # Rolling sum of the previous `window` races, shifted by one so race r is excluded.
    # Teams that didn't exist yet stay NaN; teams present but scoreless get 0.
    form = wide.fillna(0).rolling(window, min_periods=1).sum().shift(1)
    form_long = form.stack().rename("form_pts").reset_index()
    out = df.merge(race_order[["raceId", "race_idx"]], on="raceId")
    out = out.merge(form_long, on=["race_idx", "constructor_id"], how="left")
    out["form_pts"] = out.form_pts.fillna(0)
    # Rank among the constructors actually entered in race r.
    team_form = out.drop_duplicates(["raceId", "constructor_id"])[["raceId", "constructor_id", "form_pts"]].copy()
    team_form["team_rank"] = team_form.groupby("raceId").form_pts.rank(ascending=False, method="average")
    out = out.merge(team_form[["raceId", "constructor_id", "team_rank"]], on=["raceId", "constructor_id"])
    lo, hi = ranks
    out["midfield"] = out.team_rank.between(lo, hi)
    out["form_per_race"] = out.form_pts / np.minimum(window, out.race_idx.clip(lower=1)) / 2  # per car per race
    return out


def add_pit_features(df: pd.DataFrame, ps: pd.DataFrame) -> pd.DataFrame:
    clean = ps[~ps.pit_outlier]
    per_car = ps.groupby(["raceId", "driver_id"]).agg(n_stops=("stop", "max"), first_stop_lap=("lap", "min"))
    per_car = per_car.join(clean.groupby(["raceId", "driver_id"]).pit_s.mean().rename("mean_pit_s"))
    per_car = per_car.reset_index()
    out = df.merge(per_car, on=["raceId", "driver_id"], how="left")
    out["n_stops"] = out.n_stops.fillna(0)
    out["first_stop_frac"] = out.first_stop_lap / out.race_laps

    # Within-race benchmarks: computed from cars that ran a meaningful race distance.
    ran = out[(out.laps >= C.MIN_LAP_SHARE_A3 * out.race_laps) & (out.n_stops > 0)]
    bench = ran.groupby("raceId").agg(
        race_median_pit_s=("mean_pit_s", "median"),
        race_modal_stops=("n_stops", lambda s: s.mode().iloc[0]),
        race_median_first_frac=("first_stop_frac", "median"),
    ).reset_index()
    out = out.merge(bench, on="raceId", how="left")
    out["pit_time_delta"] = out.mean_pit_s - out.race_median_pit_s
    out["stop_delta"] = out.n_stops - out.race_modal_stops
    out["first_stop_rel"] = out.first_stop_frac - out.race_median_first_frac
    return out


def build(force_fetch: bool = False) -> pd.DataFrame:
    fetch(force_fetch)
    cs = build_car_starts()
    ps = build_pit_stops()
    cs = add_midfield_flag(cs)
    cs = add_pit_features(cs, ps)
    cs = cs[cs.year.isin(C.SEASONS)].reset_index(drop=True)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    cs.to_csv(C.PROCESSED / "car_starts.csv", index=False)
    ps.to_csv(C.PROCESSED / "pit_stops.csv", index=False)
    return cs


def load() -> pd.DataFrame:
    df = pd.read_csv(C.PROCESSED / "car_starts.csv", parse_dates=["date"])
    df["midfield"] = df.midfield.astype(bool)
    return df
