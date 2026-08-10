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


def test_compass_verification_metadata_describes_current_p23_1_work() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    metadata = compass.split("```yaml", 1)[1].split("```", 1)[0]
    assert "last_verified_commit_or_working_tree_state:" in metadata
    assert "PROPOSAL-027" in metadata
    assert "v16/104" in metadata
    assert "local-only AAPL reuse" in metadata
    assert "no network, Trading client or account/position/order/fill access" in metadata
    assert "DISABLED/execution_allowed=false/live_allowed=false" in metadata


def test_compass_next_direction_names_latest_completed_proposal() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    next_direction = compass.split("## B17. Next Approved Direction", 1)[1].split(
        "## B18.", 1
    )[0]
    assert "PROPOSAL-026 is complete" in next_direction
    assert "PROPOSAL-027 is complete" in next_direction
    assert "No further implementation slice is currently approved" in next_direction
    assert "awaits explicit approval" not in next_direction


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


def test_proposal_027_is_approved_disabled_and_does_not_claim_trading_meaning() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-027-per-stock-daily-volatility-profile.md"
    ).read_text(encoding="utf-8")
    assert "Status: `APPROVED / IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "Approved by the user on 2026-08-06" in proposal
    assert "median(s[t,60], s[t,120], s[t,250])" in proposal
    assert "Spectral fields never enter" in proposal
    assert "It is not the eventual reversal boundary" in proposal
    assert "- `execution_allowed`: `true`" not in proposal
    assert "- `execution_allowed`: `false`" in proposal
    assert "- `live_allowed`: `false`" in proposal
    assert "docs/persistence/SCHEMA.md" not in proposal
    assert "docs/modules/central-persistence.md" in proposal


def test_roadmap_records_completed_p26_and_p27_validations() -> None:
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    assert "P26已完成一次另行批准的真实AAPL只读验证" in roadmap
    assert "PROPOSAL-027` P23-1F 已批准并完成" in roadmap
    assert "真实AAPL网络验证未执行" not in roadmap
    assert "真实AAPL历史研究仍需另一次明确验证指令" not in roadmap
    assert "仍等待用户明确批准" not in roadmap
