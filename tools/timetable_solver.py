#!/usr/bin/env python3
"""2026학년도 2학기 2차 정기시험 2학년 시간표 전수 탐색 솔버.

16과목을 4일(목·금·월·화)에 배정하는 모든 경우를 열거한다. 동시 시행은 겹침 0인
두 쌍(O+J, N+P)만 가능하므로 기본 모형은 14개 유닛(단일 12 + 쌍 2)을
목4·금4·월4·화2 슬롯에 나누는 분할 문제다. `--extra`로 3·6교시 개방 시나리오도 돌린다.

사용법:
    python3 tools/timetable_solver.py                 # 기본 시나리오 + 증명용 사례 분석
    python3 tools/timetable_solver.py --extra         # 3·6교시 개방 시나리오까지
    python3 tools/timetable_solver.py --json out.json
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import Counter

import numpy as np

# ---------------------------------------------------------------------------
# 1. 데이터 (문제지 §2·§3·§4·§5)
# ---------------------------------------------------------------------------
RAW = """
ABCDEFGH 8
ABCDEFGJ 5
ABCDEFHN 1
ABCDEFIK 4
ABCDEFIM 2
ABCDEFIN 1
ABCDEFIO 2
ABCDEFJK 1
ABCDEFKL 1
ABCDEFLM 2
ABCDEFNO 1
ABCDEFOP 1
ABCDEGHJ 3
ABCDEGHN 1
ABCDEGJK 2
ABCDEGJL 2
ABCDEGJM 1
ABCDEGJN 1
ABCDEGJP 1
ABCDEHJN 1
ABCDEIJK 1
ABCDEIJL 1
ABCDEIJP 1
ABCDEIKL 8
ABCDEIKM 1
ABCDEIKO 2
ABCDEIKP 2
ABCDEILN 1
ABCDEILO 7
ABCDEILP 1
ABCDEIMN 2
ABCDEIMO 1
ABCDEIMP 3
ABCDEIOP 4
ABCDEJKP 1
ABCDEJMP 1
ABCDEKLM 3
ABCDEKLN 3
ABCDEKLO 2
ABCDEKOP 1
ABCDELMO 1
ABCDFGHI 1
ABCDFGHJ 18
ABCDFGHL 1
ABCDFGHM 10
ABCDFGHN 3
ABCDFGJM 2
ABCDFGKO 1
ABCDFHIM 1
ABCDFHJM 1
ABCDFHMN 1
ABCDFIKO 1
ABCDFILM 2
ABCDFILO 1
ABCDFKLN 2
ABCDFLNO 1
ABCDGHIL 1
ABCDGHIN 1
ABCDGHJL 1
ABCDGHJN 8
ABCDGHJP 1
ABCDGHKM 2
ABCDGHMN 5
ABCDGIJL 1
ABCDGJKM 2
ABCDGJKN 1
ABCDHIMN 1
ABCDHIMO 1
ABCDHKOP 1
ABCDIJKN 1
ABCDIJMN 1
ABCDIKLM 1
ABCDIKLO 2
ABCDIKOP 1
ABCDKLNO 1
ABCEFHIO 1
ABCEFIKL 1
ABCEFIKO 1
ABCEFILM 1
ABCEFILO 1
ABCEIKMP 1
ABCFHIMN 1
ABCFILMN 1
ABCFKLNO 1
"""

SUBJECTS = "ABCDEFGHIJKLMNOP"
NAMES = {
    "A": "독서와작문", "B": "미적분I", "C": "영어II", "D": "확률과통계",
    "E": "인문학과윤리", "F": "인공지능기초", "G": "화학반응의세계", "H": "역학과에너지",
    "I": "한국지리탐구", "J": "세포와물질대사", "K": "경제", "L": "심화일본어",
    "M": "지구시스템과학", "N": "프로그래밍", "O": "동아시아역사기행", "P": "심화중국어",
}
TRACK = {
    "A": "국어", "B": "수학", "C": "영어", "D": "수학", "E": "사회", "F": "정보",
    "G": "과학", "H": "과학", "I": "사회", "J": "과학", "K": "사회", "L": "제2외국어",
    "M": "과학", "N": "정보", "O": "사회", "P": "제2외국어",
}
TEACHERS = {
    "A": ["한영희", "박우정", "임서정"], "B": ["김강미", "구성희", "류진표"],
    "C": ["남혜은", "손유진", "이민경"], "D": ["송재근", "구성희"],
    "E": ["김미애", "김경서"], "F": ["김다은"], "G": ["김은경"], "H": ["최진호"],
    "I": ["노석환"], "J": ["배태안"], "K": ["김경민"], "L": ["신향숙"], "M": ["조세라"],
    "N": ["송경희"], "O": ["정인광", "손경준"], "P": ["전이슬"],
}
G1 = {  # 1학년 과목: (요일, 담당)
    "공통영어2": ("금", ["강승희", "이바다"]),
    "한국사2": ("금", ["정인광", "손경준"]),
    "통합사회2": ("월", ["김미애", "노석환", "박현수", "윤정희"]),
    "공통수학2": ("월", ["김순선", "최지혜"]),
    "공통국어2": ("화", ["김태현", "곽준철"]),
    "통합과학2": ("화", ["최진호", "이호성", "박경애", "조세라"]),
}
G1_SLOTS = {"금": [2, 7], "월": [2, 7], "화": [2, 4]}
THU_CLASS = {  # 목요일 1학년 수업 담당 (교시 -> 교사)
    1: "윤정희 손경준 곽준철 박경애 이바다 김미애 김태현 최지혜",
    2: "이바다 김태현 강승희 강진원 손경준 조세라 유경희 최가연",
    3: "유경희 문준성 박경애 곽준철 최지혜 강승희 김순선 최진호",
    4: "최지혜 최진호 김미애 노석환 최가연 이바다 박경애 손경준",
    5: "김태현 강승희 김순선 이바다 박현수 곽준철 정인광 유경희",
    6: "조세라 최지혜 문준성 유경희 곽준철 박경애 강승희 김태현",
    7: "이호성 윤정희 석경훈 김순선 정인광 최지혜 최가연 박경애",
}
THU_CLASS = {p: set(s.split()) for p, s in THU_CLASS.items()}
HOMEROOM3 = {"최광진", "배태안", "박현수", "김영주", "변영민", "남재현", "손경준", "김수현", "정재훈"}
FULL = ("A", "B", "C")
DAYS = ["목", "금", "월", "화"]
BASE_PERIODS = {"목": [2, 4, 5, 7], "금": [2, 4, 5, 7], "월": [2, 4, 5, 7], "화": [2, 4]}

combos: list[tuple[str, int]] = []
for line in RAW.strip().splitlines():
    code, n = line.split()
    combos.append((code, int(n)))
assert len(combos) == 84 and sum(n for _, n in combos) == 176
for code, _ in combos:
    assert len(code) == 8 and len(set(code)) == 8

enroll = Counter()
for code, n in combos:
    for s in code:
        enroll[s] += n


def overlap(*subs: str) -> int:
    return sum(n for code, n in combos if all(s in code for s in subs))


def teachers_of(unit: str) -> set[str]:
    t: set[str] = set()
    for s in unit:
        t |= set(TEACHERS[s])
    return t


# ---------------------------------------------------------------------------
# 2. 모형: 유닛 집합 + 요일별 교시
# ---------------------------------------------------------------------------
class Model:
    def __init__(self, units: list[str], periods: dict[str, list[int]]):
        self.units = units
        self.uidx = {u: i for i, u in enumerate(units)}
        self.periods = periods
        self.n = len(units)
        ns = 1 << self.n
        s_all = np.arange(ns, dtype=np.int64)

        def unit_mask(code: str) -> int:
            m = 0
            for u in units:
                if any(s in code for s in u):
                    m |= 1 << self.uidx[u]
            return m

        cm = np.array([unit_mask(c) for c, _ in combos], dtype=np.int64)
        cn = np.array([n for _, n in combos], dtype=np.int64)
        self.dist = np.zeros((ns, 9), dtype=np.int64)
        for ci in range(len(combos)):
            k = self._popcount(s_all & cm[ci])
            np.add.at(self.dist, (s_all, k), cn[ci])
        self.zero = self.dist[:, 0]
        self.three = self.dist[:, 3]
        self.four = self.dist[:, 4:].sum(axis=1)
        # 계열 중복 연인원
        self.track_pairs = []
        self.track_dup = np.zeros(ns, dtype=np.int64)
        for u, v in itertools.combinations(units, 2):
            tot = sum(overlap(s, t) for s in u for t in v if TRACK[s] == TRACK[t])
            if tot:
                self.track_pairs.append((u, v, tot))
                i, j = self.uidx[u], self.uidx[v]
                sel = (((s_all >> i) & 1) & ((s_all >> j) & 1)).astype(bool)
                self.track_dup[sel] += tot
        self.allowed = {(u, d): self._allowed_periods(u, d) for u in units for d in DAYS}
        self._feas: dict[tuple[int, int], bool] = {}

    @staticmethod
    def _popcount(a: np.ndarray) -> np.ndarray:
        a = a.copy()
        c = np.zeros_like(a)
        while a.any():
            c += a & 1
            a >>= 1
        return c

    def bit(self, u: str) -> int:
        return 1 << self.uidx[u]

    def names(self, mask: int) -> list[str]:
        return [u for u in self.units if (mask >> self.uidx[u]) & 1]

    def mask(self, us) -> int:
        return sum(self.bit(u) for u in us)

    # --- 절대 제약 2·3·4·5: 교시 배치 ---------------------------------------
    def _allowed_periods(self, unit: str, day: str) -> list[int]:
        teachers = teachers_of(unit)
        out = []
        for p in self.periods[day]:
            ok = True
            if day == "목" and teachers & THU_CLASS[p]:
                ok = False  # 4. 목요일 1학년 수업 충돌
            if "P" in unit and day in ("화", "목") and p <= 4:
                ok = False  # 3. 전이슬 출장
            if day in ("월", "화") and teachers & HOMEROOM3 and p != 2:
                ok = False  # 5. 3학년 담임 월·화 예외는 2교시만
            if day == "월" and p == 2 and teachers & set(G1["통합사회2"][1]):
                ok = False  # 2. 박현수 때문에 통합사회2는 월 2교시 고정
            if ok:
                out.append(p)
        return out

    def day_schedule(self, units: list[str], day: str, prefer: dict | None = None):
        """units를 day의 교시에 배치하고 1학년 과목 교시까지 정한다. 불가면 None."""
        ps = self.periods[day]
        if len(units) > len(ps):
            return None
        g1 = [k for k, (d, _) in G1.items() if d == day]
        perms = list(itertools.permutations(ps, len(units)))
        if prefer:  # 선호 배치를 먼저 시도
            pref = tuple(prefer.get(u) for u in units)
            if all(p is not None for p in pref) and pref in perms:
                perms.remove(pref)
                perms.insert(0, pref)
        for perm in perms:
            if any(perm[i] not in self.allowed[(u, day)] for i, u in enumerate(units)):
                continue
            assign = dict(zip(units, perm))
            if day == "목":
                return {"g2": assign, "g1": {}}
            for g1perm in itertools.permutations(G1_SLOTS[day]):
                g1assign = dict(zip(g1, g1perm))
                if day == "월" and g1assign["통합사회2"] != 2:
                    continue
                clash = any(
                    p == gp and teachers_of(u) & set(G1[gsub][1])
                    for gsub, gp in g1assign.items()
                    for u, p in assign.items()
                )
                if not clash:
                    return {"g2": assign, "g1": g1assign}
        return None

    def feasible(self, mask: int, di: int) -> bool:
        key = (mask, di)
        if key not in self._feas:
            self._feas[key] = self.day_schedule(self.names(mask), DAYS[di]) is not None
        return self._feas[key]

    # --- 평가 -------------------------------------------------------------
    def evaluate(self, day_masks: list[int], relax: set[str]) -> dict | None:
        """절대 제약 + 강한 선호 점검. relax에 든 선호는 위반을 허용(기록만)."""
        if any(self.zero[m] for m in day_masks):
            return None  # 절대 6
        if any(not self.feasible(m, di) for di, m in enumerate(day_masks)):
            return None  # 절대 2~5
        # 동시 시행 쌍 외의 같은 교시 겹침은 유닛 정의상 없음 (절대 1)
        three = [int(self.three[m]) for m in day_masks]
        four = [int(self.four[m]) for m in day_masks]
        viol = []
        if any(four):
            viol.append("4회")
        if three[3]:
            viol.append("화3회")
        t9 = []
        b = self.bit
        has = lambda u, di: bool(day_masks[di] & b(u)) if u in self.uidx else False  # noqa: E731
        if has("E", 2):
            t9.append("김미애: E + 통합사회2 (월)")
        if has("I", 2):
            t9.append("노석환: I + 통합사회2 (월)")
        if has("H", 3):
            t9.append("최진호: H + 통합과학2 (화)")
        if has("M", 3):
            t9.append("조세라: M + 통합과학2 (화)")
        for di in range(4):
            if has("B", di) and has("D", di):
                t9.append(f"구성희: B + D ({DAYS[di]})")
        o_unit = "OJ" if "OJ" in self.uidx else "O"
        if has(o_unit, 1):
            t9.append("정인광·손경준: O + 한국사2 (금)")
        if t9:
            viol.append("교사2과목")
        for m in day_masks:
            if bin(m & self.mask(FULL)).count("1") > 1:
                viol.append("ABC같은날")
                break
        if any(v not in relax for v in viol):
            return None
        dup = sum(int(self.track_dup[m]) for m in day_masks)
        exceptions = ["박현수(월 2교시, 통합사회2)"]
        for u in ("OJ", "O", "J"):
            if u in self.uidx:
                for di in (2, 3):
                    if has(u, di):
                        for t in sorted(teachers_of(u) & HOMEROOM3):
                            exceptions.append(f"{t}({DAYS[di]} 2교시, {u})")
        return {
            "days": day_masks,
            "three": three,
            "four": four,
            "max3": max(three),
            "total3": sum(three),
            "dup": dup,
            "exceptions": len(exceptions),
            "exception_list": exceptions,
            "earliness": sum(i * t for i, t in enumerate(three)),
            "viol": viol,
            "t9": t9,
        }

    # --- 전수 탐색 ---------------------------------------------------------
    def search(self, relax: set[str] = frozenset()) -> tuple[list[dict], int]:
        """목·금·월·화 순으로 유닛을 나누되 화요일부터 가지치기한다.

        각 요일 집합은 (a) 0과목 학생 0명, (b) 교시 배치 가능, (c) 4회 0명(완화 시 생략)
        을 만족해야 하며, 이 조건들은 유닛을 추가해도 풀리지 않으므로 중간 가지치기가 안전하다.
        반환: (가능해 목록, 방문한 완전 분할 수)
        """
        caps = [len(self.periods[d]) for d in DAYS]
        order = [3, 0, 1, 2]  # 화 → 목 → 금 → 월
        results: list[dict] = []
        visited = 0

        def ok_partial(m: int, di: int) -> bool:
            if self.zero[m]:
                return False
            if "4회" not in relax and self.four[m]:
                return False
            if di == 3 and "화3회" not in relax and self.three[m]:
                return False
            return self.feasible(m, di)

        def rec(k: int, remaining: list[int], chosen: dict[int, int]):
            nonlocal visited
            di = order[k]
            if k == len(order) - 1:
                if len(remaining) > caps[di]:
                    return
                m = sum(1 << i for i in remaining)
                visited += 1
                if ok_partial(m, di):
                    r = self.evaluate([chosen[0], chosen[1], m, chosen[3]], relax)
                    if r:
                        results.append(r)
                return
            later_cap = sum(caps[order[j]] for j in range(k + 1, len(order)))
            for size in range(max(0, len(remaining) - later_cap), min(caps[di], len(remaining)) + 1):
                for pick in itertools.combinations(remaining, size):
                    m = sum(1 << i for i in pick)
                    if not ok_partial(m, di):
                        continue
                    chosen[di] = m
                    rec(k + 1, [i for i in remaining if i not in pick], chosen)
            chosen.pop(di, None)

        rec(0, list(range(self.n)), {})
        return results, visited

    def partition_count(self) -> int:
        """가지치기 없이 열거해야 할 완전 분할 수(탐색 공간 크기)."""
        caps = [len(self.periods[d]) for d in DAYS]
        total = 0
        for sizes in itertools.product(*[range(c + 1) for c in caps]):
            if sum(sizes) != self.n:
                continue
            k = math.factorial(self.n)
            for s in sizes:
                k //= math.factorial(s)
            total += k
        return total


def sort_key(r):
    return (r["max3"], r["dup"], r["exceptions"], r["earliness"], r["total3"])


# ---------------------------------------------------------------------------
# 3. 보고용 출력
# ---------------------------------------------------------------------------
def describe(model: Model, r: dict, prefer: dict | None = None) -> str:
    out = []
    masks = r["days"]
    sched = {}
    for di, m in enumerate(masks):
        sched[DAYS[di]] = model.day_schedule(model.names(m), DAYS[di], (prefer or {}).get(DAYS[di]))
    out.append("### 배치표")
    rows = {p: {} for p in range(1, 8)}
    for d in DAYS:
        for u, p in sched[d]["g2"].items():
            rows[p][d] = " + ".join(f"{s} {NAMES[s]}" for s in u)
        for g, p in sched[d]["g1"].items():
            rows[p][d] = rows[p].get(d, "—") + f" / *1학년 {g}*"
    out.append("| 교시 | " + " | ".join(DAYS) + " |")
    out.append("|---|" + "---|" * 4)
    for p in range(1, 8):
        if any(rows[p].get(d) for d in DAYS):
            out.append(f"| {p} | " + " | ".join(rows[p].get(d, "—") for d in DAYS) + " |")
    out.append("")
    out.append("### 응시 횟수 분포")
    out.append("| 횟수 | " + " | ".join(DAYS) + " |")
    out.append("|---|" + "---|" * 4)
    for k in range(5):
        out.append(f"| {k}회 | " + " | ".join(str(int(model.dist[m][k])) for m in masks) + " |")
    out.append("")
    out.append("### 점검")
    # 같은 교시 겹침
    pair_overlaps = []
    for d in DAYS:
        for u in sched[d]["g2"]:
            if len(u) > 1:
                pair_overlaps.append((d, sched[d]["g2"][u], u, overlap(*u)))
    out.append("- 같은 교시 동시 응시자: " + ", ".join(f"{d} {p}교시 {u} {o}명" for d, p, u, o in pair_overlaps))
    # 교사 중복(같은 교시)
    clashes = []
    for d in DAYS:
        per: dict[int, list[tuple[str, set]]] = {}
        for u, p in sched[d]["g2"].items():
            per.setdefault(p, []).append((u, teachers_of(u)))
        for g, p in sched[d]["g1"].items():
            per.setdefault(p, []).append((g, set(G1[g][1])))
        for p, items in per.items():
            for (a, ta), (b, tb) in itertools.combinations(items, 2):
                if ta & tb:
                    clashes.append(f"{d} {p}교시 {a}/{b}: {ta & tb}")
    out.append(f"- 같은 교시 담당교사 중복: {len(clashes)}건 {clashes}")
    thu = [f"{u} {p}교시 {teachers_of(u) & THU_CLASS[p]}" for u, p in sched['목']['g2'].items() if teachers_of(u) & THU_CLASS[p]]
    out.append(f"- 목요일 1학년 수업 충돌: {len(thu)}건 {thu}")
    p_slot = [(d, p) for d in DAYS for u, p in sched[d]["g2"].items() if "P" in u]
    out.append(f"- 전이슬(P) 배치: {p_slot} → 화·목 1~4교시 저촉 {'없음' if all(not (d in ('화','목') and p <= 4) for d, p in p_slot) else '있음'}")
    out.append(f"- 3학년 담임 월·화 배치: {r['exceptions']}건 {r['exception_list']}")
    # 교사 하루 2과목
    out.append(f"- 교사 하루 2과목: {len(r['t9'])}건 {r['t9']}")
    dups = []
    for di, m in enumerate(masks):
        for u, v, tot in model.track_pairs:
            if m & model.bit(u) and m & model.bit(v):
                dups.append(f"{DAYS[di]} {TRACK[u[0]] if TRACK[u[0]]==TRACK[v[0]] else '혼합'}({u}+{v}) {tot}명")
    out.append(f"- 같은 날 같은 계열: {len(dups)}건, 연인원 {r['dup']}명 {dups}")
    abc_days = {s: DAYS[di] for di, m in enumerate(masks) for s in FULL if m & model.bit(s)}
    out.append(f"- A·B·C 요일: {abc_days} → {'서로 다른 날' if len(set(abc_days.values()))==3 else '같은 날 있음'}")
    rooms = []
    for d in DAYS:
        for u, p in sorted(sched[d]["g2"].items(), key=lambda x: x[1]):
            n_rooms = sum(math.ceil(enroll[s] / 20) for s in u)
            rooms.append(f"{d}{p}:{n_rooms}")
    out.append(f"- 교시별 시험실 소요(1실 20명, 최대 9실): {' '.join(rooms)} → 최대 {max(int(x.split(':')[1]) for x in rooms)}실")
    out.append(f"- 4회 응시: {r['four']}, 하루 3회: {r['three']} (최대 {r['max3']}, 합계 {r['total3']})")
    return "\n".join(out)


def explain_structure(model: Model) -> str:
    """전수 탐색 결과를 사람이 따라갈 수 있는 사례 분석으로 풀어 쓴다 (기본 시나리오 전용).

    전제: 절대 제약 1~6 + 강한 선호 7(4회 0)·8(화 3회 0)·9(교사 하루 2과목 0)·10(A·B·C 다른 날).
    """
    out = []
    b = model.bit
    nonfull = [u for u in model.units if u not in FULL]
    # 1) 화요일 2유닛이 전원을 덮으려면
    cover2 = [(u, v) for u, v in itertools.combinations(model.units, 2) if model.zero[b(u) | b(v)] == 0]
    no_full = [(u, v) for u, v in cover2 if u not in FULL and v not in FULL]
    nonD = [c for c, _ in combos if "D" not in c]
    out.append(f"1) 화요일은 2슬롯이므로 두 유닛이 전원 176명을 덮어야 함(0회 금지). 전원을 덮는 유닛 쌍 {len(cover2)}개는 모두 A·B·C 중 하나를 포함"
               f"(A·B·C 없는 쌍: {no_full or '없음'}). 근거: D 없는 학생 9명의 조합 {nonD} 전부를 D 외 한 과목으로 덮을 수 없음.")
    out.append("   따라서 화 = {전원 과목 1개 + 다른 유닛 1개}. A·B·C가 서로 다른 날이어야 하므로 목·금·월 중 정확히 하루는 전원 과목 없이 비전원 유닛 4개만으로 전원을 덮어야 함(이하 '개방일').")
    # 2) 개방일 후보
    cover4 = []
    for pick in itertools.combinations(nonfull, 4):
        m = model.mask(pick)
        if model.zero[m] == 0:
            cover4.append((pick, int(model.four[m])))
    ok4 = [p for p, f in cover4 if f == 0]
    out.append(f"2) 비전원 11유닛의 4-부분집합 {math.comb(11, 4)}개 중 전원을 덮는 것은 {len(cover4)}개, 그중 넷 다 듣는 학생(=4회 응시)이 0명인 것은 {len(ok4)}개: {ok4}")
    # 3) 각 개방일 후보에 대해 나머지 7유닛 = 화요일 짝 Y + 전원 과목과 묶일 3유닛 두 묶음
    out.append("3) 개방일 후보별로 남은 7유닛을 화요일 짝 Y(1개) + 전원 과목과 함께 갈 3유닛 묶음 2개로 나눔. 전원 과목이 있는 날의 3유닛은 셋 다 듣는 학생이 있으면 4회가 되므로 0명이어야 함.")
    survivors = []
    for od in ok4:
        rest = [u for u in nonfull if u not in od]
        splits = []
        for y in rest:
            others = [u for u in rest if u != y]
            for t1 in itertools.combinations(others, 3):
                t2 = tuple(u for u in others if u not in t1)
                if t1 < t2 and model.four[model.mask(t1) | b("A")] == 0 and model.four[model.mask(t2) | b("A")] == 0:
                    splits.append((y, t1, t2))
        out.append(f"   개방일 {od}: 70가지 분할 중 두 묶음 모두 4회 0명인 분할 {len(splits)}개 {splits}")
        for y, t1, t2 in splits:
            # 요일 배정: 개방일·묶음1·묶음2를 목·금·월에, Y를 화에. 절대 제약 + 선호 9 점검
            for perm in itertools.permutations([od, t1, t2]):
                masks = [model.mask(perm[0]), model.mask(perm[1]), model.mask(perm[2]), model.mask((y,))]
                # 전원 과목 붙이기: 묶음들과 Y에 A·B·C를 어떤 순서로 붙여도 지표는 같으므로 하나만 시도(B≠D만 피함)
                slots = [i for i in range(3) if perm[i] != od] + [3]
                found = None
                for fp in itertools.permutations(FULL):
                    ms = list(masks)
                    for i, f in zip(slots, fp):
                        ms[i] |= b(f)
                    r = model.evaluate(ms, set())
                    if r:
                        found = r
                        break
                if found:
                    survivors.append(found)
    out.append(f"4) 요일 제약(OJ 목 불가·금 불가, NP 화 불가, E·I 월 불가, H·M 화 불가, 교시 배치 가능성)을 적용해 살아남는 배치 구조: {len(survivors)}개")
    for r in survivors:
        out.append(f"   {[model.names(m) for m in r['days']]} → 3회 {r['three']}, 계열중복 {r['dup']}, 예외 {r['exceptions']}")
    eg = {k: overlap(*k) for k in (("E", "G"), ("E", "I"), ("G", "I"), ("E", "G", "I"))}
    out.append(f"5) 살아남은 구조는 모두 {{E,G,I}}·{{D,F,K,M}}·{{H,L,N+P}}·{{O+J}} 네 묶음의 순열이므로 하루 3회 인원은 묶음별로 고정됨."
               f" {{E,G,I}} 묶음에서 정확히 2과목을 듣는 학생 = E∩G {eg[('E','G')]} + E∩I {eg[('E','I')]} + G∩I {eg[('G','I')]} − 3×E∩G∩I {eg[('E','G','I')]} = {eg[('E','G')]+eg[('E','I')]+eg[('G','I')]-3*eg[('E','G','I')]}명 → 최대 3회 78명은 피할 수 없음.")
    out.append("   같은 이유로 E+I 같은 날(50명)·L+P 같은 날(1명)도 고정 → 계열 중복 51명, O+J가 화 2교시 → 3학년 담임 예외 3건도 고정.")
    return "\n".join(out)


def pareto(res: list[dict]) -> list[dict]:
    """(max3, dup) 기준 파레토 최적해만 남긴다."""
    best = []
    for r in sorted(res, key=sort_key):
        if not any(o["max3"] <= r["max3"] and o["dup"] <= r["dup"] and (o["max3"], o["dup"]) != (r["max3"], r["dup"]) for o in res):
            if not any((o["max3"], o["dup"]) == (r["max3"], r["dup"]) for o in best):
                best.append(r)
    return best


# ---------------------------------------------------------------------------
# 4. 실행
# ---------------------------------------------------------------------------
BASE_UNITS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "OJ", "NP"]
BASELINE = {"목": ["C", "G", "E", "I"], "금": ["A", "H", "NP", "L"], "월": ["D", "F", "K", "M"], "화": ["OJ", "B"]}
BASELINE_PERIODS = {
    "목": {"C": 2, "G": 4, "E": 5, "I": 7},
    "금": {"A": 2, "H": 4, "NP": 5, "L": 7},
    "월": {"D": 2, "F": 4, "K": 5, "M": 7},
    "화": {"OJ": 2, "B": 4},
}


def run_scenario(name: str, units: list[str], periods: dict[str, list[int]], relaxes: list[set[str]], top: int):
    model = Model(units, periods)
    print(f"\n#### 시나리오: {name}  (유닛 {len(units)}개, 슬롯 {sum(len(v) for v in periods.values())}개, 완전 분할 {model.partition_count():,}개)")
    summary = {}
    for relax in relaxes:
        res, visited = model.search(relax)
        res.sort(key=sort_key)
        label = "강한선호 전부 준수" if not relax else "완화: " + "·".join(sorted(relax))
        c = sorted(Counter(r["max3"] for r in res).items())
        print(f"  [{label}] 가능해 {len(res)}개 (가지치기 후 완전 분할 방문 {visited:,}) max3 분포 {c[:8]}")
        for r in res[:top]:
            print("    ", sort_key(r), [model.names(m) for m in r["days"]], "3회", r["three"], "4회", r["four"], r["viol"])
        summary[label] = (model, res)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--extra", action="store_true", help="3·6교시 개방 시나리오")
    ap.add_argument("--report", action="store_true", help="목 3교시 개방 제안안 상세")
    args = ap.parse_args()

    print("== 검산 ==")
    print("  응시 인원:", {s: enroll[s] for s in SUBJECTS})
    pairs = sorted((overlap(x, y), x, y) for x, y in itertools.combinations(SUBJECTS, 2))
    print("  겹침 0 쌍:", [(x, y) for o, x, y in pairs if o == 0], " 그 다음:", pairs[2:6])
    print("  E∩I =", overlap("E", "I"), " L∩P =", overlap("L", "P"))

    base = Model(BASE_UNITS, BASE_PERIODS)
    bmasks = [base.mask(BASELINE[d]) for d in DAYS]
    br = base.evaluate(bmasks, set())
    print("\n== baseline 재계산 ==")
    print(describe(base, br, BASELINE_PERIODS))

    print("\n== 기본 시나리오 전수 탐색 ==")
    relaxes = [set(), {"교사2과목"}, {"ABC같은날"}, {"교사2과목", "ABC같은날"}, {"화3회"}, {"4회"},
               {"4회", "화3회", "교사2과목", "ABC같은날"}]
    summ = run_scenario("기본 (목·금·월 2·4·5·7교시, 화 2·4교시)", BASE_UNITS, BASE_PERIODS, relaxes, args.top)
    strict = summ["강한선호 전부 준수"][1]
    print("\n  강한 선호 전부 준수 가능해 전체:")
    for r in strict:
        print("    ", [base.names(m) for m in r["days"]], "3회", r["three"], "계열중복", r["dup"], "예외", r["exceptions"])

    print("\n== 왜 더 나은 안이 없는가 (사례 분석) ==")
    print(explain_structure(base))

    if args.extra:
        print("\n== 3·6교시 개방 시나리오 ==")
        split_variants = {
            "쌍 2개 유지(14유닛)": BASE_UNITS,
            "O·J 분리(15유닛)": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "O", "J", "NP"],
            "N·P 분리(15유닛)": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "OJ", "N", "P"],
            "모두 분리(16유닛)": list(SUBJECTS),
        }
        scenarios = {
            "화 3교시 추가": {**BASE_PERIODS, "화": [2, 3, 4]},
            "목 3교시 추가": {**BASE_PERIODS, "목": [2, 3, 4, 5, 7]},
            "목 6교시 추가": {**BASE_PERIODS, "목": [2, 4, 5, 6, 7]},
            "금 3교시 추가": {**BASE_PERIODS, "금": [2, 3, 4, 5, 7]},
            "금 6교시 추가": {**BASE_PERIODS, "금": [2, 4, 5, 6, 7]},
            "월 3교시 추가": {**BASE_PERIODS, "월": [2, 3, 4, 5, 7]},
            "월 6교시 추가": {**BASE_PERIODS, "월": [2, 4, 5, 6, 7]},
            "목·금 3교시 추가": {**BASE_PERIODS, "목": [2, 3, 4, 5, 7], "금": [2, 3, 4, 5, 7]},
            "목·월 3교시 추가": {**BASE_PERIODS, "목": [2, 3, 4, 5, 7], "월": [2, 3, 4, 5, 7]},
            "금·월 3교시 추가": {**BASE_PERIODS, "금": [2, 3, 4, 5, 7], "월": [2, 3, 4, 5, 7]},
            "목·금·월 3교시 추가": {**BASE_PERIODS, "목": [2, 3, 4, 5, 7], "금": [2, 3, 4, 5, 7], "월": [2, 3, 4, 5, 7]},
        }
        for sname, per in scenarios.items():
            nslots = sum(len(v) for v in per.values())
            for vname, units in split_variants.items():
                if len(units) > nslots:
                    continue
                run_scenario(f"{sname} / {vname}", units, per, [set(), {"교사2과목", "ABC같은날"}], 3)

    if args.report:
        print("\n== 목 3교시 개방안 상세 ==")
        thu3 = {**BASE_PERIODS, "목": [2, 3, 4, 5, 7]}
        for vname, units in (("N·P 분리(15유닛)", ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "OJ", "N", "P"]),
                             ("쌍 2개 유지(14유닛)", BASE_UNITS)):
            model = Model(units, thu3)
            res, _ = model.search(set())
            res.sort(key=sort_key)
            print(f"\n--- {vname}: 가능해 {len(res)}개, (max3, 계열중복) 파레토 ---")
            for r in pareto(res):
                print("   ", (r["max3"], r["dup"], r["exceptions"]), [model.names(m) for m in r["days"]], r["three"])
            best = res[0]
            # 전원 과목 배치: A 화, B 금, C 월 (B는 D와 같은 날 불가)
            want = {"A": 3, "B": 1, "C": 2}
            for r in res:
                if r["max3"] == best["max3"] and all(r["days"][d] & model.bit(f) for f, d in want.items()):
                    best = r
                    break
            # 목요일 교시: OJ 3교시 고정, 2·4교시 과목 쌍은 O/J와 셋 다 듣는 학생(2-3-4 연속 3회)이 가장 적게
            thu_units = model.names(best["days"][0])
            cand = []
            for perm in itertools.permutations([2, 4, 5, 7]):
                others = [u for u in thu_units if u != "OJ"]
                assign = dict(zip(others, perm))
                assign["OJ"] = 3
                if any(assign[u] not in model.allowed[(u, "목")] for u in thu_units):
                    continue
                at = {p: u for u, p in assign.items()}
                run234 = overlap("O", at[2], at[4]) + overlap("J", at[2], at[4])
                cand.append((run234, assign))
            cand.sort(key=lambda x: x[0])
            print("   목요일 2·3·4교시 연속 3회 학생 수(교시 배치별):", [(c[0], {u: p for u, p in c[1].items()}) for c in cand[:4]])
            prefer = {"목": cand[0][1],
                      "금": {"B": 2, "F": 4, "P": 5, "I": 7, "NP": 5},
                      "월": {"C": 2, "G": 4, "N": 5, "L": 7, "NP": 5},
                      "화": {"A": 2, "D": 4}}
            print(describe(model, best, prefer))
            for di, m in enumerate(best["days"]):
                print(f"   {DAYS[di]} 계열중복 내역:", [(u, v, t) for u, v, t in model.track_pairs if m & model.bit(u) and m & model.bit(v)])

    if args.json:
        def ser(model, r):
            d = {k: v for k, v in r.items() if k != "days"}
            d["days"] = [model.names(m) for m in r["days"]]
            d["dist"] = [model.dist[m][:5].tolist() for m in r["days"]]
            return d
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"baseline": ser(base, br), "strict": [ser(base, r) for r in strict]}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
