# -*- coding: utf-8 -*-
"""하루치 과목 집합에 대해 가능한 교시 배정을 모두 열거한다 (교시 수준 절대 제약 적용)."""
import sys; sys.path.insert(0, '.')
from data import *
from functools import lru_cache
from itertools import product

BASE = {"목": {2, 4, 5, 7}, "금": {2, 4, 5, 7}, "월": {2, 4, 5, 7}, "화": {2, 4}}
DAY_PERIODS = {"목": range(1, 8), "금": range(1, 8), "월": range(1, 8), "화": range(1, 5)}
_both = {}
def both(a, b):
    k = (a, b) if a < b else (b, a)
    if k not in _both: _both[k] = sum(n for c, n in COMBOS if a in c and b in c)
    return _both[k]

def allowed(day, s, g1p, sci_day="화"):
    """g1p: {'한국사2':p, '통합사회2':2, '통합과학2':p} 그날 1학년 교시. sci_day: 통합과학2 요일."""
    ps = set(DAY_PERIODS[day])
    if day == "목":
        ps = {p for p in ps if not (set(TEACHERS[s]) & THU_G1_CLASS[p])}
    if s == "P":
        ps -= {p for d, p in JEON_AWAY if d == day}
    # 3학년 담임(배태안 J, 손경준 O): 월·화는 2교시만
    if day in ("월", "화") and (set(TEACHERS[s]) & HR3):
        ps &= {2}
    # 같은 교시 담당교사 중복(1학년 과목과)
    for g1s, p in g1p.items():
        if set(TEACHERS[s]) & set(G1[g1s]):
            ps -= {p}
    return ps

def g1_options(day, sci_day="화"):
    """그날 1학년 배치 선택지 목록: [{과목: 교시}]"""
    if day == "목": return [{}]
    if day == "화":
        a, b = 2, 4
    else:
        a, b = 2, 7
    subs = [s for s, d in G1_FIXED_DAY.items() if d == day]
    if sci_day != "화":
        subs = [s for s in subs if s != "통합과학2"]
        if day == sci_day: subs.append("통합과학2")
    opts = []
    if "통합사회2" in subs:  # 박현수(3학년 담임) → 월 2교시 고정
        others = [s for s in subs if s != "통합사회2"]
        if len(others) == 1: opts.append({"통합사회2": 2, others[0]: 7})
        else: opts.append({"통합사회2": 2})
    else:
        if len(subs) == 1: opts += [{subs[0]: a}, {subs[0]: b}]
        elif len(subs) == 2: opts += [{subs[0]: a, subs[1]: b}, {subs[0]: b, subs[1]: a}]
        else: opts.append({})
    return opts

@lru_cache(maxsize=None)
def day_configs(day, S, sci_day="화"):
    """S: frozenset 과목. 반환: list of dict(assign={s:p}, g1={s:p}, periods, dev, consec, p1, open36)"""
    S = set(S)
    units = []
    rest = set(S)
    if {"O", "J"} <= S: units.append(("O", "J")); rest -= {"O", "J"}
    if {"N", "P"} <= S: units.append(("N", "P")); rest -= {"N", "P"}
    units += [(s,) for s in sorted(rest)]
    out = []
    for g1p in g1_options(day, sci_day):
        al = {}
        ok = True
        for u in units:
            ps = set(DAY_PERIODS[day])
            for s in u: ps &= allowed(day, s, g1p, sci_day)
            if not ps: ok = False; break
            al[u] = sorted(ps)
        if not ok: continue
        # 백트래킹
        def rec(i, used, assign):
            if i == len(units):
                out.append((dict(assign), dict(g1p))); return
            u = units[i]
            for p in al[u]:
                if p in used: continue
                used.add(p)
                for s in u: assign[s] = p
                rec(i + 1, used, assign)
                used.discard(p)
                for s in u: assign.pop(s)
        rec(0, set(), {})
    res = []
    for assign, g1p in out:
        periods = sorted(set(assign.values()))
        dev = sorted(p for p in periods if p not in BASE[day]) if day != "목" else []
        consec = []
        for p, q in CONSEC_PAIRS:
            A_ = [s for s, pp in assign.items() if pp == p]
            B_ = [s for s, pp in assign.items() if pp == q]
            for a in A_:
                for b in B_:
                    consec.append((p, q, a, b, both(a, b)))
        res.append({
            "assign": assign, "g1": g1p, "periods": tuple(periods),
            "dev": tuple(dev), "ndev": len(dev),
            "consec": tuple(consec), "nconsec": len(consec), "consec_students": sum(c[4] for c in consec),
            "p1": int(1 in periods), "open36": int(bool({3, 6} & set(periods))) if day == "목" else 0,
            "nonbase": tuple(p for p in periods if p not in {2, 4, 5, 7}),
        })
    return res

def best_config(day, S, key=None, sci_day="화"):
    cfgs = day_configs(day, frozenset(S), sci_day)
    if not cfgs: return None
    if key is None:
        key = lambda c: (c["ndev"], c["consec_students"], c["nconsec"], c["p1"], c["open36"], len(c["nonbase"]), c["periods"])
    return min(cfgs, key=key)

if __name__ == "__main__":
    for day, S in [("목", "EAIH"), ("목", "HOJEL"), ("화", "OJB"), ("화", "CD"), ("금", "CGNPL"), ("월", "DFKM"), ("화", "HMJO")]:
        cf = day_configs(day, frozenset(S))
        b = best_config(day, S)
        print(day, S, len(cf), "configs; best:", b and (b["assign"], b["g1"], b["dev"], b["consec"]))
