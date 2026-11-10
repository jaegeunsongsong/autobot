import pickle, sys
from collections import Counter
from data import DAYS
mode = sys.argv[1]
rows = pickle.load(open("rows_full.pkl" if mode == "A" else "rows_fullB.pkl", "rb"))
def dayof(r, s): return next(d for d in DAYS if s in r["days"][d])
def paired(r):
    d = dayof(r, "J"); return d == dayof(r, "O") and r["periods"][d]["J"] == r["periods"][d]["O"]
def maxp(r): return max(len(set(r["periods"][d].values())) for d in DAYS)
def per(r): return " / ".join(f"{d} " + "·".join(map(str, sorted(set(r["periods"][d].values())))) for d in DAYS)
def staff(r):
    return ((1 if mode == "A" else 0) + (dayof(r,"J")=="월") + (dayof(r,"O")=="월"), (dayof(r,"J")=="화") + (dayof(r,"O")=="화"))
C = [r for r in rows if paired(r) and dayof(r, "J") in ("목", "금") and maxp(r) <= 4]
print(f"[모드 {mode}] J+O 묶음·목/금·모든 날 4교시 이하: {len(C)}개 (묶음 요일 {dict(Counter(dayof(r,'J') for r in C))})")
if C:
    mn = min(r["tue3_all"] for r in C)
    print("  화요일 3과목 최소:", mn, "| 모양:", dict(Counter(r["shape"] for r in C)), "| 담임(월,화):", Counter(staff(r) for r in C))
    best = sorted([r for r in C if r["tue3_all"] == mn], key=lambda r: (r["consec_n"], r["max3"], r["dup_n"]))
    seen = set()
    for r in best:
        k = (r["three"], r["dup_n"], r["consec_n"])
        if k in seen: continue
        seen.add(k)
        print("   ", r["shape"], r["days"], "3과목", r["three"], "계열", r["dup_cnt"], r["dup_n"], "연속", r["consec_cnt"], r["consec_n"], "1교시", [d for d in DAYS if 1 in r["periods"][d].values()], "|", per(r), "|", r["periods"]["목"])
    # 파레토 (화3+, 3과목최대, 계열, 연속)
    print("  파레토 (화3+ ≤ 6):")
    C6 = [r for r in C if r["tue3_all"] <= 6]
    keys = [(r["tue3_all"], r["max3"], r["dup_n"], r["consec_n"]) for r in C6]
    seen = set()
    for r in sorted(C6, key=lambda r: (r["tue3_all"], r["max3"], r["dup_n"], r["consec_n"])):
        k = (r["tue3_all"], r["max3"], r["dup_n"], r["consec_n"])
        if k in seen or any(o != k and all(o[i] <= k[i] for i in range(4)) for o in keys): continue
        seen.add(k)
        print("   ", r["shape"], r["days"], "화3+", r["tue3_all"], "3과목", r["three"], "계열", r["dup_cnt"], r["dup_n"], "연속", r["consec_cnt"], r["consec_n"], "|", per(r))
