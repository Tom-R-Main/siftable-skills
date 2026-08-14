#!/usr/bin/env python3
"""Analyze a supplied two-player normal-form payoff table.

This helper performs mechanical checks only. It does not infer strategies,
validate real-world payoffs, assign probabilities, or solve mixed equilibria.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any


def read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def emit(value: Any, stream: Any = sys.stdout) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False), file=stream)


def names(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or len(value) < 2:
        raise ValueError(f"{label} must contain at least two strategy names")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{label} must contain non-empty strings")
    cleaned = [item.strip() for item in value]
    if len(set(cleaned)) != len(cleaned):
        raise ValueError(f"{label} must contain unique names")
    return cleaned


def finite_number(value: Any, label: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{label} must be a finite number")
    return value


def parse_game(data: Any) -> tuple[str, str, list[str], list[str], list[list[tuple[float | int, float | int]]]]:
    if not isinstance(data, dict):
        raise ValueError("game must be a JSON object")

    row_player = data.get("row_player", "Row player")
    column_player = data.get("column_player", "Column player")
    if not isinstance(row_player, str) or not row_player.strip():
        raise ValueError("row_player must be a non-empty string")
    if not isinstance(column_player, str) or not column_player.strip():
        raise ValueError("column_player must be a non-empty string")

    row_strategies = names(data.get("row_strategies"), "row_strategies")
    column_strategies = names(data.get("column_strategies"), "column_strategies")
    raw_payoffs = data.get("payoffs")
    if not isinstance(raw_payoffs, list) or len(raw_payoffs) != len(row_strategies):
        raise ValueError("payoffs must have one row per row strategy")

    payoffs: list[list[tuple[float | int, float | int]]] = []
    for row_index, raw_row in enumerate(raw_payoffs):
        if not isinstance(raw_row, list) or len(raw_row) != len(column_strategies):
            raise ValueError(f"payoffs[{row_index}] must have one cell per column strategy")
        parsed_row: list[tuple[float | int, float | int]] = []
        for column_index, raw_cell in enumerate(raw_row):
            if not isinstance(raw_cell, list) or len(raw_cell) != 2:
                raise ValueError(f"payoffs[{row_index}][{column_index}] must be [row, column]")
            parsed_row.append(
                (
                    finite_number(raw_cell[0], f"payoffs[{row_index}][{column_index}][0]"),
                    finite_number(raw_cell[1], f"payoffs[{row_index}][{column_index}][1]"),
                )
            )
        payoffs.append(parsed_row)

    return row_player.strip(), column_player.strip(), row_strategies, column_strategies, payoffs


def best_response_indices(
    payoffs: list[list[tuple[float | int, float | int]]],
) -> tuple[list[list[int]], list[list[int]]]:
    row_best: list[list[int]] = []
    for column_index in range(len(payoffs[0])):
        best = max(payoffs[row_index][column_index][0] for row_index in range(len(payoffs)))
        row_best.append(
            [row_index for row_index in range(len(payoffs)) if payoffs[row_index][column_index][0] == best]
        )

    column_best: list[list[int]] = []
    for row_index, row in enumerate(payoffs):
        best = max(cell[1] for cell in row)
        column_best.append([column_index for column_index, cell in enumerate(row) if cell[1] == best])
    return row_best, column_best


def dominated_rows(
    payoffs: list[list[tuple[float | int, float | int]]], row_strategies: list[str]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for candidate in range(len(row_strategies)):
        dominators = []
        for alternative in range(len(row_strategies)):
            if candidate == alternative:
                continue
            if all(
                payoffs[alternative][column][0] > payoffs[candidate][column][0]
                for column in range(len(payoffs[0]))
            ):
                dominators.append(row_strategies[alternative])
        if dominators:
            results.append({"strategy": row_strategies[candidate], "dominated_by": dominators})
    return results


def dominated_columns(
    payoffs: list[list[tuple[float | int, float | int]]], column_strategies: list[str]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for candidate in range(len(column_strategies)):
        dominators = []
        for alternative in range(len(column_strategies)):
            if candidate == alternative:
                continue
            if all(row[alternative][1] > row[candidate][1] for row in payoffs):
                dominators.append(column_strategies[alternative])
        if dominators:
            results.append({"strategy": column_strategies[candidate], "dominated_by": dominators})
    return results


def extreme_strategies(
    strategies: list[str], values: list[float | int], key: str
) -> list[dict[str, float | int | str]]:
    best = max(values)
    return [{"strategy": strategy, key: value} for strategy, value in zip(strategies, values) if value == best]


def analyze(data: Any) -> dict[str, Any]:
    row_player, column_player, row_strategies, column_strategies, payoffs = parse_game(data)
    row_best, column_best = best_response_indices(payoffs)

    equilibria = []
    for row_index, row_strategy in enumerate(row_strategies):
        for column_index, column_strategy in enumerate(column_strategies):
            if row_index in row_best[column_index] and column_index in column_best[row_index]:
                equilibria.append(
                    {
                        "row_strategy": row_strategy,
                        "column_strategy": column_strategy,
                        "payoffs": list(payoffs[row_index][column_index]),
                    }
                )

    row_security = [min(cell[0] for cell in row) for row in payoffs]
    column_security = [
        min(payoffs[row_index][column_index][1] for row_index in range(len(payoffs)))
        for column_index in range(len(column_strategies))
    ]

    row_regret = []
    for row_index in range(len(row_strategies)):
        regrets = []
        for column_index in range(len(column_strategies)):
            best = max(row[column_index][0] for row in payoffs)
            regrets.append(best - payoffs[row_index][column_index][0])
        row_regret.append(max(regrets))

    column_regret = []
    for column_index in range(len(column_strategies)):
        regrets = []
        for row_index, row in enumerate(payoffs):
            best = max(cell[1] for cell in row)
            regrets.append(best - payoffs[row_index][column_index][1])
        column_regret.append(max(regrets))

    lowest_row_regret = min(row_regret)
    lowest_column_regret = min(column_regret)

    return {
        "players": {"row": row_player, "column": column_player},
        "best_responses": {
            "row": {
                column_strategies[column_index]: [row_strategies[index] for index in indices]
                for column_index, indices in enumerate(row_best)
            },
            "column": {
                row_strategies[row_index]: [column_strategies[index] for index in indices]
                for row_index, indices in enumerate(column_best)
            },
        },
        "pure_strategy_nash_equilibria": equilibria,
        "strictly_dominated": {
            "row": dominated_rows(payoffs, row_strategies),
            "column": dominated_columns(payoffs, column_strategies),
        },
        "security_strategies": {
            "row": extreme_strategies(row_strategies, row_security, "worst_case_payoff"),
            "column": extreme_strategies(column_strategies, column_security, "worst_case_payoff"),
        },
        "minimax_regret_strategies": {
            "row": [
                {"strategy": strategy, "maximum_regret": regret}
                for strategy, regret in zip(row_strategies, row_regret)
                if regret == lowest_row_regret
            ],
            "column": [
                {"strategy": strategy, "maximum_regret": regret}
                for strategy, regret in zip(column_strategies, column_regret)
                if regret == lowest_column_regret
            ],
        },
        "limitations": [
            "Results are conditional on the supplied strategies and payoffs.",
            "No mixed-strategy equilibrium, probability, or real-world payoff validation is performed.",
            "Sequential moves, private information, institutions, and bounded rationality require separate analysis.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="game JSON file, or - for standard input")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        emit(analyze(read_json(args.input)))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        emit({"error": str(exc)}, sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
