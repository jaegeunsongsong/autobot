"""저장된 공간 전체에 2단계를 적용해 완전한 지표표를 만든다."""
import pickle, sys, time, csv
from evaluate import *

name = sys.argv[1]
sols = pickle.load(open(f"space_{name}.pkl", "rb"))
t = time.time()
rows = []
infeasible = 0
for i, a in enumerate(sols):
    tt = best_timetable(a)
    if tt is None:
        infeasible += 1
        continue
    m = full_metrics(a, tt)
    r = summary_row(a, tt, m)
    r["assign"] = a
    rows.append(r)
    if i % 2000 == 0:
        print(i, f"{time.time()-t:.0f}s", flush=True)
pickle.dump(rows, open(f"rows_{name}.pkl", "wb"))
print(f"{name}: {len(sols)} 요일배정 중 교시배정 가능 {len(rows)}, 불가 {infeasible}, {time.time()-t:.0f}s")
