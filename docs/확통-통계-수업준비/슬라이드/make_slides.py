# -*- coding: utf-8 -*-
"""확률과 통계 Ⅲ 통계 — 수업용 슬라이드(16:9) HTML 생성기.

사용법
  python3 make_slides.py --out-dir <폴더>                # MathJax·글꼴을 CDN에서 불러오는 HTML
  python3 make_slides.py --out-dir <폴더> --assets <dir>  # <dir>의 tex-svg.js, nanum-400/700.woff2 를 내장 (PDF 변환용)
이후 slides_pdf.js 로 PDF 변환:  node slides_pdf.js <html> <pdf>
"""
import argparse, math, pathlib

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, AXIS = "#1b1b1b", "#666", "#9a9a9a"

# ---------------------------------------------------------------- SVG helpers
def npdf(x, m, s):
    return math.exp(-0.5 * ((x - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))

def linspace(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]

def normal_svg(curves, shade=(), ticks=(), vlines=(), W=560, H=240, xr=None, notes=(), base_labels=True):
    """curves: [dict(m,s,color,label)], shade: [dict(a,b,color,op,curve)], ticks: [(x,label)],
    vlines: [(x,label)], notes: [(x, yfrac, text, color)]"""
    pl, pr, pt, pb = 14, 14, 26, 40
    if xr is None:
        xr = (min(c["m"] - 3.6 * c["s"] for c in curves), max(c["m"] + 3.6 * c["s"] for c in curves))
    xmin, xmax = xr
    ymax = max(npdf(c["m"], c["m"], c["s"]) for c in curves) * 1.08
    X = lambda x: pl + (x - xmin) / (xmax - xmin) * (W - pl - pr)
    Y = lambda y: H - pb - y / ymax * (H - pt - pb)
    out = ['<svg class="fig" viewBox="0 0 %d %d" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
    for sh in shade:
        c = curves[sh.get("curve", 0)]
        a, b = max(sh["a"], xmin), min(sh["b"], xmax)
        pts = [(X(a), Y(0))] + [(X(x), Y(npdf(x, c["m"], c["s"]))) for x in linspace(a, b, 90)] + [(X(b), Y(0))]
        out.append('<polygon points="%s" fill="%s" fill-opacity="%.2f"/>' % (
            " ".join("%.1f,%.1f" % p for p in pts), sh.get("color", BLUE), sh.get("op", 0.35)))
    out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.5"/>' % (pl, Y(0), W - pr, Y(0), AXIS))
    for c in curves:
        pts = [(X(x), Y(npdf(x, c["m"], c["s"]))) for x in linspace(xmin, xmax, 240)]
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.5" stroke-linejoin="round"/>' % (
            " ".join("%.1f,%.1f" % p for p in pts), c.get("color", BLUE)))
        if c.get("label"):
            out.append('<text x="%.1f" y="%.1f" font-size="17" fill="%s" text-anchor="middle">%s</text>' % (
                X(c["m"]) + c.get("dx", 0), Y(npdf(c["m"], c["m"], c["s"])) - 8, c.get("color", BLUE), c["label"]))
    for x, lab in vlines:
        c = curves[0]
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.3" stroke-dasharray="5 4"/>' % (
            X(x), Y(0), X(x), Y(npdf(x, c["m"], c["s"])), MUTED))
        if lab:
            out.append('<text x="%.1f" y="%.1f" font-size="17" fill="%s" text-anchor="middle">%s</text>' % (X(x), Y(0) + 22, INK, lab))
    for x, lab in ticks:
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.5"/>' % (X(x), Y(0), X(x), Y(0) + 6, AXIS))
        out.append('<text x="%.1f" y="%.1f" font-size="17" fill="%s" text-anchor="middle">%s</text>' % (X(x), Y(0) + 24, INK, lab))
    for x, yf, txt, col in notes:
        out.append('<text x="%.1f" y="%.1f" font-size="17" font-weight="700" fill="%s" text-anchor="middle">%s</text>' % (
            X(x), Y(ymax * yf), col, txt))
    out.append("</svg>")
    return "".join(out)

def bars_svg(xs, ps, W=420, H=230, color=BLUE, labels=None, show_vals=True, overlay=None, title=None, ymax=None, xlab_every=1, xlabels=True):
    pl, pr, pt, pb = 14, 14, 30, 40
    n = len(xs)
    ymax = ymax or max(ps) * 1.15
    bw = (W - pl - pr) / n
    Y = lambda y: H - pb - y / ymax * (H - pt - pb)
    out = ['<svg class="fig" viewBox="0 0 %d %d" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
    if title:
        out.append('<text x="%d" y="18" font-size="18" font-weight="700" fill="%s">%s</text>' % (pl, INK, title))
    for i, (x, p) in enumerate(zip(xs, ps)):
        x0 = pl + i * bw + 1
        w = bw - 2
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="%s"/>' % (x0, Y(p), w, Y(0) - Y(p), color))
        if show_vals and labels is not None:
            out.append('<text x="%.1f" y="%.1f" font-size="16" fill="%s" text-anchor="middle">%s</text>' % (x0 + w / 2, Y(p) - 6, INK, labels[i]))
        if xlabels and i % xlab_every == 0:
            out.append('<text x="%.1f" y="%.1f" font-size="16" fill="%s" text-anchor="middle">%s</text>' % (x0 + w / 2, Y(0) + 22, INK, x))
    out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.5"/>' % (pl, Y(0), W - pr, Y(0), AXIS))
    if overlay:
        m, s = overlay
        pts = []
        for t in linspace(-0.5, n - 0.5, 200):
            xv = xs[0] + t * (xs[1] - xs[0]) if n > 1 else xs[0]
            pts.append((pl + (t + 0.5) * bw, Y(npdf(xv, m, s) * (xs[1] - xs[0]))))
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.5"/>' % (" ".join("%.1f,%.1f" % p for p in pts), ORANGE))
    out.append("</svg>")
    return "".join(out)

def ci_svg(W=640, H=320):
    zs = [0.3, -1.1, 0.8, -0.4, 1.5, -0.2, 0.6, -1.7, 2.4, 0.1, -0.9, 1.2, -0.5, 0.4, -1.3, 0.9, -0.1, 1.8, -0.7, 0.2]
    pl, pr, pt, pb = 20, 20, 30, 30
    cx = W / 2
    unit = (W - pl - pr) / 10.0
    rowh = (H - pt - pb) / len(zs)
    out = ['<svg class="fig" viewBox="0 0 %d %d" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
    out.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="2" stroke-dasharray="6 5"/>' % (cx, pt - 10, cx, H - pb + 6, INK))
    out.append('<text x="%.1f" y="%d" font-size="18" font-weight="700" fill="%s" text-anchor="middle">m (모르는 값, 고정)</text>' % (cx, pt - 14, INK))
    for i, z in enumerate(zs):
        y = pt + rowh * (i + 0.5)
        c = cx + z * unit
        miss = abs(z) > 1.96
        col = ORANGE if miss else BLUE
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % (c - 1.96 * unit, y, c + 1.96 * unit, y, col))
        out.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s"/>' % (c, y, col))
        if miss:
            out.append('<text x="%.1f" y="%.1f" font-size="16" fill="%s">m을 놓침</text>' % (c + 1.96 * unit + 8, y + 5, ORANGE))
    out.append('<text x="%d" y="%d" font-size="16" fill="%s">표본을 20번 뽑아 만든 95 %% 신뢰구간 20개 · 점은 각 표본평균</text>' % (pl, H - 6, MUTED))
    out.append("</svg>")
    return "".join(out)

def dots_svg(W=420, H=230):
    import random
    rnd = random.Random(7)
    pick = set(rnd.sample(range(100), 10))
    out = ['<svg class="fig" viewBox="0 0 %d %d" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
    out.append('<text x="10" y="20" font-size="18" font-weight="700" fill="%s">모집단 (전체)</text>' % INK)
    for i in range(100):
        r, c = divmod(i, 20)
        x, y = 16 + c * 20, 44 + r * 30
        if i in pick:
            out.append('<circle cx="%d" cy="%d" r="7" fill="%s"/>' % (x, y, ORANGE))
        else:
            out.append('<circle cx="%d" cy="%d" r="5.5" fill="%s" fill-opacity="0.55"/>' % (x, y, BLUE))
    out.append('<circle cx="22" cy="212" r="7" fill="%s"/><text x="36" y="218" font-size="17" fill="%s">임의추출된 표본 (크기 10)</text>' % (ORANGE, INK))
    out.append("</svg>")
    return "".join(out)

# ---------------------------------------------------------------- HTML helpers
def ul(items, cls=""):
    return '<ul class="%s">' % cls + "".join("<li>%s</li>" % i for i in items) + "</ul>"

def ol(items, cls=""):
    return '<ol class="%s">' % cls + "".join("<li>%s</li>" % i for i in items) + "</ol>"

def table(header, rows, cls=""):
    h = "<tr>" + "".join("<th>%s</th>" % c for c in header) + "</tr>"
    b = "".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in rows)
    return '<table class="%s">%s%s</table>' % (cls, h, b)

def ztab(pairs):
    return '<table class="ztab"><tr><th>z</th><th>P(0≤Z≤z)</th></tr>' + "".join(
        "<tr><td>%s</td><td>%s</td></tr>" % (z, p) for z, p in pairs) + "</table>"

def box(text, cls="", label=None):
    lab = '<span class="label">%s</span>' % label if label else ""
    return '<div class="box %s">%s%s</div>' % (cls, lab, text)

def cols(*parts, ratio=None):
    if ratio:
        return '<div class="cols">' + "".join('<div style="flex:%s">%s</div>' % (r, p) for r, p in zip(ratio, parts)) + "</div>"
    return '<div class="cols">' + "".join("<div>%s</div>" % p for p in parts) + "</div>"

def steps(*items):
    inner = '<span class="arr">→</span>'.join("<span>%s</span>" % i for i in items)
    return '<div class="steps">%s</div>' % inner

class Deck:
    def __init__(self, short, title):
        self.short, self.title, self.slides = short, title, []

    def slide(self, title, body, tag="", cls=""):
        self.slides.append(dict(title=title, body=body, tag=tag, cls=cls))

    def cover(self, title, subtitle, goals):
        body = '<div class="sub">%s</div><div class="goals"><div class="glab">학습 목표</div>%s</div>' % (subtitle, ol(goals))
        self.slides.append(dict(title=title, body=body, tag="", cls="title"))

    def section(self, title, sub=""):
        self.slides.append(dict(title=title, body='<div class="secsub">%s</div>' % sub, tag="", cls="section"))

    def problem(self, n, level, title, prob, zt=None, hint=None):
        right = ('<div class="ztwrap">%s</div>' % ztab(zt)) if zt else ""
        body = '<div class="probwrap"><div class="prob">%s</div>%s</div>' % (prob, right)
        if hint:
            body += box(hint, "gray", "생각할 것")
        self.slides.append(dict(title="예제 %d <span class='lv'>[%s]</span> %s" % (n, level, title), body=body, tag="예제 %d" % n, cls="prob"))

    def solution(self, n, title, sol, point=None, link=None):
        body = '<div class="sol">%s</div>' % sol
        if point:
            body += box(point, "", "포인트")
        if link:
            body += '<div class="link"><span class="label">고쟁이</span>%s</div>' % link
        self.slides.append(dict(title="예제 %d 풀이 — %s" % (n, title), body=body, tag="예제 %d 풀이" % n, cls="sol"))

CSS = """
@page { size: 13.333in 7.5in; margin: 0; }
html, body { margin:0; padding:0; background:#fff; }
body { font-family: "Nanum Gothic", "Noto Sans CJK KR", "Malgun Gothic", sans-serif; color:#1b1b1b; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.slide { width:1280px; height:720px; box-sizing:border-box; padding:40px 60px 44px; position:relative; page-break-after:always; break-after:page; overflow:hidden; background:#fff; }
.slide:last-child { page-break-after:auto; }
.top { position:absolute; top:12px; left:60px; right:60px; display:flex; justify-content:space-between; align-items:center; font-size:16px; color:#8a7580; }
.tag { background:#f3e9ee; color:#4a1b33; padding:2px 14px; border-radius:14px; font-weight:700; font-size:16px; }
h1 { font-size:36px; margin:14px 0 16px; color:#4a1b33; border-bottom:3px solid #c08a55; padding-bottom:8px; line-height:1.25; font-weight:700; }
h1 .lv { font-size:22px; color:#c08a55; margin:0 6px; }
.body { font-size:25px; line-height:1.5; }
.body p { margin:6px 0; }
.body ul, .body ol { margin:4px 0 8px 0; padding-left:32px; }
.body li { margin:5px 0; }
.cols { display:flex; gap:32px; align-items:flex-start; }
.cols > div { flex:1; min-width:0; }
.box { border:2px solid #c08a55; border-radius:10px; padding:8px 18px; margin:10px 0 6px; background:#fff9f3; font-size:24px; line-height:1.45; }
.box.blue { border-color:#2a78d6; background:#f1f6fd; }
.box.gray { border-color:#c9c9c9; background:#f7f7f7; color:#444; font-size:21px; }
.label { font-weight:700; color:#4a1b33; margin-right:10px; }
table { border-collapse:collapse; font-size:23px; margin:6px 0; }
th, td { border:1px solid #bbb; padding:3px 13px; text-align:center; }
th { background:#f3e9ee; }
table.ztab { font-size:19px; } table.ztab th, table.ztab td { padding:1px 12px; }
table.flow td:first-child, table.flow th:first-child { text-align:left; }
table.left td { text-align:left; }
.foot { position:absolute; bottom:12px; left:60px; right:60px; display:flex; justify-content:space-between; font-size:14px; color:#9a9a9a; }
.prob { font-size:28px; line-height:1.6; }
.probwrap { display:flex; gap:28px; align-items:flex-start; }
.probwrap .prob { flex:1; }
.ztwrap { flex:0 0 auto; }
.sol { font-size:26px; line-height:1.55; }
.sol ol, .sol ul { padding-left:32px; }
.ans { color:#b4232f; font-weight:700; }
.muted { color:#777; font-size:20px; }
.small { font-size:21px; }
.big { font-size:32px; font-weight:700; color:#4a1b33; text-align:center; margin:18px 0; }
.steps { display:flex; gap:10px; align-items:center; justify-content:center; font-size:23px; flex-wrap:wrap; margin:10px 0; }
.steps span { background:#f3e9ee; padding:6px 14px; border-radius:8px; }
.steps .arr { background:none; color:#c08a55; font-weight:700; }
.link { font-size:21px; color:#555; margin-top:6px; }
.fig { display:block; margin:4px auto; }
.cap { font-size:20px; color:#555; text-align:center; margin-top:2px; }
.patgrid { display:grid; grid-template-columns:1fr 1fr; gap:4px 40px; }
.patcell { text-align:center; }
.patcell .fig { margin:0 auto; }
.patcap { font-size:22px; margin:-4px 0 6px; }
.slide.title { background:linear-gradient(135deg,#3d1429 0%,#6b2a4a 60%,#8a4a66 100%); color:#fff; padding-top:120px; }
.slide.title h1 { color:#fff; border:none; font-size:46px; line-height:1.3; margin-bottom:6px; }
.slide.title .sub { font-size:24px; color:#e9d6de; margin-bottom:34px; }
.slide.title .goals { background:rgba(255,255,255,0.12); border-radius:14px; padding:14px 26px; font-size:23px; }
.slide.title .glab { font-weight:700; color:#f3d9a8; margin-bottom:4px; }
.slide.title ol { margin:0; padding-left:28px; } .slide.title li { margin:4px 0; }
.slide.title .top, .slide.title .foot { color:rgba(255,255,255,0.55); } .slide.title .tag { display:none; }
.slide.section { background:#f6eef2; padding-top:250px; }
.slide.section h1 { border:none; font-size:50px; text-align:center; }
.slide.section .secsub { text-align:center; font-size:26px; color:#6b2a4a; }
.kw { color:#b4232f; font-weight:700; }
.chip { display:inline-block; background:#eef3fb; color:#2a4f86; border-radius:8px; padding:0 10px; margin:0 4px; font-weight:700; }
mjx-container { font-size:106% !important; }
mjx-container[display="true"] { margin:6px 0 !important; }
"""

def render(deck, out_path, assets=None):
    if assets:
        a = pathlib.Path(assets)
        mj = "<script>" + (a / "tex-svg.js").read_text(encoding="utf-8") + "</script>"
        f4, f7 = "file://" + str(a / "nanum-400.woff2"), "file://" + str(a / "nanum-700.woff2")
    else:
        mj = '<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.js"></script>'
        base = "https://cdn.jsdelivr.net/npm/@fontsource/nanum-gothic@5.2.5/files/"
        f4, f7 = base + "nanum-gothic-korean-400-normal.woff2", base + "nanum-gothic-korean-700-normal.woff2"
    font_css = ('@font-face{font-family:"Nanum Gothic";font-weight:400;src:url("%s") format("woff2");}'
                '@font-face{font-family:"Nanum Gothic";font-weight:700;src:url("%s") format("woff2");}') % (f4, f7)
    total = len(deck.slides)
    parts = []
    for i, s in enumerate(deck.slides, 1):
        s = {k: (v.replace('\\"', '"') if isinstance(v, str) else v) for k, v in s.items()}
        parts.append('<section class="slide %s"><div class="top"><span>%s</span><span class="tag">%s</span></div>'
                     '<h1>%s</h1><div class="body">%s</div>'
                     '<div class="foot"><span>확률과 통계 Ⅲ 통계 · %s</span><span>%d / %d</span></div></section>'
                     % (s["cls"], deck.title, s["tag"], s["title"], s["body"], deck.short, i, total))
    html = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>%s</title><style>%s%s</style>'
            '<script>window.MathJax={tex:{inlineMath:[["$","$"]],displayMath:[["$$","$$"]]},svg:{fontCache:"global"}};</script>%s'
            '</head><body>%s</body></html>') % (deck.title, font_css, CSS, mj, "".join(parts))
    pathlib.Path(out_path).write_text(html, encoding="utf-8")
    return total

# ================================================================ 덱 1: 정규분포 + 정규근사 (4·5차시 합본)
def deck_normal():
    d = Deck("4·5차시 합본", "정규분포와 표준정규분포 · 이항분포의 정규근사")
    d.cover("정규분포와 표준정규분포,<br>그리고 이항분포의 정규근사",
            "확률과 통계 Ⅲ. 통계 — 4·5차시 합본 (50분) · 고쟁이 유형 09~11",
            ["정규분포곡선에서 m은 위치, σ는 퍼짐임을 그림으로 설명한다.",
             r"표준화 $Z=\dfrac{X-m}{\sigma}$로 바꾸어 표준정규분포표로 확률을 구하고, 확률이 주어지면 경계값·m·σ를 역산한다.",
             r"n이 충분히 클 때 $B(n,p)$가 근사적으로 $N(np,\,npq)$를 따름을 이용해 확률을 구한다."])

    d.slide("오늘의 흐름 (50분)", table(["단계", "시간", "내용"], [
        ["도입", "6분", "종 모양 → m은 위치, σ는 퍼짐 → 68-95-99.7 → \"σ 몇 개만큼\"(표준화의 뜻)"],
        ["개념 1", "8분", "곡선의 성질 · 표준정규분포표 읽기 4패턴 · 표준화 · 활용 절차"],
        ["예제 1~6", "22분", "표 읽기 → 역산·대칭 → 실생활 → 상대 비교 → 상위 k % → m·σ 역산"],
        ["개념 2", "4분", "이항분포의 막대그래프가 종 모양 → N(np, npq)로 근사, 4단계"],
        ["예제 7~8", "8분", "주사위 180번 → 역산 k · 식에서 n, p 읽기"],
        ["마무리", "2분", "흐름도 한 장, 과제"]], "flow") +
        box("도입 예시는 숫자가 작고 그림으로 보이는 것만. 공식은 그림에서 확인한 뒤에 적는다.", "gray"), "흐름")

    d.section("1. 도입", "심플한 예시로 감 잡기 (6분)")

    hist_x = [round(-3 + 0.5 * i, 1) for i in range(13)]
    hist_p = [npdf(x, 0, 1) * 0.5 for x in hist_x]
    d.slide("도입 ① 종 모양은 어디에나 있다", cols(
        ul(["우리 반 학생들의 <b>키</b>, 전국 모의고사 <b>점수</b>, 공장에서 나오는 과자의 <b>무게</b>…",
            "히스토그램을 그리면 <b>평균 근처가 가장 많고</b>, 양쪽으로 갈수록 드물어진다.",
            "막대를 촘촘히 하면 매끈한 <b>종 모양 곡선</b>이 된다."]) +
        box(r"이 곡선이 <b>정규분포</b> $N(m,\sigma^2)$. 연속확률변수이므로 <b>확률 = 넓이</b>, 전체 넓이는 1. (1차시 복습)", "blue"),
        bars_svg(hist_x, hist_p, W=560, H=280, labels=None, show_vals=False, overlay=(0, 1), xlabels=False) +
        '<div class="cap">가로축: 키(또는 점수, 무게), 세로축: 도수 → 곡선 아래 넓이가 비율</div>'), "도입")

    fig_s = normal_svg([dict(m=0, s=1, color=BLUE, label="σ=1", dx=0), dict(m=0, s=2, color=ORANGE, label="σ=2", dx=70),
                        dict(m=0, s=3, color=AQUA, label="σ=3", dx=150)], ticks=[(0, "m")], W=560, H=250, xr=(-9, 9))
    fig_m = normal_svg([dict(m=-3, s=1, color=BLUE, label="m₁"), dict(m=0, s=1, color=ORANGE, label="m₂"),
                        dict(m=3, s=1, color=AQUA, label="m₃")], ticks=[(-3, "m₁"), (0, "m₂"), (3, "m₃")], W=560, H=250, xr=(-7, 7))
    d.slide("도입 ② m은 위치, σ는 퍼짐", cols(
        fig_s + '<div class="cap"><b>m이 같고 σ가 다를 때</b>: σ가 크면 납작하고 넓게. 넓이는 늘 1이니까 넓어지면 낮아진다.</div>',
        fig_m + '<div class="cap"><b>σ가 같고 m이 다를 때</b>: 모양은 그대로, 위치만 옆으로 이동.</div>') +
        box("퀴즈: 두 곡선 중 봉우리가 <b>낮은</b> 쪽의 σ는? → <b>크다</b>. (고쟁이 568, 650, 662가 전부 이 한 줄)", "gray"), "도입")

    fig68 = normal_svg([dict(m=0, s=1, color=BLUE)],
                       shade=[dict(a=-3, b=3, color=BLUE, op=0.12), dict(a=-2, b=2, color=BLUE, op=0.18), dict(a=-1, b=1, color=BLUE, op=0.3)],
                       ticks=[(-3, "m−3σ"), (-2, "m−2σ"), (-1, "m−σ"), (0, "m"), (1, "m+σ"), (2, "m+2σ"), (3, "m+3σ")],
                       notes=[(0, 0.42, "68 %", INK), (0, 0.2, "95 %", INK), (0, 0.06, "99.7 %", INK)], W=640, H=290, xr=(-4, 4))
    d.slide("도입 ③ 68-95-99.7 — 크기 감각 잡기", cols(
        fig68,
        ul(["$m\\pm\\sigma$ 안에 약 <b>68 %</b>", "$m\\pm2\\sigma$ 안에 약 <b>95 %</b>", "$m\\pm3\\sigma$ 안에 약 <b>99.7 %</b>"]) +
        box("키 평균 170 cm, σ = 5 cm라면<br>165~175 cm가 약 68 %, 160~180 cm가 약 95 %.", "blue") +
        '<p class="small">이 감각이 있으면 답이 0.02인지 0.2인지 자릿수가 틀렸을 때 바로 알아챈다. (708)</p>', ratio=(1.15, 1)), "도입")

    fk = normal_svg([dict(m=76, s=10, color=BLUE)], shade=[dict(a=84, b=120, color=BLUE, op=0.35)], ticks=[(76, "76"), (84, "84")],
                    vlines=[(84, "")], W=400, H=200, notes=[(92, 0.25, "국어 84점", INK)])
    fm = normal_svg([dict(m=68, s=8, color=ORANGE)], shade=[dict(a=80, b=120, color=ORANGE, op=0.35)], ticks=[(68, "68"), (80, "80")],
                    vlines=[(80, "")], W=400, H=200, notes=[(84, 0.25, "수학 80점", INK)])
    d.slide("도입 ④ 표준화의 뜻 — \"평균에서 σ 몇 개만큼?\"", cols(
        fk + '<div class="cap">국어: 평균 76, σ 10. 84점은 평균에서 σ <b>0.8개</b> 위</div>',
        fm + '<div class="cap">수학: 평균 68, σ 8. 80점은 평균에서 σ <b>1.5개</b> 위</div>') +
        box(r"점수 자체로는 비교가 안 된다. <b>\"σ 몇 개만큼 떨어졌나\"</b>로 단위를 통일한 것이 $Z=\dfrac{X-m}{\sigma}$. "
            r"Z는 어떤 정규분포에서 왔든 항상 $N(0,1)$ → 표 <b>하나</b>로 모든 정규분포를 처리한다.", "blue"), "도입")

    d.section("2. 개념 정리", "곡선의 성질 · 표 읽기 · 표준화 · 활용 절차 (8분)")

    d.slide("개념 ① 정규분포곡선의 성질", cols(
        r'<p>확률밀도함수 $f(x)=\dfrac{1}{\sqrt{2\pi}\,\sigma}e^{-\frac{(x-m)^2}{2\sigma^2}}$ 인 분포를 $N(m,\sigma^2)$ <span class="muted">(식은 외울 필요 없음)</span></p>' +
        ol(["직선 $x=m$에 대칭, x축이 점근선",
            "$x=m$에서 최댓값",
            "곡선과 x축 사이의 넓이는 1",
            "m 일정, σ 커지면 → 가운데가 <b>낮아지고</b> 옆으로 퍼진다",
            "σ 일정, m 달라지면 → 모양 그대로 평행이동"]),
        box("<b>퀴즈 (567)</b> 옳지 <u>않은</u> 것은?<br>① x=m에 대칭이고 x축이 점근선<br>② f(x)는 x=m에서 최댓값<br>③ 곡선과 x축 사이 넓이는 1<br>"
            "④ m 일정, σ 클수록 가운데 높이가 <b>높아진다</b><br>⑤ σ 일정, m이 달라져도 모양은 안 바뀐다", "gray") +
        '<p class="muted">답 ④ — σ가 크면 넓어지니까 <b>낮아진다</b>.</p>', ratio=(1.2, 1)), "개념")

    fz = normal_svg([dict(m=0, s=1, color=BLUE)], shade=[dict(a=0, b=1.2, color=BLUE, op=0.35)], ticks=[(0, "0"), (1.2, "z")],
                    vlines=[(1.2, "")], W=440, H=210, xr=(-3.5, 3.5), notes=[(0.6, 0.18, "P(0≤Z≤z)", INK)])
    d.slide("개념 ② 표준정규분포 N(0, 1)과 표", cols(
        ul(["평균 0, 표준편차 1인 정규분포. 확률변수는 보통 $Z$로 쓴다.",
            "표준정규분포표는 <b>$P(0\\le Z\\le z)$만</b> 준다 (오른쪽 색칠 부분).",
            "나머지는 <b>대칭</b>과 <b>전체 0.5씩</b>으로 만든다: $P(Z\\ge0)=P(Z\\le0)=0.5$"]) +
        table(["z", "0.5", "1.0", "1.5", "1.96", "2.0", "2.5", "2.58", "3.0"],
              [["P(0≤Z≤z)", "0.1915", "0.3413", "0.4332", "0.4750", "0.4772", "0.4938", "0.4950", "0.4987"]], "small"),
        fz + '<div class="cap">표의 값 = 0에서 z까지의 넓이</div>', ratio=(1.3, 1)), "개념")

    def pat(a, b, lab):
        return normal_svg([dict(m=0, s=1, color=BLUE)], shade=[dict(a=a, b=b, color=BLUE, op=0.4)], ticks=[(0, "0")] + lab,
                          W=380, H=135, xr=(-3.3, 3.3))
    def cell(svg, cap):
        return '<div class="patcell">' + svg + '<div class="patcap">' + cap + '</div></div>'
    d.slide("개념 ③ 표 읽기 4패턴 — 그림부터 그린다",
        '<div class="patgrid">' +
        cell(pat(-9, 1, [(1, "a")]), r'$P(Z\le a)=0.5+P(0\le Z\le a)$') +
        cell(pat(1, 9, [(1, "a")]), r'$P(Z\ge a)=0.5-P(0\le Z\le a)$') +
        cell(pat(-1, 2, [(-1, "−a"), (2, "b")]), r'$P(-a\le Z\le b)=P(0\le Z\le a)+P(0\le Z\le b)$') +
        cell(pat(1, 2, [(1, "a"), (2, "b")]), r'$P(a\le Z\le b)=P(0\le Z\le b)-P(0\le Z\le a)$') +
        '</div>' +
        box(r"덤: $P(Z\le -a)=P(Z\ge a)$ (대칭), $P(|Z|\le a)=2P(0\le Z\le a)$. 그림 없이 부호만 보고 더할지 뺄지 정하지 말 것.", "blue"), "개념")

    d.slide("개념 ④ 표준화와 활용 절차", cols(
        box(r"$X\sim N(m,\sigma^2)$ 이면 $Z=\dfrac{X-m}{\sigma}\sim N(0,1)$<br>"
            r"$P(a\le X\le b)=P\!\left(\dfrac{a-m}{\sigma}\le Z\le\dfrac{b-m}{\sigma}\right)$", "blue") +
        '<p><b>활용 문제 5단계</b></p>' + steps("상황 읽기", "\"X는 N(m, σ²)\" 한 줄", "구할 확률을 P(a≤X≤b)로", "표준화 + 그림", "표") +
        r'<p><b>역산형</b>(확률이 주어짐): 표에서 z를 찾고 $x=m+z\sigma$. "상위 k %"는 $P(X\ge x)=\dfrac{k}{100}$.</p>',
        box("<b>자주 하는 실수</b>" + ul([r"분산 σ²으로 나눈다 → $N(40,16)$이면 σ=4", r"$P(Z\ge a)$를 $1-P(0\le Z\le a)$로 쓴다 (0.5를 빼야 함)",
                                      "그림 없이 부호만 보고 더하고 뺀다"]), "gray"), ratio=(1.5, 1)), "개념")

    d.slide("개념 체크 — 곡선 비교 (569)", cols(
        '<p>네 정규분포 ㄱ. $N(0,3^2)$ ㄴ. $N(1,1^2)$ ㄷ. $N(3,4^2)$ ㄹ. $N(5,2^2)$</p>' +
        ul(["확률밀도함수 그래프의 <b>높이가 가장 높은</b> 것은?", "<b>대칭축이 가장 왼쪽</b>에 있는 것은?"]) +
        box("높이 ↔ σ (작을수록 높다) · 대칭축 ↔ m. <span class='ans'>답: ㄴ, ㄱ</span>", "gray"),
        normal_svg([dict(m=0, s=3, color=BLUE, label="ㄱ", dx=-40), dict(m=1, s=1, color=ORANGE, label="ㄴ"),
                    dict(m=3, s=4, color=AQUA, label="ㄷ", dx=60), dict(m=5, s=2, color="#6250d6", label="ㄹ", dx=40)],
                   ticks=[(0, "0"), (1, "1"), (3, "3"), (5, "5")], W=560, H=260, xr=(-9, 14))), "개념 체크")

    d.section("3. 예제 1~6 — 정규분포", "표 읽기 → 역산·대칭 → 실생활 → 상대 비교 → 상위 k % → m·σ 역산")

    Z4 = [("1.0", "0.3413"), ("1.5", "0.4332"), ("2.0", "0.4772"), ("2.5", "0.4938")]
    d.problem(1, "기본", "표 읽기와 표준화",
              r"확률변수 $Z$는 표준정규분포 $N(0,1)$, 확률변수 $X$는 정규분포 $N(40,4^2)$을 따른다. 오른쪽 표를 이용하여 다음을 구하시오." +
              ol([r"$P(Z\le1.5)$", r"$P(|Z|\le1)$", r"$P(1\le Z\le2)$", r"$P(36\le X\le50)$"]), Z4,
              "(4)는 먼저 양 끝 36, 50을 Z의 값으로 바꾼다. σ는 4.")
    d.solution(1, "표 읽기와 표준화",
               ol([r"$P(Z\le1.5)=0.5+P(0\le Z\le1.5)=0.5+0.4332=$ <span class='ans'>0.9332</span>",
                   r"$P(|Z|\le1)=2P(0\le Z\le1)=2\times0.3413=$ <span class='ans'>0.6826</span>",
                   r"$P(1\le Z\le2)=P(0\le Z\le2)-P(0\le Z\le1)=0.4772-0.3413=$ <span class='ans'>0.1359</span>",
                   r"$\dfrac{36-40}{4}=-1,\ \dfrac{50-40}{4}=2.5$ 이므로 $P(-1\le Z\le2.5)=0.3413+0.4938=$ <span class='ans'>0.8351</span>"]),
               "네 문제 모두 종 모양을 그리고 색칠한 뒤에 식을 쓴다. (4)에서 분산 16이 아니라 <b>표준편차 4</b>로 나눈다.",
               "571, 572, 574, 657")

    d.problem(2, "기본", "역산과 대칭",
              ol([r"$P(Z\le a)=0.8413$, $P(Z\ge b)=0.0668$, $P(Z\ge c)=0.9772$ 를 만족시키는 $a,\ b,\ c$",
                  r"$X\sim N(m,\sigma^2)$ 이고 $P(X\le14)=P(X\ge26)$ 일 때 $m$",
                  r"$X\sim N(7,2^2)$ 일 때 $P(t-4\le X\le t+2)$ 가 최대가 되는 실수 $t$"]), Z4,
              "(1) 0.5보다 큰 확률의 경계는 평균의 어느 쪽? (3) 길이가 6으로 고정된 구간을 어디에 놓아야 넓이가 최대?")
    d.solution(2, "역산과 대칭",
               ol([r"$0.8413=0.5+0.3413$ → <span class='ans'>a=1</span>. $0.0668=0.5-0.4332$ → <span class='ans'>b=1.5</span>. "
                   r"$0.9772>0.5$ 이므로 c는 음수: $0.5+0.4772$ → <span class='ans'>c=−2</span>",
                   r"14와 26의 <b>중점</b>이 대칭축: $m=\dfrac{14+26}{2}=$ <span class='ans'>20</span>",
                   r"길이 6인 구간은 <b>가운데가 평균일 때</b> 넓이 최대 → 구간의 중점 $t-1=7$ → <span class='ans'>t=8</span>"]),
               r"$f(a)=f(b)$, $P(X\le a)=P(X\ge b)$ 꼴의 조건은 전부 \"a, b의 평균 = m\". 660, 661, 704, 705가 이 한 줄로 풀린다.",
               "570, 573, 652, 655, 656, 660")

    Z5 = [("0.5", "0.1915"), ("1.0", "0.3413"), ("1.5", "0.4332"), ("2.0", "0.4772")]
    d.problem(3, "기본", "실생활 활용",
              ol(["어느 공장에서 생산되는 과자 1봉지의 무게는 평균 130 g, 표준편차 10 g인 정규분포를 따른다. 임의로 고른 1봉지의 무게가 135 g 이상 145 g 이하일 확률은?",
                  "어느 세차장에서 승용차 한 대를 세차하는 데 걸리는 시간은 평균 30분, 표준편차 2분인 정규분포를 따른다. 세차 시간이 33분 이상일 확률은?"]), Z5,
              "첫 줄에 \"X는 N(130, 10²)\"부터 쓴다.")
    d.solution(3, "실생활 활용",
               ol([r"$X\sim N(130,10^2)$. $P(135\le X\le145)=P\!\left(\dfrac{135-130}{10}\le Z\le\dfrac{145-130}{10}\right)=P(0.5\le Z\le1.5)$"
                   r"$=0.4332-0.1915=$ <span class='ans'>0.2417</span>",
                   r"$X\sim N(30,2^2)$. $P(X\ge33)=P\!\left(Z\ge\dfrac{33-30}{2}\right)=P(Z\ge1.5)=0.5-0.4332=$ <span class='ans'>0.0668</span>"]),
               "68-95-99.7로 검산: 33분은 m+1.5σ 바깥이니 7 % 정도가 맞다. 답이 0.4332면 어딘가 잘못된 것.",
               "574, 575, 664, 667")

    d.problem(4, "확장", "서로 다른 분포 비교",
              "어느 반 학생 전체의 국어, 영어, 수학 성적이 각각 정규분포를 따르고 평균과 표준편차가 아래와 같다. 미정이의 점수가 국어 84점, 영어 76점, 수학 80점일 때, "
              "다른 학생들과 비교하여 <b>상대적으로</b> 성적이 높은 과목부터 차례로 나열하시오." +
              table(["", "국어", "영어", "수학"], [["평균", "76", "72", "68"], ["표준편차", "10", "12", "8"]]), None,
              "평균과 σ가 다르면 점수를 직접 비교할 수 없다. 공통 단위는?")
    d.solution(4, "서로 다른 분포 비교",
               r"<p>각 점수를 표준화한다 (평균에서 σ 몇 개 위인가).</p>" +
               table(["과목", "국어", "영어", "수학"], [["Z", r"$\dfrac{84-76}{10}=0.8$", r"$\dfrac{76-72}{12}=\dfrac13$", r"$\dfrac{80-68}{8}=1.5$"]]) +
               "<p>Z가 클수록 상대적으로 높다 → <span class='ans'>수학, 국어, 영어</span></p>",
               r"576(두 제품의 확률이 같다 → 표준화한 구간이 대칭으로 같다 → k=20.25), 618·672의 표준점수 $T=20\cdot\dfrac{X-m}{\sigma}+100$ 도 결국 Z 이야기.",
               "576, 663, 665, 673")

    d.problem(5, "확장", "상위 k % — 경계값 역산 (스키마 p.170)",
              "어느 대학 수학과의 모집인원은 60명인데 500명이 응시하였다. 응시자 500명의 점수가 평균 72점, 표준편차 10점인 정규분포를 따른다고 할 때, "
              "합격하기 위한 <b>최저 점수</b>를 오른쪽 표를 이용하여 구하시오.",
              [("1.0", "0.34"), ("1.1", "0.36"), ("1.2", "0.38"), ("1.3", "0.40")],
              "합격자 비율은? 그 비율을 P(X ≥ k) = □ 로 쓴다.")
    d.solution(5, "상위 k % — 경계값 역산",
               ol([r"합격 비율 $\dfrac{60}{500}=0.12$. 최저 점수를 k라 하면 $P(X\ge k)=0.12$",
                   r"표준화: $P\!\left(Z\ge\dfrac{k-72}{10}\right)=0.12$ → $0.5-P\!\left(0\le Z\le\dfrac{k-72}{10}\right)=0.12$",
                   r"$P(0\le Z\le z)=0.38$ 인 z를 표에서 찾는다 → $z=1.2$",
                   r"$\dfrac{k-72}{10}=1.2$ → $k=72+12=$ <span class='ans'>84점</span>"]),
               "비율 → 확률 식 → \"0.5 − 표의 값\" → z → x = m + zσ. 668(상위 5 %), 670(40명 중 3명), 672(상위 11 %)가 전부 이 다섯 단계.",
               "668, 669, 670, 671, 672")

    d.problem(6, "확장", "m, σ 역산",
              ol([r"어느 제약 회사에서 만든 알약 지름의 길이는 평균 $k$ mm, 표준편차 0.3 mm인 정규분포를 따른다. 임의로 택한 알약의 지름이 7.6 mm 이상일 확률이 0.8413일 때 $k$의 값은?",
                  r"확률변수 $X$가 정규분포 $N(m,\,4)$를 따르고 $P(X\le30)=0.1587$ 일 때 $m$의 값은?"]),
              [("1.0", "0.3413"), ("2.0", "0.4772"), ("3.0", "0.4987")],
              "(1) 0.8413은 0.5보다 크다 → 7.6은 평균의 어느 쪽? (2) 4는 분산인가 표준편차인가?")
    d.solution(6, "m, σ 역산",
               ol([r"$0.8413=0.5+0.3413=P(Z\ge-1)$ → $\dfrac{7.6-k}{0.3}=-1$ → $k=7.6+0.3=$ <span class='ans'>7.9</span>",
                   r"분산 4 → <b>σ=2</b>. $0.1587=0.5-0.3413=P(Z\le-1)$ → $\dfrac{30-m}{2}=-1$ → $m=$ <span class='ans'>32</span>"]),
               "경계와 평균의 위치 관계(왼쪽/오른쪽)를 그림으로 먼저 정하면 부호 실수가 사라진다. 654, 666, 674는 조건이 두 개여서 연립이 필요한 확장.",
               "654, 656, 665, 666, 674")

    d.section("4. 이항분포와 정규분포의 관계", "막대그래프가 종 모양이면 넓이로 구하자 (4분)")

    bx = list(range(30, 71))
    bp = [math.comb(100, k) * 0.5 ** 100 for k in bx]
    d.slide("개념 ⑤ 동전 100번: 앞면 45번 이하일 확률은?", cols(
        ul([r"앞면 횟수 $X\sim B\!\left(100,\tfrac12\right)$ (3차시).",
            r"$P(X\le45)={}_{100}C_0\!\left(\tfrac12\right)^{100}+\cdots+{}_{100}C_{45}\!\left(\tfrac12\right)^{100}$ — 항이 46개. 손으로는 불가능.",
            "그런데 X의 확률분포를 막대로 그리면 평균 50을 중심으로 <b>종 모양</b>! n이 클수록 더 매끈하다."]) +
        box(r"<b>모양만 정규분포로 바꾸고 넓이로 구하자.</b> 평균·분산은 이항분포 것을 그대로: $np=50,\ npq=25$ → $N(50,5^2)$<br>"
            r"$P(X\le45)=P\!\left(Z\le\dfrac{45-50}{5}\right)=P(Z\le-1)=0.5-0.3413=0.1587$", "blue"),
        bars_svg(bx, bp, W=560, H=300, show_vals=False, overlay=(50, 5), xlab_every=5) +
        '<div class="cap">막대: B(100, 1/2)의 확률 · 곡선: N(50, 5²)</div>', ratio=(1.2, 1)), "개념")

    d.slide("개념 ⑥ 이항분포의 정규근사 — 4단계", cols(
        box(r"$X\sim B(n,p)$ 에서 n이 충분히 크면 $X$는 근사적으로 $N(np,\,npq)$ 를 따른다. (q = 1 − p)<br>"
            r"<span class='small'>\"충분히 크다\"의 기준: $np\ge5,\ nq\ge5$. 교과서·고쟁이 문제는 모두 이 조건을 만족한다.</span>", "blue") +
        steps("① 상황 → B(n, p)", "② np, npq → N(np, npq)", r"③ $Z=\dfrac{X-np}{\sqrt{npq}}$", "④ 표") +
        ul([r"역산형: $P(X\le k)=\alpha$ 가 주어지면 표에서 z를 찾아 $k=np+z\sqrt{npq}$",
            "비율로 주어진 조건은 <b>횟수로 바꾼다</b>: 1600대 중 47.5 % ↔ 760대"]),
        box("<b>자주 하는 실수</b>" + ul([r"표준편차를 $npq$로 쓴다 (제곱근을 안 씌움)", "B(n, p)를 적지 않고 평균·표준편차를 바로 추측한다 → 반드시 n, p부터"]), "gray"),
        ratio=(1.6, 1)), "개념")

    d.problem(7, "기본", "주사위 180번 — 4단계 그대로",
              "한 개의 주사위를 180번 던질 때 나온 눈의 수가 2인 횟수를 $X$라 하자. 다음 순서로 $X\\ge35$일 확률을 구하시오." +
              ol(["$X$가 따르는 이항분포를 기호로 나타내시오.", "$X$가 근사적으로 따르는 정규분포를 기호로 나타내시오.", "$P(X\\ge35)$를 오른쪽 표를 이용하여 구하시오."]),
              Z5, "① n과 p ② np와 npq ③ 표준화 ④ 표")
    d.solution(7, "주사위 180번",
               ol([r"독립시행 180번, 1회 확률 $\tfrac16$, X는 횟수 → $X\sim B\!\left(180,\tfrac16\right)$",
                   r"$np=30,\ npq=180\times\tfrac16\times\tfrac56=25$ → $N(30,5^2)$, σ=5",
                   r"$P(X\ge35)=P\!\left(Z\ge\dfrac{35-30}{5}\right)=P(Z\ge1)=0.5-0.3413=$ <span class='ans'>0.1587</span>"]),
               r"579(치유율 60 %, 150명 중 78명 이상): $B(150,0.6)$ → $N(90,6^2)$ → $P(Z\ge-2)=0.9772$. 경계가 평균 왼쪽이면 답은 0.5보다 커야 한다.",
               "577, 578, 579, 677, 680")

    d.problem(8, "확장", "역산 k · 식에서 n, p 읽기",
              ol([r"한 개의 동전을 400번 던질 때 앞면이 나오는 횟수를 $X$라 하자. $P(X\le k)=0.9772$ 를 만족시키는 상수 $k$의 값은?",
                  r"이산확률변수 $X$의 확률질량함수가 $P(X=x)={}_{100}C_x\,p^x(1-p)^{100-x}\ (x=0,1,\cdots,100)$ 이고 $E(X)=20$ 이다. $P(24\le X\le30)$ 을 구하시오."]),
              [("1.0", "0.3413"), ("2.0", "0.4772"), ("2.5", "0.4938")],
              "(1) 0.9772 = 0.5 + □ → z는? (2) 식에서 n은 몇? p는 평균에서.")
    d.solution(8, "역산 k · 식에서 n, p 읽기",
               ol([r"$B\!\left(400,\tfrac12\right)$ → $np=200,\ npq=100$ → $N(200,10^2)$. $0.9772=0.5+0.4772$ → $\dfrac{k-200}{10}=2$ → <span class='ans'>k=220</span>",
                   r"n=100, $100p=20$ → $p=0.2$, $npq=100\times0.2\times0.8=16$ → $N(20,4^2)$. "
                   r"$P(24\le X\le30)=P(1\le Z\le2.5)=0.4938-0.3413=$ <span class='ans'>0.1525</span>"]),
               r"679(1600대 중 A사 비율 47.5~52.5 %): 비율을 대수로 바꿔 $760\le X\le840$, $N(800,20^2)$ → $P(-2\le Z\le2)=0.9544$. "
               r"이 \"비율 → 횟수\" 한 줄이 다음 시간 <b>표본비율</b>의 씨앗.",
               "580, 676, 678, 679, 681, 684")

    d.section("5. 마무리", "흐름도 한 장 · 과제")
    d.slide("01 확률분포 단원 흐름도 — 오늘 두 줄기가 만났다", cols(
        ul(["확률변수 X가 <b>이산</b> → 표·식으로 분포 → E(X), V(X), σ(X) → aX+b",
            "이산 중 \"독립시행의 횟수\"면 <b>이항분포 B(n, p)</b> → 평균 np, 분산 npq",
            "확률변수 X가 <b>연속</b> → 확률은 넓이 → 종 모양이면 <b>정규분포 N(m, σ²)</b> → 표준화 Z → 표",
            "n이 크면 <b>B(n, p) ≈ N(np, npq)</b> — 이항분포도 같은 표로 (오늘)"]) +
        box("<b>한 줄 정리</b> 정규분포는 \"평균에서 σ 몇 개\"로 바꾸면 전부 하나의 표로 통한다. 그림 → 표준화 → 표.", "blue"),
        normal_svg([dict(m=0, s=1, color=BLUE)], shade=[dict(a=-1, b=2, color=BLUE, op=0.35)],
                   ticks=[(-1, r"(a−m)/σ"), (0, "0"), (2, r"(b−m)/σ")], W=480, H=230, xr=(-3.5, 3.5)) +
        '<div class="cap">어떤 정규분포든 결국 이 그림 하나</div>', ratio=(1.4, 1)), "마무리")

    d.slide("과제 — 고쟁이", cols(
        box("<b>필수 (STEP 1, 빈출 포함)</b><br>567, 568, 571, 572, 573, 574, 575, 576<br>577, 578, 579, 580", "blue") +
        box("<b>선택 (STEP 2)</b><br>650, 653, 655, 656, 660, 663, 665, 668, 669, 672<br>676, 678, 679", "") +
        box("<b>도전 (STEP 3)</b><br>701, 703, 704, 706, 708, 713, 714", "gray"),
        '<p><b>채점 전 자기 점검</b></p>' + ul(["\"X는 N(m, σ²)\" 한 줄을 썼는가?", "분산이 아니라 표준편차로 나눴는가?", "그림을 그리고 0.5를 더했는지 뺐는지 확인했는가?",
                                        "이항분포 문제에서 B(n, p)를 먼저 적었는가?"]) +
        '<p class="muted">다음 시간: \"전교생 키 평균을 알고 싶은데 30명만 잴 수 있다면?\" → 표본평균의 분포</p>'), "과제")

    d.slide("추가 연습 (시간이 남으면)", cols(
        box(r"<b>A (577)</b> $X\sim B\!\left(48,\tfrac34\right)$ 일 때 $P(33\le X\le42)$ 를 구하시오. "
            r"<span class='muted'>(P(0≤Z≤1)=0.3413, P(0≤Z≤2)=0.4772)</span>", "") +
        box(r"<b>B (675)</b> 서로 다른 동전 2개를 동시에 100번 던질 때 한 개만 앞면이 나오는 횟수를 $X$, A·B 두 사람이 가위바위보를 162번 할 때 A가 이기는 횟수를 $Y$라 하자. "
            r"$P(X\le30)=P(Y\ge k)$ 를 만족시키는 $k$는?", ""),
        box(r"<b>A</b> $np=36,\ npq=9$ → $N(36,3^2)$, $P(-1\le Z\le2)=0.3413+0.4772=$ <span class='ans'>0.8185</span>", "gray") +
        box(r"<b>B</b> $X$: $N(50,5^2)$, $Y$: $B\!\left(162,\tfrac13\right)$ → $N(54,6^2)$. $P(X\le30)=P(Z\le-4)$, 대칭이므로 $\dfrac{k-54}{6}=4$ → <span class='ans'>k=78</span>", "gray"),
        ratio=(1.1, 1)), "추가")
    return d

# ================================================================ 덱 2: 통계적 추정 (1)
def deck_sampling():
    d = Deck("6차시", "통계적 추정 (1) 모집단과 표본, 표본평균·표본비율의 분포")
    d.cover("통계적 추정 (1)<br>모집단과 표본, 표본평균·표본비율의 분포",
            "확률과 통계 Ⅲ. 통계 — 6차시 (50분) · 고쟁이 02 유형 01~05",
            ["전수조사·표본조사, 임의추출, 복원·비복원추출의 뜻을 알고 모평균·표본평균 등의 기호를 구분한다.",
             r"작은 모집단에서 표본평균의 분포를 직접 만들어 $E(\bar X)=m,\ V(\bar X)=\dfrac{\sigma^2}{n}$ 을 확인한다.",
             r"정규모집단에서 $\bar X\sim N\!\left(m,\dfrac{\sigma^2}{n}\right)$ 을 이용해 확률을 구한다.",
             r"표본비율 $\hat p=\dfrac Xn$ 의 평균·분산을 구하고 정규근사로 확률을 구한다."])

    d.slide("오늘의 흐름 (50분)", table(["단계", "시간", "내용"], [
        ["도입", "8분", "전교생 키 → 30명만 재기 · 용어 · 모집단 {1, 2, 3}에서 크기 2 표본 9가지 나열"],
        ["개념 1", "7분", r"$E(\bar X)=m,\ V(\bar X)=\sigma^2/n$ · 정규모집단이면 $\bar X$도 정규 · 용어 구분"],
        ["예제 1~4", "13분", "직접 나열 → 표본통계량 → 공식 → 모집단 분포표에서 σ(X̄)"],
        ["개념 2", "5분", r"표본비율 $\hat p=X/n$, $X\sim B(n,p)$ → 평균 p, 분산 pq/n"],
        ["예제 5~8", "14분", "정규모집단 → 활용 → 표본비율 기본 → 표본비율 활용"],
        ["마무리", "3분", "X̄와 p̂ 비교표, 과제"]], "flow"), "흐름")

    d.section("1. 도입", "전교생 키를 30명으로 추측하기 (8분)")
    d.slide("도입 ① 다 잴 수 없으면 일부만 잰다", cols(
        ul(["전교생 1000명의 키 평균을 알고 싶다. 다 재면 <b>전수조사</b>: 정확하지만 시간이 많이 든다.",
            "30명만 뽑아 재고 전체를 <b>추측</b>하자: <b>표본조사</b>. 조사 대상 전체가 <b>모집단</b>, 뽑힌 30명이 <b>표본</b>(크기 30).",
            "뽑을 때는 누구나 같은 확률로 → <b>임의추출</b>. 뽑은 사람을 다시 넣고 뽑으면 <b>복원</b>, 안 넣으면 <b>비복원</b>.",
            "모집단이 표본보다 훨씬 크면 복원·비복원의 차이는 거의 없다. 이 단원의 임의추출은 <b>복원추출</b>로 본다."]),
        dots_svg(W=440, H=240) + '<div class="cap">717: 인구 조사·징병 검사는 전수조사, 수질·수명·출구 조사는 표본조사</div>', ratio=(1.4, 1)), "도입")

    d.slide("도입 ② 용어 — 그리고 핵심 질문 하나", cols(
        table(["", "모집단", "표본"], [
            ["평균", "모평균 $m$", r"표본평균 $\bar X=\dfrac1n(X_1+\cdots+X_n)$"],
            ["분산", r"모분산 $\sigma^2$", r"표본분산 $S^2=\dfrac{1}{n-1}\sum(X_i-\bar X)^2$"],
            ["표준편차", r"모표준편차 $\sigma$", r"표본표준편차 $S=\sqrt{S^2}$"],
            ["비율", "모비율 $p$", r"표본비율 $\hat p=\dfrac Xn$"]], "left") +
        '<p class="small">표본분산은 <b>n−1로 나눈다</b> (2022 개정, 720). 모분산(n으로 나눔)과 다르다.</p>',
        box("<b>핵심 질문</b><br>\"30명을 <u>다시</u> 뽑으면 $\\bar X$가 똑같이 나올까?\"<br><br>"
            "→ 아니다. <b>$\\bar X$는 뽑을 때마다 달라지는 확률변수</b>다.<br>그러면 분포가 있고, 평균과 분산도 있다. 그걸 알아내는 게 오늘 수업.", "blue"), ratio=(1.3, 1)), "도입")

    grid = table(["첫 번째 \\ 두 번째", "1", "2", "3"], [["1", "1", "1.5", "2"], ["2", "1.5", "2", "2.5"], ["3", "2", "2.5", "3"]])
    d.slide("도입 ③ 직접 만들어 보기 — 모집단 {1, 2, 3}, 크기 2 복원추출", cols(
        ul([r"모집단: 1, 2, 3이 적힌 공 세 개 (각 확률 $\tfrac13$). 모평균 $m=2$, 모분산 $\sigma^2=\dfrac{1+4+9}{3}-2^2=\dfrac23$",
            "크기 2인 표본을 복원추출 → 순서쌍 9가지. 각 칸은 그 표본의 평균 $\\bar X$."]) + grid,
        box(r"학생 활동 (2분): 9칸을 직접 채우고 $\bar X$가 1, 1.5, 2, 2.5, 3이 되는 횟수를 세어 보자.", "gray") +
        table([r"$\bar X$", "1", "1.5", "2", "2.5", "3", "합계"], [["P", r"$\tfrac19$", r"$\tfrac29$", r"$\tfrac39$", r"$\tfrac29$", r"$\tfrac19$", "1"]])), "도입")

    pop = bars_svg([1, 2, 3], [1 / 3] * 3, W=250, H=210, labels=["1/3", "1/3", "1/3"], title="모집단 X의 분포", ymax=0.45)
    smp = bars_svg([1, 1.5, 2, 2.5, 3], [1 / 9, 2 / 9, 3 / 9, 2 / 9, 1 / 9], W=300, H=210, color=ORANGE,
                   labels=["1/9", "2/9", "3/9", "2/9", "1/9"], title="표본평균 X̄의 분포 (n=2)", ymax=0.45)
    d.slide("도입 ④ 표본평균의 평균과 분산을 직접 계산하면",
        ul([r"$E(\bar X)=\dfrac{1\cdot1+1.5\cdot2+2\cdot3+2.5\cdot2+3\cdot1}{9}=\dfrac{18}{9}=2=m$ ✓",
            r"$E(\bar X^2)=\dfrac{1+4.5+12+12.5+9}{9}=\dfrac{13}{3}$, $V(\bar X)=\dfrac{13}{3}-4=\dfrac13=\dfrac{\sigma^2}{2}$ ✓"]) +
        cols(box("<b>감각 두 줄</b> 표본평균의 평균은 모평균과 <b>같고</b>, 분산은 <b>1/n로 줄어든다</b>.<br>\"많이 뽑을수록 표본평균은 모평균 근처에 몰린다.\" 모양도 평평했던 모집단과 달리 가운데가 높아진다.", "blue"),
             '<div class="cols">' + pop + smp + '</div>', ratio=(1.1, 1)), "도입")

    d.section("2. 개념 정리", "표본평균의 분포 · 용어 구분 · 표본비율 (7분)")
    d.slide("개념 ① 표본평균 X̄의 분포", cols(
        box(r"모평균 m, 모표준편차 σ인 모집단에서 크기 n인 표본을 임의추출할 때<br>"
            r"$$E(\bar X)=m,\qquad V(\bar X)=\frac{\sigma^2}{n},\qquad \sigma(\bar X)=\frac{\sigma}{\sqrt n}$$", "blue") +
        ul([r"모집단이 $N(m,\sigma^2)$ 이면 $\bar X\sim N\!\left(m,\dfrac{\sigma^2}{n}\right)$",
            r"모집단이 정규분포가 아니어도 n이 충분히 크면(n ≥ 30) 근사적으로 그렇다.",
            r"표준화: $Z=\dfrac{\bar X-m}{\sigma/\sqrt n}$ — 분모가 σ가 아니라 <b>$\sigma/\sqrt n$</b>"]),
        normal_svg([dict(m=0, s=2, color=BLUE, label="모집단 X", dx=-90), dict(m=0, s=1, color=ORANGE, label="X̄ (n=4)", dx=0)],
                   ticks=[(0, "m")], W=480, H=250, xr=(-7, 7)) +
        '<div class="cap">같은 평균, 표본평균은 σ/√n 만큼만 흔들린다</div>', ratio=(1.4, 1)), "개념")

    d.slide("개념 ② 상수인가 변수인가 — 기호 구분", cols(
        table(["기호", "뜻", "상수 / 변수"], [
            ["$m,\\ \\sigma$", "모평균, 모표준편차", "상수 (모르지만 정해진 값)"],
            [r"$\bar X,\ S$", "표본평균, 표본표준편차", "<b>확률변수</b> (표본마다 다름)"],
            [r"$E(\bar X)=m,\ \sigma(\bar X)=\dfrac{\sigma}{\sqrt n}$", "표본평균의 평균, 표준편차", "상수"]], "left"),
        box("<b>퀴즈 (729)</b> 모평균 10, 모분산 5인 모집단에서 크기 20인 표본. 옳지 <u>않은</u> 것은?<br>"
            r"① $\bar X$의 평균은 10 ② 분산은 $\tfrac14$ ③ 표준편차는 $\tfrac12$<br>④ $\bar X$의 분포는 <b>항상</b> 모집단의 분포와 같다<br>"
            r"⑤ 모집단이 정규분포면 $\bar X\sim N\!\left(10,\left(\tfrac12\right)^2\right)$", "gray") +
        '<p class="muted">답 ④ — 도입의 {1, 2, 3} 예시가 반례(평평 → 산 모양).</p>', ratio=(1.25, 1)), "개념")

    d.slide("개념 ③ 표본비율 p̂의 분포 — 이항분포 ÷ n", cols(
        ul([r"모비율 p인 모집단에서 크기 n인 표본 중 그 특성을 갖는 개수 $X$는 $X\sim B(n,p)$ (3차시).",
            r"표본비율 $\hat p=\dfrac Xn$ 이므로 이항분포의 평균·분산을 n으로 나누면"]) +
        box(r"$$E(\hat p)=\frac{np}{n}=p,\quad V(\hat p)=\frac{npq}{n^2}=\frac{pq}{n}$$ $$\sigma(\hat p)=\sqrt{\frac{pq}{n}}$$"
            r"n이 충분히 크면 $\hat p$는 근사적으로 $N\!\left(p,\dfrac{pq}{n}\right)$ (지난 시간 정규근사를 n으로 나눈 것)", "blue"),
        box("<b>퀴즈 (735)</b> 옳은 것만 고르면?<br>ㄱ. $E(\\hat p)=p$<br>ㄴ. $V(\\hat p)$은 n에 반비례<br>ㄷ. $\\sigma(\\hat p)$은 n에 반비례", "gray") +
        '<p class="muted">답 ㄱ, ㄴ — σ(p̂)은 <b>√n</b>에 반비례.</p>' +
        box("<b>퀴즈 (738)</b> p=0.9, n=100이면 V(p̂)=0.03?", "gray") +
        '<p class="muted">× — V = 0.09/100 = 0.0009. 0.03은 표준편차.</p>', ratio=(1.4, 1)), "개념")

    d.slide("자주 하는 실수 세 가지", ul([
        r"$\sigma(\bar X)=\dfrac{\sigma}{n}$ 으로 쓴다. <b>분산</b>이 1/n배, 표준편차는 <b>$1/\sqrt n$</b>배.",
        r"표본평균 문제를 모표준편차 σ로 표준화한다. 반드시 $\dfrac{\bar X-m}{\sigma/\sqrt n}$.",
        r"모<b>분산</b>이 주어졌는데 표준편차로 착각한다. 725: 모분산 36 → σ=6부터."]) +
        box(r"풀이 첫 줄 습관: \"$\bar X$는 $N\!\left(m,\left(\dfrac{\sigma}{\sqrt n}\right)^2\right)$\" 을 숫자로 써 놓고 시작한다.", "blue"), "개념")

    d.section("3. 예제 1~8", "직접 나열 → 공식 → 정규모집단 → 활용 → 표본비율")

    d.problem(1, "기본", "표본평균의 분포를 직접 만들기",
              "모집단의 확률분포가 오른쪽 표와 같다. 이 모집단에서 크기가 2인 표본을 복원추출하여 구한 표본평균을 $\\bar X$라 할 때" +
              ol([r"$P(\bar X=2)$", r"$E(\bar X)$, $V(\bar X)$ (직접 구한 뒤 공식으로 검산)"]) +
              table(["X", "1", "2", "3", "합계"], [["P(X=x)", r"$\tfrac13$", r"$\tfrac13$", r"$\tfrac13$", "1"]]),
              None, "도입에서 만든 9칸 표를 그대로 쓴다.")
    d.solution(1, "표본평균의 분포를 직접 만들기",
               ol([r"$\bar X=2$인 표본: (1, 3), (2, 2), (3, 1) → $P(\bar X=2)=\dfrac39=$ <span class='ans'>$\tfrac13$</span>",
                   r"분포표에서 $E(\bar X)=2$, $V(\bar X)=\dfrac{13}{3}-4=\dfrac13$. 공식 검산: $m=2$, $\sigma^2=\dfrac23$, $\dfrac{\sigma^2}{2}=\dfrac13$ ✓"]),
               r"721은 확률이 $\tfrac14,\tfrac14,\tfrac12$인 버전: $P(\bar X=2)=2\times\tfrac14\times\tfrac12+\tfrac14\times\tfrac14=\dfrac{5}{16}$. "
               "\"어떤 순서쌍이 그 평균을 만드는가\"를 세는 문제.",
               "721, 764, 765, 766, 768")

    d.problem(2, "기본", "표본통계량 계산",
              r"크기가 5인 표본 1, 3, 5, 7, 9에 대하여 표본평균 $\bar X$, 표본분산 $S^2$, 표본표준편차 $S$의 값을 차례로 구하시오.",
              None, "표본분산의 분모는 n인가, n−1인가?")
    d.solution(2, "표본통계량 계산",
               ol([r"$\bar X=\dfrac{1+3+5+7+9}{5}=$ <span class='ans'>5</span>",
                   r"$S^2=\dfrac{(1-5)^2+(3-5)^2+0+(7-5)^2+(9-5)^2}{5-1}=\dfrac{40}{4}=$ <span class='ans'>10</span>",
                   r"$S=$ <span class='ans'>$\sqrt{10}$</span>"]),
               r"n−1로 나누는 이유는 \"그래야 $E(S^2)=\sigma^2$가 된다\"고만 말해 준다. 시험에서 분모 n으로 쓰면 8이 나와 틀린다.",
               "719, 720")

    d.problem(3, "기본", "공식 적용",
              ol([r"평균 20, 표준편차 4인 모집단에서 크기 16인 표본을 임의추출할 때 $E(\bar X)$, $\sigma(\bar X)$",
                  r"모평균 6, <b>모분산</b> 36인 모집단에서 크기 16인 표본을 임의추출할 때 $\sigma(2\bar X-3)$"]),
              None, "(2)에서 36은 분산. 2차시의 aX+b 공식은 X̄에도 그대로.")
    d.solution(3, "공식 적용",
               ol([r"$E(\bar X)=$ <span class='ans'>20</span>, $\sigma(\bar X)=\dfrac{4}{\sqrt{16}}=$ <span class='ans'>1</span>",
                   r"$\sigma=6$, $\sigma(\bar X)=\dfrac{6}{4}=\dfrac32$, $\sigma(2\bar X-3)=2\times\dfrac32=$ <span class='ans'>3</span>"]),
               r"726: $V(\bar X)=\dfrac{8}{n}\le\dfrac12$ → $n\ge16$. \"분산이 □ 이하가 되는 n\"은 부등식 한 줄.",
               "723, 724, 725, 726, 769")

    d.problem(4, "기본→확장", "모집단 분포표에서 σ(X̄)",
              "모집단의 확률변수 $X$의 확률분포가 오른쪽 표와 같다. 이 모집단에서 크기가 4인 표본을 복원추출하여 구한 표본평균 $\\bar X$의 표준편차를 구하시오." +
              table(["X", "−2", "0", "1", "합계"], [["P(X=x)", r"$\tfrac14$", r"$\tfrac14$", r"$\tfrac12$", "1"]]),
              None, "먼저 모집단의 분산(2차시), 그다음 n으로 나누기(오늘).")
    d.solution(4, "모집단 분포표에서 σ(X̄)",
               ol([r"$m=-2\cdot\tfrac14+0+1\cdot\tfrac12=0$, $E(X^2)=4\cdot\tfrac14+0+1\cdot\tfrac12=\dfrac32$ → $\sigma^2=\dfrac32$",
                   r"$V(\bar X)=\dfrac{\sigma^2}{4}=\dfrac38$, $\sigma(\bar X)=\sqrt{\dfrac38}=$ <span class='ans'>$\dfrac{\sqrt6}{4}$</span>"]),
               "2단계가 전부다: ① 모집단의 평균·분산 ② n으로 나누기. 767(서술형)·770은 이 두 단계를 그대로 쓰면 만점.",
               "727, 728, 767, 770, 772")

    Z6 = [("1.0", "0.3413"), ("1.5", "0.4332"), ("2.0", "0.4772"), ("2.5", "0.4938")]
    d.problem(5, "확장", "정규모집단에서 X̄의 분포",
              ol([r"정규분포 $N(10,4^2)$을 따르는 모집단에서 크기 4인 표본을 임의추출할 때, 표본평균 $\bar X$의 평균과 분산의 합",
                  r"정규분포 $N(11,2^2)$을 따르는 모집단에서 크기 25인 표본을 임의추출할 때, $P(10\le\bar X\le12)$"]), Z6,
              r"\"$\bar X$는 N(m, (σ/√n)²)\" 한 줄을 숫자로 쓴 뒤 4차시처럼 표준화.")
    d.solution(5, "정규모집단에서 X̄의 분포",
               ol([r"$\bar X\sim N(10,2^2)$ → 평균 10, 분산 4 → 합 <span class='ans'>14</span>",
                   r"$\bar X\sim N\!\left(11,\left(\tfrac25\right)^2\right)$. $P\!\left(\dfrac{10-11}{0.4}\le Z\le\dfrac{12-11}{0.4}\right)=P(-2.5\le Z\le2.5)=2\times0.4938=$ <span class='ans'>0.9876</span>"]),
               r"731(역산): $P(15\le\bar X\le25)=P(0\le Z\le5)$ 이려면 $\dfrac{10}{10/\sqrt n}=5$ → $\sqrt n=5$ → n=25.",
               "724, 730, 731, 773, 775")

    d.problem(6, "확장", "표본평균 활용 (스키마 p.203)",
              ol(["어느 고등학교 3학년 남학생의 키는 평균 175 cm, 표준편차 5 cm인 정규분포를 따른다. 이 중 25명을 임의추출할 때 표본평균이 173 cm 이상 175 cm 이하일 확률은?",
                  "어느 가게의 달걀 한 개의 무게는 평균 50 g, 표준편차 6 g인 정규분포를 따르고, 임의추출한 달걀 4개를 한 세트로 판매한다. 한 세트의 무게가 182 g 이상일 확률은? (포장 무게 제외)"]),
              Z6, "(2) \"4개의 합이 182 이상\"을 \"4개의 평균이 □ 이상\"으로 바꾼다.")
    d.solution(6, "표본평균 활용",
               ol([r"$\bar X\sim N\!\left(175,\left(\tfrac{5}{\sqrt{25}}\right)^2\right)=N(175,1^2)$. $P(173\le\bar X\le175)=P(-2\le Z\le0)=$ <span class='ans'>0.4772</span>",
                   r"합 ≥ 182 ↔ 평균 $\bar X\ge45.5$. $\bar X\sim N\!\left(50,\left(\tfrac{6}{2}\right)^2\right)=N(50,3^2)$. "
                   r"$P(\bar X\ge45.5)=P\!\left(Z\ge\dfrac{45.5-50}{3}\right)=P(Z\ge-1.5)=0.5+0.4332=$ <span class='ans'>0.9332</span>"]),
               "합·총량의 조건은 n으로 나눠 평균의 조건으로 바꾼다 (783 짐 무게 총합 500 kg, 785 비누 40개 3000 g).",
               "732, 733, 734, 782, 783, 785")

    d.problem(7, "기본", "표본비율의 기본",
              ol([r"어느 고등학교 학생 500명 중 70명을 임의추출하여 혈액형을 조사하였더니 A형이 18명이었다. A형 학생의 표본비율 $\hat p$의 값은?",
                  r"모비율이 $\dfrac14$인 모집단에서 크기 300인 표본을 임의추출할 때 표본비율 $\hat p$의 평균과 표준편차를 구하시오."]),
              None, "(1) 분모는 500인가 70인가? (2) σ(p̂)=√(pq/n).")
    d.solution(7, "표본비율의 기본",
               ol([r"$\hat p=\dfrac{18}{70}=$ <span class='ans'>$\dfrac{9}{35}$</span> (표본 안에서의 비율이므로 분모는 70)",
                   r"$E(\hat p)=$ <span class='ans'>$\dfrac14$</span>, $\sigma(\hat p)=\sqrt{\dfrac{\frac14\cdot\frac34}{300}}=\sqrt{\dfrac{1}{1600}}=$ <span class='ans'>$\dfrac{1}{40}$</span>"]),
               r"788·789: $V(\hat p)=\dfrac{0.21}{n}=\dfrac{1}{800}$ → n=168, $\sigma(\hat p)=\sqrt{\dfrac{2/9}{n}}\le\dfrac1{30}$ → n ≥ 200. 분산·표준편차 조건은 n에 대한 부등식.",
               "722, 735, 736, 737, 786, 788, 789")

    d.problem(8, "확장", "표본비율 활용",
              "모비율이 0.8인 모집단에서 크기 100인 표본을 임의추출할 때, 표본비율 $\\hat p$이 0.88 이상일 확률을 오른쪽 표를 이용하여 구하시오.",
              [("1.0", "0.3413"), ("1.5", "0.4332"), ("2.0", "0.4772")],
              "p̂의 평균과 표준편차부터. 그다음은 정규분포 문제와 똑같다.")
    d.solution(8, "표본비율 활용",
               ol([r"$E(\hat p)=0.8$, $V(\hat p)=\dfrac{0.8\times0.2}{100}=0.0016$, $\sigma(\hat p)=0.04$ → $\hat p\sim N(0.8,0.04^2)$",
                   r"$P(\hat p\ge0.88)=P\!\left(Z\ge\dfrac{0.88-0.8}{0.04}\right)=P(Z\ge2)=0.5-0.4772=$ <span class='ans'>0.0228</span>"]),
               r"지난 시간 679(1600대 중 A사 비율 47.5~52.5 %)를 $\hat p$로 다시 풀면 $\sigma(\hat p)=\sqrt{0.25/1600}=0.0125$, $P(-2\le Z\le2)=0.9544$로 같은 답. "
               "두 풀이를 나란히 두면 \"표본비율 = 이항분포 ÷ n\"이 체감된다.",
               "739, 740, 741, 742, 790, 791, 792")

    d.section("4. 마무리", "X̄와 p̂ 한 표로 · 과제")
    d.slide("마무리 — 표본평균과 표본비율은 같은 구조", cols(
        table(["", r"표본평균 $\bar X$", r"표본비율 $\hat p$"], [
            ["평균", "$m$", "$p$"],
            ["분산", r"$\dfrac{\sigma^2}{n}$", r"$\dfrac{pq}{n}$"],
            ["표준편차", r"$\dfrac{\sigma}{\sqrt n}$", r"$\sqrt{\dfrac{pq}{n}}$"],
            ["n이 크면", r"$N\!\left(m,\dfrac{\sigma^2}{n}\right)$", r"$N\!\left(p,\dfrac{pq}{n}\right)$"],
            ["표준화", r"$\dfrac{\bar X-m}{\sigma/\sqrt n}$", r"$\dfrac{\hat p-p}{\sqrt{pq/n}}$"]], "left"),
        box("<b>한 줄 정리</b> 표본평균은 \"평균 그대로, 분산은 1/n\". 표본비율은 \"평균 p, 분산 pq/n\". 둘 다 n이 크면 정규분포.", "blue") +
        '<p class="muted">다음 시간: \"표본평균 180 cm 하나를 보고 모평균이 180이라고 단정해도 될까?\" → 신뢰구간</p>'), "마무리")

    d.slide("과제 — 고쟁이", cols(
        box("<b>필수 (STEP 1, 빈출 포함)</b><br>720, 721, 723, 724, 727, 729, 730, 732<br>733, 734, 736, 738, 739", "blue") +
        box("<b>선택 (STEP 2)</b><br>766, 767, 768, 770, 774, 777, 782<br>788, 789, 791, 792", "") +
        box("<b>도전 (STEP 3)</b><br>821, 822, 823, 824, 826", "gray"),
        '<p><b>채점 전 자기 점검</b></p>' + ul(["표준편차를 √n으로 나눴는가? (n이 아니라)", "모분산과 모표준편차를 구분했는가?",
                                        "표본분산은 n−1로 나눴는가?", "합·총량 조건을 평균 조건으로 바꿨는가?"])), "과제")
    return d


# ================================================================ 덱 3: 통계적 추정 (2)
def deck_estimation():
    d = Deck("7차시", "통계적 추정 (2) 모평균·모비율의 추정")
    d.cover("통계적 추정 (2)<br>모평균·모비율의 추정",
            "확률과 통계 Ⅲ. 통계 — 7차시 (50분) · 고쟁이 02 유형 06~09",
            [r"신뢰구간이 \"표본평균 ± k·σ/√n\"으로 만들어지는 이유와 신뢰도의 뜻을 설명한다.",
             "모평균의 신뢰도 95 %, 99 % 신뢰구간과 그 길이를 구한다.",
             r"신뢰구간·길이가 주어졌을 때 $\bar x$, n, σ, 신뢰도를 역산한다.",
             r"모비율의 신뢰구간 $\hat p\pm k\sqrt{\hat p\hat q/n}$ 과 길이 조건에서 n의 최솟값을 구한다."])

    d.slide("오늘의 흐름 (50분)", table(["단계", "시간", "내용"], [
        ["도입", "8분", "표본평균 180 하나로 m을 단정할 수 있나? → X̄의 흔들림 폭 → 95 % 그물"],
        ["개념 1", "7분", "신뢰구간 공식, 신뢰도의 뜻(그림), 길이와 n·신뢰도의 관계"],
        ["예제 1~4", "13분", "95 % 구간 → S로 대신(서술형) → 길이 → 구간에서 역산"],
        ["개념 2", "4분", r"모비율: σ 자리에 $\sqrt{\hat p\hat q}$"],
        ["예제 5~8", "15분", "n 최솟값 → 신뢰도 역산 → 모비율 구간 → 모비율 n 최솟값"],
        ["마무리", "3분", "통계적 추정 OX 체크, 과제"]], "flow"), "흐름")

    d.section("1. 도입", "표본평균 하나로 모평균을 단정해도 될까? (8분)")
    fig_sh = normal_svg([dict(m=0, s=1, color=BLUE)], shade=[dict(a=-1.96, b=1.96, color=BLUE, op=0.3)],
                        ticks=[(-1.96, "m−1.96"), (0, "m"), (1.96, "m+1.96")], vlines=[(0, "")],
                        notes=[(0, 0.3, "95 %", INK)], W=560, H=250, xr=(-3.6, 3.6))
    d.slide("도입 ① 표본평균 180 cm, 그러면 모평균은 180인가?", cols(
        ul(["어느 학교 학생 100명의 제자리멀리뛰기 기록을 재었더니 평균 $\\bar x=180$ cm. 모표준편차는 10 cm로 알려져 있다.",
            r"지난 시간: $\bar X\sim N\!\left(m,\left(\tfrac{10}{\sqrt{100}}\right)^2\right)=N(m,1^2)$. 즉 $\bar X$는 m 근처에서 <b>±1 정도</b> 흔들린다.",
            "180이 딱 m일 리는 없다. m은 <b>180 근처 어딘가</b>. \"얼마나 근처?\"가 오늘의 질문."]),
        fig_sh + '<div class="cap">X̄의 분포. 색칠 부분(m ± 1.96×1)에 X̄가 들어올 확률이 95 %</div>', ratio=(1.25, 1)), "도입")

    d.slide("도입 ② 95 % 그물 만들기", cols(
        ol([r"$\bar X$가 $m\pm1.96\times1$ 안에 있을 확률이 95 %: $P(|\bar X-m|\le1.96)=0.95$",
            r"$|\bar X-m|\le1.96$ 을 <b>m 쪽에서</b> 풀어 쓰면 $\bar X-1.96\le m\le\bar X+1.96$",
            r"숫자를 넣으면 $178.04\le m\le181.96$"]) +
        box("이것이 <b>신뢰도 95 %의 신뢰구간</b>. \"m을 95 % 확률로 잡는 그물\"을 표본평균 양쪽에 1.96×(σ/√n)만큼 펼친 것.", "blue"),
        box(r"일반식<br>$$\bar x-1.96\frac{\sigma}{\sqrt n}\ \le\ m\ \le\ \bar x+1.96\frac{\sigma}{\sqrt n}$$"
            r"<span class='small'>1.96은 $P(|Z|\le1.96)=0.95$에서 온 값. 99 %면 2.58.</span>", ""), ratio=(1.3, 1)), "도입")

    d.slide("도입 ③ 신뢰도 95 %의 뜻 — m은 고정, 구간이 움직인다", cols(
        ci_svg(W=620, H=330),
        ul(["m은 정해진 하나의 값(우리가 모를 뿐). 표본을 뽑을 때마다 $\\bar x$가 달라지니 <b>구간이 달라진다</b>.",
            "표본을 100번 뽑아 구간 100개를 만들면 그중 <b>약 95개가 m을 포함</b>한다.",
            "\"이 구간 안에 m이 95 % 확률로 있다\"가 아니라 \"이 <b>방법</b>으로 만든 구간은 95 %가 m을 잡는다\"."]) +
        box("803 ㄱ \"신뢰구간 안에 반드시 m이 있다\" → <b>×</b>", "gray"), ratio=(1.15, 1)), "도입")

    d.slide("도입 ④ 그물 폭의 감각", cols(
        ul([r"폭(길이) $=2\times1.96\times\dfrac{\sigma}{\sqrt n}$",
            "더 확실하게 잡고 싶으면(99 %) 그물을 <b>넓혀야</b> 한다: 1.96 → 2.58",
            "표본을 많이 뽑으면(n↑) 그물이 좁아져도 된다: <b>n을 4배 하면 폭은 절반</b>",
            "폭은 m의 값, $\\bar x$의 값과 무관하다 (795)"]),
        '<svg class="fig" viewBox="0 0 520 230" width="520" height="230">'
        '<line x1="260" y1="10" x2="260" y2="220" stroke="#1b1b1b" stroke-width="2" stroke-dasharray="6 5"/>'
        '<text x="260" y="24" font-size="17" text-anchor="middle" fill="#1b1b1b">m</text>'
        '<line x1="140" y1="70" x2="380" y2="70" stroke="#2a78d6" stroke-width="5" stroke-linecap="round"/><text x="396" y="76" font-size="18" fill="#1b1b1b">95 %, n</text>'
        '<line x1="102" y1="125" x2="418" y2="125" stroke="#eb6834" stroke-width="5" stroke-linecap="round"/><text x="430" y="131" font-size="18" fill="#1b1b1b">99 %, n</text>'
        '<line x1="200" y1="180" x2="320" y2="180" stroke="#2a78d6" stroke-width="5" stroke-linecap="round"/><text x="336" y="186" font-size="18" fill="#1b1b1b">95 %, 4n</text>'
        '</svg><div class="cap">신뢰도↑ → 길이↑ · n 4배 → 길이 1/2</div>', ratio=(1.3, 1)), "도입")

    d.section("2. 개념 정리", "신뢰구간 공식 · 길이와 역산 · 모비율 (7분)")
    d.slide("개념 ① 모평균의 신뢰구간", cols(
        box(r"모집단이 $N(m,\sigma^2)$, 크기 n인 표본의 평균이 $\bar x$일 때<br>"
            r"신뢰도 95 %: $\bar x-1.96\dfrac{\sigma}{\sqrt n}\le m\le\bar x+1.96\dfrac{\sigma}{\sqrt n}$<br>"
            r"신뢰도 99 %: $\bar x-2.58\dfrac{\sigma}{\sqrt n}\le m\le\bar x+2.58\dfrac{\sigma}{\sqrt n}$<br>"
            r"신뢰도 α %: $P(|Z|\le k)=\dfrac{\alpha}{100}$ 인 k로 $\bar x\pm k\dfrac{\sigma}{\sqrt n}$ "
            r"<span class='small'>(표가 $P(0\le Z\le k)$이면 $\dfrac{\alpha}{200}$)</span>", "blue"),
        ul(["σ를 모르면 n이 충분히 클 때(n ≥ 30) 표본표준편차 <b>S</b>를 대신 쓴다. (749, 752)",
            "<b>문제가 준 값을 쓴다</b>: P(0≤Z≤2)=0.475로 주면 k=2, P(0≤Z≤2.6)=0.495로 주면 k=2.6.",
            r"답안 세 줄: ① $\bar x$, σ(또는 S), n ② $k\dfrac{\sigma}{\sqrt n}$ 계산 ③ 구간"]), ratio=(1.35, 1)), "개념")

    d.slide("개념 ② 신뢰구간의 길이 — 역산은 전부 이 식 하나", cols(
        box(r"$$\text{길이 } l=2k\frac{\sigma}{\sqrt n}$$ 구간 $a\le m\le b$가 주어지면 <b>$\bar x=\dfrac{a+b}{2}$ (중점)</b>, $l=b-a$", "blue") +
        ul(["신뢰도↑(k↑) → 길이↑ · n↑ → 길이↓", "n이 4배 → 길이 1/2 · n이 100배 → 길이 1/10", "길이는 m, $\\bar x$와 무관 (795 (1) ○, (2) ×)"]),
        box("<b>자주 하는 실수</b>" + ul([r"길이를 $k\dfrac{\sigma}{\sqrt n}$(반길이)로 쓴다 → 길이는 <b>2배</b>",
                                      r"n 최솟값에서 부등호를 거꾸로: $\dfrac{1}{\sqrt n}\le\cdots$ 이면 n은 <b>크게</b>",
                                      r"신뢰도 역산에서 $\dfrac{\alpha}{100}$과 $\dfrac{\alpha}{200}$ 혼동"]), "gray")), "개념")

    d.slide("개념 ③ 모비율의 신뢰구간 — σ 자리에 √(p̂q̂)", cols(
        box(r"표본비율 $\hat p$, $\hat q=1-\hat p$, n이 충분히 클 때<br>"
            r"신뢰도 95 %: $\hat p-1.96\sqrt{\dfrac{\hat p\hat q}{n}}\le p\le\hat p+1.96\sqrt{\dfrac{\hat p\hat q}{n}}$<br>"
            r"길이: $2\times1.96\sqrt{\dfrac{\hat p\hat q}{n}}$", "blue"),
        ul([r"모평균 공식의 $\dfrac{\sigma}{\sqrt n}$ 자리에 $\sqrt{\dfrac{\hat p\hat q}{n}}$ 이 들어간 것뿐. 중점·길이·역산 요령 전부 같다.",
            r"계산 요령: $\sqrt{\dfrac{0.16}{n}}=\dfrac{0.4}{\sqrt n}$ 처럼 분자를 먼저 제곱근으로 꺼내면 소수 계산이 줄어든다."]), ratio=(1.3, 1)), "개념")

    d.section("3. 예제 1~8", "95 % 구간 → S 대신 → 길이 → 역산 → n 최솟값 → 신뢰도 역산 → 모비율")

    d.problem(1, "기본", "95 % 신뢰구간",
              "표준편차가 5인 정규분포를 따르는 모집단에서 크기 25인 표본을 임의추출하여 구한 표본평균이 100일 때, 모평균 m의 신뢰도 95 %의 신뢰구간을 구하시오. "
              "<span class='muted'>(P(0≤Z≤1.96)=0.475)</span>", None, "σ/√n 부터. 그다음 1.96배.")
    d.solution(1, "95 % 신뢰구간",
               ol([r"$\dfrac{\sigma}{\sqrt n}=\dfrac{5}{5}=1$, $1.96\times1=1.96$",
                   r"$100-1.96\le m\le100+1.96$ → <span class='ans'>$98.04\le m\le101.96$</span>"]),
               "796은 표본 9개의 값이 나열된 버전: 표본평균 30을 직접 구한 뒤 같은 절차.", "743, 796")

    d.problem(2, "기본", "σ 대신 S (서술형 틀)",
              "어느 회사 앱에 대한 소비자 만족도를 조사하기 위해 소비자 100명을 임의추출했더니 표본평균 50점, 표본표준편차 15점이었다. 전체 소비자 평가 점수의 평균 m에 대한 신뢰도 95 %의 신뢰구간을 구하시오. "
              "<span class='muted'>(P(0≤Z≤1.96)=0.475)</span>", None, "모표준편차가 없다. 무엇으로 대신하는가? 조건은?")
    d.solution(2, "σ 대신 S",
               ol(["n = 100 ≥ 30 이므로 σ 대신 표본표준편차 S = 15를 쓴다.",
                   r"$\dfrac{S}{\sqrt n}=\dfrac{15}{10}=1.5$, $1.96\times1.5=2.94$",
                   r"$50\pm2.94$ → <span class='ans'>$47.06\le m\le52.94$</span>"]),
               r"748(서술형, 99 %, P(0≤Z≤2.6)=0.495로 지정): $180\pm2.6\times\dfrac{10}{10}$ → $177.4\le m\le182.6$. 문제가 준 k값(2.6)을 그대로.",
               "748, 749, 752, 807")

    d.problem(3, "기본", "신뢰구간의 길이",
              ol(["표준편차 6인 정규모집단에서 크기 36인 표본으로 추정한 모평균의 신뢰도 95 % 신뢰구간의 길이 <span class='muted'>(P(0≤Z≤1.96)=0.475)</span>",
                  r"표준편차 σ인 정규모집단에서 크기 16인 표본으로 추정한 신뢰구간의 길이가 $l$이다. 같은 신뢰도로 크기 64인 표본으로 추정하면 길이는?"]),
              None, "길이 = 2k·σ/√n. (2)는 √n이 몇 배가 되는지만.")
    d.solution(3, "신뢰구간의 길이",
               ol([r"$2\times1.96\times\dfrac{6}{\sqrt{36}}=2\times1.96\times1=$ <span class='ans'>3.92</span>",
                   r"n이 4배 → $\sqrt n$이 2배 → 길이 <span class='ans'>$\dfrac l2$</span>"]),
               "746: 길이 4를 1로(1/4배) 줄이려면 √n이 4배 → n은 16배 → 8×16 = 128.", "745, 746, 750, 751")

    d.problem(4, "기본→확장", "구간에서 x̄와 n 역산",
              r"모표준편차가 16 g인 정규분포를 따르는 모집단에서 크기 n인 표본을 임의추출하여 모평균을 신뢰도 95 %로 추정한 신뢰구간이 $164.5\le m\le172.5$ 일 때, n의 값을 구하시오. "
              "<span class='muted'>(P(0≤Z≤2)=0.475로 계산)</span>", None, "구간의 중점은 무엇? 길이는 몇?")
    d.solution(4, "구간에서 x̄와 n 역산",
               ol([r"중점 $\bar x=\dfrac{164.5+172.5}{2}=168.5$, 길이 $172.5-164.5=8$",
                   r"$2\times2\times\dfrac{16}{\sqrt n}=8$ → $\dfrac{64}{\sqrt n}=8$ → $\sqrt n=8$ → <span class='ans'>n=64</span>"]),
               r"\"길이 = 2kσ/√n\" 하나로 n, σ, k 중 무엇이든 역산한다. 800(n+$\bar x$), 808(a+n), 809(a+n)가 전부 이 식.",
               "754, 800, 808, 809, 813")

    d.problem(5, "확장", "길이 조건에서 n의 최솟값",
              "모표준편차가 2인 정규분포를 따르는 모집단에서 신뢰도 99 %로 모평균을 추정할 때, 신뢰구간의 길이가 1.2 이하가 되도록 하는 표본의 크기 n의 최솟값은? "
              "<span class='muted'>(P(|Z|≤2.58)=0.99로 계산)</span>", None, "길이 ≤ 1.2 를 n에 대한 부등식으로. 부등호 방향에 주의.")
    d.solution(5, "길이 조건에서 n의 최솟값",
               ol([r"$2\times2.58\times\dfrac{2}{\sqrt n}\le1.2$ → $\dfrac{10.32}{\sqrt n}\le1.2$",
                   r"$\sqrt n\ge\dfrac{10.32}{1.2}=8.6$ → $n\ge73.96$ → 최솟값 <span class='ans'>74</span>"]),
               r"806(모평균과 표본평균의 <b>차</b> ≤ 0.7): 이건 <b>반길이</b> 조건 $1.96\dfrac{10}{\sqrt n}\le0.7$ → n ≥ 784. \"길이\"인지 \"차\"인지 먼저 구분.",
               "744, 753, 806, 811")

    d.problem(6, "확장", "신뢰도 역산 (스키마 p.204)",
              r"정규분포 $N(m,20^2)$을 따르는 모집단에서 크기 100인 표본을 임의추출하여 얻은 표본평균이 119.6이었다. 이 표본평균으로 추정한 모평균의 신뢰도 α %의 신뢰구간이 $116.6\le m\le122.6$ 일 때, α의 값을 오른쪽 표를 이용하여 구하시오.",
              [("1.5", "0.43"), ("1.8", "0.46"), ("2.1", "0.48"), ("2.5", "0.49")], "반길이 = k × σ/√n 에서 k를 찾는다.")
    d.solution(6, "신뢰도 역산",
               ol([r"반길이 $122.6-119.6=3$, $\dfrac{\sigma}{\sqrt n}=\dfrac{20}{10}=2$ → $3=k\times2$ → $k=1.5$",
                   r"$P(|Z|\le1.5)=2\times0.43=0.86$ → <span class='ans'>α = 86</span>"]),
               "801(스키마): 79.6 % ↔ k=1.27, 길이 2배 ↔ k=2.54 ↔ 98.9 %. \"길이가 a배면 k도 a배\"를 표에서 찾는다.",
               "797, 801, 802, 810, 812")

    d.problem(7, "확장", "모비율의 신뢰구간",
              "어느 온라인 쇼핑몰 이용자 1600명을 임의추출하여 조사했더니 1280명이 신규 제품을 재구매할 의사가 있다고 답했다. 전체 이용자 중 재구매 의사가 있는 비율 p에 대한 신뢰도 95 %의 신뢰구간을 구하시오. "
              "<span class='muted'>(P(0≤Z≤2)=0.475로 계산)</span>", None, "p̂, q̂ → √(p̂q̂/n) → k배.")
    d.solution(7, "모비율의 신뢰구간",
               ol([r"$\hat p=\dfrac{1280}{1600}=0.8$, $\hat q=0.2$, $\sqrt{\dfrac{\hat p\hat q}{n}}=\sqrt{\dfrac{0.16}{1600}}=\dfrac{0.4}{40}=0.01$",
                   r"$0.8\pm2\times0.01$ → <span class='ans'>$0.78\le p\le0.82$</span>, 즉 $\dfrac{39}{50}\le p\le\dfrac{41}{50}$"]),
               r"756(n=100, $\hat p$=0.1, k=1.96): $\sqrt{0.09/100}=0.03$, $0.1\pm0.0588$ → $0.0412\le p\le0.1588$. "
               r"757(길이): $2\times2.58\times\sqrt{\tfrac{0.64\times0.36}{144}}=2\times2.58\times0.04=0.2064$.",
               "756, 757, 758, 760, 761, 819")

    d.problem(8, "확장", "모비율 — 길이 조건에서 n의 최솟값",
              r"어느 백화점 고객 n명을 임의추출하여 조사했더니 20 %가 오전에 방문하였다. 오전 방문 고객의 비율 p에 대한 신뢰도 95 %의 신뢰구간 $a\le p\le b$에 대하여 $b-a\le0.1$ 이 되도록 하는 n의 최솟값은? "
              "<span class='muted'>(P(|Z|≤2)=0.95로 계산)</span>", None, "√(0.16/n) = 0.4/√n 으로 바꾸면 계산이 쉽다.")
    d.solution(8, "모비율 — n의 최솟값",
               ol([r"$2\times2\times\sqrt{\dfrac{0.2\times0.8}{n}}\le0.1$ → $\sqrt{\dfrac{0.16}{n}}\le0.025$",
                   r"$\dfrac{0.4}{\sqrt n}\le0.025$ → $\sqrt n\ge16$ → <span class='ans'>n ≥ 256, 최솟값 256</span>"]),
               r"832(모비율과 표본비율의 <b>차</b> ≤ 0.02, $\hat p$=0.1): 반길이 조건 $1.96\sqrt{\tfrac{0.09}{n}}\le0.02$ → $\sqrt n\ge29.4$ → n ≥ 864.36 → 865.",
               "762, 763, 816, 817, 818, 820, 832")

    d.section("4. 마무리", "OX 체크 · 과제")
    ox = [["신뢰구간의 길이는 모평균의 값과 관계없다"], ["표본평균이 커지면 신뢰구간의 길이가 길어진다"],
          ["n이 일정할 때 길이를 짧게 하면 신뢰도가 낮아진다"], ["신뢰도가 일정할 때 n을 100배 하면 길이는 1/10"],
          ["신뢰도를 높이면서 n을 크게 하면 길이는 길어진다"], ["신뢰도를 높일 때 길이를 유지하려면 n을 작게 한다"],
          ["같은 표본에서 99 % 구간은 95 % 구간을 포함한다"]]
    d.slide("마무리 ① 통계적 추정 OX — 먼저 스스로 판단 (795, 747)",
            table(["문장", "O / X"], [[r[0], ""] for r in ox], "left") +
            '<p class="muted">짝과 30초 토론 후 다음 슬라이드에서 확인.</p>', "마무리")
    d.slide("마무리 ② OX 정답과 이유",
            table(["문장", "O/X", "이유"], [
                [ox[0][0], "○", r"길이 $=2k\sigma/\sqrt n$ 에 m이 없다"],
                [ox[1][0], "×", r"$\bar x$는 중점만 옮긴다"],
                [ox[2][0], "○", "k가 작아진다"],
                [ox[3][0], "○", r"$\sqrt{100}=10$"],
                [ox[4][0], "×", "둘이 반대 방향, 알 수 없다"],
                [ox[5][0], "×", "n을 크게 해야 한다"],
                [ox[6][0], "○", "중점이 같고 더 넓다"]], "left") +
            box("<b>한 줄 정리</b> 신뢰구간 = 표본평균(또는 표본비율) ± k × (표준오차). 길이는 2k × (표준오차). 역산은 전부 이 식 하나.", "blue"), "마무리")

    d.slide("과제 — 고쟁이", cols(
        box("<b>필수 (STEP 1, 빈출 포함)</b><br>743, 744, 747, 748, 749, 753, 754<br>756, 758, 759, 762", "blue") +
        box("<b>선택 (STEP 2)</b><br>795, 797, 800, 801, 804, 806, 808<br>813, 816, 818, 819", "") +
        box("<b>도전 (STEP 3)</b><br>827, 828, 830, 832, 833, 834", "gray"),
        '<p><b>시험 전 점검</b></p>' + ul(["문제가 k를 1.96으로 주는지 2로 주는지 조건에서 먼저 확인했는가?", "\"길이\"인지 \"차(반길이)\"인지 구분했는가?",
                                      "구간이 주어지면 중점 = x̄, 길이 = b − a 부터 적었는가?", "모비율은 σ 자리에 √(p̂q̂)를 넣었는가?"])), "과제")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--assets", default=None, help="tex-svg.js, nanum-400.woff2, nanum-700.woff2 가 있는 폴더 (내장용)")
    a = ap.parse_args()
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for fn, name in [(deck_normal, "4_5차시-정규분포와-정규근사"), (deck_sampling, "6차시-표본평균과-표본비율"),
                     (deck_estimation, "7차시-모평균과-모비율의-추정")]:
        n = render(fn(), out / ("수업슬라이드-%s.html" % name), a.assets)
        print(name, n, "slides")

if __name__ == "__main__":
    main()
