"""Phase 1: download F1DB once (cached), clean, build features -> data/processed/car_starts.csv"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from f1lever import data  # noqa: E402

if __name__ == "__main__":
    df = data.build(force_fetch="--refresh" in sys.argv)
    print(f"car-starts: {len(df):,} | races: {df.race_key.nunique()} | seasons: {df.year.min()}-{df.year.max()}")
    print(f"midfield car-starts: {int(df.midfield.sum()):,} | pit-lane starts recoded: {int(df.pit_lane_start.sum())} "
          f"| DNFs kept: {int((~df.finished_classified).sum())}")
