#!/usr/bin/env python3
"""강대모의고사K 31회 → 60분 편집본 (공통 9·10·11·12·13·14·15·20·21 + 선택 28·29) 문제지/정답및해설 생성."""
import io, os, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pymupdf

SP = '/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad'
R = f'{SP}/render'
BLOCKS = json.load(open(f'{SP}/debug/blocks.json'))
FONTDIR = f'{SP}/fonts/kmw/koreanize_matplotlib/fonts'
F_GOTHIC = f'{FONTDIR}/NanumGothic.ttf'
F_GOTHIC_B = f'{FONTDIR}/NanumGothicBold.ttf'
F_SERIF = '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
F_SERIF_I = '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else f'{SP}/out'
PREV = f'{SP}/preview'
os.makedirs(OUTDIR, exist_ok=True); os.makedirs(PREV, exist_ok=True)

W, H = 2550, 3794          # 출력 캔버스 (원본 스캔과 동일, 300dpi)
STRIP_LOG = []             # (page, box, y) 괘선으로 판단해 지운 행
SEG_INFO = {}              # name -> [(p, col, y0, y1)]
SPLIT_LOG = []             # (name, seg_idx, cut_row, page_idx, col)
INK = 200

# ----------------------------------------------------------------- 원본 페이지 접근
_cache = {}


def page_arr(p):
    if p not in _cache:
        a = np.asarray(Image.open(f'{R}/p-{p:02d}.png').convert('L')).copy()
        a[a > 205] = 255          # 스캔 배경 정리
        _cache[p] = a
    return _cache[p]


def erase_vruns(gray, ncols, minrun=40, band=4):
    """gray(2차원 uint8, 복사본)의 왼쪽 ncols 열에서 세로로 minrun px 이상 이어지는 진한 잉크(단 구분선)를 찾아
    그 열 ±band 열을 흰색으로 지운다 (기울어진 선의 흐린 테두리까지 제거)."""
    dark = gray[:, :ncols] < 160
    for x in range(dark.shape[1]):
        ys = np.where(dark[:, x])[0]
        if len(ys) < minrun:
            continue
        s0 = prev = ys[0]
        for y in list(ys[1:]) + [None]:
            if y is None or y - prev > 2:
                if prev - s0 + 1 >= minrun:
                    gray[s0:prev + 1, max(0, x - band):x + band + 1] = 255
                if y is not None:
                    s0 = y
            if y is not None:
                prev = y
    return gray


def grab(p, box, pad=0, strip_rules=True, trim_x=True, erase=None, strip_top=False, erase_vcols=0):
    """box=(x0,y0,x1,y1) 영역을 잘라, 가장자리에 걸친 긴 가로선(머리글 괘선)을 지우고 여백을 트림한다.
    erase: 페이지 좌표의 상자 목록 — 자르기 전에 흰색으로 지움.  strip_top: 위쪽 14행 중 잉크가 20%를 넘는 행(기울어진 괘선 잔상) 제거."""
    x0, y0, x1, y1 = [int(v) for v in box]
    a = page_arr(p)[y0:y1, x0:x1].copy()
    for (ex0, ey0, ex1, ey1) in (erase or []):
        a[max(0, ey0 - y0):max(0, ey1 - y0), max(0, ex0 - x0):max(0, ex1 - x0)] = 255
    if erase_vcols:
        erase_vruns(a, erase_vcols)
    ink = a < INK
    h, w = ink.shape
    keep = np.ones(h, bool)
    rowsum = ink.sum(axis=1)

    def longest_run(row):
        best = cur = 0
        for v in row:
            cur = cur + 1 if v else 0
            if cur > best:
                best = cur
        return best

    if strip_rules:
        rule_rows = []
        for y in list(range(min(60, h))) + list(range(max(0, h - 60), h)):
            if rowsum[y] > 0.25 * w and longest_run(ink[y]) >= 0.3 * w:
                keep[max(0, y - 3):y + 4] = False
                rule_rows.append(y)
                STRIP_LOG.append((p, box, y0 + y))
        if rule_rows:
            # 기울어진 괘선의 나머지: 괘선 행 ±14행 안에 '완전히' 들어가는 세로 10px 이하의 잉크 조각만 지운다 (글자 획은 더 길다)
            lo, hi = max(0, min(rule_rows) - 14), min(h, max(rule_rows) + 15)
            for x in range(w):
                ys = np.where(ink[:, x])[0]
                if len(ys) == 0:
                    continue
                s0 = prev = ys[0]
                for y in list(ys[1:]) + [None]:
                    if y is None or y - prev > 1:
                        if s0 >= lo and prev < hi and prev - s0 + 1 <= 10:
                            a[s0:prev + 1, x] = 255
                        if y is not None:
                            s0 = y
                    if y is not None:
                        prev = y
            ink = a < INK
            rowsum = ink.sum(axis=1)
    if strip_top:
        # 위쪽 14행 중 '끊기지 않은 긴 가로 잉크(괘선)'가 있는 행만 지운다 (글자 행은 연속 구간이 짧다)
        for y in range(min(14, h)):
            if longest_run(ink[y]) >= 0.25 * w:
                keep[y] = False
                STRIP_LOG.append((p, box, y0 + y))
    ink2 = ink & keep[:, None]
    ys = np.where(ink2.any(axis=1))[0]
    xs = np.where(ink2.any(axis=0))[0]
    if len(ys) == 0:
        raise ValueError(f'empty crop p{p} {box}')
    a2 = a.copy(); a2[~keep] = 255
    cy0, cy1 = max(0, ys.min() - pad), min(h, ys.max() + 1 + pad)
    if trim_x:
        cx0, cx1 = max(0, xs.min() - pad), min(w, xs.max() + 1 + pad)
    else:
        cx0, cx1 = 0, w
    return Image.fromarray(a2[cy0:cy1, cx0:cx1])


def qitem(p, col, idx):
    return BLOCKS[str(p)]['cols'][col]['items'][idx]


def question_img(p, col, idx, skip_hdr=False):
    it = qitem(p, col, idx)
    x0, y0, x1, y1 = it['box']
    if skip_hdr:
        y0 = it['subs'][1][0]
    return grab(p, (x0 - 30, y0 - 6, x1 + 8, y1 + 8))


def header_img(p, col, idx):
    it = qitem(p, col, idx)
    x0, y0, x1, y1 = it['box']
    s0, s1 = it['subs'][0]
    return grab(p, (x0 - 6, s0 - 6, x1 + 8, s1 + 8), strip_rules=False)


def box_img(p, col, idx):
    it = qitem(p, col, idx)
    x0, y0, x1, y1 = it['box']
    return grab(p, (x0 - 8, y0 - 8, x1 + 8, y1 + 45), strip_rules=False)


def font(path, size):
    return ImageFont.truetype(path, size)


def text_img(txt, path, size, fill=0):
    f = font(path, size)
    bb = f.getbbox(txt)
    im = Image.new('L', (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), 255)
    ImageDraw.Draw(im).text((2 - bb[0], 2 - bb[1]), txt, font=f, fill=fill)
    return im


def paste(canvas, im, x, y):
    canvas.paste(im, (int(x), int(y)))


def paste_c(canvas, im, cx, cy):
    """중심 좌표에 붙이기"""
    paste(canvas, im, cx - im.width // 2, cy - im.height // 2)


# ----------------------------------------------------------------- 요소 추출
EL = {}


def load_elements():
    global INK
    INK = 140          # 머리글·문항 요소는 진한 잉크 기준으로 트림 (해설 조각은 200)
    EL['title'] = grab(2, (440, 255, 2070, 352))                      # 2026학년도 … 문제지
    EL['gyosi'] = grab(2, (150, 385, 490, 548), strip_rules=False)    # 제2교시
    EL['subj_c'] = grab(2, (520, 390, 2060, 548))                     # 수학 영역 (큰 제목)
    EL['subj_p'] = grab(10, (520, 385, 2060, 560))                    # 수학 영역(확률과 통계)
    EL['subj_m'] = grab(14, (520, 350, 2060, 525))                    # 수학 영역(미적분)
    EL['subj_g'] = grab(18, (520, 375, 2060, 555))                    # 수학 영역(기하)
    EL['subj_small'] = grab(3, (1080, 220, 1480, 340))                # 수학 영역 (속지 제목)
    EL['hol'] = grab(3, (2195, 205, 2425, 350), strip_rules=False)    # 홀수형
    EL['hdr5'] = header_img(2, 'L', 0)                                # 5지선다형
    EL['hdrS'] = header_img(7, 'R', 0)                                # 단답형
    EL['box_c_p'] = box_img(9, 'R', 1)      # 확인 사항 (→확률과 통계)
    EL['box_c_m'] = box_img(13, 'R', 1)     # 확인 사항 (→미적분)
    EL['box_c_g'] = box_img(17, 'R', 1)     # 확인 사항 (→기하)
    EL['box_end'] = box_img(21, 'R', 1)     # 확인 사항 (마지막)
    # 해설
    EL['banner'] = grab(22, (150, 170, 2400, 445), strip_rules=False)
    EL['sol_title'] = grab(23, (1050, 180, 1560, 350))
    EL['label_c'] = grab(22, (1600, 495, 2080, 612), strip_rules=False)
    EL['label_p'] = grab(30, (450, 337, 950, 435), strip_rules=False)
    EL['label_m'] = grab(33, (1600, 327, 2060, 425), strip_rules=False)
    EL['label_g'] = grab(37, (500, 333, 950, 435), strip_rules=False)
    EL['foot_l'] = grab(23, (990, 3520, 1225, 3590))   # 강대모의고사K
    EL['foot_r'] = grab(23, (1395, 3520, 1520, 3590))  # 31회
    # 문항
    EL['c9'] = question_img(4, 'L', 1)
    EL['c10'] = question_img(4, 'R', 0)
    EL['c11'] = question_img(5, 'L', 0)
    EL['c12'] = question_img(5, 'R', 0)
    EL['c13'] = question_img(6, 'L', 0)
    EL['c14'] = question_img(6, 'R', 0)
    EL['c15'] = question_img(7, 'L', 0)
    EL['c20'] = question_img(8, 'R', 0)
    EL['c21'] = question_img(9, 'L', 0)
    EL['p28'] = question_img(12, 'R', 0)
    EL['p29'] = question_img(13, 'L', 0, skip_hdr=True)
    EL['m28'] = question_img(16, 'R', 0)
    EL['m29'] = question_img(17, 'L', 0, skip_hdr=True)
    EL['g28'] = question_img(20, 'R', 0)
    EL['g29'] = question_img(21, 'L', 0, skip_hdr=True)
    for k, v in EL.items():
        v.save(f'{SP}/crops/{k}.png')
    INK = 200


# ----------------------------------------------------------------- 문제지 레이아웃
DIV_X = 1275
COL_X = {'L': 160, 'R': 1318}
RULE_X0, RULE_X1 = 150, 2400
FIRST_RULE_Y = 615
CONT_RULE_Y = 350
CONTENT_BOTTOM = 3440
FOOT_BOX = (1191, 3546, 1358, 3624)
HDR_GAP = 90          # 유형 머리글(5지선다형 등)과 문항 사이 간격

SUBJ = {
    'prob': dict(name='확률과 통계', file='확률과통계', subj='subj_p', box='box_c_p', q=['p28', 'p29'], label='label_p', ans={28: '②', 29: '477'}),
    'calc': dict(name='미적분', file='미적분', subj='subj_m', box='box_c_m', q=['m28', 'm29'], label='label_m', ans={28: '⑤', 29: '4'}),
    'geo': dict(name='기하', file='기하', subj='subj_g', box='box_c_g', q=['g28', 'g29'], label='label_g', ans={28: '②', 29: '208'}),
}
COMMON_Q = ['c9', 'c10', 'c11', 'c12', 'c13', 'c14', 'c15', 'c20', 'c21']
COMMON_ANS = {9: '④', 10: '②', 11: '③', 12: '②', 13: '①', 14: '③', 15: '②', 20: '12', 21: '23'}


def layout_section(items, subject):
    """items: [('hdr', img) | ('q', img) | ('break',)] → 페이지 목록.
    각 단은 상/하 두 슬롯. 문항 높이가 슬롯의 여유를 넘으면 단 전체를 차지한다."""
    pages = []

    def new_page():
        kind = 'first' if not pages else 'cont'
        top = (FIRST_RULE_Y if kind == 'first' else CONT_RULE_Y) + 40
        pages.append({'kind': kind, 'subject': subject, 'num': len(pages) + 1, 'placed': [], 'top': top})
        return pages[-1]

    page = new_page(); col_i = 0; slot = 0; pending = None
    for it in items:
        if it[0] == 'hdr':
            pending = it[1]; continue
        if it[0] == 'break':
            if slot != 0:
                col_i += 1; slot = 0
            continue
        img = it[1]
        extra = (pending.height + HDR_GAP) if pending is not None else 0
        need = img.height + extra
        if col_i > 1:
            page = new_page(); col_i = 0; slot = 0
        half = (CONTENT_BOTTOM - page['top']) // 2
        full = need > half - 100
        if full and slot != 0:
            col_i += 1; slot = 0
            if col_i > 1:
                page = new_page(); col_i = 0
            half = (CONTENT_BOTTOM - page['top']) // 2
        assert need <= CONTENT_BOTTOM - page['top'] - 10, f'too tall: {need}'
        col = 'LR'[col_i]
        y = page['top'] + slot * half
        if pending is not None:
            page['placed'].append((col, COL_X[col], y, pending)); y += pending.height + HDR_GAP; pending = None
        page['placed'].append((col, COL_X[col], y, img))
        if full:
            col_i += 1; slot = 0
        else:
            slot += 1
            if slot > 1:
                col_i += 1; slot = 0
    return pages


def add_end_box(pages, box):
    pg = pages[-1]
    y = CONTENT_BOTTOM - box.height
    used = max([yy + im.height for (c, x, yy, im) in pg['placed'] if c == 'R'], default=0)
    assert used < y - 60, f'end box overlaps column R (used {used}, box top {y})'
    pg['placed'].append(('R', COL_X['R'], y, box))


def digits_img(n, size=130, italic=False):
    return text_img(str(n), F_SERIF_I if italic else F_SERIF, size)


def render_exam_page(pg, foot_n, foot_total):
    im = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(im)
    if pg['kind'] == 'first':
        paste_c(im, EL['title'], 1256, 304)
        num = digits_img(pg['num'])
        paste(im, num, 2336 - num.width, 254)
        paste(im, EL['gyosi'], 170, 470 - EL['gyosi'].height // 2)
        paste_c(im, EL[pg['subject']], 1256, 467)
        paste(im, EL['hol'], 2356 - EL['hol'].width, 513 - EL['hol'].height // 2)
        rule_y = FIRST_RULE_Y
    else:
        n = pg['num']
        paste_c(im, EL['subj_small'], DIV_X, 280)
        num = digits_img(n)
        if n % 2 == 0:
            paste(im, num, 201, 220)
            paste(im, EL['hol'], 2407 - EL['hol'].width, 279 - EL['hol'].height // 2)
        else:
            paste(im, EL['hol'], 150, 279 - EL['hol'].height // 2)
            paste(im, num, 2333 - num.width, 247)
        rule_y = CONT_RULE_Y
    d.rectangle([RULE_X0, rule_y - 2, RULE_X1, rule_y + 2], fill=0)
    d.rectangle([DIV_X - 1, rule_y + 40, DIV_X + 1, CONTENT_BOTTOM + 20], fill=0)
    for (col, x, y, img) in pg['placed']:
        paste(im, img, x, y)
    # 쪽 번호 상자
    x0, y0, x1, y1 = FOOT_BOX
    d.rectangle([x0, y0, x1, y1], outline=0, width=3)
    d.line([(x0 + 3, y1 - 3), (x1 - 3, y0 + 3)], fill=0, width=3)
    a = digits_img(foot_n, 62); b = digits_img(foot_total, 62)
    paste(im, a, x0 + 12, y0 + 6)
    paste(im, b, x1 - 12 - b.width, y1 - 6 - b.height)
    tag = text_img('60분 편집본', F_GOTHIC, 34, fill=110)
    paste(im, tag, RULE_X1 - tag.width, y1 - tag.height)
    return im


def build_exam(key):
    S = SUBJ[key]
    items = [('hdr', EL['hdr5'])] + [('q', EL[q]) for q in COMMON_Q[:7]] + [('break',), ('hdr', EL['hdrS'])] + [('q', EL[q]) for q in COMMON_Q[7:]]
    common = layout_section(items, 'subj_c')
    add_end_box(common, EL[S['box']])
    sel_items = [('hdr', EL['hdr5']), ('q', EL[S['q'][0]]), ('break',), ('hdr', EL['hdrS']), ('q', EL[S['q'][1]])]
    sel = layout_section(sel_items, S['subj'])
    add_end_box(sel, EL['box_end'])
    pages = common + sel
    total = len(pages)
    return [render_exam_page(pg, i + 1, total) for i, pg in enumerate(pages)]


# ----------------------------------------------------------------- 해설 추출
SOL_DIV = 1275
SOL_COL_X = {'L': 180, 'R': 1345}
SOL_COL_W = 1125
SOL_RULE_Y = 400
SOL_TOP = 440
SOL_BOTTOM = 3430
SOL_FOOT_Y = 3550
_solmeta = {}


def sol_meta(p):
    """해설 페이지의 제목 괘선 y, 단 구분선 x, 각 단의 본문 왼쪽 가장자리"""
    if p in _solmeta:
        return _solmeta[p]
    a = page_arr(p) < INK
    Hp, Wp = a.shape
    sub = a[250:480]
    win = sub[:-6] | sub[1:-5] | sub[2:-4] | sub[3:-3] | sub[4:-2] | sub[5:-1] | sub[6:]
    rows = win.sum(axis=1)
    rule = int(np.argmax(rows)) + 253
    assert rows[rule - 253] > 0.25 * Wp, (p, rows[rule - 253])
    xs = range(Wp // 2 - 120, Wp // 2 + 120)
    div = max(xs, key=lambda x: a[rule + 50:Hp - 300, x - 4:x + 5].any(axis=1).sum())
    left = {}
    for col, (xa, xb) in {'L': (100, div - 20), 'R': (div + 20, 2470)}.items():
        reg_g = page_arr(p)[rule + 15:Hp - 330, xa:xb].copy()
        erase_vruns(reg_g, 90)                 # 기울어 들어온 단 구분선은 가장자리 판단에서 제외
        reg = reg_g < 140
        colsum = reg.sum(axis=0)
        lx = None
        for x in np.where(colsum >= 8)[0]:
            if colsum[x:x + 40].sum() >= 200:      # 잡티가 아니라 실제 글자 가장자리
                lx = int(x); break
        left[col] = int(xa + lx)
    _solmeta[p] = dict(rule=rule, div=div, left=left, H=Hp)
    return _solmeta[p]


SEG_PAD = 30               # 해설 조각: 본문 왼쪽 가장자리 앞 여백 (바깥으로 나온 괄호·번호 보존)


def sol_xrange(p, col):
    m = sol_meta(p)
    left = m['left'][col]
    x0 = left - SEG_PAD if col == 'L' else max(left - SEG_PAD, m['div'] + 14)
    x1 = min(left + 1100, m['div'] - 18) if col == 'L' else min(left + 1100, 2470)
    return x0, x1


def hdr_top(p, col, rule_y):
    """'N.' 큰 번호의 위쪽 y (해설 머리 괘선 rule_y 기준)"""
    a = page_arr(p) < INK
    left = sol_meta(p)['left'][col]
    reg = a[rule_y - 140:rule_y - 4, left - 5:left + 170]
    rows = np.where(reg.sum(axis=1) >= 3)[0]
    assert len(rows), (p, col, rule_y)
    runs = [[rows[0], rows[0]]]
    for y in rows[1:]:
        if y - runs[-1][1] <= 8:
            runs[-1][1] = y
        else:
            runs.append([y, y])
    return int(runs[-1][0] + rule_y - 140)


def footer_top(p):
    """해설 쪽 바닥글 상자(n/18)의 윗변 y"""
    a = page_arr(p) < INK
    Hp = a.shape[0]
    a3 = a[:-2] | a[1:-1] | a[2:]
    for y in range(Hp - 340, Hp - 100):
        row = a3[y, 1180:1440]
        # 가장 긴 연속 잉크 구간
        best = cur = 0
        for v in row:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        if best >= 110:
            return y
    raise RuntimeError(f'footer not found p{p}')


def title_rule(p):
    """'수학 영역' 제목 아래 괘선 y. 너무 희미하면 None."""
    a = page_arr(p) < 200
    sub = a[280:480]
    win = sub[:-6] | sub[1:-5] | sub[2:-4] | sub[3:-3] | sub[4:-2] | sub[5:-1] | sub[6:]
    rows = win.sum(axis=1)
    y = int(np.argmax(rows))
    return y + 283 if rows[y] >= 0.35 * a.shape[1] else None


def text_top(p, col):
    """단의 본문 첫 줄 위쪽 y. 제목('수학 영역') 영역은 제외하고, 각 열(x)에서 세로로 8px 이상 이어지는
    첫 잉크(글자 획·그림 선)를 찾아 그 최소 y를 쓴다. 휘거나 기울어진 얇은 제목 괘선(세로 2~6px)은 건너뛴다."""
    x0, x1 = sol_xrange(p, col)
    reg_g = page_arr(p)[280:900, x0:x1].copy()
    erase_vruns(reg_g, max(sol_meta(p)['left'][col] - x0 - 6, 0))
    reg = reg_g < INK
    tx0, tx1 = max(980 - x0, 0), max(1640 - x0, 0)
    reg[:66, tx0:tx1] = False
    best = None
    for x in range(reg.shape[1]):
        ys = np.where(reg[:, x])[0]
        if len(ys) == 0:
            continue
        s0 = prev = ys[0]
        for y in list(ys[1:]) + [None]:
            if y is None or y - prev > 1:
                if prev - s0 + 1 >= 8:
                    if best is None or s0 < best:
                        best = s0
                    break
                if y is not None:
                    s0 = y
            if y is not None:
                prev = y
    if best is None:
        raise RuntimeError(f'text top not found p{p} {col}')
    return int(280 + best - 6)


def col_end(p, col):
    m = sol_meta(p)
    x0, x1 = sol_xrange(p, col)
    lim = footer_top(p) - 30
    reg_g = page_arr(p)[m['rule'] + 12:lim, x0:x1].copy()
    erase_vruns(reg_g, max(m['left'][col] - x0 - 6, 0))
    reg = reg_g < INK
    rows = np.where(reg.sum(axis=1) >= 3)[0]
    return int(rows.max() + m['rule'] + 12 + 1)


def seg(p, col, start, end):
    """start: ('hdr', rule_y) | 'top'   end: ('hdr', rule_y) | 'end' | ('y', y)"""
    m = sol_meta(p)
    y0 = hdr_top(p, col, start[1]) - 10 if start != 'top' else text_top(p, col)
    if end == 'end':
        y1 = col_end(p, col) + 6
    elif end[0] == 'hdr':
        y1 = hdr_top(p, col, end[1]) - 25
    else:
        y1 = end[1]
    x0, x1 = sol_xrange(p, col)
    erase = [(980, 0, 1640, 346)] if (start == 'top' and y0 < 350) else None
    SEG_INFO.setdefault(_cur_seg[0], []).append((p, col, int(y0), int(y1)))
    off = m['left'][col] - x0
    img = grab(p, (x0, y0, x1, y1), strip_rules=False, trim_x=False, erase=erase, strip_top=True, erase_vcols=max(off - 6, 0))
    if off < SEG_PAD:
        padded = Image.new('L', (img.width + SEG_PAD - off, img.height), 255)
        padded.paste(img, (SEG_PAD - off, 0))
        img = padded
    # 본문 가장자리에서 10px 이상 왼쪽은 단 구분선 잔상뿐이므로 모두 흰색으로
    arr = np.asarray(img).copy(); arr[:, :SEG_PAD - 10] = 255
    return Image.fromarray(arr)


SOLS = {
    'c9': [(23, 'L', ('hdr', 1628), ('hdr', 2986))],
    'c10': [(23, 'L', ('hdr', 2986), 'end'), (23, 'R', 'top', ('hdr', 1245))],
    'c11': [(23, 'R', ('hdr', 1245), 'end'), (24, 'L', 'top', ('hdr', 978))],
    'c12': [(24, 'L', ('hdr', 978), 'end')],
    'c13': [(24, 'R', ('hdr', 421), 'end'), (25, 'L', 'top', ('hdr', 791))],
    'c14': [(25, 'L', ('hdr', 791), 'end'), (25, 'R', 'top', ('hdr', 2567))],
    'c15': [(25, 'R', ('hdr', 2567), 'end'), (26, 'L', 'top', 'end'), (26, 'R', 'top', ('hdr', 2614))],
    'c20': [(27, 'L', ('hdr', 2204), 'end'), (27, 'R', 'top', ('hdr', 2794))],
    'c21': [(27, 'R', ('hdr', 2794), 'end'), (28, 'L', 'top', 'end'), (28, 'R', 'top', 'end'), (29, 'L', 'top', ('hdr', 1588))],
    'p28': [(30, 'R', ('hdr', 1976), 'end'), (31, 'L', 'top', 'end'), (31, 'R', 'top', ('hdr', 1724))],
    'p29': [(31, 'R', ('hdr', 1724), 'end'), (32, 'L', 'top', ('hdr', 2728))],
    'm28': [(34, 'L', ('hdr', 3007), 'end'), (34, 'R', 'top', 'end'), (35, 'L', 'top', ('hdr', 2495))],
    'm29': [(35, 'L', ('hdr', 2495), 'end'), (35, 'R', 'top', 'end')],
    'g28': [(37, 'R', ('hdr', 2888), 'end'), (38, 'L', 'top', 'end'), (38, 'R', 'top', ('hdr', 1797))],
    'g29': [(38, 'R', ('hdr', 1797), 'end'), (39, 'L', 'top', ('y', 840))],
}
_segcache = {}


_cur_seg = [None]


def sol_segments(name):
    if name not in _segcache:
        _cur_seg[0] = name
        _segcache[name] = [seg(*s) for s in SOLS[name]]
        for i, im in enumerate(_segcache[name]):
            im.save(f'{SP}/crops/sol_{name}_{i}.png')
    return _segcache[name]


# ----------------------------------------------------------------- 해설 조판
def find_cut(img, avail, min_gap=14):
    a = np.asarray(img) < INK
    blank = ~a.any(axis=1)
    best = None
    y = 0
    n = len(blank)
    while y < n:
        if blank[y]:
            s = y
            while y < n and blank[y]:
                y += 1
            if y - s >= min_gap and s <= avail and s >= 120:
                best = (s + y) // 2
        else:
            y += 1
    return best


def trim_top(img):
    a = np.asarray(img) < INK
    ys = np.where(a.any(axis=1))[0]
    return img.crop((0, max(0, ys.min() - 2), img.width, img.height)) if len(ys) else img


def answer_table(S, width):
    """정답표 이미지 (왼쪽 단용)"""
    fb = font(F_GOTHIC_B, 40); fn = font(F_SERIF_I, 44); fa = font(F_GOTHIC, 42); fa2 = font(F_SERIF, 42); fs = font(F_GOTHIC, 30)
    rows_c = [[(9, '④'), (10, '②'), (11, '③'), (12, '②'), (13, '①')], [(14, '③'), (15, '②'), (20, '12'), (21, '23'), None]]
    rows_s = [[(28, S['ans'][28]), (29, S['ans'][29]), None, None, None]]
    cell_h = 64; ncol = 10; cw = width // ncol
    sections = [('공통과목', rows_c), (S['name'], rows_s)]
    total_h = sum(60 + cell_h * len(r) + 40 for _, r in sections) + 600
    im = Image.new('L', (width, total_h), 255); d = ImageDraw.Draw(im)
    # 제목
    d.rectangle([0, 0, width, 3], fill=0); d.rectangle([0, 10, width, 12], fill=0)
    t = text_img('• 수학 영역 •', F_GOTHIC_B, 46); paste(im, t, (width - t.width) // 2, 30)
    d.rectangle([0, 100, width, 103], fill=0)
    y = 150
    for label, rows in sections:
        h = 60 + cell_h * len(rows)
        d.rectangle([0, y, width - 1, y + h], outline=0, width=3)
        d.text((16, y + 8), label, font=fb, fill=0)
        yy = y + 60
        d.line([(0, yy), (width, yy)], fill=0, width=2)
        for r in rows:
            for j in range(ncol):
                x = j * cw
                d.line([(x, yy), (x, yy + cell_h)], fill=0, width=2)
            d.line([(0, yy + cell_h), (width, yy + cell_h)], fill=0, width=2)
            for j, cell in enumerate(r):
                if cell is None:
                    continue
                n, ans = cell
                ni = text_img(str(n), F_SERIF_I, 44); paste(im, ni, j * 2 * cw + (cw - ni.width) // 2, yy + (cell_h - ni.height) // 2)
                ai = text_img(ans, F_SERIF if (ans.isascii() and ans.isdigit()) else F_GOTHIC, 42); paste(im, ai, (j * 2 + 1) * cw + (cw - ai.width) // 2, yy + (cell_h - ai.height) // 2)
            yy += cell_h
        y += h + 40
    note1 = text_img('※ 강대모의고사K 31회에서 4점 문항만 발췌(22·30번 제외)한 60분 편집본', F_GOTHIC, 30)
    note2 = text_img('※ 공통 9문항 + 선택 2문항 = 11문항, 전 문항 4점, 44점 만점', F_GOTHIC, 30)
    paste(im, note1, 0, y + 10); paste(im, note2, 0, y + 55)
    return im.crop((0, 0, width, y + 110))


def render_sol_page(placed, first, foot_n, foot_total, S):
    im = Image.new('L', (W, H), 255); d = ImageDraw.Draw(im)
    if first:
        paste_c(im, EL['banner'], W // 2, 170 + EL['banner'].height // 2)
        top = 520
        tab = answer_table(S, 1060)
        paste(im, tab, SOL_COL_X['L'], top)
        # MEMO 상자
        my0 = top + tab.height + 80
        d.rectangle([SOL_COL_X['L'], my0, SOL_COL_X['L'] + 1060, SOL_BOTTOM], outline=0, width=3)
        memo = text_img(' MEMO ', F_GOTHIC_B, 34)
        paste(im, memo, SOL_COL_X['L'] + 30, my0 - memo.height // 2)
    else:
        paste_c(im, EL['sol_title'], SOL_DIV, 265)
        d.rectangle([120, SOL_RULE_Y - 2, 2430, SOL_RULE_Y + 2], fill=0)
        top = SOL_TOP
    for (col, x, y, img) in placed:
        paste(im, img, x, y)
    d.rectangle([SOL_DIV - 1, top - 20, SOL_DIV + 1, SOL_BOTTOM], fill=0)
    # 바닥글: 강대모의고사K [n/N] 31회
    bx0, by0, bx1, by1 = 1230, 3510, 1390, 3594
    d.rectangle([bx0, by0, bx1, by1], outline=0, width=3)
    d.line([(bx0 + 3, by1 - 3), (bx1 - 3, by0 + 3)], fill=0, width=3)
    a = digits_img(foot_n, 60); b = digits_img(foot_total, 60)
    paste(im, a, bx0 + 10, by0 + 6); paste(im, b, bx1 - 10 - b.width, by1 - 6 - b.height)
    paste(im, EL['foot_l'], bx0 - 12 - EL['foot_l'].width, 3552 - EL['foot_l'].height // 2)
    paste(im, EL['foot_r'], bx1 + 14, 3552 - EL['foot_r'].height // 2)
    tag = text_img('60분 편집본', F_GOTHIC, 34, fill=110)
    paste(im, tag, 2430 - tag.width, by1 - tag.height)
    return im


def build_solutions(key):
    S = SUBJ[key]
    # 흐름: [라벨, 해설(여러 조각)…]
    flow = [('label', EL['label_c'])] + [('sol', n) for n in COMMON_Q] + [('label', EL[S['label']])] + [('sol', n) for n in S['q']]
    pages = []          # 각 페이지: {'first': bool, 'placed': [...]}
    state = {'page': None, 'col': 0, 'y': 0}

    def new_page():
        first = not pages
        pages.append({'first': first, 'placed': []})
        state['page'] = pages[-1]; state['col'] = 1 if first else 0
        state['y'] = 520 if first else SOL_TOP
        state['top'] = state['y']

    def advance():
        state['col'] += 1
        if state['col'] > 1:
            new_page()
        else:
            state['y'] = state['top']

    def put(img, gap, tag=None):
        while True:
            y = state['y'] + (gap if state['y'] > state['top'] else 0)
            avail = SOL_BOTTOM - y
            if img.height <= avail:
                state['page']['placed'].append(('LR'[state['col']], SOL_COL_X['LR'[state['col']]] - SEG_PAD, y, img))
                state['y'] = y + img.height
                return
            cut = find_cut(img, avail)
            if cut is None:
                if state['y'] == state['top']:
                    raise RuntimeError(f'segment too tall for a column: {img.height}')
                advance(); gap = 0; continue
            top_part = img.crop((0, 0, img.width, cut))
            SPLIT_LOG.append((tag, int(cut), len(pages), 'LR'[state['col']], int(y)))
            state['page']['placed'].append(('LR'[state['col']], SOL_COL_X['LR'[state['col']]] - SEG_PAD, y, top_part))
            img = trim_top(img.crop((0, cut, img.width, img.height)))
            advance(); gap = 0

    new_page()
    for kind, v in flow:
        if kind == 'label':
            lab = v
            # 라벨은 단 중앙 정렬: 폭 1125 기준으로 가운데 배치된 이미지로 감싼다
            wrap = Image.new('L', (SEG_PAD + 1100, lab.height), 255); paste(wrap, lab, SEG_PAD + (1100 - lab.width) // 2, 0)
            put(wrap, 70)
        else:
            for i, s in enumerate(sol_segments(v)):
                put(s, 70 if i == 0 else 28, tag=(v, i))
    total = len(pages)
    return [render_sol_page(pg['placed'], pg['first'], i + 1, total, S) for i, pg in enumerate(pages)]


# ----------------------------------------------------------------- 저장
def save_pdf(images, path):
    doc = pymupdf.open()
    for im in images:
        page = doc.new_page(width=W * 72 / 300, height=H * 72 / 300)
        buf = io.BytesIO(); im.save(buf, format='PNG', optimize=True)
        page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(path, deflate=True, garbage=3)


def save_preview(images, stem):
    for i, im in enumerate(images):
        im.resize((W // 3, H // 3), Image.LANCZOS).save(f'{PREV}/{stem}_{i + 1}.png')


if __name__ == '__main__':
    load_elements()
    print('elements:', {k: (v.width, v.height) for k, v in EL.items()})
    keys = sys.argv[2].split(',') if len(sys.argv) > 2 else ['prob', 'calc', 'geo']
    for key in keys:
        S = SUBJ[key]
        ex = build_exam(key)
        save_pdf(ex, f"{OUTDIR}/강대K_31회_60분편집_{S['file']}_문제지.pdf"); save_preview(ex, f'exam_{key}')
        so = build_solutions(key)
        save_pdf(so, f"{OUTDIR}/강대K_31회_60분편집_{S['file']}_정답및해설.pdf"); save_preview(so, f'sol_{key}')
        print(key, 'exam pages', len(ex), 'solution pages', len(so))
