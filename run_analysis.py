"""Phases 2-3: analyses A1-A6 -> reports/results.md, reports/headline.json, reports/figures/*.png"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from f1lever import analysis as A, data, report as R  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    df = data.load()
    a1 = A.a1_steps(df);            print(f"A1 done ({time.time()-t0:.0f}s)")
    a2 = A.a2_grid_value(df);       print(f"A2 done ({time.time()-t0:.0f}s)")
    a3 = A.a3_strategy(df);         print(f"A3 done ({time.time()-t0:.0f}s)")
    a4 = A.a4_compare(df, a2, a3);  print(f"A4 done ({time.time()-t0:.0f}s)")
    a5 = A.a5_validate(df);         print(f"A5 done ({time.time()-t0:.0f}s)")
    a6 = A.a6_robustness(df);       print(f"A6 done ({time.time()-t0:.0f}s)")
    R.fig1_a1(a1); R.fig2_grid_curve(a2); R.fig3_slot_value(a2)
    R.fig4_strategy(a3); R.fig5_levers(a4); R.fig6_calibration(a5)
    headline = R.write_results(df, a1, a2, a3, a4, a5, a6)
    print("\nHEADLINE")
    for k, v in headline.items():
        print(f"  {k}: {v}")
    print(f"\nwrote reports/results.md and 6 figures in {time.time()-t0:.0f}s")
