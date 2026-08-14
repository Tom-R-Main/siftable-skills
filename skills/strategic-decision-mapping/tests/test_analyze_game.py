#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "analyze_game.py"
FIXTURES = SKILL / "tests" / "fixtures"


def run_fixture(name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(FIXTURES / name)],
        capture_output=True,
        text=True,
    )


class AnalyzeGameTests(unittest.TestCase):
    def test_prisoners_dilemma_finds_dominance_and_equilibrium(self) -> None:
        result = run_fixture("prisoners-dilemma.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["pure_strategy_nash_equilibria"],
            [{"column_strategy": "Defect", "payoffs": [1, 1], "row_strategy": "Defect"}],
        )
        self.assertEqual(
            payload["strictly_dominated"]["row"],
            [{"dominated_by": ["Defect"], "strategy": "Cooperate"}],
        )
        self.assertEqual(
            payload["strictly_dominated"]["column"],
            [{"dominated_by": ["Defect"], "strategy": "Cooperate"}],
        )
        self.assertEqual(payload["minimax_regret_strategies"]["row"][0]["strategy"], "Defect")

    def test_coordination_game_preserves_both_equilibria(self) -> None:
        result = run_fixture("coordination.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        equilibria = json.loads(result.stdout)["pure_strategy_nash_equilibria"]
        self.assertEqual(
            [(item["row_strategy"], item["column_strategy"]) for item in equilibria],
            [("Standard A", "Standard A"), ("Standard B", "Standard B")],
        )

    def test_rejects_an_incomplete_payoff_table(self) -> None:
        invalid = {
            "row_strategies": ["A", "B"],
            "column_strategies": ["X", "Y"],
            "payoffs": [[[1, 1], [0, 0]]],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json") as handle:
            json.dump(invalid, handle)
            handle.flush()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", handle.name],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("one row per row strategy", json.loads(result.stderr)["error"])


if __name__ == "__main__":
    unittest.main()
