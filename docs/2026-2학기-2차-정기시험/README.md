# 2026학년도 2학기 2차 정기시험 시간표 절충안 (조대부고)

12/10(목)~12/15(화) 2차 정기시험의 2학년 16과목·1학년 6과목 배치를 §5 수강 데이터(176명·84조합)로
전수 탐색해 서로 다른 트레이드오프의 절충안 5개를 정리한 폴더다.

## 파일

| 파일 | 내용 |
| --- | --- |
| `절충안-5개.md` | 데이터 검산, 안 X·Y 재계산, 탐색 방법, 구조적 사실, 절충안 5개(배치표·분포·점검표·기회비용), 비교표·추천, 조건부 분석, 확인 질문 |

## 계산 도구

`tools/exam2/`에 있다. 재현:

```bash
cd tools/exam2
python3 verify_data.py                 # §5 데이터 검산
gcc -O2 -o enum enum.c                 # 일자 분할 전수 탐색기
./enum 0 7 parts_strict.txt            # 도움반 면제 없이 (1,440개)
./enum 1 7 parts_allow1.txt            # 1명 위반 허용 (16,398개, 도움반 조합 확인용)
python3 analyze.py                     # 교시 배정 + 지표 계산 → .pkl
python3 crosscheck.py                  # 독립 구현으로 열거 결과 교차 검증
python3 report.py                      # 절충안-5개.md 생성
```

`axes.py`(축별 최적), `query.py`·`pareto.py`(조회), `build.py`(시간표 생성), `evaluate.py`(점검표),
`variant_sci.py`(통합과학2 이동 변형)도 같은 폴더에 있다. 생성물(`parts_*`, `*.pkl`, `enum`, `combos.txt`)은 커밋하지 않는다.
