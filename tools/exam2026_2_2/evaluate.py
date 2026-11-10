"""완성된 시간표(요일 배정 + 교시 배정)의 모든 지표를 계산하고, 요일 배정마다 최선의 교시 배정을 찾는다."""
import itertools, math, functools
from data import *
from layer1 import day_sets, distribution
from layer2 import assignments, consecutive_cost, triple_consecutive, g1_slots, units_of

FULL = {"목": (1, 2, 3, 4, 5, 6, 7), "금": (1, 2, 3, 4, 5, 6, 7), "월": (1, 2, 3, 4, 5, 6, 7), "화": (1, 2, 3, 4)}
STD = {"목": {2, 3, 4, 5, 6, 7}, "금": {2, 4, 5, 7}, "월": {2, 4, 5, 7}, "화": {2, 4}}  # 선호 교시(벗어나면 dev)


@functools.lru_cache(maxsize=None)
def day_options(day, subs, allowed, k, h):
    """하루치 가능한 교시 배정 전부를 (비용키, sp) 로. 쌍 사용 여부도 모두 포함.
    비용키 = (연속 인원합, 연속 건수, 선호 밖 교시 수, 목1교시 사용)"""
    out = {}
    for pj in (True, False):
        for pn in (True, False):
            if not pj and not ({"J", "O"} <= set(subs)):
                continue
            if not pn and not ({"N", "P"} <= set(subs)):
                continue
            for sp in assignments(day, set(subs), allowed, k, h, pj, pn):
                cc = consecutive_cost(day, sp)
                used = set(sp.values())
                key = (sum(x[4] for x in cc), len(cc), len(used - STD[day]), 1 if (day == "목" and 1 in used) else 0)
                t = tuple(sorted(sp.items()))
                if t not in out or key < out[t]:
                    out[t] = key
    # 비용키별 대표 하나씩 + 전체 최소
    res = sorted(((key, t, dict(t)) for t, key in out.items()))
    res = [(key, sp) for key, _, sp in res]
    return res


def teacher2_count(ds, k):
    """교사 하루 2과목(1학년 포함) 건수 — 요일 배정과 k(통합과학2 요일)로 결정"""
    n = 0
    if "O" in ds["금"]: n += 2          # 정인광·손경준 + 한국사2
    soc = "월" if G1_MODE == "A" else "금"
    sci = ("금" if k else "월") if G1_MODE == "A" else "월"
    if "E" in ds[soc]: n += 1          # 김미애 + 통합사회2
    if "I" in ds[soc]: n += 1          # 노석환 + 통합사회2
    if "H" in ds[sci]: n += 1           # 최진호 + 통합과학2
    if "M" in ds[sci]: n += 1           # 조세라 + 통합과학2
    for d in DAYS:
        if "B" in ds[d] and "D" in ds[d]: n += 1   # 구성희
    return n


def best_timetable(assign, allowed=FULL, objective=None):
    """요일 배정에 대해 (k,h) 와 교시 배정을 골라 비용 최소.
    비용 = (교사 하루 2과목 건수, 연속 인원합, 연속 건수, 선호 밖 교시 수, 목1교시)"""
    ds = day_sets(assign)
    best = None
    for k in (0, 1):
        for h in (2, 7):
            per_day = {}
            ok = True
            for d in DAYS:
                opts = day_options(d, tuple(sorted(ds[d])), tuple(allowed[d]), k, h)
                if not opts:
                    ok = False; break
                per_day[d] = opts[0]
            if not ok:
                continue
            tot = (teacher2_count(ds, k),) + tuple(sum(per_day[d][0][i] for d in DAYS) for i in range(4))
            cand = (tot, k, h, {d: per_day[d][1] for d in DAYS})
            if best is None or cand[0] < best[0]:
                best = cand
    return best   # (cost, k, h, periods{day: {subj: p}})


def full_metrics(assign, tt):
    cost, k, h, per = tt
    ds = day_sets(assign)
    dist = distribution(assign)
    m = {}
    m["dist"] = dist
    m["three"] = {d: sum(n for c, n in COMBOS if len(set(c) & ds[d]) == 3) for d in DAYS}   # 전체 176명 기준
    m["three_nonex"] = dict(m["three"])
    m["four"] = {d: sum(n for c, n in COMBOS if len(set(c) & ds[d]) >= 4) for d in DAYS}
    m["zero"] = {d: sum(n for c, n in COMBOS if len(set(c) & ds[d]) == 0) for d in DAYS}
    m["tue3_all"] = sum(n for c, n in COMBOS if len(set(c) & ds["화"]) >= 3)
    m["tue3_nonex"] = sum(n for c, n in COMBOS if len(set(c) & ds["화"]) >= 3 and c != EXEMPT_ALL)
    m["max3"] = max(m["three"].values())
    m["sum3"] = sum(m["three"].values())
    # 예외
    exc = [("박현수", "통합사회2", "월", 2)] if G1_MODE == "A" else []
    for s, who in (("J", "배태안"), ("O", "손경준")):
        d = assign[SUBJ_IDX[s]]
        if d in ("월", "화"):
            exc.append((who, NAMES[s], d, per[d][s]))
    m["exc"] = exc
    # 교사 하루 2과목 (1학년 포함)
    t2 = []
    for d in DAYS:
        load = {}
        for s in ds[d]:
            for t in TEACHERS[s]:
                load.setdefault(t, []).append(f"{s} {NAMES[s]}({per[d][s]}교시)")
        for g, gp in g1_slots(d, k, h):
            for t in G1[g]:
                load.setdefault(t, []).append(f"{g}({gp}교시)")
        for t, L in load.items():
            if len(L) >= 2:
                t2.append((d, t, L))
    m["teacher2"] = t2
    # 계열
    dup = []
    for d in DAYS:
        for a, b in itertools.combinations(sorted(ds[d]), 2):
            if FIELD[a] == FIELD[b]:
                dup.append((d, a, b, FIELD[a], overlap(a, b)))
    m["dup"] = dup
    m["dup_n"] = sum(x[4] for x in dup)
    # ABC
    m["abc_days"] = {s: assign[SUBJ_IDX[s]] for s in "ABC"}
    m["abc_ok"] = len(set(m["abc_days"].values())) == 3
    # 연속
    cons = []
    trip = []
    for d in DAYS:
        for x in consecutive_cost(d, per[d]):
            cons.append((d,) + x)
        for x in triple_consecutive(d, per[d]):
            trip.append((d,) + x)
    m["consec"] = cons
    m["consec_n"] = sum(x[5] for x in cons)
    m["triple"] = trip
    # 시험실
    rooms = {}
    for d in DAYS:
        bp = {}
        for s, p in per[d].items():
            bp.setdefault(p, []).append(s)
        for p, L in bp.items():
            rooms[(d, p)] = sum(math.ceil(enrol(s) / 20) for s in L)
    m["rooms"] = rooms
    m["rooms_max"] = max(rooms.values())
    # 1학년 교시와 어긋남
    dev = []
    for d in DAYS:
        used = set(per[d].values())
        off = used - STD[d]
        if off:
            dev.append((d, sorted(off)))
    m["dev"] = dev
    m["thu_p1"] = 1 in set(per["목"].values())
    m["k"], m["h"] = k, h
    m["sci_day"] = ("금" if k else "월") if G1_MODE == "A" else "월"
    return m


def summary_row(assign, tt, m):
    ds = day_sets(assign)
    return dict(
        shape="·".join(str(len(units_of(ds[d], True, True))) for d in DAYS),
        days={d: "".join(sorted(ds[d])) for d in DAYS},
        exc=len(m["exc"]), tue3=m["tue3_nonex"], tue3_all=m["tue3_all"], max3=m["max3"], sum3=m["sum3"],
        three=tuple(m["three_nonex"][d] for d in DAYS), four=sum(m["four"].values()),
        dup_cnt=len(m["dup"]), dup_n=m["dup_n"], consec_n=m["consec_n"], consec_cnt=len(m["consec"]),
        dev=len(m["dev"]), dev_detail=m["dev"], thu_p1=m["thu_p1"], t2=len(m["teacher2"]),
        periods={d: dict(sorted(tt[3][d].items(), key=lambda x: x[1])) for d in DAYS}, k=tt[1], h=tt[2],
    )
