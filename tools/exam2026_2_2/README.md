# exam2026_2_2 — 2학기 2차 정기시험 시간표 전수 탐색기

| 파일 | 역할 |
| --- | --- |
| `data.py` | §5 학생 데이터(84개 조합), 과목·교사·계열, 1학년 과목, 면제 학생, 목요일 수업 충돌표. `python3 data.py` 로 검산 |
| `layer1.py` | 1단계: 과목→요일 배정을 CP-SAT `enumerate_all_solutions` 로 전수 열거. 요일 수준 제약(0과목·4과목 금지, A·P 화요일 금지, 교시 수 상한, 강한 선호 on/off) |
| `layer2.py` | 2단계: 하루치 과목을 교시에 배정. 교사 동시 배치, 목요일 1학년 수업 충돌, 전이슬 출장, 3학년 담임 예외 2교시 규칙, 연속 교시 비용 |
| `evaluate.py` | 요일 배정마다 최선의 교시 배정을 고르고 모든 지표(예외, 교사 하루 2과목, 계열 중복, 3과목 분포, 연속 교시, 시험실)를 계산 |
| `enumerate_all.py` | 1단계 공간을 열거해 `space_<이름>.pkl` 로 저장. 예: `python3 enumerate_all.py full 7,7,7,4 hard` |
| `analyze.py` | 저장된 공간 전체에 2단계를 적용해 `rows_<이름>.pkl` 생성 |
| `space.py` | 여러 교시 구조(4·4·4·2, 4·3·4·3, …)의 해 수와 지표 분포 요약 |
| `verify_claims.py` | 보고서 4절의 최적성 주장을 `rows_full.pkl` 로 검증하고 `claims.pkl` 저장 |
| `report.py` / `plans.py` | 다섯 안의 배치표·분포표·점검표를 마크다운으로 렌더링 |
| `build_doc.py` | `docs/2026-2학기-2차-정기시험-시간표/최적화-결과.md` 생성 |

의존성: `pip install ortools` (numpy 불필요). Python 3.13 에서 확인.

중간 산출물(`*.pkl`, `*.log`)은 커밋하지 않는다.
