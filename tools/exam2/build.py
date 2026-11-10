# -*- coding: utf-8 -*-
"""분할 문자열 + 교시 선택 키 → 완전한 시간표(1학년 포함) 생성."""
import sys; sys.path.insert(0, '.')
from data import *
from periods import day_configs
from axes import CFG_KEYS
from evaluate import evaluate, fmt_report

G1_KSE = {"공통국어2": "금", "공통수학2": "월", "공통영어2": "화"}  # 기본 선택(교환 가능, 국어≠화)

def build(part, ck="default", override=None, sci_day="화", g1_kse=G1_KSE):
    """part: 'EHJKMO|AFIP|BGLN|CD' 형식. override: {요일: 교시튜플} 로 특정 교시 집합 강제."""
    sets = [frozenset(s) for s in part.split("|")]
    g2, g1 = {}, {}
    for i, d in enumerate(DAYS):
        cs = day_configs(d, sets[i], sci_day)
        if override and d in override:
            cs = [c for c in cs if c["periods"] == tuple(override[d])]
            assert cs, f"{d} {override[d]} 불가"
        c = min(cs, key=CFG_KEYS[ck])
        for s, p in c["assign"].items(): g2[s] = (d, p)
        for s, p in c["g1"].items(): g1[s] = (d, p)
    # 1학년 국·수·영: 고정 과목이 쓰지 않은 교시에
    for s, d in g1_kse.items():
        used = {p for t, (dd, p) in g1.items() if dd == d}
        slots = [2, 4] if d == "화" else [2, 7]
        free = [p for p in slots if p not in used]
        g1[s] = (d, free[0])
    return {"g2": g2, "g1": g1}

if __name__ == "__main__":
    PLANS = [
        ("안 1 — 학생 하루 3과목 최소(36명)·예외 1건", "EHJKMO|AFIP|BGLN|CD", "default", None),
        ("안 2 — 같은 날 같은 계열 최소(47명)", "EGMNOP|AFIJ|BHKL|CD", "default", None),
        ("안 3 — 전 요일 2·4·5·7 통일(4·4·4·2)", "AEGI|BHLNP|DFKM|CJO", "base", None),
        ("안 4 — 목요일 기본형 유지·1교시 없음·예외 1건", "AFIP|EHJKMO|BGLN|CD", "no_p1", None),
        ("안 5 — 균형안(예외 2건: 배태안만)", "EGMNOP|AHIK|BFJL|CD", "default", None),
    ]
    for title, part, ck, ov in PLANS:
        plan = build(part, ck, ov)
        R = evaluate(plan)
        print(fmt_report(plan, R, title)); print()
