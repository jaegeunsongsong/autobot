"""최종 PDF 전수 검토: 배치 겹침/범위, 문항 크롭 완전성, 분할 지점 띠, 버전 간 공통 쪽 일치, 정답표."""
import sys, io, hashlib, json
sys.path.insert(0, '/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad/src')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pymupdf
import build
from build import SP, EL, SUBJ, COMMON_Q, SOLS

REPO = '/home/user/autobot/docs/강대모의고사K-31회-60분편집'
font = ImageFont.truetype(f'{SP}/fonts/kmw/koreanize_matplotlib/fonts/NanumGothicBold.ttf', 20)
problems = []

build.load_elements()

# ---------- 1. 문항 크롭 완전성: 원본 블록 영역 잉크 vs 크롭 잉크
B = json.load(open(f'{SP}/debug/blocks.json'))
QSRC = {'c8': (4,'L',0), 'c9': (4,'L',1), 'c10': (4,'R',0), 'c11': (5,'L',0), 'c12': (5,'R',0), 'c13': (6,'L',0), 'c14': (6,'R',0),
        'c18': (8,'L',0), 'c19': (8,'L',1), 'c20': (8,'R',0), 'c21': (9,'L',0),
        'p26': (11,'R',0), 'p27': (12,'L',0), 'p28': (12,'R',0), 'p29': (13,'L',0),
        'm26': (15,'R',0), 'm27': (16,'L',0), 'm28': (16,'R',0), 'm29': (17,'L',0),
        'g26': (19,'R',0), 'g27': (20,'L',0), 'g28': (20,'R',0), 'g29': (21,'L',0)}
print('== 문항 크롭 완전성 (원본 블록 잉크 대비) ==')
for k, (p, col, i) in QSRC.items():
    it = B[str(p)]['cols'][col]['items'][i]
    x0, y0, x1, y1 = it['box']
    if k in ('p29', 'm29', 'g29'):
        y0 = it['subs'][1][0]
    src = build.page_arr(p)[y0:y1, x0:x1] < 140
    crop = np.asarray(EL[k]) < 140
    ratio = crop.sum() / max(1, src.sum())
    flag = '' if 0.97 <= ratio <= 1.03 else '  <<< CHECK'
    print(f'  {k}: 원본 {int(src.sum())} / 크롭 {int(crop.sum())} = {ratio:.3f}  크기 {EL[k].size} 블록 {x1-x0}x{y1-y0}{flag}')
    if flag: problems.append(f'{k} ink ratio {ratio:.3f}')

# ---------- 2. 문제지 배치 겹침/범위
print('== 문제지 배치 검사 ==')
def ink_extent(im):
    a = np.asarray(im) < 200
    ys = np.where(a.any(axis=1))[0]; xs = np.where(a.any(axis=0))[0]
    if len(ys) == 0:
        return None
    return int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())

def check_placed(placed, bottom, label, div=build.DIV_X):
    """실제 잉크 기준: 단 구분선 침범, 아래 경계 초과, 같은 단 안의 겹침"""
    boxes = []
    for (c, x, y, im) in placed:
        e = ink_extent(im)
        if e is None:
            continue
        y0, y1, x0, x1 = e
        boxes.append((c, x + x0, y + y0, x + x1, y + y1))
    for i, (c, xa, ya, xb, yb) in enumerate(boxes):
        if yb > bottom + 2:
            problems.append(f'{label}: 항목 {i} 잉크가 아래 경계 초과 {yb} > {bottom}'); print('  !!', problems[-1])
        if c == 'L' and xb > div - 10:
            problems.append(f'{label}: L 항목 {i} 잉크가 단 구분선 침범 {xb}'); print('  !!', problems[-1])
        if c == 'R' and xa < div + 10:
            problems.append(f'{label}: R 항목 {i} 잉크가 단 구분선 침범 {xa}'); print('  !!', problems[-1])
        for j in range(i + 1, len(boxes)):
            c2, xa2, ya2, xb2, yb2 = boxes[j]
            if c == c2 and not (yb + 15 <= ya2 or yb2 + 15 <= ya):
                problems.append(f'{label}: 항목 {i}와 {j} 겹침/간격부족 ({ya}-{yb} vs {ya2}-{yb2})'); print('  !!', problems[-1])

for key in ['prob', 'calc', 'geo']:
    S = SUBJ[key]
    items = [('hdr', EL['hdr5'])] + [('q', EL[q]) for q in COMMON_Q[:7]] + [('break',), ('hdr', EL['hdrS'])] + [('q', EL[q]) for q in COMMON_Q[7:]]
    common = build.layout_section(items, 'subj_c'); build.add_end_box(common, EL[S['box']])
    sel_items = [('hdr', EL['hdr5'])] + [('q', EL[q]) for q in S['q'][:3]] + [('hdr', EL['hdrS']), ('q', EL[S['q'][3]])]
    sel = build.layout_section(sel_items, S['subj']); build.add_end_box(sel, EL['box_end'])
    for pi, pg in enumerate(common + sel):
        check_placed(pg['placed'], build.CONTENT_BOTTOM, f'{key} 문제지 {pi+1}쪽')
        order = [c for (c, x, y, im) in sorted(pg['placed'], key=lambda t: (t[0], t[2]))]
    # 문항 순서: 배치된 이미지의 id로 순서 확인
    seq = []
    for pg in common + sel:
        for (c, x, y, im) in sorted(pg['placed'], key=lambda t: (t[0] != 'L', t[2])):
            for k in COMMON_Q + S['q']:
                if EL[k] is im: seq.append(k)
    expect = COMMON_Q + S['q']
    print(f'  {key}: 문항 순서 {"OK" if seq == expect else "!! " + str(seq)}  쪽수 {len(common)+len(sel)}')
    if seq != expect: problems.append(f'{key} 문항 순서 {seq}')

# ---------- 3. 해설 배치 겹침/범위 + 분할 지점 띠
print('== 해설 배치 검사 ==')
captured = {}
orig_render = build.render_sol_page
def capture_render(placed, first, foot_n, foot_total, S):
    captured.setdefault(S['name'], []).append(list(placed))
    return orig_render(placed, first, foot_n, foot_total, S)
build.render_sol_page = capture_render
sol_imgs = {}
for key in ['prob', 'calc', 'geo']:
    build.SPLIT_LOG.clear()
    sol_imgs[key] = build.build_solutions(key)
    pages = captured[SUBJ[key]['name']]
    for pi, placed in enumerate(pages):
        check_placed(placed, build.SOL_BOTTOM, f'{key} 해설 {pi+1}쪽', div=build.SOL_DIV)
    print(f'  {key}: 해설 {len(pages)}쪽, 분할 {len(build.SPLIT_LOG)}곳')
    # 분할 지점 띠: 분할된 단의 아래 160px + 다음 단의 위 160px
    strips = []
    splits = list(build.SPLIT_LOG)
    for (tag, cut, page_idx, col, y) in splits:
        pg = sol_imgs[key][page_idx - 1]
        x0 = build.SOL_COL_X[col] - build.SEG_PAD
        strips.append((f'{key} {tag[0]}[{tag[1]}] p{page_idx}{col} 아래', pg.crop((x0, build.SOL_BOTTOM - 170, x0 + 1130, build.SOL_BOTTOM + 5))))
        # 다음 단
        if col == 'L':
            npg, ncol = pg, 'R'
        else:
            npg, ncol = sol_imgs[key][page_idx], 'L'
        nx0 = build.SOL_COL_X[ncol] - build.SEG_PAD
        ntop = (520 if page_idx == 0 else build.SOL_TOP)
        strips.append((f'→ 다음 단 p{page_idx + (col == "R")}{ncol} 위', npg.crop((nx0, ntop - 5, nx0 + 1130, ntop + 170))))
    sw, sh = 565, 88
    sheet = Image.new('L', (sw * 2 + 30, (sh + 28) * ((len(strips) + 1) // 2) + 10), 160); d = ImageDraw.Draw(sheet)
    for k2, (label, im) in enumerate(strips):
        r, c = divmod(k2, 2); x = 10 + c * (sw + 10); yy = 10 + r * (sh + 28)
        d.text((x, yy), label, fill=0, font=font); sheet.paste(im.resize((sw, sh)), (x, yy + 24))
    sheet.save(f'{SP}/debug/splits_{key}.png')
build.render_sol_page = orig_render

# ---------- 4. 저장소 PDF: 쪽수·크기·빈 쪽·버전 간 공통 쪽 일치
print('== 저장소 PDF 검사 ==')
hashes = {}
for key, name in [('prob', '확률과통계'), ('calc', '미적분'), ('geo', '기하')]:
    for kind, n_exp in [('문제지', 4), ('정답및해설', 8)]:
        doc = pymupdf.open(f'{REPO}/강대K_31회_60분편집_{name}_{kind}.pdf')
        ok = len(doc) == n_exp
        for pi in range(len(doc)):
            pix = doc[pi].get_pixmap(dpi=72)
            a = np.frombuffer(pix.samples, dtype=np.uint8)
            dark = (a < 128).mean()
            if dark < 0.003:
                problems.append(f'{name} {kind} {pi+1}쪽 거의 빈 쪽'); print('  !!', problems[-1])
            hashes[(key, kind, pi)] = hashlib.md5(pix.samples).hexdigest()
        r = doc[0].rect
        print(f'  {name} {kind}: {len(doc)}쪽 {"OK" if ok else "!!"} 크기 {round(r.width/72*25.4)}x{round(r.height/72*25.4)}mm')
        if not ok: problems.append(f'{name} {kind} 쪽수 {len(doc)}')
for kind, rng in [('문제지', range(2)), ('정답및해설', range(1, 5))]:
    same = all(hashes[('prob', kind, i)] == hashes[('calc', kind, i)] == hashes[('geo', kind, i)] for i in rng)
    print(f'  공통 부분 동일 여부 ({kind} {rng.start+1}~{rng.stop}쪽): {"동일" if same else "!! 다름"}')
    if not same: problems.append(f'{kind} 공통 쪽 불일치')

# ---------- 5. 정답표 모음
tabs = []
for key, name in [('prob', '확률과통계'), ('calc', '미적분'), ('geo', '기하')]:
    doc = pymupdf.open(f'{REPO}/강대K_31회_60분편집_{name}_정답및해설.pdf')
    im = Image.open(io.BytesIO(doc[0].get_pixmap(dpi=300).tobytes('png'))).convert('L')
    tabs.append(im.crop((160, 640, 1260, 1180)))
sheet = Image.new('L', (1100, 540 * 3 + 20), 160)
for i, t in enumerate(tabs): sheet.paste(t, (0, i * 550))
sheet.resize((825, (540 * 3 + 20) * 825 // 1100)).save(f'{SP}/debug/tables_all.png')

print('== 문제 목록 ==', problems if problems else '없음')
