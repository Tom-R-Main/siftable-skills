#!/usr/bin/env python3
"""Clean completed prose of invisible Unicode carriers and exotic spaces.

Adapted from guillaumemeyer/watermarks-remover v0.3.1 (MIT). This is a
deterministic text-hygiene filter, not a statistical-watermark detector.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path


STRIP_CODEPOINTS = frozenset(
    {
        0x00AD,  # soft hyphen
        0x034F,  # combining grapheme joiner
        0x061C,  # Arabic letter mark
        0x115F,
        0x1160,
        0x17B4,
        0x17B5,
        0x180B,
        0x180C,
        0x180D,
        0x180E,
        0x200B,
        0x200C,
        0x200D,
        0x200E,
        0x200F,
        0x202A,
        0x202B,
        0x202C,
        0x202D,
        0x202E,
        0x2060,
        0x2061,
        0x2062,
        0x2063,
        0x2064,
        0x2066,
        0x2067,
        0x2068,
        0x2069,
        0x206A,
        0x206B,
        0x206C,
        0x206D,
        0x206E,
        0x206F,
        0xFEFF,
        *range(0xFE00, 0xFE10),
        0xFFF9,
        0xFFFA,
        0xFFFB,
    }
)

SPACE_HOMOGLYPHS = {
    cp: " "
    for cp in (
        0x00A0,
        0x1680,
        0x2000,
        0x2001,
        0x2002,
        0x2003,
        0x2004,
        0x2005,
        0x2006,
        0x2007,
        0x2008,
        0x2009,
        0x200A,
        0x202F,
        0x205F,
        0x3000,
    )
}


def _should_strip(codepoint: int) -> bool:
    return (
        codepoint in STRIP_CODEPOINTS
        or 0xE0001 <= codepoint <= 0xE007F
        or 0xE0100 <= codepoint <= 0xE01EF
    )


def clean_text(text: str) -> tuple[str, dict[str, object]]:
    """Return cleaned text and machine-readable removal statistics."""
    removed: Counter[str] = Counter()
    replaced: Counter[str] = Counter()
    output: list[str] = []

    for character in text:
        codepoint = ord(character)
        label = f"U+{codepoint:04X} {unicodedata.name(character, 'UNKNOWN')}"
        if _should_strip(codepoint):
            removed[label] += 1
        elif codepoint in SPACE_HOMOGLYPHS:
            replaced[label] += 1
            output.append(" ")
        elif unicodedata.category(character) == "Cf":
            removed[label] += 1
        else:
            output.append(character)

    cleaned = "".join(output)
    stats: dict[str, object] = {
        "input_length": len(text),
        "output_length": len(cleaned),
        "removed": dict(removed),
        "replaced": dict(replaced),
        "removed_count": sum(removed.values()),
        "replaced_count": sum(replaced.values()),
    }
    return cleaned, stats


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8", errors="surrogateescape")


def _write(text: str, path: str) -> None:
    if path == "-":
        sys.stdout.write(text)
        return
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="-", help="Input file or - for stdin")
    parser.add_argument("-o", "--output", default="-", help="Output file or - for stdout")
    parser.add_argument("--stats", action="store_true", help="Print JSON stats to stderr")
    args = parser.parse_args()

    cleaned, stats = clean_text(_read(args.path))
    _write(cleaned, args.output)
    if args.stats:
        print(json.dumps(stats, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
