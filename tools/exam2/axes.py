# -*- coding: utf-8 -*-
"""축별 최적 분할 선택: 교시 배정은 축별 키로 요일마다 독립 선택(사전식 순서는 성분합과 호환)."""
import sys, pickle; sys.path.insert(0, '.')
from data import *
from periods import day_configs
from query import load

CFG_KEYS = {
    # (요일별 교시 배정 선택 키) 이름 → 함수
    "default": lambda c: (c["ndev"], c["consec_students"], c["nconsec"], c["p1"], c["open36"], len(c["nonbase"]), c["periods"]),
    "no_p1":   lambda c: (c["ndev"], c["p1"], c["consec_students"], c["nconsec"], c["open36"], len(c["nonbase"]), c["periods"]),
    "base":    lambda c: (c["ndev"], len(c["nonbase"]), c["consec_students"], c["p1"], c["periods"]),
}
def with_cfg(m, ck, sci_day="화"):
    """축별 교시 키로 요일 배정을 다시 고르고 합계 지표를 갱신한 사본"""
    m = dict(m)
    cfgs = []
    for i, d in enumerate(DAYS):
        cs = day_configs(d, m["sets"][i], sci_day)
        cfgs.append(min(cs, key=CFG_KEYS[ck]))
    m["cfg"] = cfgs
    m["ndev"] = sum(c["ndev"] for c in cfgs); m["consec_students"] = sum(c["consec_students"] for c in cfgs)
    m["nconsec"] = sum(c["nconsec"] for c in cfgs); m["p1"] = sum(c["p1"] for c in cfgs); m["open36"] = cfgs[0]["open36"]
    m["nonbase"] = sum(len(c["nonbase"]) for c in cfgs); m["maxper"] = max(len(c["periods"]) for c in cfgs)
    return m

AXES = {
    "①예외1건": dict(ck="default", flt=lambda m: m["exc"] == 1,
                 key=lambda m: (m["max3"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["p1"], m["sum3"])),
    "②3과목최대": dict(ck="default", flt=lambda m: True,
                 key=lambda m: (m["max3"], m["sum3"], m["exc"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["p1"])),
    "③계열중복": dict(ck="default", flt=lambda m: True,
                 key=lambda m: (m["series_students"], m["max3"], m["exc"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["p1"], m["sum3"])),
    "④기본형통일": dict(ck="base", flt=lambda m: m["ndev"] == 0 and m["nonbase"] == 0,
                 key=lambda m: (m["max3"], m["exc"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["sum3"])),
    "⑤1교시없음": dict(ck="no_p1", flt=lambda m: m["p1"] == 0,
                 key=lambda m: (m["max3"], m["exc"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["sum3"])),
    "⑥연속없음": dict(ck="default", flt=lambda m: m["consec_students"] == 0,
                 key=lambda m: (m["max3"], m["exc"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["p1"], m["sum3"])),
    "⑦3과목합": dict(ck="default", flt=lambda m: True,
                 key=lambda m: (m["sum3"], m["max3"], m["exc"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["p1"])),
    "⑧5교시요일없음": dict(ck="default", flt=lambda m: m["maxper"] <= 4,
                 key=lambda m: (m["max3"], m["exc"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["p1"], m["sum3"])),
    "⑩예외1+목기본형+1교시없음": dict(ck="no_p1", flt=lambda m: m["exc"] == 1 and m["open36"] == 0 and m["p1"] == 0,
                 key=lambda m: (m["max3"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["sum3"])),
    "⑪목기본형+1교시없음": dict(ck="no_p1", flt=lambda m: m["cfg"][0]["nonbase"] == () and m["p1"] == 0,
                 key=lambda m: (m["max3"], m["exc"], m["series_students"], len(m["teacher_day"]), m["abc_same"], m["ndev"], m["consec_students"], m["sum3"])),
    "⑨예외1+교사0+ABC": dict(ck="default", flt=lambda m: m["exc"] == 1 and len(m["teacher_day"]) == 0 and m["abc_same"] == 0,
                 key=lambda m: (m["max3"], m["series_students"], m["ndev"], m["consec_students"], m["p1"], m["sum3"])),
}
def row(m):
    sets = " | ".join("".join(sorted(s)) for s in m["sets"])
    per = " ".join("".join(map(str, c["periods"])) for c in m["cfg"])
    return (f"{sets:32s} exc{m['exc']} 3과목{m['three']} max{m['max3']:3d} sum{m['sum3']:3d} 계열{m['series_students']:3d} "
            f"교사2{len(m['teacher_day'])} ABC{m['abc_same']} dev{m['ndev']} 연속{m['consec_students']:3d} p1{m['p1']} 36{m['open36']} [{per}]"
            + (f" viol={COMBOS[m['viol']][0]}" if m['viol'] >= 0 else ""))
def run(fn, flt_extra=lambda m: True, n=3, sci_day="화", axes=None):
    ms = [m for m in load(fn) if m["feasible"] and flt_extra(m)]
    for name, ax in AXES.items():
        if axes and name not in axes: continue
        cand = [with_cfg(m, ax["ck"], sci_day) for m in ms]
        cand = [m for m in cand if ax["flt"](m)]
        cand.sort(key=ax["key"])
        print(f"--- {name}: {len(cand)}건 ---")
        for m in cand[:n]: print("  " + row(m))
if __name__ == "__main__":
    fn = sys.argv[1]; flt = sys.argv[2] if len(sys.argv) > 2 else "True"; n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    run(fn, lambda m: eval(flt), n)
