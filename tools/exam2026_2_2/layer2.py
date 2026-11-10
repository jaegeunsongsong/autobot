"""2단계: 하루치 과목 집합을 교시에 배정. 교사 동시 배치·목요일 수업 충돌·출장·예외 2교시 규칙을
검사하고 연속 교시 비용(두 과목 모두 응시자)을 계산한다."""
import itertools
from data import *


def units_of(subs, pair_jo, pair_np):
    """subs: set of subjects on the day. 반환: list of tuple(subjects in one slot)."""
    subs = set(subs)
    units = []
    if pair_jo and {"J", "O"} <= subs:
        units.append(("J", "O")); subs -= {"J", "O"}
    if pair_np and {"N", "P"} <= subs:
        units.append(("N", "P")); subs -= {"N", "P"}
    units += [(s,) for s in sorted(subs)]
    return units


def g1_slots(day, k, h):
    """1학년 과목의 (과목, 교시). k=1: 통합과학2 금(공통국어2 월), k=0: 통합과학2 월.
    h: 금요일 한국사2 교시(2 또는 7). 월요일 통합사회2는 박현수 예외 규칙으로 2교시 고정."""
    if day == "금":
        other = "통합과학2" if k else "공통국어2"
        return [("한국사2", h), (other, 9 - h)]
    if day == "월":
        other = "공통국어2" if k else "통합과학2"
        return [("통합사회2", 2), (other, 7)]
    if day == "화":
        return [("공통수학2", 2), ("공통영어2", 4)]
    return []


def slot_ok(day, unit, p, k, h):
    """unit(튜플)을 day의 p교시에 둘 수 있는가 (절대 제약만)."""
    for s in unit:
        if day == "목" and p in THU_BLOCK.get(s, ()):
            return False            # 목요일 1학년 수업 충돌
        if s == "P" and p in P_BLOCK.get(day, ()):
            return False            # 전이슬 출장
        if s in ("J", "O") and day in ("월", "화") and p != 2:
            return False            # 3학년 담임 예외는 2교시만
    # 1학년 과목과 같은 교시 교사 중복
    for g, gp in g1_slots(day, k, h):
        if gp != p:
            continue
        gt = set(G1[g])
        for s in unit:
            if gt & set(TEACHERS[s]):
                return False
    return True


def assignments(day, subs, allowed, k, h, pair_jo=True, pair_np=True):
    """가능한 모든 교시 배정을 생성. yield dict subject->period, cost dict."""
    units = units_of(subs, pair_jo, pair_np)
    if len(units) > len(allowed):
        return
    for perm in itertools.permutations(sorted(allowed), len(units)):
        ok = all(slot_ok(day, u, p, k, h) for u, p in zip(units, perm))
        if not ok:
            continue
        # 구성희 B+D 같은 교시 (절대) — 같은 날이면 다른 교시여야 함
        sp = {s: p for u, p in zip(units, perm) for s in u}
        if "B" in sp and "D" in sp and sp["B"] == sp["D"]:
            continue
        yield sp


def consecutive_cost(day, sp):
    """연속 교시 쌍마다 두 과목 모두 응시자 수. 반환 list of (p1,p2,subs1,subs2,n)"""
    bp = {}
    for s, p in sp.items():
        bp.setdefault(p, []).append(s)
    out = []
    for p1, p2 in CONSEC:
        if p1 in bp and p2 in bp:
            n = sum(overlap(a, b) for a in bp[p1] for b in bp[p2])
            out.append((p1, p2, tuple(bp[p1]), tuple(bp[p2]), n))
    return out


def triple_consecutive(day, sp):
    bp = {}
    for s, p in sp.items():
        bp.setdefault(p, []).append(s)
    out = []
    for p1, p2, p3 in [(1, 2, 3), (2, 3, 4), (5, 6, 7)]:
        if p1 in bp and p2 in bp and p3 in bp:
            n = sum(overlap(a, b, c) for a in bp[p1] for b in bp[p2] for c in bp[p3])
            out.append(((p1, p2, p3), n))
    return out


def best_assignment(day, subs, allowed, k, h, pair_jo=True, pair_np=True, prefer=None):
    """연속 교시 비용(인원 합, 건수) 최소 -> prefer 집합(예: {2,4,5,7}) 밖 교시 수 최소 -> 1교시 사용 최소"""
    best = None
    for sp in assignments(day, subs, allowed, k, h, pair_jo, pair_np):
        cc = consecutive_cost(day, sp)
        used = set(sp.values())
        dev = len(used - prefer) if prefer else 0
        key = (sum(x[4] for x in cc), len(cc), dev, 1 if 1 in used else 0, tuple(sorted(sp.items())))
        if best is None or key < best[0]:
            best = (key, sp, cc)
    return best


NONCONSEC = {  # 연속 없는 교시 조합
    4: [(1, 3, 5, 7), (1, 4, 5, 7), (2, 4, 5, 7)],
}
