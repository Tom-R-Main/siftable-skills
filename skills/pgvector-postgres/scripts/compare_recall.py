#!/usr/bin/env python3
"""Compare approximate result IDs with an exact reference and report recall@k."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def identity(value: Any) -> str:
    if value is None or isinstance(value, (dict, list)):
        raise ValueError("query IDs and result IDs must be non-null JSON scalars")
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def parse_runs(raw: Any, label: str) -> dict[str, tuple[Any, list[Any]]]:
    if isinstance(raw, dict):
        raw = raw.get("queries")
    if not isinstance(raw, list):
        raise ValueError(f"{label} must be a list or an object containing a queries list")
    runs: dict[str, tuple[Any, list[Any]]] = {}
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or "query_id" not in item or not isinstance(item.get("ids"), list):
            raise ValueError(f"{label}[{index}] must contain query_id and an ids list")
        query_key = identity(item["query_id"])
        if query_key in runs:
            raise ValueError(f"{label} contains duplicate query_id {item['query_id']!r}")
        ids = item["ids"]
        id_keys = [identity(value) for value in ids]
        if len(id_keys) != len(set(id_keys)):
            raise ValueError(f"{label} query {item['query_id']!r} contains duplicate result IDs")
        runs[query_key] = (item["query_id"], ids)
    return runs


def compare(exact: dict[str, tuple[Any, list[Any]]], approx: dict[str, tuple[Any, list[Any]]], k: int) -> dict[str, Any]:
    if set(exact) != set(approx):
        missing = sorted(set(exact) - set(approx))
        extra = sorted(set(approx) - set(exact))
        raise ValueError(f"query sets differ; missing={missing}, extra={extra}")
    rows: list[dict[str, Any]] = []
    recalls: list[float] = []
    for key in sorted(exact):
        query_id, exact_ids = exact[key]
        _, approx_ids = approx[key]
        exact_top = exact_ids[:k]
        approx_top = approx_ids[:k]
        exact_keys = {identity(value) for value in exact_top}
        approx_keys = {identity(value) for value in approx_top}
        overlap = len(exact_keys & approx_keys)
        denominator = len(exact_top)
        recall = overlap / denominator if denominator else None
        if recall is not None:
            recalls.append(recall)
        rows.append(
            {
                "query_id": query_id,
                "exact_count": denominator,
                "approx_count": len(approx_top),
                "overlap_count": overlap,
                "recall_at_k": round(recall, 12) if recall is not None else None,
                "result_shortfall": max(0, denominator - len(approx_top)),
            }
        )
    mean = sum(recalls) / len(recalls) if recalls else None
    return {
        "k": k,
        "query_count": len(rows),
        "mean_recall_at_k": round(mean, 12) if mean is not None else None,
        "queries": rows,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--exact", required=True, help="Exact-result JSON path, or - for stdin")
    result.add_argument("--approx", required=True, help="Approximate-result JSON path")
    result.add_argument("--k", required=True, type=int, help="Positive rank cutoff")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.k < 1:
            raise ValueError("k must be positive")
        exact = parse_runs(load_json(args.exact), "exact")
        approx = parse_runs(load_json(args.approx), "approx")
        print(json.dumps(compare(exact, approx, args.k), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
