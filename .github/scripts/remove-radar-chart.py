#!/usr/bin/env python3
"""生成されたSVGから五角形のコントリビューションレーダーチャートを除去する。"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

GROUP_TOKEN = re.compile(r"<g\b[^>]*>|</g>")
RADAR_POLYGON = re.compile(r'<polygon\b[^>]*\bclass=["\']radar["\']')


def remove_radar_groups(svg: str) -> str:
    """レーダーを含む最上位のg要素だけを、元の文字列を保って除去する。"""
    depth = 0
    group_start: int | None = None
    ranges: list[tuple[int, int]] = []

    for match in GROUP_TOKEN.finditer(svg):
        token = match.group(0)
        if token.startswith("</"):
            depth -= 1
            if depth < 0:
                raise ValueError("SVGのg要素が正しく閉じられていません")
            if depth == 0:
                if group_start is None:
                    raise ValueError("SVGのg要素の開始位置を特定できません")
                group_end = match.end()
                group = svg[group_start:group_end]
                if RADAR_POLYGON.search(group):
                    ranges.append((group_start, group_end))
                group_start = None
        else:
            if depth == 0:
                group_start = match.start()
            depth += 1

    if depth != 0:
        raise ValueError("SVGのg要素が正しく閉じられていません")
    if not ranges:
        raise ValueError("レーダーチャートを含む最上位のg要素が見つかりません")

    updated = svg
    for start, end in reversed(ranges):
        updated = updated[:start] + updated[end:]

    # 生成物を壊さないよう、除去後のSVGとして解析できることを確認する。
    ET.fromstring(updated)
    if RADAR_POLYGON.search(updated):
        raise ValueError("レーダーチャートをすべて除去できませんでした")
    return updated


def main() -> int:
    paths = [Path(path) for path in sys.argv[1:]]
    if not paths:
        print("SVGファイルを1つ以上指定してください", file=sys.stderr)
        return 2

    for path in paths:
        original = path.read_text(encoding="utf-8")
        updated = remove_radar_groups(original)
        if updated == original:
            print(f"変更なし: {path}")
            continue
        path.write_text(updated, encoding="utf-8")
        print(f"レーダーチャートを除去: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
