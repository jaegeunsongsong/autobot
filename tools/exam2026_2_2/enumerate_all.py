"""1단계 전체 공간을 열거해 pickle 로 저장."""
import pickle, sys, time
from layer1 import *

name = sys.argv[1]
cap = dict(zip(DAYS, map(int, sys.argv[2].split(","))))
hard = sys.argv[3] == "hard"
t = time.time()
sols = enumerate_day_assignments(cap, hard_prefs=hard)
pickle.dump(sols, open(f"space_{name}.pkl", "wb"))
print(name, cap, "hard" if hard else "soft", len(sols), f"{time.time()-t:.0f}s")
