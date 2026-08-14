#!/usr/bin/env python3
"""Synthetic full-text backend for the search-local-corpus contract tests."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "corpus.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    args = parser.parse_args()
    request = json.load(sys.stdin)
    query_terms = set(re.findall(r"[a-z0-9_]+", str(request.get("query", "")).lower()))
    collection = request.get("collection")
    limit = int(request.get("limit", 10))
    corpus = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    ranked = []
    for row in corpus:
        if collection and row.get("collection") != collection:
            continue
        haystack = f"{row['source']} {row['passage']}".lower()
        matches = sum(term in haystack for term in query_terms)
        if matches:
            ranked.append((matches / max(1, len(query_terms)), row))
    ranked.sort(key=lambda item: (-item[0], item[1]["source"]))
    results = []
    for score, row in ranked[:limit]:
        results.append({**row, "score": round(score, 6), "image_path": None, "metadata": {"retrieval": "synthetic-full-text"}})
    print(json.dumps({"results": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
