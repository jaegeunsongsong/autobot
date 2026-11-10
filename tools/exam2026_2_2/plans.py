"""최종 5개 안과 보고서(마크다운) 생성."""
import pickle, sys
from collections import Counter
from report import *
from layer1 import enumerate_day_assignments, metrics
from layer2 import units_of

NO1 = dict(FULL); NO1["목"] = (2, 3, 4, 5, 6, 7)

PLANS = [
    dict(pid="①", title="화요일 2과목 · 3학년 담임 예외 1건 · 계열 중복 47명 (추천)",
         days={"목": "EGMNOP", "금": "AFIJ", "월": "BHKL", "화": "CD"}, allowed=NO1,
         cost=["목요일을 2·3·4·5·7 다섯 교시로 운영한다. 연속 교시 2건(2-3교시 G→O 1명, 3-4교시 O→M 3명)이 생긴다. 목요일 1교시를 쓰면(변형 ①-a: M 1교시·O 3교시·G 4교시) 연속은 1건 1명(3-4교시 O→G)으로 줄지만 08:40 시작 부담이 생긴다.",
               "J+O 쌍을 풀어 15교시를 쓴다. O는 목 3교시(정인광·손경준 공강), J는 금 7교시.",
               "금요일(A·F·I·J) 3과목 학생이 55명으로 네 날 중 가장 많다. 표준안(70명)보다는 적다.",
               "같은 날 같은 계열이 목요일에 2건(E+O 사회 25명, G+M 과학 22명) 남는다. 화 2과목 구조에서 계열 중복의 최솟값이다."]),
    dict(pid="②", title="하루 3과목 인원 최소 (최대 36명) · 예외 1건 · 화요일 2과목",
         days={"목": "EHJKMO", "금": "AFIP", "월": "BGLN", "화": "CD"}, allowed=FULL,
         cost=["목요일에 6과목을 1·2·3·4·5·7 여섯 교시로 치른다(1교시 포함). 연속 교시 3건 6명(1-2교시 K→H 3명, 2-3교시 H→O 3명, 3-4교시 O→J 0명). 1교시를 쓰지 않으면(J2·O3·M4·E5·H6·K7) 연속이 4건 21명으로 늘어난다.",
               "같은 날 같은 계열이 6건 138명(목요일에 사회 E·K·O, 과학 H·J·M이 몰림). §6-4와 같은 값이다.",
               "§6-4의 36/32/36 안이 금요일에 두었던 묶음을 목요일로 옮긴 구조다. 그 덕에 O가 금요일에서 빠져 정인광·손경준의 하루 2과목(한국사2+O)이 사라진다.",
               "목요일 감독 교시가 6개라 교사 대기 부담이 가장 크다."]),
    dict(pid="③", title="같은 날 같은 계열 0건 (화요일 3과목 구조)",
         days={"목": "DEHL", "금": "AFKM", "월": "BJNOP", "화": "CGI"}, allowed=FULL,
         cost=["화요일에 3과목(G·I·C)을 1·2·4교시로 치러 마지막 날 3과목 학생이 4명(ABCDFGHI, ABCDGHIL, ABCDGHIN, ABCDGIJL 각 1명, 모두 일반 학생) 생긴다. 최우선 목표를 어긴다.",
               "화요일 1교시(08:40)를 쓰고, 1-2교시 연속(G→I 4명, 위 4명과 동일)이 생긴다. 1교시를 피해 2·3·4교시로 하면 연속이 73명 이상으로 뛴다.",
               "J+O 쌍이 월요일 2교시로 가서 3학년 담임 예외가 3건(박현수·배태안·손경준)이다.",
               "계열 중복 0건은 화요일 2과목 구조에서는 불가능하고(최솟값 47명), 예외 1건과 함께 하려면 화요일 3과목 학생이 15명 이상이 된다."]),
    dict(pid="④", title="연속 교시 0건 · 전 요일 2·4·5·7 동일 체계 (표준 4·4·4·2)",
         days={"목": "BEHI", "금": "AGLNP", "월": "DFKM", "화": "CJO"}, allowed=FULL,
         cost=["3학년 담임 예외 3건(박현수·배태안·손경준, 모두 월·화 2교시). 이 구조에서는 피할 수 없다(증명 4-3).",
               "목요일(B·E·H·I) 3과목 학생 70명. 이 구조의 최솟값이며, 도움반 학생 1명은 4과목(면제).",
               "같은 날 같은 계열 2건 51명(목 E+I 사회 50명, 금 L+P 제2외국어 1명).",
               "목요일을 D·F·K·M, 금요일을 A·E·H·I로 바꾼 거울상(3과목 40/70/39)도 같은 값이다. 1학년과 교시가 완전히 맞고 연속 교시가 없어 운영이 가장 단순하다."]),
    dict(pid="⑤", title="화요일 3과목 구조의 최선 — 마지막 날 3과목 1명 · 예외 2건 (참고안)",
         days={"목": "BEHI", "금": "AJLNP", "월": "DFKM", "화": "CGO"}, allowed=FULL,
         cost=["화요일 3과목 구조에서 마지막 날 3과목 학생의 최솟값은 1명(ABCDFGKO, 일반 학생)이고 이 안이 그것을 달성한다. 0명은 불가능하다(증명 4-1).",
               "그 1명이 화요일 1-2교시(G→O) 연속 응시자이기도 하다. 화요일 1교시를 쓴다.",
               "표준안 ④에서 J만 금요일 4교시로 빼고 G를 화요일로 옮긴 꼴이라, 목요일 70명·계열 51명은 그대로다. 예외는 배태안이 빠져 2건(박현수·손경준).",
               "교사 부담(하루 2과목·예외) 축의 최적은 예외 1건·하루 2과목 0건이고 ①·②가 이미 달성하므로 별도 안을 두지 않았다."]),
]


def build():
    out = []
    rows = []
    for P in PLANS:
        a = assign_from(P["days"])
        extra = ""
        if P["pid"] == "①":
            tt1 = best_timetable(a, allowed=FULL)
            m1 = full_metrics(a, tt1)
            extra = ("변형 ①-a (목요일 1교시 사용): 목 " + ", ".join(f"{s}{p}" for s, p in sorted(tt1[3]['목'].items(), key=lambda x: x[1]))
                     + f" → 연속 {len(m1['consec'])}건 {m1['consec_n']}명 (" + "; ".join(f"{p1}-{p2}교시 {'+'.join(x)}→{'+'.join(y)} {n}명" for d, p1, p2, x, y, n in m1['consec']) + "). 나머지 요일과 모든 인원 지표는 동일.")
        md, m, r, tt = plan_md(P["pid"], P["title"], a, allowed=P["allowed"], cost_lines=P["cost"], extra_md=extra)
        out.append(md)
        r["pid"] = P["pid"]; r["title"] = P["title"]; r["m"] = m
        rows.append(r)
    return out, rows


def compare_md(rows):
    hdr = ["항목"] + [r["pid"] for r in rows]
    lines = ["| " + " | ".join(hdr) + " |", "|---|" + "---|" * len(rows)]
    def add(name, f):
        lines.append("| " + name + " | " + " | ".join(str(f(r)) for r in rows) + " |")
    add("요일 배정", lambda r: " / ".join(f"{d} {r['days'][d]}" for d in DAYS))
    add("교시 수 (목·금·월·화)", lambda r: "·".join(str(len(set(r["periods"][d].values()))) for d in DAYS))
    add("목요일 교시", lambda r: "·".join(map(str, sorted(set(r["periods"]["목"].values())))))
    add("화요일 교시", lambda r: "·".join(map(str, sorted(set(r["periods"]["화"].values())))))
    add("마지막 날 3과목 이상", lambda r: f"{r['tue3_all']}명")
    add("3학년 담임 예외", lambda r: f"{r['exc']}건")
    add("교사 하루 2과목", lambda r: f"{r['t2']}건")
    add("하루 3과목 (목/금/월/화)", lambda r: "/".join(map(str, r["three"])) + f" (최대 {r['max3']}, 합 {r['sum3']})")
    add("하루 4과목 (면제 외)", lambda r: "0명")
    add("같은 날 같은 계열", lambda r: f"{r['dup_cnt']}건 {r['dup_n']}명")
    add("연속 교시", lambda r: f"{r['consec_cnt']}건 {r['consec_n']}명")
    add("1교시 사용", lambda r: ", ".join(d for d in DAYS if 1 in set(r["periods"][d].values())) or "없음")
    add("1학년 교시와 어긋남 (금·월·화)", lambda r: "; ".join(f"{d} {','.join(map(str,ps))}교시" for d, ps in r["dev_detail"] if d != "목") or "없음")
    def pairs(r):
        out = []
        for d in DAYS:
            p = r["periods"][d]
            if "J" in p and "O" in p and p["J"] == p["O"]: out.append(f"J+O 동시({d}{p['J']})")
            if "N" in p and "P" in p and p["N"] == p["P"]: out.append(f"N+P 동시({d}{p['N']})")
        return ", ".join(out) or "쌍 미사용"
    add("동시 시행 쌍", pairs)
    return "\n".join(lines)


if __name__ == "__main__":
    plans_md, rows = build()
    for r in rows:
        print(r["pid"], r["shape"], r["days"], "exc", r["exc"], "tue3", r["tue3_all"], "3과목", r["three"], "계열", r["dup_cnt"], r["dup_n"], "연속", r["consec_cnt"], r["consec_n"], "t2", r["t2"], "dev", r["dev_detail"], "k", r["k"])
