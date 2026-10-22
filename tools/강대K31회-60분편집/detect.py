"""Detect column structure and ink blocks on rendered exam pages (300 DPI)."""
import sys, json
import numpy as np
from PIL import Image, ImageDraw

R = '/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad/render'
OUT = '/tmp/claude-0/-home-user-autobot/41e35f19-0f38-5c5f-a4f3-52eb600de19d/scratchpad/debug'
import os
os.makedirs(OUT, exist_ok=True)


def load(page):
    im = Image.open(f'{R}/p-{page:02d}.png').convert('L')
    a = np.asarray(im)
    return im, a


def find_divider(ink, y0, y1):
    """vertical divider line near the horizontal centre"""
    W = ink.shape[1]
    xs = range(W // 2 - 120, W // 2 + 120)
    best = max(xs, key=lambda x: ink[y0:y1, x - 4:x + 5].any(axis=1).sum())
    col = ink[y0:y1, best - 6:best + 7].any(axis=1)
    ys = np.where(col)[0] + y0
    return best, ys.min(), ys.max()


def find_header_rule(ink):
    W = ink.shape[1]
    sub = ink[:1000]
    win = sub[:-2] | sub[1:-1] | sub[2:]
    rows = win.sum(axis=1)
    rows[:100] = 0
    y = int(np.argmax(rows)) + 1
    assert rows[y - 1] > 0.2 * W, rows[y - 1]
    return y


def blocks(profile, gap, minrows=3):
    """split boolean row profile into [y0,y1) runs separated by >= gap blank rows"""
    ys = np.where(profile)[0]
    if len(ys) == 0:
        return []
    out = []
    start = prev = ys[0]
    for y in ys[1:]:
        if y - prev > gap:
            out.append((int(start), int(prev) + 1))
            start = y
        prev = y
    out.append((int(start), int(prev) + 1))
    return [b for b in out if b[1] - b[0] >= minrows]


def analyse(page, gap=400):
    im, a = load(page)
    ink = a < 140
    H, W = ink.shape
    rule = find_header_rule(ink)
    div, dy0, dy1 = find_divider(ink, rule + 50, H - 300)
    # footer: page box around y ~ 3570; content bottom = min(dy1, 3480)
    bottom = H - 330
    top = rule + 20
    cols = {'L': (150, div - 25), 'R': (div + 25, W - 120)}
    res = {'page': page, 'rule': rule, 'div': div, 'div_y': (int(dy0), int(dy1)), 'top': top, 'bottom': int(bottom), 'cols': {}}
    dbg = im.convert('RGB')
    d = ImageDraw.Draw(dbg)
    d.line([(0, rule), (W, rule)], fill='red', width=3)
    d.line([(div, top), (div, bottom)], fill='blue', width=3)
    for name, (x0, x1) in cols.items():
        sub = ink[top:bottom, x0:x1]
        prof = sub.sum(axis=1) > 0
        bl = [b for b in blocks(prof, gap) if b[1] - b[0] >= 20 and sub[b[0]:b[1]].sum() > 400]
        items = []
        for (y0, y1) in bl:
            seg = sub[y0:y1]
            cols_ink = np.where(seg.any(axis=0))[0]
            bx0, bx1 = int(cols_ink.min()) + x0, int(cols_ink.max()) + x0 + 1
            by0, by1 = y0 + top, y1 + top
            # sub-blocks with small gap (to split section headers)
            subs = [(s0 + by0, s1 + by0) for (s0, s1) in blocks(seg.sum(axis=1) > 0, 50)]
            items.append({'box': [bx0, by0, bx1, by1], 'subs': subs})
            d.rectangle([bx0, by0, bx1, by1], outline='green', width=4)
            d.text((bx0, by0 - 40), f'{name}{len(items)} h={by1-by0}', fill='red')
        res['cols'][name] = {'x': [x0, x1], 'items': items}
    dbg.resize((W // 4, H // 4)).save(f'{OUT}/d-{page:02d}.png')
    return res


if __name__ == '__main__':
    pages = [int(p) for p in sys.argv[1:]] or list(range(2, 22))
    allres = {}
    for p in pages:
        r = analyse(p)
        allres[p] = r
        print(f"page {p}: rule={r['rule']} div={r['div']} divy={r['div_y']} bottom={r['bottom']}")
        for c in 'LR':
            for i, it in enumerate(r['cols'][c]['items']):
                print(f"   {c}{i+1} box={it['box']} h={it['box'][3]-it['box'][1]} subs={[(s1-s0) for s0,s1 in it['subs']][:6]} gaps={[it['subs'][k+1][0]-it['subs'][k][1] for k in range(min(5,len(it['subs'])-1))]}")
    json.dump(allres, open(f'{OUT}/blocks.json', 'w'))
