# -*- coding: utf-8 -*-
"""전수 열거된 일자 분할에 대해 지표를 계산한다."""
import sys; sys.path.insert(0, '.')
from data import *
from periods import day_configs, best_config, both
from evaluate import day_dist
from itertools import combinations
import pickle

def load_parts(fn):
    parts = []
    for line in open(fn):
        a, v = line.split(); parts.append((a, int(v)))
    return parts

TEACHER_DAY_RULES = {  # (과목, 요일) → 교사 하루 2과목 (1학년 과목과 같은 날)
    ("E", "월"): "김미애(통합사회2)", ("I", "월"): "노석환(통합사회2)",
    ("H", "화"): "최진호(통합과학2)", ("M", "화"): "조세라(통합과학2)",
    ("O", "금"): "정인광·손경준(한국사2)",
}

def day_sets(a):
    return [frozenset(s for s, d in zip(SUBJECTS, a) if d == str(i)) for i in range(4)]

def metrics(a, viol, sci_day="화"):
    S = day_sets(a)
    m = {"a": a, "viol": viol, "sets": S}
    dist = [day_dist(set(s))[0] for s in S]
    m["dist"] = dist
    m["three"] = [dist[i][3] for i in range(4)]
    m["max3"] = max(m["three"]); m["sum3"] = sum(m["three"])
    m["four"] = [dist[i][4] for i in range(4)]
    # 계열 중복
    ser = []; tot = 0
    for i in range(4):
        for x, y in combinations(sorted(S[i]), 2):
            if SERIES[x] == SERIES[y]:
                k = both(x, y); tot += k; ser.append((DAYS[i], x, y, k))
    m["series"] = ser; m["series_students"] = tot
    # 교사 하루 2과목
    rules = dict(TEACHER_DAY_RULES)
    if sci_day != "화":
        rules.pop(("H", "화")); rules.pop(("M", "화"))
        rules[("H", sci_day)] = "최진호(통합과학2)"; rules[("M", sci_day)] = "조세라(통합과학2)"
    td = [f"{d} {who}+{s}" for (s, d), who in rules.items() if s in S[DAYS.index(d)]]
    if any(("B" in s and "D" in s) for s in S): td.append("구성희 B+D 같은 날")
    m["teacher_day"] = td
    m["abc_same"] = int(len({a[0], a[1], a[2]}) < 3)
    m["exc"] = 1 + sum(1 for s in "JO" if a[SUBJECTS.index(s)] in "23")
    m["pairOJ"] = int(a[SUBJECTS.index("O")] == a[SUBJECTS.index("J")])
    m["pairNP"] = int(a[SUBJECTS.index("N")] == a[SUBJECTS.index("P")])
    slots = [len(S[i]) for i in range(4)]
    if m["pairOJ"]: slots[int(a[SUBJECTS.index("O")])] -= 1
    if m["pairNP"]: slots[int(a[SUBJECTS.index("N")])] -= 1
    m["slots"] = slots
    # 교시 배정
    cfgs = [best_config(DAYS[i], S[i], sci_day=sci_day) for i in range(4)]
    m["cfg"] = cfgs
    m["feasible"] = all(c is not None for c in cfgs)
    if m["feasible"]:
        m["ndev"] = sum(c["ndev"] for c in cfgs)
        m["consec_students"] = sum(c["consec_students"] for c in cfgs)
        m["nconsec"] = sum(c["nconsec"] for c in cfgs)
        m["p1"] = sum(c["p1"] for c in cfgs)
        m["open36"] = cfgs[0]["open36"]
        m["thu_nonbase"] = cfgs[0]["nonbase"]
    return m

if __name__ == "__main__":
    import collections
    for fn in ["parts_strict.txt", "parts_allow1.txt"]:
        parts = load_parts(fn)
        ms = [metrics(a, v) for a, v in parts]
        feas = [m for m in ms if m["feasible"]]
        print(fn, "분할", len(ms), "교시배정 가능", len(feas))
        pickle.dump(ms, open(fn.replace(".txt", ".pkl"), "wb"))
        c = collections.Counter((m["exc"], m["max3"]) for m in feas)
        print(" (예외, max3) 분포:", sorted(c.items())[:40])
        print(" min max3:", min(m["max3"] for m in feas), " min series:", min(m["series_students"] for m in feas))
        print(" min sum3:", min(m["sum3"] for m in feas))
        # 안 X, Y 포함 여부
        for name, a in [("X", "".join({"E":"0","A":"0","I":"0","H":"0","C":"1","G":"1","N":"1","P":"1","L":"1","D":"2","F":"2","K":"2","M":"2","O":"3","J":"3","B":"3"}[s] for s in SUBJECTS)),
                        ("Y", "".join({"H":"0","O":"0","J":"0","E":"0","L":"0","A":"1","G":"1","I":"1","N":"1","P":"1","B":"2","F":"2","K":"2","M":"2","C":"3","D":"3"}[s] for s in SUBJECTS))]:
            hit = [m for m in ms if m["a"] == a]
            print(f" 안 {name} {a}: ", "포함" if hit else "미포함", hit and (hit[0]["viol"], COMBOS[hit[0]["viol"]][0] if hit[0]["viol"]>=0 else None))
