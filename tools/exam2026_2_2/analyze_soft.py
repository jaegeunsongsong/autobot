"""강한 선호를 풀고(절대 제약만) 화2 구조를 열거·평가. 위반한 선호를 집계."""
import pickle, sys, time
from layer1 import *
from evaluate import *

cap = dict(zip(DAYS, map(int, sys.argv[1].split(","))))
name = sys.argv[2]
t = time.time()
sols = enumerate_day_assignments(cap, hard_prefs=False)
print("soft", cap, len(sols), f"{time.time()-t:.0f}s", flush=True)
rows = []
for a in sols:
    tt = best_timetable(a)
    if tt is None:
        continue
    m = full_metrics(a, tt)
    r = summary_row(a, tt, m)
    r["assign"] = a
    r["t2_detail"] = m["teacher2"]
    r["abc_ok"] = m["abc_ok"]
    rows.append(r)
pickle.dump(rows, open(f"rows_{name}.pkl", "wb"))
print("rows", len(rows), f"{time.time()-t:.0f}s")
