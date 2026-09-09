#!/usr/bin/env python3
"""HWPX(한글 문서) 읽기 도구.

한컴오피스 없이 .hwpx 파일에서 본문·표·이미지를 뽑아낸다.

의존성:
    pip install python-hwpx pillow lxml

사용법:
    python3 tools/hwpx_extract.py <파일.hwpx> [...] --out out/
        --md        리치 마크다운(표·서식 보존)  [기본]
        --txt       평문 텍스트
        --html      HTML
        --tables    표를 셀 단위 JSON으로
        --images    포함된 이미지를 PNG로
        --pages     조판 미리보기 HTML(페이지 나눔은 근사치)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def _slug(path: Path) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "_", path.stem).strip("_") or "doc"


def export_text(path: Path, out: Path, kinds: set[str]) -> None:
    from hwpx.document import HwpxDocument

    doc = HwpxDocument.open(str(path))
    stem = _slug(path)
    if "md" in kinds:
        (out / f"{stem}.md").write_text(doc.text.markdown(rich=True), encoding="utf-8")
    if "txt" in kinds:
        (out / f"{stem}.txt").write_text(doc.text.plain(), encoding="utf-8")
    if "html" in kinds:
        (out / f"{stem}.html").write_text(doc.text.html(), encoding="utf-8")


def export_tables(path: Path, out: Path) -> None:
    """표를 (행, 열) 격자로 펴서 JSON으로 저장한다.

    python-hwpx의 마크다운 내보내기는 셀 병합을 HTML로 흘려보내므로,
    값끼리 기계적으로 대조하려면 원본 XML의 cellAddr를 직접 읽는 편이 정확하다.
    """
    from lxml import etree

    def cell_text(tc) -> str:
        lines = [
            "".join(t.text or "" for t in para.iter(HP + "t"))
            for para in tc.iter(HP + "p")
        ]
        return "\n".join(lines).strip()

    tables = []
    with zipfile.ZipFile(path) as zf:
        sections = sorted(n for n in zf.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        for name in sections:
            root = etree.fromstring(zf.read(name))
            for index, tbl in enumerate(root.iter(HP + "tbl")):
                rows: dict[int, list[tuple[int, str]]] = {}
                for tc in tbl.iter(HP + "tc"):
                    addr = tc.find(HP + "cellAddr")
                    if addr is None:
                        continue
                    row = int(addr.get("rowAddr"))
                    col = int(addr.get("colAddr"))
                    rows.setdefault(row, []).append((col, cell_text(tc)))
                grid = [[text for _, text in sorted(cells)] for _, cells in sorted(rows.items())]
                tables.append({"section": name, "index": index, "grid": grid})
    (out / f"{_slug(path)}.tables.json").write_text(
        json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def export_images(path: Path, out: Path) -> None:
    from PIL import Image

    stem = _slug(path)
    image_dir = out / f"{stem}.images"
    image_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.startswith(("BinData/", "Preview/")):
                continue
            if name.endswith("/") or name.endswith(".txt"):
                continue
            with zf.open(name) as handle:
                try:
                    image = Image.open(handle)
                    image.load()
                except Exception:
                    continue
            target = image_dir / (Path(name).stem + ".png")
            image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB").save(target)


def export_pages(path: Path, out: Path) -> None:
    from hwpx.tools.layout_preview import render_layout_preview

    preview = render_layout_preview(str(path))
    stem = _slug(path)
    page_dir = out / f"{stem}.pages"
    page_dir.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}.layout.html").write_text(preview.html, encoding="utf-8")
    for number, document in enumerate(preview.page_html_documents(), 1):
        (page_dir / f"p{number}.html").write_text(document, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HWPX 파일에서 본문·표·이미지를 추출한다.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("out"))
    for flag in ("md", "txt", "html", "tables", "images", "pages"):
        parser.add_argument(f"--{flag}", action="store_true")
    args = parser.parse_args(argv)

    kinds = {f for f in ("md", "txt", "html", "tables", "images", "pages") if getattr(args, f)}
    if not kinds:
        kinds = {"md"}
    args.out.mkdir(parents=True, exist_ok=True)

    for path in args.files:
        if not path.is_file():
            print(f"건너뜀(파일 없음): {path}", file=sys.stderr)
            continue
        export_text(path, args.out, kinds)
        if "tables" in kinds:
            export_tables(path, args.out)
        if "images" in kinds:
            export_images(path, args.out)
        if "pages" in kinds:
            export_pages(path, args.out)
        print(f"추출 완료: {path.name} -> {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
