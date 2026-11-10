"""월·화 각각 3학년 담임 1명 이하 조건에서의 최선 (rows 파일 지정)."""
import pickle, sys
from collections import Counter
from data import DAYS, G1_MODE
rows = pickle.load(open(sys.argv[1], "rb"))
park_mon = (G1_MODE == "A") and (len(sys.argv) < 3 or sys.argv[2] != "nopark")
def dayof(r, s): return next(d for d in DAYS if s in r["days"][d])
def ok(r):
    dJ, dO = dayof(r, "J"), dayof(r, "O")
    mon = (dJ == "월") + (dO == "월") + (1 if park_mon else 0)
    tue = (dJ == "화") + (dO == "화")
    return mon <= 1 and tue <= 1
C = [r for r in rows if ok(r)]
def maxp(r): return max(len(set(r["periods"][d].values())) for d in DAYS)
def jo(r): return f"J{dayof(r,'J')} O{dayof(r,'O')}"
def per(r): return " / ".join(f"{d} " + "·".join(map(str, sorted(set(r["periods"][d].values())))) for d in DAYS)
def show(r): print(" ", r["days"], jo(r), "exc", r["exc"], "화3+", r["tue3_all"], "3과목", r["three"], "계열", r["dup_cnt"], r["dup_n"], "연속", r["consec_cnt"], r["consec_n"], "|", per(r))
print(f"모드 {G1_MODE}, 박현수 월요일 계수 {park_mon}: 조건 만족 {len(C)} / 전체 {len(rows)}")
A = [r for r in C if r["tue3_all"] == 0]
print("\nA. 마지막날 3회 0명:", len(A), "하루 최대 교시:", dict(Counter(maxp(r) for r in A)))
for r in sorted(A, key=lambda r: (maxp(r), r["consec_n"], r["max3"], r["dup_n"]))[:6]: show(r)
B = [r for r in C if maxp(r) <= 4]
print("\nB. 모든 날 4교시 이하:", len(B), "화3+ 최소:", min(r["tue3_all"] for r in B) if B else None)
B4 = [r for r in B if r["tue3_all"] <= 4]
keys = [(r["tue3_all"], r["max3"], r["dup_n"], r["consec_n"]) for r in B4]
seen = set()
for r in sorted(B4, key=lambda r: (r["tue3_all"], r["max3"], r["dup_n"], r["consec_n"])):
    k = (r["tue3_all"], r["max3"], r["dup_n"], r["consec_n"])
    if k in seen or any(o != k and all(o[i] <= k[i] for i in range(4)) for o in keys): continue
    seen.add(k); show(r)
B0 = [r for r in B if r["consec_n"] == 0]
print("\nB 중 연속 0건:", len(B0), "화3+ 최소:", min((r["tue3_all"] for r in B0), default=None))
for r in sorted(B0, key=lambda r: (r["tue3_all"], r["max3"], r["dup_n"]))[:4]: show(r)
