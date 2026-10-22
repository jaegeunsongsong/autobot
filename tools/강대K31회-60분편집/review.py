"""내용 검토: 괘선 제거 로그, 해설 경계 공백 검사, 단 위·아래 띠 모음 이미지 생성"""
import sys, io
sys.path.insert(0, '/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad/src')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import build
from build import SP, EL, SOLS, SEG_INFO, SPLIT_LOG, STRIP_LOG

build.load_elements()
print('== 괘선으로 지운 행 (머리글·문항 요소 추출 중) ==')
by = {}
for (p, box, y) in STRIP_LOG:
    by.setdefault((p, box), []).append(y)
for k, ys in by.items():
    print('  page', k[0], 'box', k[1], 'rows', ys[:12], '...' if len(ys) > 12 else '')
STRIP_LOG.clear()

out = {}
for key in ['prob', 'calc', 'geo']:
    SPLIT_LOG.clear()
    pages = build.build_solutions(key)
    out[key] = (pages, list(SPLIT_LOG))
    print(f'== {key}: 분할 지점 ==', SPLIT_LOG)

print('== 해설 조각 경계 공백 검사 (경계 ±3행에 잉크가 있으면 글줄이 잘렸을 수 있음) ==')
for name, segs in SEG_INFO.items():
    for i, (p, col, y0, y1) in enumerate(segs):
        a = build.page_arr(p) < build.INK
        x0, x1 = build.sol_xrange(p, col)
        top_ink = int(a[y0 - 3:y0 + 3, x0:x1].sum())
        bot_ink = int(a[y1 - 3:y1 + 3, x0:x1].sum())
        spec = SOLS[name][i]
        flag = ''
        if spec[2] != 'top' and top_ink > 0: flag += ' <top-ink>'
        if spec[3] != 'end' and bot_ink > 0: flag += ' <bottom-ink>'
        print(f'  {name}[{i}] p{p}{col} y{y0}-{y1} start={spec[2]} end={spec[3]} ink@top={top_ink} ink@bottom={bot_ink}{flag}')
print('== 해설 조각 추출 중 지운 행 ==', STRIP_LOG[:20])

# 띠 모음: 각 쪽·단의 위 230px / 아래 230px
font = ImageFont.truetype(f'{SP}/fonts/kmw/koreanize_matplotlib/fonts/NanumGothicBold.ttf', 22)
for key, (pages, splits) in out.items():
    sel = range(len(pages)) if key == 'prob' else range(6, len(pages))
    strips = []
    for pi in sel:
        im = pages[pi]
        for col, x0 in (('L', 168), ('R', 1333)):
            top = 520 if pi == 0 else build.SOL_TOP
            if pi == 0 and col == 'L':
                continue
            t = im.crop((x0, top - 10, x0 + 1130, top + 230))
            b = im.crop((x0, build.SOL_BOTTOM - 240, x0 + 1130, build.SOL_BOTTOM + 10))
            strips.append((f'{key} p{pi+1}{col} TOP', t))
            strips.append((f'{key} p{pi+1}{col} BOTTOM', b))
    sw = 565; sh = 120
    sheet = Image.new('L', (sw * 2 + 30, (sh + 30) * ((len(strips) + 1) // 2) + 10), 160)
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(strips):
        r, c = divmod(i, 2)
        x = 10 + c * (sw + 10); y = 10 + r * (sh + 30)
        d.text((x, y), label, fill=0, font=font)
        sheet.paste(im.resize((sw, sh)), (x, y + 26))
    sheet.save(f'{SP}/debug/strips_{key}.png')
    print(key, 'strips', len(strips), sheet.size)

# 좌우 가장자리 잘림 검사: 조각 이미지의 첫/끝 2열에 잉크가 있으면 글자가 잘렸을 가능성
print('== 해설 조각 좌우 가장자리 검사 ==')
for name in SOLS:
    for i, im in enumerate(build.sol_segments(name)):
        a = np.asarray(im) < build.INK
        l = int(a[:, :2].sum()); r = int(a[:, -2:].sum())
        pad = int(a[:, :build.SEG_PAD - 4].sum())
        print(f'  {name}[{i}] w={im.width} ink@left2={l} ink@right2={r} ink@pad={pad}' + (' <LEFT>' if l else '') + (' <RIGHT>' if r else ''))
for key in ['prob', 'calc', 'geo']:
    print(key, 'meta', {p: (build.sol_meta(p)['left'], build.sol_meta(p)['div']) for p in sorted(set(s[0] for n in SOLS for s in SOLS[n]))} if key == 'prob' else '')
