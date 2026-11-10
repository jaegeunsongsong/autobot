"""1단계: 과목 -> 요일 배정 전수 열거 (CP-SAT enumerate_all_solutions).

요일 수준에서 결정되는 제약만 건다. 교시 수준(교사 동시 배치, 목요일 수업 충돌,
연속 교시)은 layer2 에서 요일별로 따로 검사한다.
"""
import itertools, sys, time
from ortools.sat.python import cp_model
from data import *

D = DAYS  # 목 금 월 화


def enumerate_day_assignments(cap, hard_prefs=True, jo_pair_allowed=True, np_pair_allowed=True,
                              extra=None, limit=10_000_000):
    """cap: dict day -> 그 요일에 쓸 수 있는 최대 유닛 수(교시 수).
    hard_prefs: 강한 선호(ABC 다른 날, 교사 하루 2과목 금지)를 절대 제약으로 둘지.
    반환: list of dict subject->day, 그리고 각 해의 k(통합과학2 요일) 가능 집합은 layer2에서.
    """
    m = cp_model.CpModel()
    y = {(s, d): m.NewBoolVar(f"y_{s}_{d}") for s in SUBJECTS for d in D}
    for s in SUBJECTS:
        m.AddExactlyOne(y[s, d] for d in D)
    # 절대 제약
    m.Add(y["A", "화"] == 0)          # 마지막 날 국어 금지
    m.Add(y["P", "화"] == 0)          # 전이슬 화요일 출장
    # 학생 하루 0과목/4과목 금지 (면제 처리)
    for c, n in COMBOS:
        for d in D:
            cnt = sum(y[s, d] for s in c)
            if c == EXEMPT_ALL:
                continue
            m.Add(cnt >= 1)
            if c == EXEMPT_FOUR:
                m.Add(cnt <= 4)
            else:
                m.Add(cnt <= 3)
    # 쌍 사용 여부 변수: 같은 날이면 유닛 1개 절약 가능 (쓸지 말지는 layer2 에서도 선택 가능하나
    # 여기서는 '최대 절약' 가정으로 용량만 검사)
    pj = {d: m.NewBoolVar(f"pj_{d}") for d in D}   # J,O 같은 날 d
    pn = {d: m.NewBoolVar(f"pn_{d}") for d in D}
    for d in D:
        # pj[d] == y[J,d] AND y[O,d]
        m.AddBoolAnd([y["J", d], y["O", d]]).OnlyEnforceIf(pj[d])
        m.AddBoolOr([y["J", d].Not(), y["O", d].Not()]).OnlyEnforceIf(pj[d].Not())
        m.AddBoolAnd([y["N", d], y["P", d]]).OnlyEnforceIf(pn[d])
        m.AddBoolOr([y["N", d].Not(), y["P", d].Not()]).OnlyEnforceIf(pn[d].Not())
        units = sum(y[s, d] for s in SUBJECTS)
        saved = (pj[d] if jo_pair_allowed else 0) + (pn[d] if np_pair_allowed else 0)
        m.Add(units - saved <= cap[d])
    if not jo_pair_allowed:
        # 쌍을 안 쓰면 같은 날에 둘 수는 있으나 교시 2개 필요 — 위 용량식으로 처리됨
        pass
    # 강한 선호를 절대 제약으로
    if hard_prefs:
        for d in D:
            m.Add(y["A", d] + y["B", d] + y["C", d] <= 1)  # ABC 다른 날
            m.Add(y["B", d] + y["D", d] <= 1)              # 구성희
        m.Add(y["E", "월"] == 0)   # 김미애 통합사회2
        m.Add(y["I", "월"] == 0)   # 노석환 통합사회2
        m.Add(y["O", "금"] == 0)   # 정인광·손경준 한국사2
        # 최진호(H)·조세라(M) 는 통합과학2(금 또는 월)와 다른 날: k 변수
        k = m.NewBoolVar("sci_on_fri")   # 1이면 통합과학2 금, 0이면 월
        m.Add(y["H", "금"] == 0).OnlyEnforceIf(k)
        m.Add(y["M", "금"] == 0).OnlyEnforceIf(k)
        m.Add(y["H", "월"] == 0).OnlyEnforceIf(k.Not())
        m.Add(y["M", "월"] == 0).OnlyEnforceIf(k.Not())
    if extra:
        extra(m, y)

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.sols = set()
        def on_solution_callback(self):
            a = tuple(next(d for d in D if self.Value(y[s, d])) for s in SUBJECTS)
            self.sols.add(a)
            if len(self.sols) >= limit:
                self.StopSearch()
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.num_workers = 1
    cb = CB()
    solver.Solve(m, cb)
    return sorted(cb.sols)


def day_sets(assign):
    """assign: tuple of day per subject -> dict day -> set(subjects)"""
    out = {d: set() for d in D}
    for s, d in zip(SUBJECTS, assign):
        out[d].add(s)
    return out


def distribution(assign):
    """요일별 응시 횟수 분포: dict day -> Counter{k: 학생수}, 면제학생 별도"""
    ds = day_sets(assign)
    dist = {d: Counter() for d in D}
    for c, n in COMBOS:
        for d in D:
            dist[d][len(set(c) & ds[d])] += n
    return dist


def metrics(assign):
    ds = day_sets(assign)
    dist = distribution(assign)
    three = {d: sum(n for k, n in dist[d].items() if k >= 3) for d in D}
    four = {d: sum(n for k, n in dist[d].items() if k >= 4) for d in D}
    zero = {d: dist[d][0] for d in D}
    # 계열 중복
    dup = []
    for d in D:
        for a, b in itertools.combinations(sorted(ds[d]), 2):
            if FIELD[a] == FIELD[b]:
                dup.append((d, a, b, overlap(a, b)))
    exc = 1 + (1 if assign[SUBJ_IDX["J"]] in ("월", "화") else 0) + (1 if assign[SUBJ_IDX["O"]] in ("월", "화") else 0)
    return dict(dist=dist, three=three, four=four, zero=zero, dup=dup, dup_n=sum(x[3] for x in dup),
                dup_cnt=len(dup), exc=exc, tue3=three["화"], max3=max(three.values()), sum3=sum(three.values()))


if __name__ == "__main__":
    t = time.time()
    cap = {"목": 4, "금": 4, "월": 4, "화": 2}
    sols = enumerate_day_assignments(cap)
    print(f"4·4·4·2 요일배정 해 (강한선호 절대): {len(sols)}개, {time.time()-t:.1f}s")
    for a in sols[:5]:
        print(day_sets(a), metrics(a)["exc"], metrics(a)["three"], metrics(a)["dup"])
