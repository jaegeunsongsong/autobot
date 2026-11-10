# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, '.')
from data import *
from itertools import combinations

tot = sum(n for _, n in COMBOS)
print("조합 수", len(COMBOS), "합계", tot)
assert all(len(c) == 8 for c, _ in COMBOS), "8과목 아님"
enroll = {s: sum(n for c, n in COMBOS if s in c) for s in SUBJECTS}
for s in SUBJECTS:
    flag = "OK" if enroll[s] == ENROLL[s] else "MISMATCH"
    print(f"{s} {NAME[s]:10s} 데이터={enroll[s]:4d} 표={ENROLL[s]:4d} {flag}")
def inter(a, b): return sum(n for c, n in COMBOS if a in c and b in c)
for a, b, exp in [("E", "I", 50), ("H", "J", 33), ("E", "O", 25), ("L", "P", 1)]:
    print(f"{a}∩{b} = {inter(a,b)} (기대 {exp}) {'OK' if inter(a,b)==exp else 'MISMATCH'}")
zero = [(a, b) for a, b in combinations(SUBJECTS, 2) if inter(a, b) == 0]
print("겹침 0 쌍:", zero)
small = sorted(((inter(a, b), a, b) for a, b in combinations(SUBJECTS, 2)), key=lambda t: t[0])[:8]
print("겹침 적은 순:", small)
for name, info in EXEMPT.items():
    cnt = dict(COMBOS).get(info["combo"])
    print(f"면제 {name} {info['combo']}: 데이터 내 인원 = {cnt}")
