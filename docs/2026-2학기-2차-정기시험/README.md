# 2026학년도 2학기 2차 정기시험 2학년 시간표 최적화

16과목(동시 시행 가능 쌍 O+J·N+P)을 목·금·월·화 4일에 배정하는 문제의 전수 탐색 결과다.

| 파일 | 내용 |
| --- | --- |
| `문제-시간표최적화.md` | 문제지 원문(제약·학생 수강 조합 데이터·baseline) |
| `검토-시간표최적화.md` | baseline 재계산, 최적성 증명, 3·6교시 개방 시나리오, 제안안(절충안)과 대안 |

솔버는 `tools/timetable_solver.py`다. numpy만 있으면 된다.

```bash
python3 tools/timetable_solver.py            # 기본 시나리오 + 사례 분석 (약 5초)
python3 tools/timetable_solver.py --extra    # 3·6교시 개방 시나리오 (수 분)
python3 tools/timetable_solver.py --report   # 목 3교시 개방 제안안 상세
```
