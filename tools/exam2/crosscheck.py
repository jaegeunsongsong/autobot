# 독립 구현(파이썬·numpy)으로 C 열거기의 strict 결과를 교차 검증
import sys; sys.path.insert(0, '.')
import numpy as np
from data import *
M = np.array([[s in c for s in SUBJECTS] for c, n in COMBOS], dtype=np.int8)  # 84x16
cnt = np.array([n for c, n in COMBOS]); nmax = cnt.copy()
for e in EXEMPT.values():
    if e["type"] == "체육부": nmax[[c for c, n in COMBOS].index(e["combo"])] -= 1
cap = np.array([3, 3, 3, 2])
found = set(); nodes = 0
load = np.zeros((4, 84), dtype=np.int8)
def dfs(s, assign):
    global nodes; nodes += 1
    if s == 16:
        if (load == 0).any(): return
        a = "".join(map(str, assign))
        n = [assign.count(d) for d in range(4)]
        if assign[14] == assign[9]: n[assign[14]] -= 1
        if assign[13] == assign[15]: n[assign[13]] -= 1
        if n[3] > 4 or max(n[:3]) > 7: return
        found.add(a); return
    for d in range(4):
        if d == 3 and s in (0, 15): continue
        load[d] += M[:, s]
        if not ((load[d] > cap[d]) & (nmax > 0)).any():
            assign.append(d); dfs(s + 1, assign); assign.pop()
        load[d] -= M[:, s]
dfs(0, [])
c_set = {line.split()[0] for line in open("parts_strict.txt")}
print("python nodes", nodes, "feasible", len(found), "| C feasible", len(c_set), "| 일치" if found == c_set else "| 불일치")
