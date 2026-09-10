# 2026학년도 2학기 1차 정기시험 가정통신문 (조대부고)

한컴오피스 없이 HWPX 원본에서 추출한 텍스트와 검토 결과를 모아 둔 폴더다.

## 파일

| 파일 | 내용 |
| --- | --- |
| `원문-1학년.md` / `원문-2학년.md` / `원문-3학년.md` | HWPX에서 표·서식을 보존해 추출한 본문 |
| `표-원자료.json` | 모든 표를 셀 단위 격자로 편 원자료 (기계 대조용) |
| `검토-결과.md` | 세 문서 검토 결과와 수정 문안 |
| `검토-결과.html` | 같은 내용을 교정지 형태로 정리한 페이지 |

## 추출 방법

```bash
pip install python-hwpx pillow lxml
python3 tools/hwpx_extract.py <파일.hwpx> --out out/ --md --tables --images
```

추출은 `tools/hwpx_extract.py`가 담당한다. 마크다운 본문, 셀 단위 표 JSON,
포함된 이미지, 조판 미리보기를 각각 뽑을 수 있다.

조판 미리보기(`--pages`)의 페이지 나눔은 근사치이므로 실제 인쇄 페이지 판정에는
쓰지 않는다. 페이지 1은 HWPX에 들어 있는 `Preview/PrvImage.png`가 정확하다.
