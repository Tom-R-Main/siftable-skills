#!/usr/bin/env python3
"""Query a configured local corpus backend and validate its JSON response."""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import subprocess
import sys
from typing import Any


def fail(message: str, code: int = 2) -> int:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    return code


def validate_result(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"results[{index}] must be an object")
    normalized: dict[str, Any] = {}
    for field in ("source", "locator", "passage"):
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"results[{index}].{field} must be a non-empty string")
        normalized[field] = item
    if "score" in value:
        score = value["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(float(score)):
            raise ValueError(f"results[{index}].score must be a finite number")
        normalized["score"] = float(score)
    if "image_path" in value:
        image_path = value["image_path"]
        if image_path is not None and not isinstance(image_path, str):
            raise ValueError(f"results[{index}].image_path must be a string or null")
        normalized["image_path"] = image_path
    if "metadata" in value:
        metadata = value["metadata"]
        if not isinstance(metadata, dict):
            raise ValueError(f"results[{index}].metadata must be an object")
        normalized["metadata"] = metadata
    if "collection" in value:
        collection = value["collection"]
        if collection is not None and not isinstance(collection, str):
            raise ValueError(f"results[{index}].collection must be a string or null")
        normalized["collection"] = collection
    return normalized


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--query", required=True, help="Focused retrieval query")
    result.add_argument("--collection", help="Optional backend collection")
    result.add_argument("--limit", type=int, default=10, help="Maximum results, from 1 through 100")
    result.add_argument("--command", help="Explicit backend command; defaults to LOCAL_CORPUS_COMMAND")
    result.add_argument("--timeout-seconds", type=float, default=60.0)
    return result


def main() -> int:
    args = parser().parse_args()
    if not args.query.strip():
        return fail("query must be non-empty")
    if not 1 <= args.limit <= 100:
        return fail("limit must be from 1 through 100")
    if not 0 < args.timeout_seconds <= 600:
        return fail("timeout-seconds must be greater than 0 and at most 600")
    command_text = args.command or os.environ.get("LOCAL_CORPUS_COMMAND", "")
    if not command_text.strip():
        return fail("LOCAL_CORPUS_COMMAND is not configured")
    try:
        command = shlex.split(command_text)
    except ValueError as exc:
        return fail(f"backend command is invalid: {exc}")
    if not command:
        return fail("backend command is empty")
    payload = {"query": args.query, "collection": args.collection, "limit": args.limit}
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return fail("backend executable was not found", 127)
    except subprocess.TimeoutExpired:
        return fail("backend timed out", 124)
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "no diagnostic"
        return fail(f"backend exited {completed.returncode}: {detail}", 1)
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return fail(f"backend returned invalid JSON: {exc}", 1)
    if not isinstance(response, dict) or not isinstance(response.get("results"), list):
        return fail("backend response must be an object with a results array", 1)
    try:
        results = [validate_result(item, index) for index, item in enumerate(response["results"][: args.limit])]
    except ValueError as exc:
        return fail(str(exc), 1)
    print(json.dumps({"results": results}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
