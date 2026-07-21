from __future__ import annotations

import re
from pathlib import Path


def test_active_intent_ids_are_unique() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    ledger = compass.split("## B11. Active Intent Ledger", 1)[1].split("## B12.", 1)[0]
    intent_ids = re.findall(r"^\| (INTENT-\d{3}) \|", ledger, flags=re.MULTILINE)
    assert intent_ids
    assert len(intent_ids) == len(set(intent_ids))


def test_canonical_architecture_invariants_are_monotonic_and_unique() -> None:
    architecture = Path("docs/architecture/OVERVIEW.md").read_text(encoding="utf-8")
    invariants = architecture.split("## Architecture Invariants", 1)[1].split(
        "Changing an invariant requires", 1
    )[0]
    numbers = [
        int(value)
        for value in re.findall(r"^(\d+)\. ", invariants, flags=re.MULTILINE)
    ]
    assert numbers == list(range(1, len(numbers) + 1))


def test_compass_verification_metadata_describes_current_phase_five_c_work() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    metadata = compass.split("```yaml", 1)[1].split("```", 1)[0]
    assert "last_verified_commit_or_working_tree_state:" in metadata
    assert "Phase 5C exact standardized-state-to-Target-Position adapter" in metadata
    assert "central Schema v8" in metadata
    assert "v7→v8 backup/migration" in metadata
    assert "zero default linked rows" in metadata


def test_compass_does_not_deny_verified_research_backtesting() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    stale_claim = (
        "implement a trading strategy, indicator strategy, signal, backtest, "
        "investment advice, or profit guarantee"
    )
    assert stale_claim not in compass
    assert "isolated research-only Backtesting exists" in compass


def test_proposal_index_does_not_claim_local_factor_history_is_inactive() -> None:
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    assert "implementation remains inactive" not in proposal_index
    assert "active local `NO_EXECUTION` preview evidence" in proposal_index
