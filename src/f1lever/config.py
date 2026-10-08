"""Every assumption in one place. Change a value here and rerun; nothing else is hard-coded."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "f1db"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

F1DB_CSV_URL = "https://github.com/f1db/f1db/releases/latest/download/f1db-csv.zip"

SEASONS = list(range(2018, 2026))          # 2018-2025 inclusive
HISTORY_START = 2017                        # needed so early-2018 races have rolling form
TRAIN_SEASONS = list(range(2018, 2025))     # 2018-2024
TEST_SEASON = 2025

# Standard points scale for every season (no fastest-lap point, no sprints)
POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

MIDFIELD_RANKS = (4, 8)    # inclusive constructor rank range
MIDFIELD_WINDOW = 5        # previous races used for the rolling rank

PIT_OUTLIER_MULT = 2.5     # stop > 2.5x race median pit-lane time = repair/penalty/red flag
MIN_LAP_SHARE_A3 = 0.5     # A3 sample: car completed >= 50% of race laps

PIT_IMPROVEMENT_S = 0.5    # lever B "realistic improvement": 0.5 s faster per stop

USD_PER_PLACE = 8.5e6      # published estimate (The Race, 2025); confidential in reality
USD_SENSITIVITY = [5e6, 8.5e6, 12e6]

N_BOOT = 500               # race-clustered bootstrap replicates
SEED = 42
