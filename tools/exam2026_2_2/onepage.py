"""첨부 양식(한 장짜리 시간표)과 같은 레이아웃으로 안을 PDF 로 렌더링."""
import glob, math, sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from data import *
from layer1 import day_sets
from layer2 import g1_slots
from evaluate import best_timetable, full_metrics, FULL

FONT_DIR = "/usr/share/fonts/truetype/nanum/"
def _font(cands):
    for c in cands:
        p = glob.glob(FONT_DIR + c)
        if p: return p[0]
    raise FileNotFoundError(cands)
pdfmetrics.registerFont(TTFont("KR", _font(["NanumGothic.ttf", "NanumBarunGothic.ttf"])))
pdfmetrics.registerFont(TTFont("KR-B", _font(["NanumGothicBold.ttf", "NanumBarunGothicBold.ttf"])))
pdfmetrics.registerFontFamily("KR", normal="KR", bold="KR-B", italic="KR", boldItalic="KR-B")

G1_N = 156
GRAY = colors.HexColor("#999999")
DARK = colors.HexColor("#555555")
HEAD_BG = colors.HexColor("#e9e9e9")
GREEN_BG = colors.HexColor("#e6f2df")

def P(text, size=8, bold=False, color=colors.black, align=TA_CENTER, leading=None):
    st = ParagraphStyle("x", fontName="KR-B" if bold else "KR", fontSize=size, leading=leading or size * 1.25,
                        alignment=align, textColor=color)
    return Paragraph(text, st)

def subj_para(items):
    """items: list of (name, n, teachers)."""
    names = " /<br/>".join(f"<b>{nm}</b> {n}명" for nm, n, _ in items)
    teachers = " / ".join("·".join(t) for _, _, t in items)
    return P(f"{names}<br/><font size=6 color='#555555'>{teachers}</font>", size=8, leading=9.5)

def build_cells(assign, tt):
    cost, k, h, per = tt
    ds = day_sets(assign)
    cells = {}   # (day, grade, period) -> list items
    for d in DAYS:
        bp = {}
        for s, p in per[d].items():
            bp.setdefault(p, []).append(s)
        for p, L in bp.items():
            cells[(d, 2, p)] = [(NAMES[s], enrol(s), TEACHERS[s]) for s in sorted(L)]
        for g, gp in g1_slots(d, k, h):
            cells.setdefault((d, 1, gp), []).append((g, G1_N, G1[g]))
    return cells

def render(assign, tt, m, label, tagline, out_pdf, extra_lines=()):
    cells = build_cells(assign, tt)
    doc = SimpleDocTemplate(out_pdf, pagesize=landscape(A4), leftMargin=9*mm, rightMargin=9*mm, topMargin=8*mm, bottomMargin=8*mm,
                            title=f"2026학년도 2학기 2차 정기시험 시간표 ({label})")
    story = []
    story.append(P(f"2026학년도 2학기 2차 정기시험 시간표 ({label})", size=16, bold=True, leading=20))
    story.append(Spacer(1, 2*mm))
    story.append(P("1학년 156명 12/11(금)~12/15(화) 3일간 · 2학년 176명 12/10(목)~12/15(화) 4일간 · 3학년 2차 지필평가 없음", size=8.5, color=DARK))
    story.append(Spacer(1, 3*mm))

    # ---- 본표 ----
    periods = [1, 2, 3, 4, "점심", 5, 6, 7]
    header1 = [P("교시", 8, True), P("시간", 8, True)]
    for d in DAYS:
        header1 += [P(DATES[d], 8.5, True), ""]
    header2 = ["", ""] + [P(g, 7.5, True) for d in DAYS for g in ("1학년", "2학년")]
    data = [header1, header2]
    row_h = [5.5*mm, 5*mm]
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "KR"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#444444")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, 1), HEAD_BG),
        ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1)),
        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    for i, d in enumerate(DAYS):
        c = 2 + 2*i
        style.append(("SPAN", (c, 0), (c+1, 0)))
    for ri, p in enumerate(periods):
        r = 2 + ri
        if p == "점심":
            data.append([P("점심", 7.5, True), P("12:45~13:45", 7.5)] + [""] * 8)
            style += [("SPAN", (2, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f3f3f3"))]
            row_h.append(4.5*mm)
            continue
        row = [P(str(p), 8, True), P(PERIOD_TIME[p], 7.5)]
        maxn = 0
        for d in DAYS:
            for g in (1, 2):
                items = cells.get((d, g, p))
                if d == "목" and g == 1:
                    row.append(P("정 상 수 업", 8, color=DARK) if p in (1, 5) else "")
                elif d == "화" and p >= 5:
                    row.append(P("4교시 후 중식 뒤 귀가", 8, color=DARK) if (g == 1 and p == 5) else "")
                elif items:
                    row.append(subj_para(items)); maxn = max(maxn, len(items))
                else:
                    row.append(P("자습", 7, color=GRAY))
        data.append(row)
        row_h.append({0: 5.5*mm, 1: 12.5*mm, 2: 16*mm}.get(min(maxn, 2)) if maxn else 5.5*mm)
    # 목요일 1학년 '정상수업' 병합(1~4교시, 5~7교시), 화요일 귀가 병합(5~7교시 × 2열)
    style += [("SPAN", (2, 2), (2, 5)), ("SPAN", (2, 7), (2, 9)), ("SPAN", (8, 7), (9, 9))]
    t = Table(data, colWidths=[11*mm, 21*mm] + [30.5*mm] * 8, rowHeights=row_h)
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(P("※ 1학년 12/10(목)은 정상 수업 ※ 12/15(화)는 4교시 후 중식 뒤 귀가 ※ 한 칸의 두 과목은 같은 교시·다른 시험실 시행(중복 수강자 0명) ※ 작은 글씨는 담당교사 ※ 인원은 전출·자퇴·위탁 반영 응시 대상", size=7.5, color=DARK, leading=10))
    story.append(Spacer(1, 4*mm))

    # ---- 분포표 + 요약 ----
    dist = m["dist"]
    dd = [[P("응시", 8, True)] + [P(DATES[d], 8, True) for d in DAYS]]
    for kk in range(5):
        dd.append([P(f"{kk}회", 8, kk in (0, 4))] + [P(str(dist[d].get(kk, 0)), 8, kk in (0, 4)) for d in DAYS])
    dt = Table(dd, colWidths=[18*mm] + [27*mm] * 4, rowHeights=[6*mm] * 6)
    dt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "KR"), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#444444")),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("BACKGROUND", (0, 1), (-1, 1), GREEN_BG), ("BACKGROUND", (0, 5), (-1, 5), GREEN_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    four = sum(n for c, n in COMBOS for d in DAYS if len(set(c) & day_sets(assign)[d]) >= 4)
    four_reg = sum(n for c, n in COMBOS for d in DAYS if len(set(c) & day_sets(assign)[d]) >= 4 and c not in (EXEMPT_ALL, EXEMPT_FOUR))
    lines = ["1학년 156명(6과목) · 2학년 176명(16과목) · 전원 1인 8과목",
             f"{label} — {tagline}",
             f"하루 3과목 최대 {m['max3']}명 · 마지막날 3과목 {m['tue3_all']}명",
             f"4과목 {four}명{('(일반 학생 ' + str(four_reg) + '명, 하루 4과목 금지 위반)') if four_reg else ('(도움반 1명, 면제)' if four else '(도움반 포함)')} · 교사 하루 2과목 {len(m['teacher2'])}건",
             f"계열 중복 {m['dup_n']}명({len(m['dup'])}건) · 3학년담임 예외 {len(m['exc'])}건",
             f"연속 교시 {len(m['consec'])}건 {m['consec_n']}명"] + list(extra_lines)
    summary = P("<br/>".join(lines), size=8, leading=12)
    left = [[P("2학년 일자별 응시 횟수 분포", 9, True)], [dt]]
    lt = Table(left, colWidths=[126*mm]); lt.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("BOTTOMPADDING", (0, 0), (0, 0), 3)]))
    outer = Table([[lt, summary]], colWidths=[130*mm, 140*mm])
    outer.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(outer)
    doc.build(story)
    return out_pdf


def tt_from_periods(periods, k, h):
    return ((0,), k, h, periods)


if __name__ == "__main__":
    from report import assign_from
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    # 1) 첨부 B안 재현(양식 검증용): 목 A2 L4 N+P5 H7 / 금 C2 E4 G5 I7 / 월 D2 F4 K5 M7 / 화 J+O2 B4, 통합과학2 금, 한국사2 금 2교시
    a = assign_from({"목": "AHLNP", "금": "CEGI", "월": "DFKM", "화": "BJO"})
    tt = tt_from_periods({"목": {"A": 2, "L": 4, "N": 5, "P": 5, "H": 7}, "금": {"C": 2, "E": 4, "G": 5, "I": 7},
                          "월": {"D": 2, "F": 4, "K": 5, "M": 7}, "화": {"J": 2, "O": 2, "B": 4}}, k=1, h=2)
    m = full_metrics(a, tt)
    render(a, tt, m, "B안", "4과목 완전 0명형 · 전 요일 2·4·5·7", f"{out_dir}/B안-재현.pdf")
    print("B안 재현", m["max3"], m["tue3_all"], m["dup_n"], len(m["exc"]), len(m["teacher2"]), m["consec_n"])
