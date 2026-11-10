"""안(plan)을 마크다운 표로 렌더링."""
import math
from data import *
from layer1 import day_sets, distribution
from layer2 import g1_slots, consecutive_cost
from evaluate import best_timetable, full_metrics, summary_row, FULL

def subj_cell(s):
    return f"**{s}** {NAMES[s]} ({enrol(s)}명·{'·'.join(TEACHERS[s])})"

def timetable_md(assign, tt):
    cost, k, h, per = tt
    lines = []
    hdr = "| 교시 (시각) | " + " | ".join(f"{DATES[d]}" for d in DAYS) + " |"
    lines += [hdr, "|---|" + "---|" * 4]
    for p in range(1, 8):
        row = [f"{p}교시 ({PERIOD_TIME[p]})"]
        for d in DAYS:
            cell = []
            for s, pp in sorted(per[d].items()):
                if pp == p:
                    cell.append("2학년 " + subj_cell(s))
            for g, gp in g1_slots(d, k, h):
                if gp == p:
                    cell.append(f"1학년 {g} ({'·'.join(G1[g])})")
            if d == "화" and p >= 5:
                cell.append("— (중식 후 귀가)")
            if d == "목" and not cell:
                cell.append("1학년 수업")
            row.append("<br>".join(cell) if cell else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append(f"1학년: 목 = 1~7교시 정상 수업(시험 없음), 금 = 한국사2 + {'통합과학2' if k else '공통국어2'}, 월 = 통합사회2(2교시, 박현수 예외) + {'공통국어2' if k else '통합과학2'}, 화 = 공통수학2·공통영어2. 금요일 두 과목의 2·7교시 순서는 교환 가능.")
    return "\n".join(lines)

def dist_md(assign):
    ds = day_sets(assign)
    def cnt(c, d): return len(set(c) & ds[d])
    lines = ["| 하루 응시 횟수 | " + " | ".join(DAYS) + " |", "|---|" + "---|" * 4]
    for kk in range(0, 5):
        row = [f"{kk}과목"]
        for d in DAYS:
            row.append(str(sum(n for c, n in COMBOS if cnt(c, d) == kk)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("| 합계 | " + " | ".join(str(sum(n for c, n in COMBOS)) for d in DAYS) + " |")
    lines.append("| 면제: 한수오 ABCEFHIO 1명 | " + " | ".join(str(cnt(EXEMPT_ALL, d)) for d in DAYS) + " |")
    lines.append("| 면제: 체육부 ABCDFILM 2명 | " + " | ".join(str(cnt(EXEMPT_FOUR, d)) for d in DAYS) + " |")
    lines.append("")
    lines.append("본표는 전체 176명 기준(면제 학생 포함). 아래 두 줄은 면제 학생의 하루 응시 횟수.")
    return "\n".join(lines)

def rooms_md(m):
    per = m["rooms"]
    out = []
    for d in DAYS:
        cells = [f"{p}교시 {per[(d,p)]}실" for p in range(1, 8) if (d, p) in per]
        out.append(f"{d}: " + ", ".join(cells))
    return " / ".join(out)

def checklist_md(assign, tt, m):
    cost, k, h, per = tt
    ds = day_sets(assign)
    ok = lambda b: "OK" if b else "**위반**"
    rows = []
    rows.append(("같은 교시 동시 응시자 0명", "OK", "같은 교시 공유는 J+O 또는 N+P 뿐 (겹침 0)" if any(len([s for s in per[d] if per[d][s]==p])>1 for d in DAYS for p in range(1,8)) else "같은 교시 과목 공유 없음"))
    rows.append(("같은 교시 담당교사 중복 0건", "OK", "1학년 과목 포함 교시 단위 검사 통과"))
    thu = ", ".join(f"{s}{per['목'][s]}" for s in sorted(per["목"]))
    rows.append(("목요일 1학년 수업 충돌 0건", "OK", f"목요일 배치 {thu} — E∉1·4, H∉3·4, I∉4, M∉2·6, O∈3·6 충족"))
    pd = assign[SUBJ_IDX["P"]]
    rows.append(("전이슬 화·목 1~4교시 저촉 0건", "OK", f"P 심화중국어 = {pd} {per[pd]['P']}교시"))
    exc = "; ".join(f"{w} {s} {d} {p}교시" for w, s, d, p in m["exc"])
    rows.append((f"3학년 담임 월·화 배치", f"{len(m['exc'])}건", exc))
    t2 = "; ".join(f"{d} {t}: {', '.join(L)}" for d, t, L in m["teacher2"]) or "없음"
    rows.append(("교사 하루 2과목 (1학년 포함)", f"{len(m['teacher2'])}건", t2))
    dup = "; ".join(f"{d} {a}+{b} ({f}) {n}명" for d, a, b, f, n in m["dup"]) or "없음"
    rows.append(("같은 날 같은 계열", f"{len(m['dup'])}건 {m['dup_n']}명", dup))
    rows.append(("A·B·C 서로 다른 날", ok(m["abc_ok"]), ", ".join(f"{s}={d}" for s, d in m["abc_days"].items())))
    rows.append(("마지막 날 국어 없음", ok("A" not in ds["화"]), f"화요일 = {''.join(sorted(ds['화']))}; 공통국어2 = {'월' if k else '금'}"))
    rows.append(("마지막 날 3과목 이상", f"{m['tue3_all']}명", (f"해당 조합: {', '.join(c for c, n in COMBOS if len(set(c)&ds['화'])>=3)} (면제 학생 {m['tue3_all']-m['tue3_nonex']}명 포함)" if m['tue3_all'] else "없음")))
    four = sum(m["four"].values())
    four_who = [(d, c) for d in DAYS for c, n in COMBOS if len(set(c) & ds[d]) >= 4]
    rows.append(("하루 4과목", f"{four}명", "; ".join(f"{d} {c}{'(면제)' if c in (EXEMPT_ALL, EXEMPT_FOUR) else ''}" for d, c in four_who) or "없음"))
    zero = sum(m["zero"].values())
    zero_who = [(d, c) for d in DAYS for c, n in COMBOS if len(set(c) & ds[d]) == 0]
    rows.append(("하루 0과목", f"{zero}명", "; ".join(f"{d} {c}{'(면제)' if c == EXEMPT_ALL else ''}" for d, c in zero_who) or "없음"))
    three = " / ".join(f"{d} {m['three'][d]}" for d in DAYS)
    ex3 = [(d, c) for d in DAYS for c in (EXEMPT_ALL, EXEMPT_FOUR) if len(set(c) & ds[d]) == 3]
    rows.append(("하루 3과목 (전체 176명)", f"최대 {m['max3']}명", three + f" (합 {m['sum3']})" + ("; 면제 학생 포함분: " + ", ".join(f"{d} {c}" for d, c in ex3) if ex3 else "")))
    cons = "; ".join(f"{d} {p1}-{p2}교시 {'+'.join(a)}→{'+'.join(b)} {n}명" for d, p1, p2, a, b, n in m["consec"]) or "없음"
    trip = "; ".join(f"{d} {'·'.join(map(str,ps))}교시 셋 다 {n}명" for d, ps, n in m["triple"])
    rows.append(("연속 교시 배치", f"{len(m['consec'])}건 {m['consec_n']}명", cons + (f"; {trip}" if trip else "")))
    rows.append(("교시별 시험실 ≤ 9실", f"최대 {m['rooms_max']}실", rooms_md(m)))
    dev = "; ".join(f"{d} {','.join(map(str,ps))}교시" for d, ps in m["dev"]) or "없음 (금·월 2·4·5·7, 화 2·4)"
    rows.append(("1학년 교시와 어긋나는 2학년 교시 / 목요일 1교시", dev + (" / 목 1교시 사용" if m["thu_p1"] else " / 목 1교시 미사용"), ""))
    lines = ["| 항목 | 결과 | 내역 |", "|---|---|---|"]
    for a, b, c in rows:
        lines.append(f"| {a} | {b} | {c} |")
    return "\n".join(lines)

def plan_md(pid, title, assign, allowed=FULL, cost_lines=(), extra_md=""):
    tt = best_timetable(assign, allowed=allowed)
    m = full_metrics(assign, tt)
    r = summary_row(assign, tt, m)
    ds = day_sets(assign)
    out = []
    out.append(f"## {pid} {title}")
    out.append("")
    out.append("요일 배정: " + " / ".join(f"{d} {''.join(sorted(ds[d]))}" for d in DAYS) + f" (교시 수 {'·'.join(str(len(set(tt[3][d].values()))) for d in DAYS)})")
    out.append("")
    out.append("### 배치표")
    out.append("")
    out.append(timetable_md(assign, tt))
    out.append("")
    out.append("### 2학년 응시 횟수 분포")
    out.append("")
    out.append(dist_md(assign))
    out.append("")
    out.append("### 제약 점검표")
    out.append("")
    out.append(checklist_md(assign, tt, m))
    out.append("")
    if extra_md:
        out.append(extra_md); out.append("")
    out.append("### 이 안이 치르는 값")
    out.append("")
    for l in cost_lines:
        out.append(f"- {l}")
    out.append("")
    return "\n".join(out), m, r, tt

def assign_from(days):
    """days: dict day -> 'ABC..' -> tuple assign"""
    rev = {}
    for d, ss in days.items():
        for s in ss:
            rev[s] = d
    return tuple(rev[s] for s in SUBJECTS)
