# -*- coding: utf-8 -*-
"""시간표 1개를 §4 제약 전 항목에 대해 점검하고 분포를 계산한다."""
import sys, math
sys.path.insert(0, '.')
from data import *
from itertools import combinations
from collections import defaultdict, Counter

CAP = {"목": 3, "금": 3, "월": 3, "화": 2}  # 하루 4과목 금지, 마지막날 3과목 금지

def students_both(a, b):
    return sum(n for c, n in COMBOS if a in c and b in c)

def rooms(s):
    return math.ceil(ENROLL[s] / 20)

def day_dist(S):
    """S: 그날 2학년 과목 집합. {횟수: 학생수} 와 조합별 횟수."""
    dist = Counter(); per = {}
    for c, n in COMBOS:
        k = len(set(c) & S); dist[k] += n; per[c] = k
    return dist, per

def evaluate(plan, g1_science_day="화"):
    g2, g1 = plan["g2"], plan["g1"]
    R = {}
    # 교시별 과목(1·2학년)
    slot = defaultdict(list)
    for s, (d, p) in g2.items(): slot[(d, p)].append(("2", s))
    for s, (d, p) in g1.items(): slot[(d, p)].append(("1", s))
    # 1. 같은 교시 동시 응시자
    v = []
    for (d, p), L in slot.items():
        g2s = [s for g, s in L if g == "2"]
        for a, b in combinations(g2s, 2):
            k = students_both(a, b)
            if k: v.append(f"{d}{p}교시 {a}+{b} {k}명")
    R["동시응시"] = v
    # 2. 같은 교시 담당교사 중복
    v = []
    for (d, p), L in slot.items():
        seen = defaultdict(list)
        for g, s in L:
            for t in (TEACHERS[s] if g == "2" else G1[s]): seen[t].append(s)
        for t, ss in seen.items():
            if len(ss) > 1: v.append(f"{d}{p}교시 {t}: {'+'.join(ss)}")
    R["교사동시"] = v
    # 3. 목요일 1학년 수업 충돌
    v = []
    for s, (d, p) in g2.items():
        if d == "목":
            hit = set(TEACHERS[s]) & THU_G1_CLASS[p]
            if hit: v.append(f"목{p}교시 {s} {','.join(sorted(hit))}")
    R["목수업충돌"] = v
    # 4. 전이슬
    d, p = g2["P"]
    R["전이슬"] = [f"{d}{p}교시"] if (d, p) in JEON_AWAY else []
    # 5. 3학년 담임 월·화
    exc, hard = [], []
    for s, (d, p) in list(g2.items()) + list(g1.items()):
        if d in ("월", "화"):
            ts = TEACHERS[s] if s in TEACHERS else G1[s]
            for t in ts:
                if t in HR3:
                    (exc if p == 2 else hard).append(f"{t} {d}{p}교시 {s}")
    R["담임예외"] = exc; R["담임위반"] = hard
    # 6. 교사 하루 2과목
    v = []
    byday = defaultdict(lambda: defaultdict(list))
    for s, (d, p) in g2.items():
        for t in TEACHERS[s]: byday[d][t].append(s)
    for s, (d, p) in g1.items():
        for t in G1[s]: byday[d][t].append(s)
    for d in DAYS:
        for t, ss in byday[d].items():
            if len(ss) > 1: v.append(f"{d} {t}: {'+'.join(ss)}")
    R["교사하루2"] = v
    # 7. 같은 날 같은 계열
    v = []; tot = 0
    for d in DAYS:
        ss = sorted(s for s, (dd, p) in g2.items() if dd == d)
        for a, b in combinations(ss, 2):
            if SERIES[a] == SERIES[b]:
                k = students_both(a, b); tot += k
                v.append(f"{d} {SERIES[a]}({a}+{b}) {k}명")
    R["계열중복"] = v; R["계열중복인원"] = tot
    # 8. A·B·C
    abc = [g2[s][0] for s in "ABC"]
    R["ABC다른날"] = len(set(abc)) == 3
    # 9. 분포
    dist = {}; viol4 = []; violT = []; viol0 = []
    for d in DAYS:
        S = {s for s, (dd, p) in g2.items() if dd == d}
        dd_, per = day_dist(S); dist[d] = dd_
        for c, n in COMBOS:
            k = per[c]
            if k == 0: viol0.append((d, c, n))
            if k >= 4: viol4.append((d, c, n))
            if d == "화" and k >= 3: violT.append((d, c, n))
    R["분포"] = dist
    # 면제 적용: 체육부 2명(4과목·화3과목 면제), 도움반은 조합 식별 불가 → 미적용
    def apply_exempt(lst):
        out = []
        for d, c, n in lst:
            m = n - sum(1 for e in EXEMPT.values() if e["type"] == "체육부" and e["combo"] == c)
            if m > 0: out.append((d, c, m))
        return out
    R["4과목"] = apply_exempt(viol4); R["4과목_전체"] = viol4
    R["화3과목"] = apply_exempt(violT); R["화3과목_전체"] = violT
    R["0과목"] = viol0
    R["마지막날국어"] = [s for s in ["A"] if g2[s][0] == "화"] + [s for s in ["공통국어2"] if g1[s][0] == "화"]
    # 10. 연속 교시
    v = []
    for d in DAYS:
        for p, q in CONSEC_PAIRS:
            A_ = [s for g, s in slot.get((d, p), []) if g == "2"]
            B_ = [s for g, s in slot.get((d, q), []) if g == "2"]
            for a in A_:
                for b in B_:
                    v.append(f"{d} {p}-{q}교시 {a}+{b} {students_both(a,b)}명")
    R["연속교시"] = v
    # 11. 교시별 시험실
    v = {}
    for (d, p), L in slot.items():
        r = sum(rooms(s) for g, s in L if g == "2")
        if r: v[(d, p)] = r
    R["시험실"] = v; R["시험실초과"] = [k for k, r in v.items() if r > 9]
    # 3과목 인원
    R["3과목"] = {d: dist[d][3] for d in DAYS}
    R["3과목최대"] = max(R["3과목"].values()); R["3과목합"] = sum(R["3과목"].values())
    # 1학년 날짜 규칙
    v = []
    for s, d in G1_FIXED_DAY.items():
        if g1[s][0] != d: v.append(f"{s} {g1[s][0]}≠{d}")
    for d in ("금", "월", "화"):
        n = sum(1 for s, (dd, p) in g1.items() if dd == d)
        if n != 2: v.append(f"1학년 {d} {n}과목")
    R["1학년규칙"] = v
    return R

def fmt_report(plan, R, title):
    g2, g1 = plan["g2"], plan["g1"]
    L = [f"### {title}", ""]
    periods = sorted({p for d, p in list(g2.values()) + list(g1.values())})
    L.append("| 교시 | 시각 | " + " | ".join(DATES[d] for d in DAYS) + " |")
    L.append("|---|---|" + "---|" * 4)
    for p in periods:
        row = []
        for d in DAYS:
            cell = [s for s, (dd, pp) in g1.items() if (dd, pp) == (d, p)]
            cell += [f"{s} {NAME[s]}" for s in SUBJECTS if g2[s] == (d, p)]
            row.append(" / ".join(cell) if cell else "—")
        L.append(f"| {p} | {PERIOD_TIME[p]} | " + " | ".join(row) + " |")
    L.append("")
    L.append("2학년 응시 횟수 분포 (명)")
    L.append("")
    L.append("| 횟수 | " + " | ".join(DAYS) + " |")
    L.append("|---|" + "---|" * 4)
    for k in range(5):
        L.append(f"| {k}회 | " + " | ".join(str(R['분포'][d][k]) for d in DAYS) + " |")
    L.append("")
    def ok(lst): return "OK" if not lst else f"**{len(lst)}건** " + "; ".join(lst)
    L.append("| 점검 항목 | 결과 |")
    L.append("|---|---|")
    L.append(f"| 같은 교시 동시 응시자 0명 | {ok(R['동시응시'])} |")
    L.append(f"| 같은 교시 담당교사 중복 0건 | {ok(R['교사동시'])} |")
    L.append(f"| 목요일 1학년 수업 충돌 0건 | {ok(R['목수업충돌'])} |")
    L.append(f"| 전이슬 화·목 1~4교시 저촉 0건 | {ok(R['전이슬'])} |")
    L.append(f"| 3학년 담임 월·화 배치(2교시 외) 0건 | {ok(R['담임위반'])} |")
    L.append(f"| 3학년 담임 예외(월·화 2교시) | {len(R['담임예외'])}건: " + "; ".join(R['담임예외']) + " |")
    L.append(f"| 교사 하루 2과목 | {ok(R['교사하루2'])} |")
    L.append(f"| 같은 날 같은 계열 | {ok(R['계열중복'])} (합 {R['계열중복인원']}명) |")
    L.append(f"| A·B·C 서로 다른 날 | {'OK' if R['ABC다른날'] else '**위반**'} |")
    L.append(f"| 마지막날 국어 없음 | {ok(R['마지막날국어'])} |")
    L.append(f"| 마지막날 3과목 0명 | {ok([f'{c} {n}명' for d,c,n in R['화3과목']])} |")
    L.append(f"| 4과목 0명 | {ok([f'{d} {c} {n}명' for d,c,n in R['4과목']])} |")
    L.append(f"| 0과목 0명 | {ok([f'{d} {c} {n}명' for d,c,n in R['0과목']])} |")
    L.append(f"| 연속 교시 배치 | {ok(R['연속교시'])} |")
    rs = ", ".join(f"{d}{p}={r}" for (d, p), r in sorted(R['시험실'].items(), key=lambda t: (DAYS.index(t[0][0]), t[0][1])))
    L.append(f"| 교시별 시험실 ≤ 9실 | {'OK' if not R['시험실초과'] else '**초과**'} ({rs}) |")
    L.append(f"| 1학년 일자 규칙 | {ok(R['1학년규칙'])} |")
    L.append(f"| 하루 3과목 인원 | " + " / ".join(f"{d} {R['3과목'][d]}" for d in DAYS) + f" (최대 {R['3과목최대']}, 합 {R['3과목합']}) |")
    return "\n".join(L)

if __name__ == "__main__":
    pass
