"""최종안 정리 문서(마크다운 + PDF)."""
import math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from onepage import P, pdfmetrics, HEAD_BG, GREEN_BG, DARK, GRAY   # 폰트 등록 재사용
from data import *
from layer1 import day_sets
from layer2 import g1_slots
from evaluate import full_metrics
from report import assign_from, timetable_md, dist_md, checklist_md
from onepage import tt_from_periods

OUT = "/home/user/autobot/docs/2026-2학기-2차-정기시험-시간표"
assign = assign_from({"목": "BJLNOP", "금": "AEGI", "월": "DFKM", "화": "CH"})
PER = {"목": {"L": 1, "J": 3, "O": 3, "B": 5, "N": 7, "P": 7}, "금": {"A": 2, "E": 4, "G": 5, "I": 7},
       "월": {"D": 2, "F": 4, "K": 5, "M": 7}, "화": {"H": 2, "C": 4}}
tt = tt_from_periods(PER, k=1, h=2)
m = full_metrics(assign, tt)
ds = day_sets(assign)
four = [(d, c) for d in DAYS for c, n in COMBOS if len(set(c) & ds[d]) >= 4]
cnt = lambda c, d: len(set(c) & ds[d])

decisions = [
    "세포와물질대사(J)+동아시아역사기행(O)은 한 묶음으로 목요일 3교시(정인광·손경준 공강).",
    "월·화요일 3학년 담임 잔류는 각 1명 이하: 월 박현수(통합사회2 2교시) 1명, 화 0명.",
    "모든 날 4교시 이하. 목 1·3·5·7, 금·월 2·4·5·7(1학년과 동일), 화 2·4(1학년과 동일).",
    "마지막 날(화) 3과목 학생 0명. 연속 교시 0건. 교사 하루 2과목 0건.",
    "대가: 목요일 4과목 학생 3명(일반 학생, 하루 4과목 금지 위반), 목요일 1교시 사용, 금요일 3과목 78명.",
]
notes = [
    "하루 4과목 금지는 의뢰서의 절대 제약(면제는 도움반 1명·체육부 2명)이므로, 아래 3명에 대한 양해 또는 예외 처리가 전제다. 심화일본어를 목요일 밖으로 옮기면 그날이 5교시가 되고, 화요일을 3과목으로 하면 화요일 3과목 학생이 3명 이상 생긴다.",
    "목요일 1교시(08:40) 심화일본어는 등교 직후 시작이다. 1교시를 피하려면 심화일본어를 2교시 또는 4교시로 옮겨야 하는데, 그러면 3교시 J+O와 붙어 연속 교시가 생긴다(심화일본어와 세포와물질대사 5명 + 동아시아역사기행 17명 = 22명).",
    "금요일(독서와작문·인문학과윤리·화학반응의세계·한국지리탐구) 3과목 학생 78명은 B안과 같은 값이다. 목·금을 바꾸거나(목 A·E·G·I) 다른 배열로 낮추려면 J+O 목요일 조건과 충돌한다.",
    "같은 날 같은 계열: 금 인문학과윤리+한국지리탐구(사회) 50명, 목 심화일본어+심화중국어(제2외국어) 1명.",
    "1학년: 금 = 한국사2(2교시)+통합과학2(7교시), 월 = 통합사회2(2교시)+공통국어2(7교시), 화 = 공통수학2(2교시)+공통영어2(4교시). 월요일 지구시스템과학(조세라) 때문에 통합과학2는 금요일이어야 한다. 금요일 두 과목의 2·7교시 순서는 바꿔도 된다.",
]
changes_vs_B = [
    "B안: 목 A·L·N+P·H / 금 C·E·G·I / 월 D·F·K·M / 화 J+O·B (예외 월 1 + 화 2, 3과목 39/78/40/0).",
    "최종안: J+O를 화요일 2교시에서 목요일 3교시로, 독서와작문을 목요일에서 금요일로, 영어II를 금요일에서 화요일로, 역학과에너지를 목요일에서 화요일로, 미적분I을 화요일에서 목요일로 옮겼다.",
    "그 결과 화요일 3학년 담임 2명이 0명이 되고 연속 교시 없이 4교시 체계가 유지되지만, 목요일 4과목 3명이 생긴다.",
]

# ---------- 마크다운 ----------
md = []
md.append("# 2026학년도 2학기 2차 정기시험 시간표 최종안 정리\n")
md.append("## 1. 결정 사항\n")
md += [f"- {x}" for x in decisions]
md.append("\n## 2. 배치표\n")
md.append(timetable_md(assign, tt))
md.append("\n## 3. 2학년 응시 횟수 분포\n")
md.append(dist_md(assign))
md.append("\n## 4. 제약 점검표\n")
md.append(checklist_md(assign, tt, m))
md.append("\n## 5. 목요일 4과목 학생 3명\n")
md.append("| 수강 조합 | 인원 | 목요일 응시 |\n|---|---|---|")
for d, c in four:
    md.append(f"| {c} | 1 | " + ", ".join(f"{NAMES[s]}({PER['목'][s]}교시)" for s in sorted(set(c) & ds['목'], key=lambda s: PER['목'][s])) + " |")
md.append("\n데이터에 이름이 없어 조합으로만 특정된다. 각 조합은 1명이다.\n")
md.append("## 6. 유의사항\n")
md += [f"- {x}" for x in notes]
md.append("\n## 7. B안과의 차이\n")
md += [f"- {x}" for x in changes_vs_B]
open(f"{OUT}/최종안-정리.md", "w").write("\n".join(md) + "\n")

# ---------- PDF ----------
doc = SimpleDocTemplate(f"{OUT}/최종안-정리.pdf", pagesize=A4, leftMargin=14*mm, rightMargin=14*mm, topMargin=12*mm, bottomMargin=12*mm,
                        title="2026학년도 2학기 2차 정기시험 시간표 최종안 정리")
L = lambda t, size=9, bold=False: Paragraph(t, ParagraphStyle("l", fontName="KR-B" if bold else "KR", fontSize=size, leading=size*1.45, alignment=TA_LEFT))
H = lambda t: Paragraph(t, ParagraphStyle("h", fontName="KR-B", fontSize=12, leading=16, spaceBefore=8, spaceAfter=4))
story = [Paragraph("2026학년도 2학기 2차 정기시험 시간표 최종안 정리", ParagraphStyle("t", fontName="KR-B", fontSize=16, leading=20, alignment=TA_CENTER)), Spacer(1, 2*mm),
         P("1학년 156명 12/11(금)~12/15(화) · 2학년 176명 12/10(목)~12/15(화) · 3학년 2차 지필평가 없음", 8.5, color=DARK), Spacer(1, 4*mm)]
def bullets(items):
    return [L("• " + x) for x in items]
story.append(H("1. 결정 사항")); story += bullets(decisions)
# 배치표 (세로형: 교시 × 요일, 1·2학년 함께)
story.append(H("2. 배치표"))
cells = {}
for d in DAYS:
    bp = {}
    for s, p in PER[d].items(): bp.setdefault(p, []).append(s)
    for p, Ls in bp.items():
        cells[(d, p)] = "<br/>".join(f"<b>{NAMES[s]}</b> {enrol(s)}명 <font size=6.5 color='#555555'>{'·'.join(TEACHERS[s])}</font>" for s in sorted(Ls))
    for g, gp in g1_slots(d, 1, 2):
        cells[(d, gp)] = (cells.get((d, gp), "") + ("<br/>" if (d, gp) in cells else "")) + f"<font color='#1f5fa8'>1학년 {g}</font> <font size=6.5 color='#555555'>{'·'.join(G1[g])}</font>"
data = [[P("교시", 8, True), P("시각", 8, True)] + [P(DATES[d], 8, True) for d in DAYS]]
for p in range(1, 8):
    row = [P(str(p), 8, True), P(PERIOD_TIME[p], 7.5)]
    for d in DAYS:
        if d == "화" and p >= 5: row.append(P("귀가", 7, color=GRAY)); continue
        row.append(P(cells[(d, p)], 7.5, leading=9.5) if (d, p) in cells else P("1학년 수업" if d == "목" else "자습", 7, color=GRAY))
    data.append(row)
    if p == 4:
        data.append([P("점심", 7.5, True), P("12:45~13:45", 7.5)] + [""] * 4)
t = Table(data, colWidths=[11*mm, 24*mm] + [36.5*mm] * 4)
t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "KR"), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")), ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#444444")),
                       ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                       ("SPAN", (2, 5), (-1, 5)), ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#f3f3f3")),
                       ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
story.append(t)
story.append(L("1학년 목요일은 1~7교시 정상 수업. 화요일은 4교시 후 중식 뒤 귀가. 한 칸의 두 2학년 과목은 같은 교시·다른 시험실(중복 수강자 0명).", 7.5))
# 분포
story.append(H("3. 2학년 응시 횟수 분포 (전체 176명)"))
dd = [[P("응시", 8, True)] + [P(DATES[d], 8, True) for d in DAYS]]
for kk in range(5):
    dd.append([P(f"{kk}회", 8, kk in (0, 4))] + [P(str(m["dist"][d].get(kk, 0)), 8, kk in (0, 4)) for d in DAYS])
dd.append([P("면제: 한수오 ABCEFHIO", 7.5)] + [P(str(cnt(EXEMPT_ALL, d)), 7.5) for d in DAYS])
dd.append([P("면제: 체육부 ABCDFILM 2명", 7.5)] + [P(str(cnt(EXEMPT_FOUR, d)), 7.5) for d in DAYS])
dt = Table(dd, colWidths=[42*mm] + [30*mm] * 4, rowHeights=[6*mm] * 8)
dt.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "KR"), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")), ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#444444")),
                        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("BACKGROUND", (0, 1), (-1, 1), GREEN_BG), ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#fde9e7")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
story.append(dt)
story.append(L("4회 행의 3명은 목요일 일반 학생이다(5절). 면제 학생 행은 그 학생의 하루 응시 횟수.", 7.5))
story.append(PageBreak())
# 점검표
story.append(H("4. 제약 점검표"))
ok = lambda b: "OK" if b else "위반"
rows = [
    ("같은 교시 동시 응시자 0명", "OK", "같은 교시 공유는 J+O(목 3교시), N+P(목 7교시)뿐, 겹침 0명"),
    ("같은 교시 담당교사 중복 0건", "OK", "1학년 과목 포함 교시 단위 검사 통과"),
    ("목요일 1학년 수업 충돌 0건", "OK", "L 1교시(신향숙 수업 없음), J+O 3교시(손경준 1·2·4, 정인광 5·7 수업 회피), B 5교시, N+P 7교시"),
    ("전이슬 화·목 1~4교시 저촉 0건", "OK", "심화중국어 목 7교시"),
    ("3학년 담임 월·화 배치", "월 1명 · 화 0명", "박현수 통합사회2 월 2교시. 배태안·손경준은 목 3교시"),
    ("교사 하루 2과목 (1학년 포함)", "0건", "김미애·노석환(월 통합사회2) 과목은 금요일, 최진호 역학과에너지 화요일·통합과학2 금요일, 조세라 지구시스템과학 월요일·통합과학2 금요일, 구성희 B 목·D 월, 정인광·손경준 한국사2 금·O 목"),
    ("같은 날 같은 계열", "2건 51명", "금 인문학과윤리+한국지리탐구(사회) 50명, 목 심화일본어+심화중국어(제2외국어) 1명"),
    ("A·B·C 서로 다른 날", "OK", "A 금, B 목, C 화"),
    ("마지막 날 국어 없음", "OK", "화 = 역학과에너지·영어II, 공통국어2 월"),
    ("마지막 날 3과목 이상", "0명", ""),
    ("하루 4과목", "3명 (위반)", "목 ABCDFLNO, ABCDKLNO, ABCFKLNO 각 1명, 일반 학생"),
    ("하루 0과목", "0명", ""),
    ("하루 3과목 (전체 176명)", "최대 78명", "목 54 / 금 78 / 월 40 / 화 0 (합 172)"),
    ("연속 교시 배치", "0건", "목 1·3·5·7, 화 2·4"),
    ("교시별 시험실 ≤ 9실", f"최대 {m['rooms_max']}실", "목 1교시 3실·3교시 5실·5교시 9실·7교시 4실 / 금 9·5·5·4 / 월 9·5·3·3 / 화 2교시 4실·4교시 9실"),
    ("1학년 교시와 어긋남 / 1교시", "금·월·화 없음 / 목 1교시 사용", ""),
]
ct = Table([[P("항목", 8, True), P("결과", 8, True), P("내역", 8, True)]] + [[L(a, 8), L(b, 8, b.endswith("위반)") or b == "위반"), L(c, 7.5)] for a, b, c in rows], colWidths=[46*mm, 30*mm, 106*mm])
ct.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "KR"), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")), ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#444444")),
                        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 11), (-1, 11), colors.HexColor("#fde9e7"))]))
story.append(ct)
story.append(H("5. 목요일 4과목 학생 3명"))
ft = Table([[P("수강 조합", 8, True), P("인원", 8, True), P("목요일 응시 과목", 8, True)]] +
           [[L(c, 8), L("1", 8), L(", ".join(f"{NAMES[s]}({PER['목'][s]}교시)" for s in sorted(set(c) & ds['목'], key=lambda s: PER['목'][s])), 8)] for d, c in four],
           colWidths=[30*mm, 14*mm, 138*mm])
ft.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "KR"), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")), ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
story.append(ft)
story.append(L("데이터에 이름이 없어 수강 조합으로만 특정된다. 세 명 모두 심화일본어·프로그래밍·동아시아역사기행을 함께 듣는다.", 8))
story.append(H("6. 유의사항")); story += bullets(notes)
story.append(H("7. B안과의 차이")); story += bullets(changes_vs_B)
doc.build(story)
print("written", f"{OUT}/최종안-정리.pdf", f"{OUT}/최종안-정리.md")
