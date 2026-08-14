#!/usr/bin/env python3
"""Deterministic helpers for the predict-future skill.

The script deliberately does not research, forecast, reconcile disagreements, or
calibrate probabilities. It handles the mechanical seams around those judgments.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
from typing import Any


FORECAST_TYPES = {"binary", "categorical", "numeric", "milestone"}
RECORD_KINDS = {"question", "version", "evidence", "resolution"}
MODES = ("QUICK", "STANDARD", "DEEP")
VAGUE_TERMS = {
    "common",
    "generally available",
    "leading",
    "mainstream",
    "major",
    "material",
    "meaningful",
    "qualifying",
    "receipt",
    "significant",
    "stable",
    "standard",
    "success",
    "widely adopted",
}
LEDGER_TITLE = "Personal Forecast Ledger"


def read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def probability(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number from 0 to 1")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be a number from 0 to 1")
    return result


def iso_date(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty ISO date or datetime")
        return
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            errors.append(f"{label} must be an ISO date or datetime")


def cmd_validate_question(args: argparse.Namespace) -> int:
    data = read_json(args.input)
    if not isinstance(data, dict):
        emit({"valid": False, "errors": ["question spec must be a JSON object"], "warnings": []})
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    required_strings = (
        "question_id",
        "original_question",
        "claim_or_metric",
        "resolution_rule",
        "void_conditions",
    )
    for key in required_strings:
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} must be a non-empty string")

    forecast_type = data.get("forecast_type")
    if forecast_type not in FORECAST_TYPES:
        errors.append(f"forecast_type must be one of: {', '.join(sorted(FORECAST_TYPES))}")
    if forecast_type == "categorical":
        outcomes = data.get("outcomes")
        if not isinstance(outcomes, list) or len(outcomes) < 2 or not all(isinstance(x, str) and x.strip() for x in outcomes):
            errors.append("categorical forecasts require at least two named outcomes")
        elif len(set(outcomes)) != len(outcomes):
            errors.append("categorical outcomes must be unique")

    iso_date(data.get("resolution_date"), "resolution_date", errors)
    iso_date(data.get("information_cutoff"), "information_cutoff", errors)

    sources = data.get("resolution_sources")
    if not isinstance(sources, list) or not sources or not all(isinstance(x, str) and x.strip() for x in sources):
        errors.append("resolution_sources must be a non-empty list of source names or URIs")
    for key in ("assumptions", "exclusions"):
        if not isinstance(data.get(key), list):
            errors.append(f"{key} must be a list")
    if not isinstance(data.get("conditional"), bool):
        errors.append("conditional must be true or false")

    terms = data.get("adjudication_terms")
    covered: set[str] = set()
    if not isinstance(terms, list):
        errors.append("adjudication_terms must be a list")
    else:
        for index, item in enumerate(terms):
            if not isinstance(item, dict):
                errors.append(f"adjudication_terms[{index}] must be an object")
                continue
            for key in ("term", "interpretation"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    errors.append(f"adjudication_terms[{index}].{key} must be a non-empty string")
            if isinstance(item.get("term"), str):
                covered.add(item["term"].strip().lower())
            rejected = item.get("alternatives_rejected", [])
            if not isinstance(rejected, list):
                errors.append(f"adjudication_terms[{index}].alternatives_rejected must be a list")

    searchable = " ".join(
        str(data.get(key, "")) for key in ("original_question", "claim_or_metric", "resolution_rule")
    ).lower()
    uncovered = sorted(term for term in VAGUE_TERMS if term in searchable and term not in covered)
    if uncovered:
        warnings.append(
            "potentially resolution-sensitive terms lack explicit adjudication: " + ", ".join(uncovered)
        )
    if data.get("forecast_type") == "milestone":
        warnings.append("validate each milestone as its own scoreable child question")
    if not errors:
        warnings.append("syntactic validation passed; a human or resolver must still confirm scoreability")

    emit({"valid": not errors, "errors": errors, "warnings": warnings})
    return 0 if not errors else 1


def yes(value: str) -> bool:
    return value.lower() == "yes"


def cmd_preflight(args: argparse.Namespace) -> int:
    requested = args.requested.upper()
    limitations: list[str] = []
    real_world = yes(args.real_world)
    retrieval_capability = yes(args.retrieval_capability)
    retrieval_completed = yes(args.retrieval_completed)
    calculator = yes(args.calculator)
    baseline = yes(args.external_baseline)
    calibrator = yes(args.validated_calibrator)
    ledger = yes(args.ledger)
    scheduler = yes(args.scheduler)

    if real_world and not retrieval_capability:
        effective = "BLOCKED"
        limitations.append("current retrieval capability is required for a real-world forecast")
    else:
        effective = "QUICK"
        if args.isolated_contexts >= 3:
            effective = "STANDARD"
        else:
            limitations.append("fewer than three isolated contexts; label output single-model or limited-ensemble")
        deep_ready = (
            args.isolated_contexts >= 3
            and args.model_families >= 2
            and baseline
            and calibrator
            and ledger
            and scheduler
        )
        if deep_ready:
            effective = "DEEP"
        elif requested == "DEEP":
            limitations.append("DEEP requirements are incomplete; mode downgraded")

    if not calculator:
        limitations.append("calculator unavailable; do not perform manual aggregation or scoring")
    if real_world and retrieval_capability and not retrieval_completed:
        limitations.append("retrieval is available but not completed; do not issue a probability yet")
    if args.model_families < 2 and args.isolated_contexts >= 3:
        limitations.append("isolated forecasts come from fewer than two model families")
    if not baseline:
        limitations.append("no external statistical, market, or human baseline")
    if not calibrator:
        limitations.append("no applicable held-out calibrator; report raw probabilities")
    if not ledger:
        limitations.append("persistent ledger unavailable or disabled")
    if not scheduler:
        limitations.append("no scheduler; review and resolution checks require manual invocation")

    if effective != "BLOCKED" and MODES.index(effective) > MODES.index(requested):
        effective = requested
    emit(
        {
            "requested_mode": requested,
            "effective_mode": effective,
            "capabilities": {
                "retrieval_capability": retrieval_capability,
                "retrieval_completed": retrieval_completed,
                "isolated_contexts": args.isolated_contexts,
                "model_families": args.model_families,
                "calculator": calculator,
                "external_baseline": baseline,
                "validated_calibrator": calibrator,
                "sift_cli": bool(shutil.which(args.sift_bin)),
                "ledger": ledger,
                "scheduler": scheduler,
            },
            "limitations": limitations,
            "forecast_ready": effective != "BLOCKED" and (not real_world or retrieval_completed),
        }
    )
    return 2 if effective == "BLOCKED" else 0


def summarize(values: list[float]) -> dict[str, Any]:
    ordered = sorted(values)
    trimmed = None
    if len(values) >= 10:
        trim = max(1, math.floor(len(values) * 0.1))
        trimmed = statistics.fmean(ordered[trim:-trim])
    return {
        "count": len(values),
        "mean": round(statistics.fmean(values), 12),
        "median": round(statistics.median(values), 12),
        "trimmed_mean": None if trimmed is None else round(trimmed, 12),
        "min": round(ordered[0], 12),
        "max": round(ordered[-1], 12),
    }


def cmd_aggregate(args: argparse.Namespace) -> int:
    data = read_json(args.input)
    members = data.get("members") if isinstance(data, dict) else None
    if not isinstance(members, list) or not members:
        raise ValueError("members must be a non-empty list")
    kind = data.get("type")
    if kind == "binary":
        values = [probability(member.get("value"), f"members[{index}].value") for index, member in enumerate(members)]
        result = summarize(values)
    elif kind == "categorical":
        category_sets = []
        for index, member in enumerate(members):
            dist = member.get("distribution")
            if not isinstance(dist, dict) or not dist:
                raise ValueError(f"members[{index}].distribution must be a non-empty object")
            normalized = {str(key): probability(value, f"members[{index}].distribution.{key}") for key, value in dist.items()}
            if not math.isclose(sum(normalized.values()), 1.0, abs_tol=1e-6):
                raise ValueError(f"members[{index}].distribution must sum to 1")
            category_sets.append(normalized)
        categories = list(category_sets[0])
        if any(set(dist) != set(categories) for dist in category_sets[1:]):
            raise ValueError("every categorical member must use the same outcomes")
        result = {category: summarize([dist[category] for dist in category_sets]) for category in categories}
    else:
        raise ValueError("aggregate supports type binary or categorical")

    diversity = {
        "member_ids": [member.get("id") for member in members],
        "model_families": sorted({str(member["model_family"]) for member in members if member.get("model_family")}),
        "evidence_packets": sorted({str(member["evidence_packet"]) for member in members if member.get("evidence_packet")}),
    }
    emit({"type": kind, "mechanical_aggregate": result, "diversity": diversity})
    return 0


def skill_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for top in ("SKILL.md", "agents", "references", "scripts"):
        candidate = root / top
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                path
                for path in candidate.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith(".")
            )
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def cmd_fingerprint(args: argparse.Namespace) -> int:
    root = Path(args.skill_root).expanduser().resolve()
    digest = hashlib.sha256()
    paths = skill_files(root)
    if not paths:
        raise ValueError(f"no skill files found under {root}")
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    emit({"algorithm": "sha256", "content_hash": digest.hexdigest(), "file_count": len(paths)})
    return 0


def table_cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def cmd_render_evidence(args: argparse.Namespace) -> int:
    data = read_json(args.input)
    rows = data.get("evidence") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError("evidence input must be a list or an object with an evidence list")
    selected = rows[: args.limit]
    print("| ID | Observation | Direction | Mechanism | Limitation | Source |")
    print("|---|---|---|---|---|---|")
    for index, row in enumerate(selected, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"evidence row {index} must be an object")
        values = (
            row.get("id", f"E{index}"),
            row.get("observation", row.get("claim", "")),
            row.get("direction", ""),
            row.get("mechanism", ""),
            row.get("limitation", row.get("limitations", "")),
            row.get("source", ""),
        )
        print("| " + " | ".join(table_cell(value) for value in values) + " |")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    data = read_json(args.input)
    kind = data.get("type") if isinstance(data, dict) else None
    if kind == "binary":
        forecast = probability(data.get("forecast"), "forecast")
        outcome = data.get("outcome")
        if outcome not in (0, 1, False, True):
            raise ValueError("binary outcome must be 0 or 1")
        observed = int(outcome)
        likelihood = forecast if observed else 1.0 - forecast
        result = {
            "brier_score": round((forecast - observed) ** 2, 12),
            "log_loss": round(-math.log(max(likelihood, 1e-15)), 12),
        }
    elif kind == "categorical":
        forecast = data.get("forecast")
        outcome = data.get("outcome")
        if not isinstance(forecast, dict) or outcome not in forecast:
            raise ValueError("categorical forecast must be an object containing the observed outcome")
        distribution = {str(key): probability(value, f"forecast.{key}") for key, value in forecast.items()}
        if not math.isclose(sum(distribution.values()), 1.0, abs_tol=1e-6):
            raise ValueError("categorical forecast must sum to 1")
        result = {
            "multiclass_brier_score": round(
                sum((value - (1.0 if key == outcome else 0.0)) ** 2 for key, value in distribution.items()),
                12,
            ),
            "log_loss": round(-math.log(max(distribution[str(outcome)], 1e-15)), 12),
        }
    elif kind == "numeric":
        quantiles = data.get("quantiles")
        outcome = data.get("outcome")
        if not isinstance(quantiles, dict) or not isinstance(outcome, (int, float)) or isinstance(outcome, bool):
            raise ValueError("numeric score requires quantiles and a numeric outcome")
        losses: dict[str, float] = {}
        previous_value: float | None = None
        for key, estimate in sorted(quantiles.items(), key=lambda item: float(item[0])):
            q = probability(float(key), f"quantile {key}")
            if not 0.0 < q < 1.0 or not isinstance(estimate, (int, float)) or isinstance(estimate, bool):
                raise ValueError("numeric quantiles must use probabilities between 0 and 1 and numeric estimates")
            estimate_value = float(estimate)
            if previous_value is not None and estimate_value < previous_value:
                raise ValueError("numeric quantile estimates must be non-decreasing")
            previous_value = estimate_value
            error = float(outcome) - estimate_value
            losses[key] = round(max(q * error, (q - 1.0) * error), 12)
        result = {
            "pinball_loss_by_quantile": losses,
            "mean_pinball_loss": round(statistics.fmean(losses.values()), 12),
        }
    else:
        raise ValueError("score supports type binary, categorical, or numeric")
    emit({"type": kind, "score": result})
    return 0


def ledger_contract() -> dict[str, Any]:
    fields = [
        ("record_id", "text"),
        ("record_kind", "select"),
        ("question_id", "text"),
        ("version_id", "text"),
        ("issued_at", "date"),
        ("information_cutoff", "date"),
        ("resolution_date", "date"),
        ("probability", "number"),
        ("distribution_json", "text"),
        ("source_uri", "url"),
        ("skill_hash", "text"),
        ("model_ids_json", "text"),
        ("supersedes_id", "text"),
        ("payload_json", "text"),
    ]
    return {
        "title": LEDGER_TITLE,
        "description": "Append-only personal forecast questions, versions, evidence, and resolutions.",
        "fields": [{"name": name, "fieldType": kind} for name, kind in fields],
        "metadata": {
            "contract": "predict-future-ledger-v1",
            "appendOnly": True,
            "allowedRecordKinds": sorted(RECORD_KINDS),
            "mutationPolicy": "clients may add and query; historical records are never updated or deleted",
        },
    }


def resolve_sift(binary: str) -> str:
    resolved = shutil.which(binary)
    if not resolved:
        raise ValueError(f"Sift CLI not found: {binary}; add it to PATH or pass --sift-bin")
    return resolved


def run_sift(argv: list[str]) -> Any:
    completed = subprocess.run(argv, check=False, capture_output=True, text=True)
    if completed.returncode:
        message = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"Sift CLI failed: {message}")
    output = completed.stdout.strip()
    if not output:
        return {"ok": True}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"output": output}


def cmd_ledger_contract(_: argparse.Namespace) -> int:
    emit(ledger_contract())
    return 0


def normalize_ledger_record(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("ledger record must be a JSON object")
    required = ("record_id", "record_kind", "question_id", "issued_at", "skill_hash", "payload_json")
    for key in required:
        if data.get(key) in (None, ""):
            raise ValueError(f"ledger record requires {key}")
    if data["record_kind"] not in RECORD_KINDS:
        raise ValueError(f"record_kind must be one of: {', '.join(sorted(RECORD_KINDS))}")
    iso_date(data.get("issued_at"), "issued_at", errors := [])
    if errors:
        raise ValueError(errors[0])
    allowed = {field["name"] for field in ledger_contract()["fields"]}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError("unknown ledger fields: " + ", ".join(unknown))
    result = dict(data)
    for key in ("distribution_json", "model_ids_json", "payload_json"):
        if key in result and result[key] is not None and not isinstance(result[key], str):
            result[key] = json.dumps(result[key], sort_keys=True, separators=(",", ":"))
    if "probability" in result and result["probability"] is not None:
        result["probability"] = probability(result["probability"], "probability")
    return result


def cmd_ledger_init(args: argparse.Namespace) -> int:
    contract = ledger_contract()
    binary = args.sift_bin
    argv = [
        binary,
        "datasets",
        "create",
        "--title",
        contract["title"],
        "--description",
        contract["description"],
        "--fields",
        json.dumps(contract["fields"], separators=(",", ":")),
        "--metadata",
        json.dumps(contract["metadata"], separators=(",", ":")),
        "--json",
    ]
    if not args.execute:
        emit({"dry_run": True, "operation": "create", "argv": argv, "contract": contract})
        return 0
    resolved = resolve_sift(binary)
    listing = run_sift([resolved, "datasets", "list", "--limit", "200", "--json"])
    datasets = listing.get("datasets", []) if isinstance(listing, dict) else []
    matches = [item for item in datasets if isinstance(item, dict) and item.get("title") == LEDGER_TITLE]
    if matches:
        existing = matches[0]
        metadata = existing.get("metadata") if isinstance(existing.get("metadata"), dict) else {}
        if metadata.get("contract") != contract["metadata"]["contract"]:
            raise ValueError(
                f"a dataset titled {LEDGER_TITLE!r} already exists without the expected contract; inspect it before choosing a different title"
            )
        contract_result = run_sift([resolved, "datasets", "contract", str(existing.get("id")), "--json"])
        schema = contract_result.get("schema", {}) if isinstance(contract_result, dict) else {}
        actual_fields = schema.get("fields", []) if isinstance(schema, dict) else []
        actual = {
            str(field.get("name")): str(field.get("type"))
            for field in actual_fields
            if isinstance(field, dict) and field.get("name") and field.get("type")
        }
        expected = {str(field["name"]): str(field["fieldType"]) for field in contract["fields"]}
        if actual != expected:
            raise ValueError(
                f"the existing {LEDGER_TITLE!r} dataset has schema drift; inspect `sift datasets contract {existing.get('id')}` before appending"
            )
        emit({"created": False, "reused": True, "dataset": existing})
        return 0
    argv[0] = resolved
    emit(run_sift(argv))
    return 0


def dataset_id(args: argparse.Namespace) -> str:
    value = args.dataset_id or os.environ.get("PREDICT_FUTURE_LEDGER_ID")
    if not value:
        raise ValueError("provide --dataset-id or PREDICT_FUTURE_LEDGER_ID")
    return value


def cmd_ledger_append(args: argparse.Namespace) -> int:
    record = normalize_ledger_record(read_json(args.input))
    argv = [args.sift_bin, "datasets", "add", dataset_id(args), "--record", json.dumps(record, separators=(",", ":")), "--json"]
    if not args.execute:
        emit({"dry_run": True, "operation": "append", "argv": argv, "record": record})
        return 0
    argv[0] = resolve_sift(args.sift_bin)
    emit(run_sift(argv))
    return 0


def cmd_ledger_read(args: argparse.Namespace) -> int:
    filters = [{"field": "question_id", "value": args.question_id}]
    argv = [
        args.sift_bin,
        "datasets",
        "query",
        dataset_id(args),
        "--filters",
        json.dumps(filters, separators=(",", ":")),
        "--limit",
        str(args.limit),
        "--json",
    ]
    if args.dry_run:
        emit({"dry_run": True, "operation": "query", "argv": argv})
        return 0
    argv[0] = resolve_sift(args.sift_bin)
    emit(run_sift(argv))
    return 0


def add_yes_no(parser: argparse.ArgumentParser, name: str, default: str) -> None:
    parser.add_argument(name, choices=("yes", "no"), default=default)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-question", help="Check a forecast question specification")
    validate.add_argument("--input", required=True, help="JSON file or - for stdin")
    validate.set_defaults(func=cmd_validate_question)

    preflight = sub.add_parser("preflight", help="Determine the highest honest operating mode")
    preflight.add_argument("--requested", choices=("quick", "standard", "deep"), default="standard")
    add_yes_no(preflight, "--real-world", "yes")
    preflight.add_argument(
        "--retrieval-capability",
        "--current-retrieval",
        dest="retrieval_capability",
        choices=("yes", "no"),
        default="no",
        help="Whether fresh retrieval can be performed; --current-retrieval is a compatibility alias",
    )
    add_yes_no(preflight, "--retrieval-completed", "no")
    preflight.add_argument("--isolated-contexts", type=int, default=1)
    preflight.add_argument("--model-families", type=int, default=1)
    add_yes_no(preflight, "--calculator", "yes")
    add_yes_no(preflight, "--external-baseline", "no")
    add_yes_no(preflight, "--validated-calibrator", "no")
    add_yes_no(preflight, "--ledger", "no")
    add_yes_no(preflight, "--scheduler", "no")
    preflight.add_argument("--sift-bin", default="sift")
    preflight.set_defaults(func=cmd_preflight)

    aggregate = sub.add_parser("aggregate", help="Mechanically aggregate isolated member forecasts")
    aggregate.add_argument("--input", required=True, help="JSON file or - for stdin")
    aggregate.set_defaults(func=cmd_aggregate)

    fingerprint = sub.add_parser("fingerprint", help="Hash behavior-bearing skill content")
    fingerprint.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    fingerprint.set_defaults(func=cmd_fingerprint)

    evidence = sub.add_parser("render-evidence", help="Render the decisive evidence table")
    evidence.add_argument("--input", required=True, help="JSON file or - for stdin")
    evidence.add_argument("--limit", type=int, default=8)
    evidence.set_defaults(func=cmd_render_evidence)

    score = sub.add_parser("score", help="Score a resolved binary, categorical, or numeric forecast")
    score.add_argument("--input", required=True, help="JSON file or - for stdin")
    score.set_defaults(func=cmd_score)

    contract = sub.add_parser("ledger-contract", help="Print the Siftable ledger contract")
    contract.set_defaults(func=cmd_ledger_contract)

    init = sub.add_parser("ledger-init", help="Plan or create the personal Siftable ledger")
    init.add_argument("--sift-bin", default="sift")
    init.add_argument("--execute", action="store_true", help="Execute the create operation; default is dry-run")
    init.set_defaults(func=cmd_ledger_init)

    append = sub.add_parser("ledger-append", help="Validate and plan or append one immutable ledger record")
    append.add_argument("--dataset-id")
    append.add_argument("--input", required=True, help="JSON file or - for stdin")
    append.add_argument("--sift-bin", default="sift")
    append.add_argument("--execute", action="store_true", help="Execute the add operation; default is dry-run")
    append.set_defaults(func=cmd_ledger_append)

    read = sub.add_parser("ledger-read", help="Read records for one forecast question")
    read.add_argument("--dataset-id")
    read.add_argument("--question-id", required=True)
    read.add_argument("--limit", type=int, default=100)
    read.add_argument("--sift-bin", default="sift")
    read.add_argument("--dry-run", action="store_true")
    read.set_defaults(func=cmd_ledger_read)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        return int(args.func(args))
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
