#!/usr/bin/env python3
"""유튜브 영상 분석 자료 추출 도구.

유튜브 링크를 주면 세 가지 경로로 영상 내용을 글자로 바꾼다.

  1. 자막   : 유튜브가 가진 자막(제작자 자막 → 자동 생성 자막 순)을 받아온다.
  2. 음성   : 오디오를 내려받아 Whisper(faster-whisper)로 직접 받아쓴다.
  3. 화면   : 일정 간격으로 프레임을 뽑아 OCR(tesseract kor+eng)로 화면 글자를 읽는다.

결과는 영상별 폴더에 JSON(원자료)과 마크다운(통합 타임라인)으로 저장하고,
전체 목록은 index.md 로 정리한다. 분석(요약·해석)은 이 자료를 읽고 사람이나
LLM이 하는 다음 단계다.

의존성:
    pip install -r tools/requirements-youtube.txt
    apt-get install ffmpeg tesseract-ocr tesseract-ocr-kor tesseract-ocr-eng

사용법:
    python3 tools/youtube_analyze.py URL [URL ...] [--out out/youtube]
    python3 tools/youtube_analyze.py --links-file youtube-links.txt
        --langs ko,en        자막 언어 우선순위 (기본 ko,en)
        --asr-model small    Whisper 모델 (tiny/base/small/medium/large-v3, 기본 small)
        --asr-lang ko        음성 언어 (비우면 자동 감지)
        --no-asr / --no-ocr / --no-subs   단계 생략
        --frame-interval 4   OCR 프레임 간격(초)
        --ocr-psm 11         tesseract 페이지 분할 모드
        --cookies FILE       로그인 쿠키(봇 차단 우회가 필요할 때)
        --keep-media         받은 오디오·비디오·프레임을 지우지 않음

네트워크가 유튜브 본체(youtube.com, googlevideo.com)를 막는 환경에서는
자막·음성·화면 단계가 실패하고, 메타데이터만 youtubei.googleapis.com 경유로
받아온다. 그런 환경에서는 .github/workflows/youtube-analyze.yml 처럼
외부 러너에서 돌리는 방법을 쓴다.
"""
from __future__ import annotations

import argparse
import base64
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# --------------------------------------------------------------------------
# 공통
# --------------------------------------------------------------------------

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def log(msg: str) -> None:
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


def video_id_from_url(url: str) -> str | None:
    """watch?v=, youtu.be/, shorts/, embed/, live/ 형태를 모두 받는다."""
    url = url.strip()
    if VIDEO_ID_RE.match(url):
        return url
    try:
        p = urllib.parse.urlparse(url if "://" in url else "https://" + url)
    except ValueError:
        return None
    host = (p.hostname or "").lower()
    if host in ("youtu.be", "www.youtu.be"):
        cand = p.path.strip("/").split("/")[0]
        return cand if VIDEO_ID_RE.match(cand) else None
    if "youtube" in host:
        qs = urllib.parse.parse_qs(p.query)
        if "v" in qs and VIDEO_ID_RE.match(qs["v"][0]):
            return qs["v"][0]
        m = re.match(r"^/(?:shorts|embed|live|v)/([A-Za-z0-9_-]{11})", p.path)
        if m:
            return m.group(1)
    return None


def fmt_ts(sec: float) -> str:
    sec = max(0, int(round(sec)))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_ts(text: str) -> float | None:
    m = re.match(r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})\s*$", text or "")
    if not m:
        return None
    h = int(m.group(1) or 0)
    return h * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# --------------------------------------------------------------------------
# 1) 메타데이터 · 자막 (yt-dlp)
# --------------------------------------------------------------------------

PLAYER_CLIENT_ATTEMPTS = [
    None,                       # yt-dlp 기본값
    ["tv", "web_safari"],
    ["mweb"],
    ["android_vr"],
]


def _ydl(opts_extra: dict, cookies: str | None, clients: list[str] | None):
    import yt_dlp  # 지연 임포트: 설치 안 된 환경에서도 도구 자체는 뜨게

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "skip_download": True,
        "ignoreerrors": False,
        "retries": 3,
        "socket_timeout": 30,
    }
    if cookies:
        opts["cookiefile"] = cookies
    if clients:
        opts["extractor_args"] = {"youtube": {"player_client": clients}}
    opts.update(opts_extra)
    return yt_dlp.YoutubeDL(opts)


def ytdlp_info(url: str, cookies: str | None) -> tuple[dict | None, str]:
    """영상 정보 dict 를 돌려준다. 클라이언트를 바꿔가며 몇 번 시도한다."""
    last_err = ""
    for clients in PLAYER_CLIENT_ATTEMPTS:
        try:
            with _ydl({}, cookies, clients) as ydl:
                info = ydl.extract_info(url, download=False)
            if info:
                info["_player_clients"] = clients
                return info, ""
        except Exception as e:  # noqa: BLE001
            last_err = f"{type(e).__name__}: {e}"
            log(f"  yt-dlp 정보 조회 실패 (client={clients}): {last_err[:200]}")
    return None, last_err


def meta_from_info(info: dict) -> dict:
    chapters = [
        {"start": c.get("start_time", 0), "end": c.get("end_time"), "title": c.get("title", "")}
        for c in (info.get("chapters") or [])
    ]
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "channel_url": info.get("channel_url") or info.get("uploader_url"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "description": info.get("description") or "",
        "tags": info.get("tags") or [],
        "categories": info.get("categories") or [],
        "chapters": chapters,
        "source": "yt-dlp",
    }


def _pick_track(tracks: dict, langs: list[str], auto: bool) -> tuple[str, dict] | None:
    """langs 우선순위대로 트랙을 고른다. 자동 자막은 원본(-orig)을 먼저."""
    if not tracks:
        return None
    order: list[str] = []
    for lang in langs:
        if auto:
            order.append(f"{lang}-orig")
        order.append(lang)
    for key in order:
        if key in tracks:
            return key, _pick_format(tracks[key])
    # 접두어 일치 (ko-KR 등)
    for lang in langs:
        for key in tracks:
            if key.split("-")[0] == lang:
                return key, _pick_format(tracks[key])
    return None


def _pick_format(fmts: list[dict]) -> dict:
    for want in ("json3", "srv3", "vtt", "ttml", "srv1"):
        for f in fmts:
            if f.get("ext") == want:
                return f
    return fmts[0]


def parse_json3(data: bytes) -> list[dict]:
    d = json.loads(data.decode("utf-8", "replace"))
    segs = []
    for ev in d.get("events", []):
        text = "".join(s.get("utf8", "") for s in ev.get("segs", []) or [])
        text = text.replace("\n", " ").strip()
        if not text or ev.get("aAppend"):
            continue
        start = ev.get("tStartMs", 0) / 1000
        dur = ev.get("dDurationMs", 0) / 1000
        segs.append({"start": start, "end": start + dur, "text": text})
    return segs


def parse_vtt(data: bytes) -> list[dict]:
    text = data.decode("utf-8", "replace")
    segs = []
    block: list[str] = []
    for line in text.splitlines() + [""]:
        if line.strip():
            block.append(line)
            continue
        if not block:
            continue
        tl = next((b for b in block if "-->" in b), None)
        if tl:
            a, b = [x.strip().split(" ")[0] for x in tl.split("-->")[:2]]
            body = " ".join(x for x in block[block.index(tl) + 1 :])
            body = re.sub(r"<[^>]+>", "", body).strip()
            if body:
                segs.append({"start": _vtt_ts(a), "end": _vtt_ts(b), "text": body})
        block = []
    # 자동 자막 VTT는 같은 문장이 겹쳐 반복되므로 연속 중복 제거
    out: list[dict] = []
    for s in segs:
        if out and s["text"] == out[-1]["text"]:
            out[-1]["end"] = s["end"]
        else:
            out.append(s)
    return out


def _vtt_ts(t: str) -> float:
    parts = t.replace(",", ".").split(":")
    parts = [float(p) for p in parts]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def fetch_subtitles(info: dict, langs: list[str], cookies: str | None) -> dict:
    """{'kind': 'manual'|'auto', 'lang': .., 'segments': [...]} 또는 {'error': ..}."""
    picks = []
    p = _pick_track(info.get("subtitles") or {}, langs, auto=False)
    if p:
        picks.append(("manual", *p))
    p = _pick_track(info.get("automatic_captions") or {}, langs, auto=True)
    if p:
        picks.append(("auto", *p))
    if not picks:
        return {"error": "자막 트랙 없음", "available": {
            "manual": sorted((info.get("subtitles") or {}).keys()),
            "auto": sorted((info.get("automatic_captions") or {}).keys())[:30],
        }}
    result = {"tracks": [], "available": {
        "manual": sorted((info.get("subtitles") or {}).keys()),
        "auto": sorted((info.get("automatic_captions") or {}).keys())[:30],
    }}
    with _ydl({}, cookies, info.get("_player_clients")) as ydl:
        for kind, lang, fmt in picks:
            try:
                data = ydl.urlopen(fmt["url"]).read()
                segs = parse_json3(data) if fmt.get("ext") in ("json3",) else parse_vtt(data) if fmt.get("ext") == "vtt" else _parse_srv3(data)
                result["tracks"].append({"kind": kind, "lang": lang, "ext": fmt.get("ext"), "segments": segs})
                log(f"  자막 {kind}/{lang}: {len(segs)}개 구간")
            except Exception as e:  # noqa: BLE001
                log(f"  자막 {kind}/{lang} 받기 실패: {e}")
                result["tracks"].append({"kind": kind, "lang": lang, "error": str(e)})
    return result


def _parse_srv3(data: bytes) -> list[dict]:
    """srv3/srv1 XML(<p t= d=>, <text start= dur=>) 을 대충 파싱."""
    import html
    from xml.etree import ElementTree as ET

    root = ET.fromstring(data.decode("utf-8", "replace"))
    segs = []
    for el in root.iter():
        if el.tag == "p" and el.get("t") is not None:
            start = int(el.get("t", 0)) / 1000
            dur = int(el.get("d", 0)) / 1000
            text = "".join(el.itertext()).strip()
        elif el.tag == "text" and el.get("start") is not None:
            start = float(el.get("start", 0))
            dur = float(el.get("dur", 0))
            text = html.unescape("".join(el.itertext())).strip()
        else:
            continue
        if text:
            segs.append({"start": start, "end": start + dur, "text": text.replace("\n", " ")})
    return segs


# --------------------------------------------------------------------------
# 1b) 메타데이터 예비 경로: InnerTube `next` (youtubei.googleapis.com)
#     yt-dlp 가 막힌 환경(예: youtube.com 차단)에서도 제목·설명·챕터는 받아진다.
# --------------------------------------------------------------------------

INNERTUBE_HOST = "https://youtubei.googleapis.com/youtubei/v1/"
WEB_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")


def innertube(endpoint: str, body: dict, retries: int = 3) -> dict | None:
    payload = {"context": {"client": {"clientName": "WEB", "clientVersion": "2.20250912.01.00",
                                      "hl": "ko", "gl": "KR"}}, **body}
    headers = {"Content-Type": "application/json", "User-Agent": WEB_UA,
               "X-YouTube-Client-Name": "1", "X-YouTube-Client-Version": "2.20250912.01.00",
               "Origin": "https://www.youtube.com"}
    for attempt in range(retries):
        req = urllib.request.Request(INNERTUBE_HOST + endpoint + "?prettyPrint=false",
                                     data=json.dumps(payload).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            log(f"  innertube/{endpoint} HTTP {e.code} (시도 {attempt + 1})")
        except Exception as e:  # noqa: BLE001
            log(f"  innertube/{endpoint} 실패: {e} (시도 {attempt + 1})")
        time.sleep(4 * (attempt + 1))
    return None


def _walk(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for v in obj.values():
            yield from _walk(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, key)


def _runs(x) -> str:
    if not x:
        return ""
    if isinstance(x, str):
        return x
    if "simpleText" in x:
        return x["simpleText"]
    if isinstance(x.get("content"), str):
        return x["content"]
    return "".join(r.get("text", "") for r in x.get("runs", []))


def meta_from_innertube(vid: str) -> dict | None:
    d = innertube("next", {"videoId": vid})
    if not d:
        return None
    vp = next(_walk(d, "videoPrimaryInfoRenderer"), {})
    vs = next(_walk(d, "videoSecondaryInfoRenderer"), {})
    owner = next(_walk(vs, "videoOwnerRenderer"), {})
    views = _runs(next(_walk(vp, "videoViewCountRenderer"), {}).get("viewCount"))
    desc_obj = next(_walk(vs, "attributedDescription"), None)
    desc = _runs(desc_obj) if desc_obj else _runs(vs.get("description"))
    likes = ""
    for s in _walk(d, "segmentedLikeDislikeButtonViewModel"):
        likes = next(_walk(s, "accessibilityText"), "") or ""
        break
    chapters = []
    seen = set()
    for mm in _walk(d, "macroMarkersListItemRenderer"):
        t = parse_ts(_runs(mm.get("timeDescription")))
        title = _runs(mm.get("title"))
        if t is not None and (t, title) not in seen:
            seen.add((t, title))
            chapters.append({"start": t, "end": None, "title": title})
    chapters.sort(key=lambda c: c["start"])
    for i, c in enumerate(chapters[:-1]):
        c["end"] = chapters[i + 1]["start"]
    if not chapters:
        chapters = chapters_from_description(desc)
    return {
        "id": vid,
        "title": _runs(vp.get("title")),
        "channel": _runs(owner.get("title")),
        "channel_url": None,
        "subscriber_text": _runs(owner.get("subscriberCountText")),
        "upload_date_text": _runs(vp.get("dateText")),
        "view_text": views,
        "like_text": likes,
        "description": desc,
        "chapters": chapters,
        "source": "innertube-next",
    }


def chapters_from_description(desc: str) -> list[dict]:
    """설명란의 '00:57 사업자등록증 발급' 같은 줄에서 챕터를 뽑는다."""
    chapters = []
    for line in desc.splitlines():
        m = re.match(r"^\s*((?:\d+:)?\d{1,2}:\d{2})\s*[-–|]?\s*(.+?)\s*$", line)
        if m:
            t = parse_ts(m.group(1))
            if t is not None:
                chapters.append({"start": t, "end": None, "title": m.group(2)})
    chapters.sort(key=lambda c: c["start"])
    for i, c in enumerate(chapters[:-1]):
        c["end"] = chapters[i + 1]["start"]
    return chapters


# --------------------------------------------------------------------------
# 2) 음성 → 글자 (faster-whisper)
# --------------------------------------------------------------------------

def download_media(url: str, out_dir: Path, vid: str, kind: str, cookies: str | None,
                   clients: list[str] | None) -> Path | None:
    if kind == "audio":
        fmt = "bestaudio[ext=m4a]/bestaudio/best"
        tmpl = str(out_dir / f"{vid}.audio.%(ext)s")
    else:
        fmt = "bestvideo[height<=720][ext=mp4]/bestvideo[height<=720]/best[height<=720]/best"
        tmpl = str(out_dir / f"{vid}.video.%(ext)s")
    for attempt_clients in ([clients] if clients else []) + [c for c in PLAYER_CLIENT_ATTEMPTS if c != clients]:
        try:
            with _ydl({"skip_download": False, "format": fmt, "outtmpl": tmpl}, cookies, attempt_clients) as ydl:
                ydl.download([url])
            for p in out_dir.glob(f"{vid}.{kind}.*"):
                if p.suffix not in (".part", ".ytdl"):
                    return p
        except Exception as e:  # noqa: BLE001
            log(f"  {kind} 내려받기 실패 (client={attempt_clients}): {str(e)[:200]}")
    return None


def to_wav16k(src: Path, dst: Path) -> bool:
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
             "-c:a", "pcm_s16le", str(dst)])
    if r.returncode != 0:
        log(f"  ffmpeg 변환 실패: {r.stderr[:300]}")
        return False
    return True


def transcribe(wav: Path, model_name: str, lang: str | None) -> dict:
    from faster_whisper import WhisperModel

    log(f"  Whisper({model_name}) 모델 로드")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(wav), language=lang, vad_filter=True, beam_size=5,
                                      condition_on_previous_text=False)
    out = []
    last_log = time.time()
    for s in segments:
        out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
        if time.time() - last_log > 30:
            log(f"    ... {fmt_ts(s.end)} 까지 받아씀")
            last_log = time.time()
    return {"model": model_name, "language": info.language, "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 1), "segments": out}


# --------------------------------------------------------------------------
# 3) 화면 → 글자 (ffmpeg 프레임 + tesseract OCR)
# --------------------------------------------------------------------------

def extract_frames(video: Path, frames_dir: Path, interval: float) -> list[tuple[float, Path]]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
             "-vf", f"fps=1/{interval},scale='min(1280,iw)':-2", str(frames_dir / "f_%05d.png")])
    if r.returncode != 0:
        log(f"  프레임 추출 실패: {r.stderr[:300]}")
        return []
    frames = sorted(frames_dir.glob("f_*.png"))
    # fps=1/N 은 대략 N/2, N/2+N, ... 시점의 프레임을 고른다
    return [((i * interval) + interval / 2, p) for i, p in enumerate(frames)]


def ocr_frame(path: Path, psm: int, langs: str = "kor+eng") -> list[str]:
    r = run(["tesseract", str(path), "stdout", "-l", langs, "--psm", str(psm)])
    if r.returncode != 0:
        return []
    lines = []
    for line in r.stdout.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        # 글자(한글/영문/숫자)가 2자 이상인 줄만
        if len(re.findall(r"[가-힣A-Za-z0-9]", line)) >= 2:
            lines.append(line)
    return lines


def _norm(s: str) -> str:
    return re.sub(r"[\s\W_]+", "", s).lower()


def ocr_video(video: Path, work: Path, interval: float, psm: int, keep: bool) -> dict:
    frames = extract_frames(video, work / "frames", interval)
    log(f"  프레임 {len(frames)}장 OCR 시작")
    with ThreadPoolExecutor(max_workers=max(1, (os.cpu_count() or 2))) as ex:
        results = list(ex.map(lambda fp: ocr_frame(fp[1], psm), frames))
    entries = []
    prev_norm = ""
    for (t, path), lines in zip(frames, results):
        text = " / ".join(lines)
        n = _norm(text)
        if not n:
            continue
        if prev_norm and difflib.SequenceMatcher(None, prev_norm, n).ratio() > 0.8:
            entries[-1]["end"] = t + interval / 2
            continue
        entries.append({"start": t - interval / 2, "end": t + interval / 2, "lines": lines, "frame": path.name})
        prev_norm = n
    if not keep:
        shutil.rmtree(work / "frames", ignore_errors=True)
    return {"interval": interval, "psm": psm, "frames": len(frames), "entries": entries}


# --------------------------------------------------------------------------
# 4) 보고서
# --------------------------------------------------------------------------

def chapter_of(chapters: list[dict], t: float) -> str:
    cur = ""
    for c in chapters:
        if t >= c["start"]:
            cur = c["title"]
        else:
            break
    return cur


def write_report(v: dict, out_dir: Path) -> Path:
    meta = v["meta"] or {}
    lines: list[str] = []
    title = meta.get("title") or v["id"]
    lines.append(f"# {title}\n")
    lines.append(f"- URL: https://www.youtube.com/watch?v={v['id']}")
    for label, key in (("채널", "channel"), ("구독자", "subscriber_text"), ("게시일", "upload_date"),
                       ("게시일", "upload_date_text"), ("길이", "duration"), ("조회수", "view_count"),
                       ("조회수", "view_text"), ("좋아요", "like_count"), ("좋아요", "like_text")):
        val = meta.get(key)
        if val not in (None, ""):
            if key == "duration":
                val = fmt_ts(val)
            lines.append(f"- {label}: {val}")
    lines.append(f"- 메타데이터 출처: {meta.get('source', '없음')}")
    st = v["status"]
    lines.append(f"- 자막: {st.get('subs')} / 음성인식: {st.get('asr')} / 화면OCR: {st.get('ocr')}\n")

    if meta.get("description"):
        lines.append("## 설명란\n")
        lines.append("```text")
        lines.append(meta["description"].strip())
        lines.append("```\n")

    chapters = meta.get("chapters") or []
    if chapters:
        lines.append("## 챕터\n")
        for c in chapters:
            lines.append(f"- {fmt_ts(c['start'])} {c['title']}")
        lines.append("")

    # 말(음성) 타임라인: 유튜브 자막(제작자 > 자동) 우선, 없으면 Whisper
    speech: list[dict] = []
    speech_src = ""
    subs = v.get("subs") or {}
    for want in ("manual", "auto"):
        for tr in subs.get("tracks", []):
            if tr.get("kind") == want and tr.get("segments"):
                speech = tr["segments"]
                speech_src = f"유튜브 {'제작자' if want == 'manual' else '자동 생성'} 자막 ({tr['lang']})"
                break
        if speech:
            break
    asr = v.get("asr") or {}
    if not speech and asr.get("segments"):
        speech = asr["segments"]
        speech_src = f"Whisper {asr.get('model')} 음성인식 (감지 언어 {asr.get('language')})"

    ocr = v.get("ocr") or {}
    events = []
    for s in speech:
        events.append((s["start"], "말", s["text"]))
    for e in ocr.get("entries", []):
        events.append((e["start"], "화면", " / ".join(e["lines"])))
    events.sort(key=lambda x: x[0])

    lines.append("## 통합 타임라인\n")
    if speech_src:
        lines.append(f"말 출처: {speech_src}. 화면 글자는 tesseract OCR 결과라 오탈자가 있을 수 있다.\n")
    if not events:
        lines.append("_확보된 자막·음성·화면 텍스트가 없다._\n")
    cur_ch = None
    for t, kind, text in events:
        ch = chapter_of(chapters, t) if chapters else None
        if chapters and ch != cur_ch:
            cur_ch = ch
            lines.append(f"\n### [{fmt_ts(t)}] {ch}\n")
        mark = "🗣" if kind == "말" else "🖥"
        lines.append(f"- `{fmt_ts(t)}` {mark} {text}")
    lines.append("")

    if asr.get("segments") and speech is not asr["segments"]:
        lines.append("## Whisper 음성인식 전문 (자막과 대조용)\n")
        lines.append(f"모델 {asr.get('model')}, 감지 언어 {asr.get('language')} (확신도 {asr.get('language_probability')})\n")
        for s in asr["segments"]:
            lines.append(f"- `{fmt_ts(s['start'])}` {s['text']}")
        lines.append("")

    if subs.get("available"):
        lines.append("## 자막 트랙 목록\n")
        lines.append(f"- 제작자 자막: {', '.join(subs['available'].get('manual') or []) or '없음'}")
        lines.append(f"- 자동 자막: {', '.join(subs['available'].get('auto') or []) or '없음'}\n")

    errors = v.get("errors") or []
    if errors:
        lines.append("## 처리 중 문제\n")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    path = out_dir / f"{v['id']}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_index(videos: list[dict], out_root: Path) -> Path:
    lines = ["# 유튜브 영상 추출 결과 목록\n",
             "| # | 영상 | 채널 | 길이 | 자막 | 음성인식 | 화면OCR | 보고서 |",
             "|---|---|---|---|---|---|---|---|"]
    for i, v in enumerate(videos, 1):
        m = v["meta"] or {}
        dur = fmt_ts(m["duration"]) if m.get("duration") else "-"
        st = v["status"]
        lines.append(f"| {i} | [{m.get('title') or v['id']}](https://www.youtube.com/watch?v={v['id']}) | "
                     f"{m.get('channel') or '-'} | {dur} | {st.get('subs')} | {st.get('asr')} | {st.get('ocr')} | "
                     f"[{v['id']}.md]({v['id']}/{v['id']}.md) |")
    path = out_root / "index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# 파이프라인
# --------------------------------------------------------------------------

def process(url: str, vid: str, args) -> dict:
    out_dir = Path(args.out) / vid
    out_dir.mkdir(parents=True, exist_ok=True)
    v: dict = {"id": vid, "url": url, "meta": None, "subs": None, "asr": None, "ocr": None,
               "status": {"subs": "생략", "asr": "생략", "ocr": "생략"}, "errors": []}
    log(f"=== {vid} ({url})")

    info, err = (None, "yt-dlp 미사용")
    if not args.no_ytdlp:
        info, err = ytdlp_info(url, args.cookies)
    if info:
        v["meta"] = meta_from_info(info)
        log(f"  제목: {v['meta']['title']} / {v['meta']['channel']} / {fmt_ts(v['meta']['duration'] or 0)}")
    else:
        v["errors"].append(f"yt-dlp 정보 조회 실패: {err[:300]}")
        log("  InnerTube next 로 메타데이터 대체 시도")
        v["meta"] = meta_from_innertube(vid)
        if v["meta"]:
            log(f"  제목: {v['meta']['title']} / {v['meta']['channel']}")
        else:
            v["errors"].append("InnerTube 메타데이터도 실패")

    # 자막
    if not args.no_subs:
        if info:
            v["subs"] = fetch_subtitles(info, args.langs, args.cookies)
            ok = [t for t in v["subs"].get("tracks", []) if t.get("segments")]
            v["status"]["subs"] = (", ".join(f"{t['kind']}/{t['lang']} {len(t['segments'])}구간" for t in ok)
                                   if ok else f"실패 ({v['subs'].get('error', '트랙 받기 실패')})")
        else:
            v["status"]["subs"] = "실패 (영상 정보 없음)"

    clients = info.get("_player_clients") if info else None
    media_dir = out_dir / "media"
    media_dir.mkdir(exist_ok=True)

    # 음성
    if not args.no_asr:
        audio = download_media(url, media_dir, vid, "audio", args.cookies, clients) if info or not args.no_ytdlp else None
        if audio:
            wav = media_dir / f"{vid}.16k.wav"
            if to_wav16k(audio, wav):
                try:
                    v["asr"] = transcribe(wav, args.asr_model, args.asr_lang or None)
                    v["status"]["asr"] = f"{args.asr_model} {len(v['asr']['segments'])}구간 ({v['asr']['language']})"
                except Exception as e:  # noqa: BLE001
                    v["errors"].append(f"Whisper 실패: {e}")
                    v["status"]["asr"] = "실패 (Whisper)"
            else:
                v["status"]["asr"] = "실패 (ffmpeg 변환)"
        else:
            v["status"]["asr"] = "실패 (오디오 내려받기)"
            v["errors"].append("오디오를 내려받지 못함 (네트워크 차단 또는 봇 차단)")

    # 화면
    if not args.no_ocr:
        if shutil.which("tesseract") is None:
            v["status"]["ocr"] = "실패 (tesseract 없음)"
        else:
            video = download_media(url, media_dir, vid, "video", args.cookies, clients) if info or not args.no_ytdlp else None
            if video:
                v["ocr"] = ocr_video(video, out_dir, args.frame_interval, args.ocr_psm, args.keep_media)
                v["status"]["ocr"] = f"{v['ocr']['frames']}프레임 → {len(v['ocr']['entries'])}개 화면"
            else:
                v["status"]["ocr"] = "실패 (비디오 내려받기)"
                v["errors"].append("비디오를 내려받지 못함 (네트워크 차단 또는 봇 차단)")

    if not args.keep_media:
        shutil.rmtree(media_dir, ignore_errors=True)

    (out_dir / "data.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    report = write_report(v, out_dir)
    log(f"  보고서: {report}")
    return v


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*", help="유튜브 URL 또는 11자리 영상 ID")
    ap.add_argument("--links-file", help="URL 목록 파일 (한 줄에 하나, # 주석 가능)")
    ap.add_argument("--out", default="out/youtube")
    ap.add_argument("--langs", default="ko,en", help="자막 언어 우선순위")
    ap.add_argument("--asr-model", default="small")
    ap.add_argument("--asr-lang", default="", help="음성 언어 코드 (비우면 자동 감지)")
    ap.add_argument("--frame-interval", type=float, default=4.0)
    ap.add_argument("--ocr-psm", type=int, default=11)
    ap.add_argument("--cookies", help="쿠키 파일 (Netscape 형식)")
    ap.add_argument("--no-subs", action="store_true")
    ap.add_argument("--no-asr", action="store_true")
    ap.add_argument("--no-ocr", action="store_true")
    ap.add_argument("--no-ytdlp", action="store_true", help="yt-dlp 를 쓰지 않고 InnerTube 메타데이터만")
    ap.add_argument("--keep-media", action="store_true")
    args = ap.parse_args(argv)
    args.langs = [x.strip() for x in args.langs.split(",") if x.strip()]

    urls = list(args.urls)
    if args.links_file:
        for line in Path(args.links_file).read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                urls.append(line)
    if not urls:
        ap.error("URL 이 없습니다")

    # 같은 영상은 한 번만 (si= 같은 추적 파라미터는 무시)
    seen: dict[str, str] = {}
    for u in urls:
        vid = video_id_from_url(u)
        if not vid:
            log(f"영상 ID 를 읽을 수 없는 URL 건너뜀: {u}")
            continue
        seen.setdefault(vid, u)
    log(f"영상 {len(seen)}개 처리 (입력 {len(urls)}개, 중복 제거)")

    videos = []
    for vid, u in seen.items():
        try:
            videos.append(process(u, vid, args))
        except Exception as e:  # noqa: BLE001
            log(f"  {vid} 처리 중 예외: {e}")
            videos.append({"id": vid, "url": u, "meta": None, "status": {"subs": "예외", "asr": "예외", "ocr": "예외"},
                           "errors": [str(e)]})
    idx = write_index(videos, Path(args.out))
    log(f"목록: {idx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
