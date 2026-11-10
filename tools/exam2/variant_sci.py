# 통합과학2를 금/월로 옮기는 경우(사용자 희망) — strict 분할에 대해 지표 재계산
import sys, pickle; sys.path.insert(0, '.')
from analyze import metrics, load_parts
from axes import run, AXES
for sci in ["금", "월"]:
    ms = [metrics(a, v, sci_day=sci) for a, v in load_parts("parts_strict.txt")]
    pickle.dump(ms, open(f"parts_strict_sci{sci}.pkl", "wb"))
    print(f"######## 통합과학2 → {sci} ########  교시배정 가능 {sum(m['feasible'] for m in ms)}/{len(ms)}")
    run(f"parts_strict_sci{sci}.pkl", n=2, sci_day=sci, axes=["①예외1건", "②3과목최대", "③계열중복", "④기본형통일", "⑤1교시없음"])
