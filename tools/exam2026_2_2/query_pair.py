import pickle, sys
from collections import Counter
from data import DAYS
mode = sys.argv[1]
rows = pickle.load(open("rows_full.pkl" if mode == "A" else "rows_fullB.pkl", "rb"))
def dayof(r, s): return next(d for d in DAYS if s in r["days"][d])
def paired_jo(r):
    d = dayof(r, "J")
    return d == dayof(r, "O") and r["periods"][d]["J"] == r["periods"][d]["O"]
def maxp(r): return max(len(set(r["periods"][d].values())) for d in DAYS)
def staff(r):
    mon = (1 if mode == "A" else 0) + (dayof(r, "J") == "월") + (dayof(r, "O") == "월")
    tue = (dayof(r, "J") == "화") + (dayof(r, "O") == "화")
    return mon, tue
def per(r): return " / ".join(f"{d} " + "·".join(map(str, sorted(set(r["periods"][d].values())))) for d in DAYS)
C = [r for r in rows if paired_jo(r) and dayof(r, "J") in ("월", "화") and maxp(r) <= 4]
print(f"[모드 {mode}: 통합사회2 {'월' if mode=='A' else '금'}] J+O 묶음·월/화 2교시·모든 날 4교시 이하: {len(C)}개")
for where in ("월", "화"):
    S = [r for r in C if dayof(r, "J") == where]
    if not S:
        print(f"  J+O {where}요일: 0개"); continue
    mn = min(r["tue3_all"] for r in S)
    print(f"  J+O {where}요일: {len(S)}개, 화요일 3과목 최소 {mn}명, 모양 {dict(Counter(r['shape'] for r in S))}, 3학년담임 (월,화) = {staff(S[0])}")
    best = sorted([r for r in S if r["tue3_all"] == mn], key=lambda r: (r["consec_n"], r["max3"], r["dup_n"]))
    seen = set()
    for r in best:
        k = (r["three"], r["dup_n"], r["consec_n"], tuple(sorted(r["days"].items())))
        if k in seen: continue
        seen.add(k)
        print("    ", r["shape"], r["days"], "3과목", r["three"], "계열", r["dup_cnt"], r["dup_n"], "연속", r["consec_cnt"], r["consec_n"], "|", per(r))
        if len(seen) >= 4: break
    # 4·3·4·3 만 따로
    S2 = [r for r in S if r["shape"] in ("4·3·4·3",)]
    if S2:
        mn2 = min(r["tue3_all"] for r in S2)
        print(f"    (4·3·4·3 만: {len(S2)}개, 화3+ 최소 {mn2}명)")
