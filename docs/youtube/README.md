# 유튜브 영상 → 글자(자막·음성·화면) 추출 파이프라인

유튜브 링크를 주면 영상의 세 가지 정보를 글자로 바꿔 분석 자료를 만든다.

| 경로 | 무엇을 읽나 | 도구 |
|---|---|---|
| 자막 | 유튜브에 올라온 자막(제작자 자막 → 자동 생성 자막 순) | yt-dlp / InnerTube |
| 음성 | 오디오를 받아 직접 받아쓰기 | faster-whisper (CPU, int8) |
| 화면 | 몇 초마다 프레임을 뽑아 화면 글자 읽기 | ffmpeg + tesseract (kor+eng) |

결과는 영상별로 `data.json`(원자료)과 `<영상ID>.md`(챕터별 통합 타임라인)로 저장되고,
전체 목록은 `index.md`에 정리된다.

## 실행 방법 1 — 내 컴퓨터에서

```bash
# 1회 설치
pip install -r tools/requirements-youtube.txt
sudo apt-get install ffmpeg tesseract-ocr tesseract-ocr-kor tesseract-ocr-eng   # macOS: brew install ffmpeg tesseract tesseract-lang

# 실행 (링크는 여러 개 가능, si= 같은 추적 파라미터·중복은 자동 정리)
python3 tools/youtube_analyze.py "https://youtu.be/XeRij5IJJ-I" "https://youtube.com/shorts/4IQZNDEjrJg"
python3 tools/youtube_analyze.py --links-file youtube-links.txt --out out/youtube
```

주요 옵션은 `python3 tools/youtube_analyze.py -h` 로 볼 수 있다.
`--asr-model medium` 으로 바꾸면 한국어 받아쓰기 정확도가 오르고 시간은 2~3배 든다.
집·학교 IP에서 "Sign in to confirm you're not a bot" 이 뜨면 브라우저에서 내보낸
쿠키 파일을 `--cookies cookies.txt` 로 넘긴다.

## 실행 방법 2 — GitHub Actions 에서 (링크만 올리면 됨)

`youtube-links.txt` 에 링크를 적어 push 하면 `.github/workflows/youtube-analyze.yml` 이
러너에서 위 파이프라인을 돌리고 결과를 `docs/youtube/원자료/` 에 커밋한다.
Actions 탭에서 `youtube-analyze` 를 수동 실행(Run workflow)해 링크·모델을 직접 넣을 수도 있다.

GitHub 러너 IP 는 유튜브가 데이터센터로 보고 자주 막는다. 막히면 저장소 Settings →
Secrets → `YOUTUBE_COOKIES` 에 브라우저에서 내보낸 cookies.txt 내용을 넣어 두면
워크플로가 자동으로 그 쿠키를 쓴다. 쿠키가 먹히는지는 `youtube-probe` 워크플로(진단용,
Actions 탭에서 수동 실행)를 돌려 로그의 자막 파일 목록으로 확인할 수 있다.

## 결과물 위치

- `docs/youtube/원자료/index.md` — 영상별 추출 상태 표
- `docs/youtube/원자료/<영상ID>/<영상ID>.md` — 메타데이터·설명란·챕터·통합 타임라인·댓글
- `docs/youtube/원자료/<영상ID>/data.json` — 같은 내용의 원자료(JSON)
- `docs/youtube/사업자등록-영상-9편-분석.md` — 2026-09-22 요청분 9편의 분석 문서

## 이 저장소를 만든 세션(Claude Code 클라우드)의 제약

세션 컨테이너의 네트워크 정책이 `youtube.com`, `googlevideo.com`, `huggingface.co` 를
막고 있어 그 안에서는 메타데이터(제목·채널·설명·챕터)만 `youtubei.googleapis.com` 경유로
받아지고, 자막·오디오·비디오는 받을 수 없다. 그래서 실제 추출은 GitHub Actions 러너에서
돌리는 구조로 만들었다.
