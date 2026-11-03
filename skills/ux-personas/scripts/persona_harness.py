#!/usr/bin/env python3
"""Build bounded UX persona sessions and audit recorded evidence, using stdlib only.

This tool does not drive a browser or certify that submitted observations are true.
The host agent runs each packet using its available driver and records artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
STATUSES = {"completed", "abandoned", "blocked", "budget_exhausted"}
LIMIT = 32 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")


def strings(value, label, nonempty=False):
    require(isinstance(value, list), f"{label} must be a list")
    require(not nonempty or len(value) > 0, f"{label} must not be empty")
    for item in value:
        text(item, label)
    require(len(value) == len(set(value)), f"{label} contains duplicate values")


def identifier(value, label):
    require(isinstance(value, str) and len(value) <= 80 and ID.fullmatch(value),
            f"{label} must use lowercase words joined by single hyphens")


def budget(value):
    require(type(value) is int and 1 <= value <= 200, "max_steps must be an integer from 1 to 200")
    return value


def validate_study(study):
    require(isinstance(study, dict), "study must be an object")
    require(type(study.get("schema_version")) is int and study["schema_version"] == 1,
            "schema_version must be integer 1")
    identifier(study.get("id"), "study.id")
    text(study.get("product"), "product")
    require(isinstance(study.get("target"), dict), "target must be an object")
    text(study["target"].get("revision"), "target.revision")
    budget(study.get("max_steps", 20))
    for group in ("personas", "journeys"):
        rows = study.get(group)
        require(isinstance(rows, list) and rows, f"{group} must be a nonempty list")
        require(len(rows) <= 100, f"{group} has more than 100 entries")
        seen = set()
        for row in rows:
            require(isinstance(row, dict), f"{group} entries must be objects")
            identifier(row.get("id"), f"{group}.id")
            require(row["id"] not in seen, f"duplicate {group} id: {row['id']}")
            seen.add(row["id"])
            if group == "personas":
                text(row.get("name"), "persona.name")
                for key in ("goals", "knowledge", "assumptions", "prior_experience"):
                    strings(row.get(key), f"persona.{key}", nonempty=key == "goals")
                require(isinstance(row.get("constraints"), dict), "constraints must be an object")
                budget(row["constraints"].get("max_steps", study.get("max_steps", 20)))
                evidence = row.get("evidence")
                require(isinstance(evidence, list), "persona.evidence must be a list")
                for item in evidence:
                    require(isinstance(item, dict), "evidence entries must be objects")
                    text(item.get("source"), "evidence.source")
                    text(item.get("claim"), "evidence.claim")
                require(evidence or row["assumptions"], "ungrounded persona needs explicit assumptions")
            else:
                for key in ("goal", "initial_state"):
                    text(row.get(key), f"journey.{key}")
                strings(row.get("success_criteria"), "success_criteria", nonempty=True)
                text(row.get("start_url"), "start_url")
                parsed = urlsplit(row["start_url"])
                require(parsed.scheme in {"http", "https"} and parsed.hostname and
                        not parsed.username and not parsed.password, "start_url must be HTTP(S), without credentials")
    require(len(study["personas"]) * len(study["journeys"]) <= 500, "study exceeds 500 sessions")
    return study


def sessions(study):
    for persona in study["personas"]:
        for journey in study["journeys"]:
            yield f"{persona['id']}--{journey['id']}", persona, journey


def session_packet(study, session, persona, journey):
    return {
        "schema_version": 1, "session_id": session, "study_hash": digest(study),
        "target": study["target"], "product": study["product"],
        "persona": persona, "journey": journey,
        "max_steps": min(study.get("max_steps", 20), persona["constraints"].get("max_steps", study.get("max_steps", 20))),
        "experience_mode": "returning" if persona["prior_experience"] else "fresh",
        "instructions": [
            "Use a separate browser context and reset to the journey initial_state. Record inability to isolate or seed as blocked.",
            "Use only this persona, its explicit prior_experience, current visible UI and this session's observations. Do not use source code, hidden routes, other personas' runs, or solution hints.",
            "Choose actions from the observed interface toward the goal; do not invent browser actions or results. Respect constraints and existing action authorization.",
            "Save each observation artifact inside this session directory; record one observation per numbered browser step. Never save credentials or cookies in evidence.",
            "Record uncertainty and feelings as model judgments. Accessibility simulation does not establish assistive-technology compatibility.",
            "A completed outcome requires browser observation artifacts covering every success criterion. Artifacts establish recorded evidence, not independent truth certification.",
            "Stop on completion, abandonment, inability to proceed, or max_steps. Do not execute a mutation with uncertain prior outcome again without reconciliation.",
            "Prior experience is frozen for this run. Learning across versions requires an explicit edited persona and a separate returning-user study.",
        ],
    }


def plan(study, output):
    validate_study(study)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "study": study, "study_hash": digest(study),
                "session_ids": [sid for sid, _, _ in sessions(study)]}
    write_json(root / "manifest.json", manifest)
    for sid, persona, journey in sessions(study):
        folder = root / "sessions" / sid
        folder.mkdir(parents=True)
        packet = session_packet(study, sid, persona, journey)
        write_json(folder / "packet.json", packet)
        (folder / "packet.md").write_text(
            f"# {persona['name']}: {journey['goal']}\n\n"
            + "\n".join(f"- {line}" for line in packet["instructions"])
            + "\n\nFull session contract:\n\n```json\n"
            + json.dumps(packet, indent=2, ensure_ascii=False) + "\n```\n", encoding="utf-8")
        (folder / "events.jsonl").touch()
    return {"run": str(root), "sessions": len(manifest["session_ids"]), "study_hash": manifest["study_hash"]}


def load_run(root):
    root = Path(root).resolve()
    manifest = read_json(run_path(root, "manifest.json", "file"))
    require(isinstance(manifest, dict) and manifest.get("schema_version") == 1, "invalid run manifest")
    study = validate_study(manifest.get("study"))
    require(manifest.get("study_hash") == digest(study), "study snapshot hash mismatch")
    expected = [sid for sid, _, _ in sessions(study)]
    require(manifest.get("session_ids") == expected, "session matrix does not match study")
    return root, study


def run_path(root, relative, kind, missing=False):
    """Reject indirection within a run without rejecting canonical /tmp parents."""
    relative = Path(relative)
    require(not relative.is_absolute() and ".." not in relative.parts,
            "run metadata path must stay inside the run")
    current = root
    for index, component in enumerate(relative.parts):
        current = current / component
        require(not current.is_symlink(), "run metadata paths must not contain symlinks")
        final = index == len(relative.parts) - 1
        if final and missing and not current.exists():
            return current
        expected_directory = not final or kind == "directory"
        require(current.is_dir() if expected_directory else current.is_file(),
                "run metadata must use ordinary directories and files")
    return current


def checked_path(root, relative, folder):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(),
            "artifact must be a relative run path")
    require(".." not in Path(relative).parts, "artifact paths must not contain parent traversal")
    raw = root / relative
    path = raw.resolve()
    require(path.is_relative_to(folder.resolve()), "artifact must stay inside its own session")
    current = raw
    while current != root:
        require(not current.is_symlink(), "artifact paths must not contain symlinks")
        current = current.parent
        require(current == root or current.is_relative_to(root), "invalid artifact path")
    require(path.is_file() and path.stat().st_size <= LIMIT, "artifact missing or larger than 32 MiB")
    require(path.name not in {"events.jsonl", "packet.json", "packet.md", ".record-lock"},
            "session metadata is not observation evidence")
    return path


def artifact_records(root, folder, paths):
    require(isinstance(paths, list), "artifacts must be a list")
    result = []
    for relative in paths:
        path = checked_path(root, relative, folder)
        result.append({"path": str(path.relative_to(root)),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    require(len({row["path"] for row in result}) == len(result), "duplicate artifact")
    return result


def validate_event(event, previous, packet):
    require(isinstance(event, dict), "event must be an object")
    require(not previous or previous[-1]["kind"] != "outcome", "session is already terminal")
    require(type(event.get("step")) is int, "step must be an integer")
    kind = event.get("kind")
    require(isinstance(kind, str) and kind in {"observation", "judgment", "outcome"}, "invalid event kind")
    text(event.get("summary"), "event.summary")
    source = event.get("source")
    require(isinstance(source, str) and source in {"browser", "model", "fixture"}, "invalid event source")
    require(isinstance(event.get("artifacts"), list), "event.artifacts must be a list")
    last_step = max((e["step"] for e in previous), default=0)
    require(0 <= event["step"] <= packet["max_steps"], "step exceeds session budget")
    criteria = event.get("criteria", [])
    strings(criteria, "criteria")
    require(set(criteria) <= set(packet["journey"]["success_criteria"]), "unknown success criterion")
    if kind == "observation":
        require(source in {"browser", "fixture"}, "observations require browser or fixture source")
        require(event["step"] == last_step + 1, "observations require the next consecutive step")
        require(event["artifacts"], "observations require saved artifacts")
        require("status" not in event, "only outcome events have status")
    else:
        require(source == "model", "judgment/outcome source must be model")
        require(event["step"] == last_step, "judgment/outcome step must equal latest observation step")
        require(not criteria, "only observations may cover success criteria")
        if kind == "judgment":
            require("status" not in event, "only outcome events have status")
        else:
            require(isinstance(event.get("status"), str) and event["status"] in STATUSES,
                    "invalid terminal status")
            if event["status"] == "completed":
                covered = {c for e in previous if e["kind"] == "observation" and e["source"] == "browser"
                           for c in e.get("criteria", [])}
                require(covered == set(packet["journey"]["success_criteria"]),
                        "completion needs recorded browser evidence for every success criterion")
            if event["status"] == "budget_exhausted":
                require(last_step == packet["max_steps"], "budget is not exhausted")
    require(kind == "outcome" or len(previous) < packet["max_steps"] * 4, "event limit reached; record an outcome")


def load_events(root, folder, packet):
    folder = run_path(root, folder.relative_to(root), "directory")
    packet_path = run_path(root, folder.relative_to(root) / "packet.json", "file")
    events_path = run_path(root, folder.relative_to(root) / "events.jsonl", "file")
    run_path(root, folder.relative_to(root) / "packet.md", "file")
    run_path(root, folder.relative_to(root) / ".record-lock", "directory", missing=True)
    run_path(root, folder.relative_to(root) / ".events.tmp", "file", missing=True)
    require(read_json(packet_path) == packet, "session packet differs from study snapshot")
    events = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        validate_event(event, events, packet)
        require(event.get("session_id") == packet["session_id"] and
                event.get("study_hash") == packet["study_hash"], "event identity mismatch")
        require(event.get("sequence") == len(events) + 1, "event sequence mismatch")
        require(event.get("previous_hash") == (digest(events[-1]) if events else None), "event chain mismatch")
        artifacts = event["artifacts"]
        require(all(isinstance(a, dict) and set(a) == {"path", "sha256"} for a in artifacts),
                "invalid stored artifact records")
        require(artifact_records(root, folder, [a["path"] for a in artifacts]) == artifacts,
                "recorded artifact changed")
        events.append(event)
    return events


@contextmanager
def recording_lock(root, folder):
    lock = run_path(root, folder.relative_to(root) / ".record-lock", "directory", missing=True)
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("session recording is locked; reconcile interrupted writer before retry") from exc
    try:
        yield
    finally:
        lock.rmdir()


def record(root, sid, event):
    root, study = load_run(root)
    lookup = {key: (p, j) for key, p, j in sessions(study)}
    require(sid in lookup, "unknown session id")
    persona, journey = lookup[sid]
    folder = run_path(root, Path("sessions") / sid, "directory")
    packet = session_packet(study, sid, persona, journey)
    with recording_lock(root, folder):
        previous = load_events(root, folder, packet)
        validate_event(event, previous, packet)
        event = {key: event[key] for key in ("step", "kind", "summary", "source", "artifacts", "criteria", "status")
                 if key in event}
        event["artifacts"] = artifact_records(root, folder, event["artifacts"])
        event.update(session_id=sid, study_hash=digest(study), sequence=len(previous) + 1,
                     previous_hash=digest(previous[-1]) if previous else None)
        temporary = run_path(root, folder.relative_to(root) / ".events.tmp", "file", missing=True)
        with temporary.open("x", encoding="utf-8") as stream:
            for row in [*previous, event]:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        temporary.replace(folder / "events.jsonl")
    return event


def summarize(root):
    root, study = load_run(root)
    rows = []
    for sid, persona, journey in sessions(study):
        packet = session_packet(study, sid, persona, journey)
        events = load_events(root, root / "sessions" / sid, packet)
        observations = [e for e in events if e["kind"] == "observation"]
        status = events[-1]["status"] if events and events[-1]["kind"] == "outcome" else (
            "budget_exhausted_unclosed" if len(observations) >= packet["max_steps"] else
            "incomplete" if events else "not_run")
        rows.append({"session_id": sid, "persona_id": persona["id"], "journey_id": journey["id"],
                     "status": status, "steps": len(observations),
                     "evidence_sources": sorted({e["source"] for e in observations}),
                     "observations": observations,
                     "judgments": [e for e in events if e["kind"] == "judgment"],
                     "outcome": events[-1] if events and events[-1]["kind"] == "outcome" else None})
    return {"schema_version": 1, "study_id": study["id"], "study_hash": digest(study),
            "target": study["target"], "run": str(root),
            "limits": "Synthetic sessions. Browser evidence is submitted by the driver and integrity-checked, not independently authenticated. No human conversion, satisfaction or accessibility claims.",
            "counts": dict(Counter(row["status"] for row in rows)), "sessions": rows}


def markdown(report):
    lines = [f"# UX persona study: {report['study_id']}", "", report["limits"], "",
             f"Target revision: `{report['target']['revision']}`", "",
             "| Session | Status | Steps | Recorded evidence |", "|---|---|---:|---|"]
    for row in report["sessions"]:
        lines.append(f"| {row['session_id']} | {row['status']} | {row['steps']} | {', '.join(row['evidence_sources']) or 'none'} |")
    for row in report["sessions"]:
        lines += ["", f"## {row['session_id']}", ""]
        for event in [*row["observations"], *row["judgments"], *([row["outcome"]] if row["outcome"] else [])]:
            summary = event["summary"].replace("\n", " ")
            lines.append(f"- {event['kind']} ({event['source']}, step {event['step']}): {summary}")
            for artifact in event["artifacts"]:
                absolute = Path(report["run"]) / artifact["path"]
                lines.append(f"  - Evidence: [artifact](<{absolute}>); SHA-256 `{artifact['sha256']}`")
    return "\n".join(lines) + "\n"


def report(root, output):
    result = summarize(root)
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination / "report.json", result)
    (destination / "report.md").write_text(markdown(result), encoding="utf-8")
    return {"report": str(destination / "report.md"), "counts": result["counts"]}


def comparison_contract(study):
    contract = json.loads(json.dumps(study))
    contract.pop("target")
    contract.pop("id")
    # Only the origin may change between a baseline and preview deployment.
    for journey in contract["journeys"]:
        url = urlsplit(journey["start_url"])
        journey["start_url"] = [url.path, url.query, url.fragment]
    contract["personas"].sort(key=lambda row: row["id"])
    contract["journeys"].sort(key=lambda row: row["id"])
    return contract


def compare(before, after):
    _, old_study = load_run(before)
    _, new_study = load_run(after)
    require(comparison_contract(old_study) == comparison_contract(new_study),
            "incompatible studies: persona knowledge/experience, goals, paths, initial state, criteria or budgets changed")
    old, new = summarize(before), summarize(after)
    previous = {r["session_id"]: r for r in old["sessions"]}
    rows = []
    for row in new["sessions"]:
        baseline = previous[row["session_id"]]
        comparable = (baseline["status"] in STATUSES and row["status"] in STATUSES and
                      baseline["evidence_sources"] == row["evidence_sources"] == ["browser"])
        rows.append({"session_id": row["session_id"], "before": baseline["status"], "after": row["status"],
                     "comparable": comparable,
                     "step_delta": row["steps"] - baseline["steps"] if comparable else None,
                     "candidate_regression": comparable and baseline["status"] == "completed" and row["status"] != "completed"})
    return {"schema_version": 1, "before": old["target"], "after": new["target"],
            "limits": "Matched synthetic sessions; observational comparison, not causal or human validation. Driver/model and initial-state equivalence still need review.",
            "sessions": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate study JSON without effects")
    validate.add_argument("study", type=Path)
    planning = commands.add_parser("plan", help="write a fresh persona × journey run directory")
    planning.add_argument("study", type=Path)
    planning.add_argument("--output", required=True, type=Path)
    recording = commands.add_parser("record", help="append a validated event and bind its artifacts")
    recording.add_argument("run", type=Path)
    recording.add_argument("--session", required=True)
    recording.add_argument("--event", type=Path, required=True)
    reporting = commands.add_parser("report", help="audit evidence and report every planned session")
    reporting.add_argument("run", type=Path)
    reporting.add_argument("--output", required=True, type=Path)
    comparing = commands.add_parser("compare", help="compare compatible recorded runs")
    comparing.add_argument("before", type=Path)
    comparing.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            study = validate_study(read_json(args.study))
            result = {"valid": True, "study_hash": digest(study), "sessions": len(list(sessions(study)))}
        elif args.command == "plan":
            result = plan(read_json(args.study), args.output)
        elif args.command == "record":
            result = record(args.run, args.session, read_json(args.event))
        elif args.command == "report":
            result = report(args.run, args.output)
        else:
            result = compare(args.before, args.after)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
