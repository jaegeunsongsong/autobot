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

GitHub 러너 IP 는 유튜브가 데이터센터로 보고 항상 막는다("Sign in to confirm you're not a bot").
로그인 쿠키를 넣어야만 풀린다.

### 쿠키 시크릿 넣는 법 (한 번만)

1. 크롬(또는 엣지)에 **"Get cookies.txt LOCALLY"** 같은 cookies.txt 내보내기 확장을 설치한다.
   (Cookie-Editor 처럼 JSON 으로 내보내는 확장도 워크플로가 자동 변환하므로 써도 된다.)
2. 시크릿(사생활 보호) 창을 열어 youtube.com 에 로그인한다. 아무 영상이나 한 번 연다.
3. 확장으로 **youtube.com 도메인 쿠키를 내보낸다**. 첫 줄이 `# Netscape HTTP Cookie File` 인
   텍스트 파일(cookies.txt)이 나온다.
4. 그 시크릿 창은 **로그아웃하지 말고 그냥 닫는다** (로그아웃하면 쿠키가 무효가 된다).
5. GitHub 저장소 → **Settings → Secrets and variables → Actions → "Secrets" 탭 →
   New repository secret**. Name 은 정확히 `YOUTUBE_COOKIES`, Secret 에는 cookies.txt 파일
   내용 **전체**를 붙여 넣는다.
   - "Variables" 탭이 아니라 **"Secrets" 탭**이어야 한다. Variables 에 넣으면 워크플로가
     오류로 알려 준다.
   - Environment secrets 가 아니라 **Repository secrets** 여야 한다.
6. Actions 탭 → `youtube-analyze` → Run workflow. 로그의 "쿠키" 단계에
   `youtube.com 쿠키 줄 수: N | 로그인 쿠키 포함: True` 가 찍히면 정상이다.
   `쿠키 사용` 대신 `시크릿이 비어 있습니다` 가 찍히면 5번을 다시 확인한다.

쿠키는 개인 계정 정보다. 공용 저장소라면 유튜브용 별도 구글 계정을 만들어 쓰는 편이 안전하다.
쿠키가 먹히는지만 빨리 보려면 `youtube-probe` 워크플로(진단용, Actions 탭에서 수동 실행)를
돌려 로그의 자막 파일 목록으로 확인할 수 있다.

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
