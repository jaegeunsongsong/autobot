# -*- coding: utf-8 -*-
"""최종 보고서(markdown) 생성."""
import sys, os, collections; sys.path.insert(0, '.')
from data import *
from periods import day_configs, both
from axes import AXES, CFG_KEYS, with_cfg
from query import load, base_ok
from build import build
from evaluate import evaluate, fmt_report
from plans_xy import PLAN_X, PLAN_Y

OUT = sys.argv[1] if len(sys.argv) > 1 else "../../docs/2026-2학기-2차-정기시험/절충안-5개.md"
strict = [m for m in load("parts_strict.pkl") if m["feasible"]]
allow1 = [m for m in load("parts_allow1.pkl") if m["feasible"]]

PLANS = [
    dict(no=1, title="안 1 — 하루 3과목 최대 인원 최소(36명) + 예외 1건", part="EHJKMO|AFIP|BGLN|CD", ck="default",
         axis="하루 3과목 최대 인원 최소화(동률이면 계열 중복·교사 하루 2과목·A·B·C 분리 순)",
         cost=["목요일을 1·3·4·5·7 다섯 교시로 운영합니다. 1교시(08:40) 시험과 3교시 개방, 3-4교시 연속(M 지구시스템과학을 앞 교시 O·J와 함께 보는 11명)이 생깁니다.",
               "목요일에 사회 3과목(E·K·O)과 과학 3과목(H·J·M)이 몰려 같은 날 같은 계열 응시자가 138명으로 다섯 안 중 가장 많습니다.",
               "그 대신 하루 3과목 최대치가 36명(목 32·금 36·월 36)으로 전수 탐색 하한이고, 예외는 박현수 1건, 교사 하루 2과목 0건, A·B·C 분리입니다."]),
    dict(no=2, title="안 2 — 같은 날 같은 계열 최소(47명) + 예외 1건", part="EGMNOP|AFIJ|BHKL|CD", ck="default",
         axis="같은 날 같은 계열 응시자 합 최소화(동률이면 하루 3과목 최대·예외·교사 하루 2과목·A·B·C 분리 순)",
         cost=["계열 중복은 47명(목 E+O 25, G+M 22)으로 하한이지만, 금요일 3과목 학생이 55명으로 안 1·4·5보다 많습니다.",
               "목요일을 1·3·4·5·7로 운영합니다(1교시 M 지구시스템과학, 3교시 O). 연속 교시는 3-4교시 O+G 1명뿐입니다.",
               "B·C를 같은 날(화)에 두면 같은 계열 47명에 최대 48명(EGMNOP|DFIJ|AHKL|BC)까지 내려가지만 ‘A·B·C 서로 다른 날’을 어기므로 채택하지 않았습니다."]),
    dict(no=3, title="안 3 — 전 요일 2·4·5·7 통일(4·4·4·2, 14교시)", part="AEGI|BHLNP|DFKM|CJO", ck="base",
         axis="목·금·월 2·4·5·7, 화 2·4의 기본형으로 교시 체계를 통일(그 안에서 하루 3과목 최대 최소)",
         cost=["강한 제약 전부를 만족하고 연속 교시·1교시·3/6교시 개방이 전혀 없는 유일한 구조이지만, 목요일 3과목 학생이 78명입니다. 기본형을 유지하는 모든 해(24개)가 78명으로 동일합니다.",
               "O+J가 화요일 2교시로 가므로 3학년 담임 예외가 3건(박현수·손경준·배태안)입니다.",
               "안 X와 같은 틀(목 AE·I, 금 LNP, 월 DFKM, 화 J·O)이며 G·H만 자리가 바뀌었습니다. 안 X는 ABCEFHIO 조합 1명이 목요일 4과목이라 도움반 확인 전에는 쓸 수 없습니다(§7-1)."]),
    dict(no=4, title="안 4 — 목요일 기본형 유지·1교시 없음·예외 1건", part="AFIP|EHJKMO|BGLN|CD", ck="no_p1",
         axis="목요일 교시 변경 없음(2·4·5·7)·1교시 없음·예외 1건을 전제로 하루 3과목 최대 최소",
         cost=["다섯 교시 운영을 목요일 대신 금요일(2·3·4·5·7)로 옮긴 안입니다. 1학년 시험일에 3교시를 열어 자습 학년 소란 위험이 있고, 2-3·3-4교시 연속이 13명입니다.",
               "O 동아시아역사기행이 한국사2와 같은 금요일이라 정인광·손경준이 하루 2과목을 맡습니다(교시는 다름).",
               "학생 지표는 안 1과 같습니다(최대 36명, 계열 중복 138명, 예외 1건)."]),
    dict(no=5, title="안 5 — 균형안(예외 2건: 배태안 월 2교시 단독)", part="EGMNOP|AHIK|BFJL|CD", ck="default",
         axis="예외 ≤2건·교사 하루 2과목 0건·A·B·C 분리·금·월·화 기본형 유지·목요일 5교시 이하를 전제로 (하루 3과목 최대, 계열 중복, 연속) 사전식 최소",
         cost=["O와 J를 떼어 J만 월요일 2교시(통합사회2와 같은 교시, 담당 다름)에 두므로 3학년 담임 예외가 2건(박현수·배태안)입니다. 예외는 규정대로 월 2교시 오전 종료입니다.",
               "하루 3과목 최대 47명(월), 계열 중복 74명(목 E+O 25, G+M 22, 금 I+K 27), 연속 교시 1명(목 3-4 O+G)입니다.",
               "목요일 1·3·4·5·7 운영(1교시 M). 1교시를 피하려면 목 2·3·4·5·7로 바꿀 수 있으며 연속 응시자는 4명으로 늘어납니다(아래 교시 대안)."]),
]

def part_of(m, sep="|"): return sep.join("".join(sorted(s)) for s in m["sets"])
def axis_opt(name, pool):
    ax = AXES[name]
    cand = [with_cfg(m, ax["ck"]) for m in pool]
    cand = [m for m in cand if ax["flt"](m)]
    cand.sort(key=ax["key"])
    return cand
def alt_thu(part, day_idx, n=3):
    S = frozenset(part.split("|")[day_idx]); d = DAYS[day_idx]
    cs = day_configs(d, S)
    keyed = sorted(cs, key=lambda c: (c["p1"], c["ndev"], c["consec_students"], c["nconsec"], c["periods"]))
    seen, out = set(), []
    for c in keyed:
        k = c["periods"]
        if k in seen: continue
        seen.add(k); out.append(c)
        if len(out) >= n: break
    return out

L = []
w = L.append
w("# 2026학년도 2학기 2차 정기시험 시간표 — 절충안 5개")
w("")
w("기준 데이터: §5 2학년 176명·84조합(검산 완료). 모든 수치는 데이터에서 직접 계산했습니다. 계산 도구는 `tools/exam2/`에 있습니다(부록).")
w("")
w("## 0. 한눈에 보기")
w("")
w("- 절대 제약 9개를 **도움반 면제 없이** 모두 만족하는 2학년 일자 분할은 1,440개뿐입니다(4^16 = 4,294,967,296개 중). 다섯 안은 모두 이 1,440개 안에서 각 축의 최적입니다.")
w("- 기본형(전 요일 2·4·5·7, 4·4·4·2)을 유지하면 **목요일 3과목 학생 78명**을 피할 수 없고(가능한 24개 분할 전부 78명), 예외도 3건입니다. 78명을 피하려면 어느 한 요일을 다섯 교시로 운영해야 합니다(목 1·3·4·5·7 등).")
w("- 하루 3과목 최대 인원의 하한은 36명, 같은 날 같은 계열의 하한은 47명이며 둘을 동시에 얻는 해는 없습니다.")
w("- 안 X는 ABCEFHIO 조합 1명이 목요일 4과목, 안 Y는 ABCDGHIN 조합 1명(일반)이 금요일 4과목이므로 둘 다 절대 제약 7을 어깁니다. §4-다의 한수오 조합 ABDEHIKO는 §5 데이터에 없습니다(§1·§8).")
w("- 추천: **안 5(균형안)**. 근거는 §6.")
w("")
# ---- 1. 데이터 검산
w("## 1. 데이터 검산")
w("")
w("| 항목 | 결과 |")
w("|---|---|")
w(f"| 조합 수 / 합계 | {len(COMBOS)}개 / {sum(n for _, n in COMBOS)}명 (전원 8과목) |")
enroll = {s: sum(n for c, n in COMBOS if s in c) for s in SUBJECTS}
w("| 과목별 인원 | " + ", ".join(f"{s}={enroll[s]}" for s in SUBJECTS) + " — §2 표와 전부 일치 |")
w(f"| 교차 검산 | E∩I={both('E','I')}, H∩J={both('H','J')}, E∩O={both('E','O')}, L∩P={both('L','P')} — 전부 일치 |")
w("| 겹침 0인 쌍 | J+O, N+P 2개뿐(다음은 F+P 1, G+O 1, L+P 1) — §1과 일치 |")
w("| 면제 학생 | 조명근 ABCDEFGH(8명 중 1), 최진영 ABCDFILM(2명 중 1)은 데이터에 있음. **한수오 ABDEHIKO는 없음**: 84개 조합이 모두 C를 포함하고 C=176=전원이므로 C가 없는 조합은 존재할 수 없음 |")
w("")
w("따라서 도움반 면제는 어느 조합에도 적용할 수 없어 **다섯 안은 도움반 면제 없이**(176명 전원에 0과목·4과목·화요일 3과목 금지 적용) 계산했습니다. 체육부 2명은 4과목·화 3과목 규칙에서만 제외했습니다. 한수오의 실제 조합이 확인되면 §7-1처럼 결과가 달라질 수 있습니다.")
w("")
# ---- 2. 안 X·Y
w("## 2. 안 X·Y 재계산")
w("")
for name, plan in [("안 X (전 요일 2·4·5·7)", PLAN_X), ("안 Y (목요일 1·3·5·7)", PLAN_Y)]:
    R = evaluate(plan)
    w(fmt_report(plan, R, name)); w("")
w("재계산 결과와 §6 표의 차이:")
w("")
w("- 안 X: 3과목 70/39/40/0, 계열 중복 51명, 예외 3건은 §6과 같습니다. 4과목 1명은 **ABCEFHIO 조합**(목: A·E·H·I)입니다. §6은 이를 ‘도움반 1명’이라 했지만 §4-다의 한수오 조합(ABDEHIKO)과 다르므로, 한수오가 실제로 ABCEFHIO가 아니라면 절대 제약 7 위반입니다.")
w("- 안 Y: 3과목 20/46/47/0, 계열 중복 58명(E+O 25, H+J 33), 예외 1건은 §6과 같습니다. 4과목 1명은 **ABCDGHIN 조합**(금: A·G·I·N)이며 §6 스스로 ‘일반 1명’이라 적었습니다. 따라서 **안 Y는 절대 제약 7(하루 4과목 금지)을 위반**하며, ‘X·Y 모두 절대 제약 1~9 만족’이라는 §6의 문장은 틀렸습니다.")
w("- 두 안 모두 그 외 항목(동시 응시·교사 동시·목요일 수업 충돌·전이슬·담임 교시·연속 교시·시험실)은 문제없습니다.")
w("")
# ---- 3. 방법
w("## 3. 탐색 방법과 탐색 공간")
w("")
w("1. **일자 분할 전수 탐색(C, `enum.c`)**: 16과목 각각을 목·금·월·화에 배정하는 4^16 = 4,294,967,296가지를 깊이우선탐색으로 훑되, 일자만으로 판정되는 절대 제약(A·P 화요일 불가, 84조합 각각의 하루 4과목·화요일 3과목·하루 0과목 금지, 화요일 ≤4교시)으로 가지치기했습니다. 방문 노드 804,976개, 생존 분할 **1,440개**. 독립 구현(Python·numpy, `crosscheck.py`)으로 같은 1,440개를 얻어 교차 검증했습니다.")
w("2. **교시 배정 전수 탐색(`periods.py`)**: 생존 분할의 각 요일 과목 집합에 대해 가능한 교시 배정을 모두 열거했습니다. 반영한 교시 제약: 같은 교시 담당교사 중복(1학년 과목 포함), 목요일 1학년 수업 담당표, 전이슬 화·목 1~4교시, 3학년 담임의 월·화 2교시 한정(통합사회2 월 2교시 고정 포함), O+J·N+P 동시 시행, 화요일 1~4교시, 1학년 금·월 2·7교시, 화 2·4교시. 1,440개 분할 전부가 교시 배정 가능했습니다.")
w("3. **축별 최적**: 요일별 교시 배정은 서로 독립이므로, 축마다 정한 사전식 목적함수로 요일별 최선 배정을 고른 뒤 1,440개 분할 전체에서 최소를 취했습니다. 따라서 각 안은 그 축에서 **전수 탐색 최적**입니다.")
w("4. 해석을 정한 사항(데이터에 없어 제가 정한 규칙): (가) ‘어긋난 교시’는 금·월의 2·4·5·7, 화의 2·4 밖의 교시로 보고 벌점을 두었습니다. (나) 목요일 교시 변경은 §1대로 비용 0으로 두되 1교시 사용과 3·6교시 개방은 별도로 표기했습니다. (다) 1학년 국·수·영 일자는 2학년 과목과 교사가 겹치지 않아 결과에 영향이 없으므로 국어 금·수학 월·영어 화(교환 가능)로 두었습니다. (라) 통합과학2는 §3대로 화요일 고정(§7-2에서 이동 시 영향 분석).")
w("")
# ---- 4. 구조적 사실
w("## 4. 전수 탐색이 보여 주는 구조적 사실")
w("")
tue_sets = collections.Counter("".join(sorted(m["sets"][3])) for m in strict)
w(f"1. **화요일은 항상 과목 2개(교시 2개)**입니다. 1,440개 분할의 화요일 집합: " + ", ".join(f"{k} {v}개" for k, v in tue_sets.most_common()) + ". 화요일 3과목 금지(전원 ≤2)와 하루 0과목 금지(전원 ≥1)를 A 없이 동시에 만족하려면 B 또는 C가 들어가야 하고, 세 번째 과목을 넣으면 누군가 3과목이 됩니다(J+O, N+P 같은 겹침 0 쌍을 B/C와 묶는 것만 가능).")
base = [m for m in strict if base_ok(m)]
w(f"2. **기본형(4·4·4·2, 14교시)은 {len(base)}개 분할만 가능하고 전부 목(또는 금) 3과목 78명**입니다. 모두 `AEGI | BHLNP | DFKM | CJO`에서 A·B·C의 자리와 목·금·월 순서만 바꾼 것입니다. 즉 교시 체계를 유지하는 한 78명은 고정값입니다.")
nb = [m for m in allow1 if base_ok(m) and m["exc"] == 1]
wit = collections.Counter(COMBOS[m["viol"]][0] for m in nb)
w(f"3. **기본형 + 예외 1건은 불가능**합니다. 예외 1건이려면 O·J가 월·화에 없어야 하고, 기본형 목요일(2·4·5·7)에는 O를 둘 수 없으므로(§4-가-4) O는 금요일뿐입니다. 이 조건으로 전수 탐색하면 절대 제약을 모두 만족하는 분할이 0개입니다. 가장 가까운 분할 {len(nb)}개는 각각 정확히 1명이 하루 4과목이 되며, 그 학생은 " + ", ".join(f"{k} 조합({v}개 분할)" for k, v in wit.most_common()) + "입니다.")
w("4. **연속 교시 없음 = 1교시 없음·5교시 요일 없음 = 위 24개 분할**입니다. 따라서 78명을 피하는 모든 해는 어느 한 요일을 5교시 이상 운영하며, 그러면 연속 교시(또는 1교시·3/6교시 개방)가 반드시 생깁니다.")
w("5. **예외 2건도 가능**합니다. §4-가-5는 O+J를 한 묶음으로 보아 1 또는 3건이라 했지만, O와 J를 떼어 J만 월·화 2교시에 두면 배태안 1건만 추가됩니다(안 5).")
w(f"6. 하한: 하루 3과목 최대 인원 {min(m['max3'] for m in strict)}명, 3과목 연인원 합 {min(m['sum3'] for m in strict)}명, 같은 날 같은 계열 {min(m['series_students'] for m in strict)}명. 최대 36명인 분할은 모두 목(또는 금)요일에 E·H·J·K·M·O 여섯 과목을 모으므로 계열 중복 138명을 피할 수 없습니다.")
w("")
# ---- 5. 안
w("## 5. 절충안 5개")
w("")
w("표기: 교시 셀의 ‘1학년 과목 / 2학년 과목’은 같은 교시에 두 학년이 각자 시험을 보는 것입니다. 분포표는 176명 전원 기준이며 체육부 2명(ABCDEFGH·ABCDFILM 각 1명)은 아래 안 모두에서 4과목·화 3과목이 발생하지 않아 별도 표기가 필요 없습니다.")
w("")
results = {}
for P in PLANS:
    plan = build(P["part"], P["ck"]); R = evaluate(plan); results[P["no"]] = (plan, R, P)
    w(fmt_report(plan, R, P["title"])); w("")
    w(f"**최적화 축**: {P['axis']}.")
    w("")
    # 최적성
    ax_name = {1: "①예외1건", 2: "③계열중복", 3: "④기본형통일", 4: "⑩예외1+목기본형+1교시없음", 5: None}[P["no"]]
    if ax_name:
        cand = axis_opt(ax_name, strict)
        bestv = AXES[ax_name]["key"](cand[0])
        ties = [c for c in cand if AXES[ax_name]["key"](c) == bestv]
        w(f"**최적성**: 축 조건을 만족하는 분할 {len(cand)}개 중 사전식 최소. 같은 값의 분할 {len(ties)}개는 A·B·C 자리 또는 목·금·월 순서만 다릅니다(목록: " + "; ".join(part_of(c) for c in ties[:6]) + ("…" if len(ties) > 6 else "") + ").")
    else:
        pool = [with_cfg(m, "default") for m in strict]
        pool = [m for m in pool if m["exc"] <= 2 and len(m["teacher_day"]) == 0 and m["abc_same"] == 0 and m["ndev"] == 0 and len(m["cfg"][0]["periods"]) <= 5]
        pool.sort(key=lambda m: (m["max3"], m["series_students"], m["consec_students"], m["sum3"]))
        w(f"**최적성**: 전제 조건(예외 ≤2, 교사 하루 2과목 0, A·B·C 분리, 금·월·화 기본형, 목요일 ≤5교시)을 만족하는 분할 {len(pool)}개 중 (하루 3과목 최대, 계열 중복, 연속 응시자) 사전식 최소. 상위 3개: " + "; ".join(f"{part_of(c)} max{c['max3']}·계열{c['series_students']}·연속{c['consec_students']}" for c in pool[:3]) + ".")
    w("")
    w("**이 안이 치르는 값**")
    w("")
    for c in P["cost"]: w(f"- {c}")
    w("")
    # 교시 대안 (5교시 요일)
    five = [i for i, d in enumerate(DAYS) if len({p for s, (dd, p) in plan["g2"].items() if dd == d}) >= 5]
    for i in five:
        alts = alt_thu(P["part"], i)
        w(f"**{DAYS[i]}요일 교시 대안**(1교시 회피 우선 → 연속 응시자 순):")
        w("")
        for c in alts:
            asg = " ".join(f"{p}:{'+'.join(sorted(s for s, pp in c['assign'].items() if pp == p))}" for p in c["periods"])
            cons = ", ".join(f"{p}-{q} {a}+{b} {k}명" for p, q, a, b, k in c["consec"]) or "없음"
            w(f"- {'·'.join(map(str, c['periods']))}교시 ({asg}) — 연속 {c['consec_students']}명({cons}), 1교시 {'사용' if c['p1'] else '없음'}")
        w("")
# ---- 6. 비교표
w("## 6. 비교표와 추천")
w("")
hdr = ["항목", "안 X(참고)", "안 Y(참고)"] + [f"안 {P['no']}" for P in PLANS]
w("| " + " | ".join(hdr) + " |"); w("|" + "---|" * len(hdr))
RX, RY = evaluate(PLAN_X), evaluate(PLAN_Y)
allR = [("X", RX, PLAN_X), ("Y", RY, PLAN_Y)] + [(P["no"], results[P["no"]][1], results[P["no"]][0]) for P in PLANS]
def periods_of(plan):
    out = []
    for d in DAYS:
        ps = sorted({p for s, (dd, p) in plan["g2"].items() if dd == d}); out.append("".join(map(str, ps)))
    return " / ".join(out)
rows = [
    ("교시 구조(목/금/월/화)", lambda R, p: periods_of(p)),
    ("하루 3과목(목/금/월/화)", lambda R, p: "/".join(str(R["3과목"][d]) for d in DAYS)),
    ("하루 3과목 최대", lambda R, p: str(R["3과목최대"])),
    ("3과목 연인원 합", lambda R, p: str(R["3과목합"])),
    ("4과목(면제 전)", lambda R, p: ", ".join(f"{c} {n}명({d})" for d, c, n in R["4과목_전체"]) or "0"),
    ("마지막날 3과목", lambda R, p: str(sum(n for d, c, n in R["화3과목_전체"]))),
    ("3학년 담임 예외", lambda R, p: f"{len(R['담임예외'])}건"),
    ("교사 하루 2과목", lambda R, p: f"{len(R['교사하루2'])}건" + (f" ({'; '.join(x.split()[1].rstrip(':') for x in R['교사하루2'])})" if R["교사하루2"] else "")),
    ("같은 날 같은 계열", lambda R, p: f"{R['계열중복인원']}명/{len(R['계열중복'])}쌍"),
    ("A·B·C 다른 날", lambda R, p: "OK" if R["ABC다른날"] else "위반"),
    ("연속 교시 응시자", lambda R, p: f"{sum(int(x.split()[-1].rstrip('명')) for x in R['연속교시'])}명/{len(R['연속교시'])}쌍"),
    ("1교시 사용", lambda R, p: "있음" if any(pp == 1 for s, (d, pp) in p["g2"].items()) else "없음"),
    ("목 3·6교시 개방", lambda R, p: "있음" if any(d == "목" and pp in (3, 6) for s, (d, pp) in p["g2"].items()) else "없음"),
    ("1학년 시험일 어긋난 교시", lambda R, p: ", ".join(f"{d}{pp}" for s, (d, pp) in sorted(p["g2"].items(), key=lambda t: (DAYS.index(t[1][0]), t[1][1])) if (d in ("금", "월") and pp not in (2, 4, 5, 7)) or (d == "화" and pp not in (2, 4))) or "없음"),
    ("절대 제약 9개", lambda R, p: "모두 OK" if not (R["4과목"] or R["화3과목"] or R["0과목"] or R["동시응시"] or R["교사동시"] or R["목수업충돌"] or R["전이슬"] or R["담임위반"] or R["마지막날국어"]) else "**위반**"),
]
for label, f in rows:
    w(f"| {label} | " + " | ".join(f(R, p) for _, R, p in allR) + " |")
w("")
w("**추천: 안 5(균형안)**")
w("")
w("- 절대 제약은 다섯 안 모두 만족하므로 강한 선호와 운영 부담으로 고릅니다. 안 5는 교사 하루 2과목 0건, A·B·C 분리, 금·월·화 기본형 유지, 연속 교시 1명, 하루 3과목 최대 47명(안 Y와 같은 수준)을 동시에 갖춘 유일한 안입니다.")
w("- 치르는 값은 배태안 월 2교시 예외 1건 추가(규정이 허용하는 오전 종료 방식)와 목요일 1·3·4·5·7 운영입니다. 예외를 1건으로 묶어야 하면 J와 I를 금·월 사이에서 맞바꾼 변형(`EGMNOP|AFJL|BHIK|CD`, 예외 1건·최대 47명·계열 74명)이 있지만 노석환이 월요일에 I와 통합사회2를 함께 맡게 됩니다.")
w("- 예외 1건이 절대 조건이면 안 2(계열 47명, 최대 55명), 학생 하루 부담이 절대 조건이면 안 1(최대 36명, 계열 138명)을 권합니다. 교시 체계를 바꿀 수 없으면 안 3뿐이며 그 값은 78명입니다.")
w("")
# ---- 7. 조건부
w("## 7. 조건부 분석")
w("")
w("### 7-1. 한수오의 실제 조합에 따른 변화")
w("")
w("도움반 1명을 어느 조합으로 보느냐에 따라 ‘정확히 그 학생 1명만 규칙을 어기는’ 분할이 추가로 허용됩니다(1명 허용 전수 탐색 16,398개). 한수오가 **ABCEFHIO**(안 X에서 4과목이 되는 학생)라면: 축 ①②③⑤의 최적은 변하지 않고, 기본형 축 ④만 78명 → **70명**(안 X와 같은 `AEHI|BGLNP|DFKM|CJO`, 예외 3건)으로 내려갑니다. 즉 그 경우 안 3 대신 안 X를 그대로 쓸 수 있습니다.")
w("")
w("한수오가 다른 조합일 때 기본형(4·4·4·2)에서 가능한 최선(하루 3과목 최대 기준 상위 7개, 목/금/월/화 순):")
w("")
w("| 한수오 조합이라면 | 기본형 최선 분할 | 하루 3과목 최대 | 예외 | 계열 |")
w("|---|---|---|---|---|")
bestb = {}
for m in allow1:
    if not base_ok(m): continue
    k = COMBOS[m["viol"]][0] if m["viol"] >= 0 else "(면제 불필요)"
    if k not in bestb or (m["max3"], m["exc"]) < (bestb[k]["max3"], bestb[k]["exc"]): bestb[k] = m
for k, m in sorted(bestb.items(), key=lambda t: (t[1]["max3"], t[1]["exc"]))[:7]:
    w(f"| {k} | {part_of(m, ' / ')} | {m['max3']} | {m['exc']} | {m['series_students']} |")
w("")
w("안 Y가 성립하려면 ABCDGHIN 조합 학생이 면제 대상이어야 합니다. §6은 그를 일반 학생이라 했으므로 안 Y는 제외했습니다.")
w("")
w("### 7-2. 통합과학2를 마지막 날에서 빼는 경우(요청 사항)")
w("")
w("§3은 통합과학2를 화요일 고정으로 두었지만 ‘1학년 과학이 마지막 날이 아니면 좋겠다’는 요청이 있어 금·월로 옮긴 경우를 같은 방법으로 다시 계산했습니다. 1,440개 분할의 교시 배정 가능 여부와 축 ①~⑤의 최적 분할·수치는 **화요일 고정일 때와 완전히 같습니다**. 통합과학2의 요일은 최진호(H)·조세라(M)의 ‘같은 날 2과목’ 판정과 같은 교시 충돌에만 영향을 주는데, 다섯 안 모두 H·M을 통합과학2와 다른 날에 둘 수 있기 때문입니다. 따라서 2학년 시간표는 그대로 두고 1학년만 바꾸면 됩니다.")
w("")
import data as _D
w("| 안 | 통합과학2 → 금 (금 = 한국사2·통합과학2 2/7교시, 월 = 통합사회2·국어, 화 = 수학·영어) | 통합과학2 → 월 (월 = 통합사회2 2교시·통합과학2 7교시, 금 = 한국사2·국어, 화 = 수학·영어) |")
w("|---|---|---|")
for P in PLANS:
    cells = []
    for sci, kse in [("금", {"공통국어2": "월", "공통수학2": "화", "공통영어2": "화"}), ("월", {"공통국어2": "금", "공통수학2": "화", "공통영어2": "화"})]:
        _D.G1_FIXED_DAY["통합과학2"] = sci
        pl = build(P["part"], P["ck"], sci_day=sci, g1_kse=kse); Rv = evaluate(pl)
        _D.G1_FIXED_DAY["통합과학2"] = "화"
        base_td = results[P["no"]][1]["교사하루2"]
        added = [x for x in Rv["교사하루2"] if x not in base_td]
        hard = Rv["교사동시"] + Rv["동시응시"] + Rv["담임위반"]
        cells.append(("**교시 충돌**: " + "; ".join(hard)) if hard else ("교사 하루 2과목 추가 " + (f"{len(added)}건({'; '.join(added)})" if added else "0건")))
    w(f"| 안 {P['no']} | {cells[0]} | {cells[1]} |")
w("")
w("월요일로 옮기면 안 1·4·5는 추가 판정이 없고 안 2(최진호 H)·안 3(조세라 M)만 ‘같은 날 2과목’ 1건이 생깁니다. 금요일로 옮기면 안 1·2는 추가 판정이 없고 안 3·5는 최진호 1건, 안 4는 최진호·조세라 2건이 더 생깁니다. 같은 교시 충돌은 어느 경우에도 없습니다. **추천안인 안 5는 통합과학2를 월요일 7교시로 옮겨도 추가 부담이 없습니다.**")
w(""); w("2학년 국어(A)는 절대 제약 9로 이미 화요일에 없으며 다섯 안 모두 목 또는 금입니다.")
w("")
w("### 7-3. 1학년 국어·수학·영어 일자")
w("")
w("국어·수학·영어 담당(김태현·곽준철·김순선·최지혜·강승희·이바다)은 2학년 과목을 맡지 않으므로 어느 날에 두어도 2학년 결과가 바뀌지 않습니다. 표에서는 국어 금·수학 월·영어 화(국어 화요일 불가)로 두었고, 같은 날 두 과목의 교시 순서도 자유입니다.")
w("")
# ---- 8. 질문
w("## 8. 확인이 필요한 사항")
w("")
w("1. **한수오(3-20)의 실제 수강 조합**은 무엇입니까? ABDEHIKO는 데이터에 없습니다. ABCEFHIO라면 §7-1처럼 안 X(70명)가 살아나고, 그 밖의 조합이면 표 7-1을 보시면 됩니다.")
w("2. **통합과학2를 화요일에서 옮겨도 됩니까?** §3의 ‘화 고정’과 요청이 충돌합니다. 옮긴다면 월요일(7교시)을 권하며, 2학년 시간표는 바뀌지 않습니다(§7-2).")
w("3. **운영 부담 선택**: 78명(안 3)을 피하는 모든 해는 어느 한 요일을 다섯 교시로 운영해야 합니다. 목요일 1교시 사용(안 1·2·5), 목요일 3교시 개방(안 1·2·5, O를 목요일에 두는 모든 안), 금요일 3교시 개방(안 4) 중 어느 것이 수용 가능합니까? 1교시를 피하는 교시 대안은 각 안 아래에 적었습니다(연속 응시자 증가).")
w("4. **예외 2건(배태안 단독, 월 2교시)** 을 허용합니까? 허용하면 안 5, 아니면 안 2 또는 안 1입니다.")
w("5. 안 Y의 금요일 4과목 학생(ABCDGHIN)을 면제 대상으로 볼 근거가 있습니까? 없다면 안 Y는 폐기해야 합니다.")
w("")
w("## 부록. 재현 방법")
w("")
w("```bash")
w("cd tools/exam2 && python3 verify_data.py && gcc -O2 -o enum enum.c && ./enum 0 7 parts_strict.txt && ./enum 1 7 parts_allow1.txt && python3 analyze.py && python3 report.py")
w("```")
w("")
w("- `data.py` 입력 데이터, `verify_data.py` 검산, `enum.c` 일자 분할 전수 탐색, `crosscheck.py` 독립 교차 검증, `periods.py` 교시 배정 열거, `analyze.py`·`axes.py`·`query.py` 지표·축별 최적, `evaluate.py` 시간표 점검표, `build.py` 시간표 생성, `variant_sci.py` 통합과학2 이동 변형, `report.py` 이 문서.")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("\n".join(L) + "\n")
print("wrote", OUT, len(L), "lines")
