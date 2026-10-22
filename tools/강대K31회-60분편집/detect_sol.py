"""Detect solution headers ("N. ______ 정답 X" rules) on the 해설 pages 22-39."""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw

R = '/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad/render'
OUT = '/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad/debug'
os.makedirs(OUT, exist_ok=True)


def analyse(page):
    im = Image.open(f'{R}/p-{page:02d}.png').convert('L')
    a = np.asarray(im)
    ink = a < 140
    H, W = ink.shape
    # header rule: strongest long row in top 700px
    sub = ink[:700]
    win = sub[:-2] | sub[1:-1] | sub[2:]
    rows = win.sum(axis=1); rows[:100] = 0
    rule = int(np.argmax(rows)) + 1
    # divider
    xs = range(W // 2 - 120, W // 2 + 120)
    div = max(xs, key=lambda x: ink[rule + 50:H - 300, x - 4:x + 5].any(axis=1).sum())
    bottom = H - 300
    cols = {'L': (120, div - 25), 'R': (div + 25, W - 100)}
    res = {'page': page, 'rule': rule, 'div': div, 'bottom': bottom, 'cols': {}}
    dbg = im.convert('RGB'); d = ImageDraw.Draw(dbg)
    d.line([(0, rule), (W, rule)], fill='red', width=3)
    d.line([(div, rule), (div, bottom)], fill='blue', width=3)
    for name, (x0, x1) in cols.items():
        seg = ink[rule + 10:bottom, x0:x1]
        cw = x1 - x0
        # long horizontal rules: use 3-row window
        win = seg[:-2] | seg[1:-1] | seg[2:]
        rs = win.sum(axis=1)
        cand = np.where(rs > 0.4 * cw)[0]
        # group consecutive rows
        rules = []
        for y in cand:
            if rules and y - rules[-1][1] <= 6:
                rules[-1][1] = y
            else:
                rules.append([y, y])
        heads = []
        for (ya, yb) in rules:
            yy = (ya + yb) // 2 + rule + 10
            # a header rule has the big number just above-left and no vertical line crossing it
            above = ink[yy - 110:yy - 5, x0:x0 + 140]
            below = ink[yy + 5:yy + 60, x0:x1]
            vert = ink[yy - 40:yy + 40, x0:x1].all(axis=0).sum()  # columns fully inked across the rule
            big = above.sum()
            is_head = big > 600 and vert < 3
            heads.append({'y': int(yy), 'thick': int(yb - ya + 1), 'big': int(big), 'vert': int(vert), 'head': bool(is_head)})
            d.line([(x0, yy), (x1, yy)], fill='green' if is_head else 'orange', width=5)
            if is_head:
                d.rectangle([x0, yy - 110, x0 + 140, yy - 5], outline='magenta', width=3)
        # content extent
        ys = np.where(seg.any(axis=1))[0]
        ext = (int(ys.min() + rule + 10), int(ys.max() + rule + 10)) if len(ys) else None
        res['cols'][name] = {'x': [x0, x1], 'rules': heads, 'extent': ext}
    small = dbg.resize((W // 4, H // 4))
    ds = ImageDraw.Draw(small)
    from PIL import ImageFont
    f = ImageFont.truetype('/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad/fonts/kmw/koreanize_matplotlib/fonts/NanumGothicBold.ttf', 16)
    for name in 'LR':
        x0 = res['cols'][name]['x'][0]
        for h in res['cols'][name]['rules']:
            ds.text((x0 // 4 + (0 if name == 'L' else 120), h['y'] // 4 - 18), f"{h['y']} b{h['big']}", fill='red', font=f)
    small.save(f'{OUT}/s-{page:02d}.png')
    return res


if __name__ == '__main__':
    pages = [int(p) for p in sys.argv[1:]] or list(range(22, 40))
    allres = {}
    for p in pages:
        r = analyse(p)
        allres[p] = r
        print(f"page {p} (해설 {p-21}): rule={r['rule']} div={r['div']} bottom={r['bottom']}")
        for c in 'LR':
            cc = r['cols'][c]
            print(f"   {c} x={cc['x']} extent={cc['extent']} heads={[h['y'] for h in cc['rules'] if h['head']]} other_rules={[(h['y'],h['big'],h['vert']) for h in cc['rules'] if not h['head']]}")
    json.dump(allres, open(f'{OUT}/sol.json', 'w'))
