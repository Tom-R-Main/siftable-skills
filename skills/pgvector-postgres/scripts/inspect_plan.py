#!/usr/bin/env python3
"""Summarize PostgreSQL EXPLAIN (FORMAT JSON) without judging plan quality."""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any


NODE_FIELDS = (
    "Node Type",
    "Relation Name",
    "Alias",
    "Index Name",
    "Scan Direction",
    "Plan Rows",
    "Actual Rows",
    "Actual Loops",
    "Rows Removed by Filter",
    "Index Cond",
    "Filter",
    "Order By",
    "Sort Key",
    "Shared Hit Blocks",
    "Shared Read Blocks",
    "Temp Read Blocks",
    "Temp Written Blocks",
)


def load(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def unwrap(raw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(raw, list) and len(raw) == 1:
        raw = raw[0]
    if not isinstance(raw, dict) or not isinstance(raw.get("Plan"), dict):
        raise ValueError("expected EXPLAIN (FORMAT JSON) with a top-level Plan object")
    return raw, raw["Plan"]


def walk(node: dict[str, Any], path: str, rows: list[dict[str, Any]]) -> None:
    summary = {"path": path}
    summary.update({field: node[field] for field in NODE_FIELDS if field in node})
    rows.append(summary)
    children = node.get("Plans", [])
    if not isinstance(children, list):
        raise ValueError(f"Plans at {path} must be a list")
    for index, child in enumerate(children):
        if not isinstance(child, dict):
            raise ValueError(f"plan child {path}.{index} must be an object")
        walk(child, f"{path}.{index}", rows)


def summarize(raw: Any) -> dict[str, Any]:
    envelope, plan = unwrap(raw)
    nodes: list[dict[str, Any]] = []
    walk(plan, "0", nodes)
    counts = collections.Counter(str(node.get("Node Type", "unknown")) for node in nodes)
    index_names = sorted({str(node["Index Name"]) for node in nodes if node.get("Index Name")})
    relations = sorted({str(node["Relation Name"]) for node in nodes if node.get("Relation Name")})
    return {
        "top_node_type": plan.get("Node Type"),
        "node_count": len(nodes),
        "node_type_counts": dict(sorted(counts.items())),
        "index_names": index_names,
        "relations": relations,
        "flags": {
            "uses_index": bool(index_names),
            "uses_sequential_scan": any(node.get("Node Type") == "Seq Scan" for node in nodes),
            "has_filter": any("Filter" in node or node.get("Rows Removed by Filter", 0) for node in nodes),
            "has_sort": any(node.get("Node Type") in {"Sort", "Incremental Sort"} for node in nodes),
        },
        "planning_time_ms": envelope.get("Planning Time"),
        "execution_time_ms": envelope.get("Execution Time"),
        "nodes": nodes,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--input", required=True, help="EXPLAIN JSON path, or - for stdin")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        print(json.dumps(summarize(load(args.input)), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
