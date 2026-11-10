import sys, pickle; sys.path.insert(0, '.')
from query import row, load
fn = sys.argv[1]; flt = sys.argv[2] if len(sys.argv) > 2 else "True"
ms = [m for m in load(fn) if m["feasible"] and eval(flt)]
def vec(m): return (m['exc'], m['max3'], m['sum3'], m['series_students'], len(m['teacher_day']), m['abc_same'], m['p1'], m['consec_students'], m['ndev'], m['open36'], len(m['cfg'][0]['periods']))
vs = [(vec(m), m) for m in ms]
front = []
for v, m in vs:
    dom = any(all(w[i] <= v[i] for i in range(len(v))) and w != v for w, _ in vs)
    if not dom: front.append((v, m))
seen = set(); 
front.sort(key=lambda t: t[0])
print(len(front), "비지배 분할")
for v, m in front:
    if v in seen: continue
    seen.add(v); print(row(m))
