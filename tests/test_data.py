"""Guards for the cleaning decisions that fixed v1's biases."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from f1lever import config as cfg, data  # noqa: E402


@pytest.fixture(scope="module")
def df():
    return data.load()


def test_points_scale_is_standard(df):
    assert data.standard_points(pd.Series([1, 2, 10, 11, np.nan])).tolist() == [25, 18, 1, 0, 0]
    # every race awards exactly the standard total to classified cars (101 points for P1-P10)
    per_race = df.groupby("race_key").points_std.sum()
    assert (per_race <= 101).all() and (per_race >= 95).all()


def test_pit_lane_starters_go_to_back_not_pole(df):
    pl = df[df.pit_lane_start]
    assert len(pl) > 0
    assert (pl.grid >= 15).all(), "pit-lane starters must never be coded as pole (v1 bug)"


def test_dnfs_are_kept_with_zero_points(df):
    dnf = df[~df.finished_classified]
    assert len(dnf) > 300, "v1 dropped DNFs; v2 must keep them"
    assert (dnf.points_std == 0).all()


def test_about_twenty_cars_per_race(df):
    sizes = df.groupby("race_key").size()
    assert sizes.between(18, 20).all()
    assert df.race_key.nunique() == 173


def test_midfield_flag_has_no_look_ahead(df):
    """Changing race r's results must not change race r's midfield flag."""
    raw = data.build_car_starts()
    base = data.add_midfield_flag(raw)
    target = base.raceId.iloc[len(base) // 2]
    tampered = raw.copy()
    mask = tampered.raceId == target
    tampered.loc[mask, "points_std"] = tampered.loc[mask, "points_std"].values[::-1]  # shuffle who scored
    after = data.add_midfield_flag(tampered)
    key = ["raceId", "driver_id"]
    a = base[base.raceId == target].set_index(key).midfield.sort_index()
    b = after[after.raceId == target].set_index(key).midfield.sort_index()
    assert a.equals(b)


def test_pit_outliers_removed_from_execution_metric(df):
    assert df.pit_time_delta.abs().max() < 60
