# -*- coding: utf-8 -*-
import sys, pickle; sys.path.insert(0, '.')
from data import *
from periods import day_configs
def row(m):
    sets = " | ".join("".join(sorted(s)) for s in m["sets"])
    cfg = m["cfg"]
    per = " ".join("".join(map(str, c["periods"])) for c in cfg)
    return (f"{sets:34s} exc{m['exc']} 3과목{m['three']} max{m['max3']:3d} sum{m['sum3']:3d} 계열{m['series_students']:3d} "
            f"교사2{len(m['teacher_day'])} ABC{m['abc_same']} dev{m['ndev']} 연속{m['consec_students']:3d} p1{m['p1']} 36{m['open36']} 교시[{per}] "
            + (f"viol={COMBOS[m['viol']][0]}" if m['viol'] >= 0 else ""))
def load(fn): return pickle.load(open(fn, "rb"))
def base_ok(m):
    """전 요일 기본형(목·금·월 ⊆ 2457, 화 ⊆ 24)으로 배정 가능한가"""
    for i, d in enumerate(DAYS):
        base = {2, 4} if d == "화" else {2, 4, 5, 7}
        if not any(set(c["periods"]) <= base for c in day_configs(d, m["sets"][i])): return False
    return True
if __name__ == "__main__":
    fn = sys.argv[1]; flt = sys.argv[2]; key = sys.argv[3]; n = int(sys.argv[4]) if len(sys.argv) > 4 else 15
    ms = load(fn)
    ms = [m for m in ms if m["feasible"] and eval(flt)]
    ms.sort(key=lambda m: eval(key))
    print(len(ms), "건")
    for m in ms[:n]: print(row(m))
