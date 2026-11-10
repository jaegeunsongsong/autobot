"""탐색 공간 크기와 §6 검증용 1단계 열거."""
import time
from layer1 import *

def run(name, cap, **kw):
    t = time.time()
    sols = enumerate_day_assignments(cap, **kw)
    ms = [metrics(a) for a in sols]
    excs = Counter(m["exc"] for m in ms)
    tue3 = Counter(m["tue3"] for m in ms)
    max3 = Counter(m["max3"] for m in ms)
    dupn = Counter(m["dup_n"] for m in ms)
    print(f"[{name}] cap={cap} {kw}: {len(sols)}개 ({time.time()-t:.1f}s)")
    print(f"   예외={dict(excs)}  화3+={dict(tue3)}  하루3최대={dict(sorted(max3.items()))}  계열중복인원={dict(sorted(dupn.items()))}")
    return sols

if __name__ == "__main__":
    run("4·4·4·2 표준", {"목": 4, "금": 4, "월": 4, "화": 2})
    run("4·3·4·3", {"목": 4, "금": 3, "월": 4, "화": 3})
    run("4·5·4·1", {"목": 4, "금": 5, "월": 4, "화": 1})
    run("화 1과목, 나머지 자유", {"목": 7, "금": 7, "월": 7, "화": 1})
    run("4·5·4·2 (쌍 하나만)", {"목": 4, "금": 5, "월": 4, "화": 2})
    run("5·4·4·2", {"목": 5, "금": 4, "월": 4, "화": 2})
    run("4·4·5·2", {"목": 4, "금": 4, "월": 5, "화": 2})
    run("화2, 나머지 ≤5", {"목": 5, "금": 5, "월": 5, "화": 2})
    run("화2, 나머지 ≤7", {"목": 7, "금": 7, "월": 7, "화": 2})
    run("화3, 나머지 ≤7", {"목": 7, "금": 7, "월": 7, "화": 3})
    run("화4, 나머지 ≤7 (전체)", {"목": 7, "금": 7, "월": 7, "화": 4})
    run("화4, 나머지 ≤7, 선호 무시(절대제약만)", {"목": 7, "금": 7, "월": 7, "화": 4}, hard_prefs=False)
