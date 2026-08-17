from __future__ import annotations

import re
from pathlib import Path


def test_active_intent_ids_are_unique() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    ledger = compass.split("## B11. Active Intent Ledger", 1)[1].split("## B12.", 1)[0]
    intent_ids = re.findall(r"^\| (INTENT-\d{3}) \|", ledger, flags=re.MULTILINE)
    assert intent_ids
    assert len(intent_ids) == len(set(intent_ids))


def test_proposal_files_are_continuous_unique_and_canonically_indexed() -> None:
    proposal_paths = sorted(Path("docs/proposals").glob("PROPOSAL-[0-9][0-9][0-9]-*.md"))
    proposal_ids = [
        int(re.match(r"PROPOSAL-(\d{3})-", path.name).group(1))
        for path in proposal_paths
    ]
    assert proposal_ids == list(range(1, 41))
    assert len(proposal_ids) == len(set(proposal_ids))
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    for proposal_id in proposal_ids:
        assert f"PROPOSAL-{proposal_id:03d}" in proposal_index


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


def test_compass_verification_metadata_preserves_history_and_records_p36() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    metadata = compass.split("```yaml", 1)[1].split("```", 1)[0]
    assert "last_verified_commit_or_working_tree_state:" in metadata
    assert "main feature commit 7ad1e1f" in metadata
    assert "PROPOSAL-028" in metadata
    assert "CHECKPOINT-20260810-006" in metadata
    assert "v17/110" in metadata
    assert "local-only AAPL reuse" in metadata
    assert "P27 result 6ae54c4a-8d3b-5ae1-8c82-4bb2fb5bbef5" in metadata
    assert "P23-2A" in metadata
    assert "one separately approved read-only AAPL validation" in metadata
    assert "VALID_NO_REVERSAL result 4447da24-2d25-5fbd-a7fd-fb0c3e501249" in metadata
    assert "no Trading client or account/position/order/fill access occurred" in metadata
    assert "DISABLED/execution_allowed=false/live_allowed=false" in metadata
    assert "main feature commit 7ad1e1f implements approved PROPOSAL-029" in metadata
    assert "v18/116" in metadata
    assert "formula 01d365bc-32b6-4ed8-b740-eab77a18206e" in metadata
    assert "configuration 02ca70ac-ad8f-495d-b7d9-50f609bd91db" in metadata
    assert "active counts 1/1/5/3/3/18" in metadata
    assert "market_history.before-p30-validation.20260811T0428081654404Z.sqlite3" in metadata
    assert "v19/120" in metadata
    assert "market_history.schema-v18-to-v19.20260811T191208556475Z.sqlite3" in metadata
    assert "market_history.schema-v19-to-v20.20260812T015933497519Z.sqlite3" in metadata
    assert "active SQLite v23/139 SHA-256" in metadata
    assert "Run/stage/symbol/binding/message 66/122/63/289/293" in metadata
    assert "market_history.schema-v21-to-v22.20260814T192644633800Z.sqlite3" in metadata
    assert "exactly seven empty P37 tables and zero backfill" in metadata
    assert "market_history.schema-v20-to-v21.20260813T042448969415Z.sqlite3" in metadata
    assert "P39 1/1" in metadata
    assert "market_history.before-p32-validation.20260812T0041129668196Z.sqlite3" in metadata
    assert "54/101/52/261→57/107/55/270" in metadata
    assert "0/0/0/0→3/3/3/3" in metadata
    assert "40e500b2-e263-4eeb-b2f1-d9da14451b9a" in metadata
    assert "2aa38bac-fe18-4bc1-bc94-d99b20fc6362" in metadata
    assert "b88b4752-cafd-47d4-ba27-1a81e1421927" in metadata
    assert "market_history.before-p34-validation.20260812T073041241799Z.sqlite3" in metadata
    assert "Run/stage/symbol/binding/message 66/122/63/289/293" in metadata
    assert "market_history.before-p38-validation.20260814T222041041676Z.sqlite3" in metadata
    assert "P37 1/2/1/1/3/0/3" in metadata
    assert "both P39 tables zero" in metadata
    assert "market_history.before-p36-validation.20260814T062213721771Z.sqlite3" in metadata
    assert "edc6ee3e-8d73-4606-8bf3-0643d8c024b3" in metadata
    assert "7d30a584541dc3e95db49f2bccdae8e644a25e93" in metadata
    assert "98ea64f73b869e1488ec2cf987734fbe88d341ed" in metadata
    assert "p40_validation_checkpoint" in metadata
    assert "446A471ABEC1857AE502BBDA461E9704B74C3F2B6AC8A3E8ABD9B0CD4150EDA6" in metadata
    assert "schema_v23_migration_checkpoint" in metadata
    assert "market_history.schema-v22-to-v23.20260815T095551214859Z.sqlite3" in metadata
    assert "one separately approved AAPL validation exists" in compass
    assert "no default, real-symbol validation or financial consumer" not in compass


def test_compass_next_direction_names_latest_completed_proposal() -> None:
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    next_direction = compass.split("## B17. Next Approved Direction", 1)[1].split(
        "## B18.", 1
    )[0]
    assert "PROPOSAL-026 is complete" in next_direction
    assert "PROPOSAL-027 is complete" in next_direction
    assert "PROPOSAL-028 is complete" in next_direction
    assert "PROPOSAL-029 is approved, implemented and verified disabled" in next_direction
    assert "No further implementation or validation slice is currently approved" in next_direction
    assert "only the explicit disabled P31 Decision consumer is approved" in next_direction
    assert "PROPOSAL-030" in next_direction
    assert "its five local operations are complete" in next_direction
    assert "All three are `VALID_LINEAR`" in next_direction
    assert "PROPOSAL-031 is approved, implemented and verified disabled" in next_direction
    assert "PROPOSAL-033 is approved, implemented and verified disabled" in next_direction
    assert "PROPOSAL-034 is approved and completed as a bounded `DRY_RUN`" in next_direction
    assert "PROPOSAL-035 option A and P35-D1–D10 are approved and implemented" in next_direction
    assert "PROPOSAL-036 is approved and completed as a bounded `DRY_RUN`" in next_direction
    assert "PROPOSAL-038 P38-D1–D10 is approved and completed as a bounded `DRY_RUN`" in next_direction
    assert "PROPOSAL-039 P39-D1–D12 is approved, implemented and verified disabled" in next_direction
    assert "P40 created one explicitly selected local AAPL validation row" in next_direction
    assert "no default selection, P31/Decision/Risk consumer" in next_direction
    assert "PROPOSAL-040 P40-D1–D10 is approved and completed" in next_direction
    assert "P39 is now `1/1`; no P31/Decision/Risk consumer" in next_direction
    assert "P23-4C2 daily opportunity counting remains pending and unapproved" in next_direction
    assert "P33 is its sole approved structural Risk consumer" in next_direction
    assert "numerical approval and every later consumer remain unapproved" in next_direction
    assert "PROPOSAL-032 is approved and completed as a bounded `DRY_RUN`" in next_direction
    assert "P32 itself created no Risk review or downstream behavior" in next_direction


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


def test_proposal_028_is_implemented_disabled_without_claiming_trading() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-028-symmetric-reversal-observation-laboratory.md"
    ).read_text(encoding="utf-8")
    assert "Status: `IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "Full PROPOSAL-028 package explicitly approved by the user" in proposal
    assert "explicitly selected A and A1" in proposal
    assert "threshold_log_distance = shared_multiplier × profile_log_scale" in proposal
    assert "candidate when down_reversal_distance[t] >= T" in proposal
    assert "candidate when up_reversal_distance[t] >= T" in proposal
    assert "confirmation_completed_session_count=2" in proposal
    assert "FORWARD_FROZEN_PROFILE" in proposal
    assert "formal `AssetStateTransition` facts" in proposal
    assert "Database: completed additive central SQLite v16/104→v17/110" in proposal
    assert "market_history.schema-v16-to-v17.20260810T192850337602Z.sqlite3" in proposal
    assert "Validation result: disabled definition `2954f4c8-c57c-4054-a535-738e7a868aaf`" in proposal
    assert "`VALID_NO_REVERSAL`" in proposal
    assert "- `execution_allowed`: `true`" not in proposal
    assert "- `execution_allowed`: `false`" in proposal
    assert "- `live_allowed`: `false`" in proposal


def test_proposal_029_is_implemented_disabled_and_preserves_target_boundaries() -> None:
    proposal_path = Path(
        "docs/proposals/PROPOSAL-029-cycle-aware-bounded-target-position-laboratory.md"
    )
    proposal = proposal_path.read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    assert "Status: `IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "explicitly approved PROPOSAL-029 and all recommended P29-D1–D10" in proposal
    assert "x = ln(P / R) / k" in proposal
    assert "P_linear_raw(x) = P_neutral - s*x" in proposal
    assert "beta / (exp(beta) - 1) = rho" in proposal
    assert "P29-D1" in proposal and "P29-D10" in proposal
    assert "central SQLite database from v17/110 to v18/116" in proposal
    assert "market_history.schema-v17-to-v18.20260811T031305700700Z.sqlite3" in proposal
    assert "all six new tables are empty" in proposal
    assert "Target Position must not import the Asset State implementation" in proposal
    assert "- `execution_allowed`: `true`" not in proposal
    assert "- `execution_allowed`: `false`" in proposal
    assert "- `live_allowed`: `false`" in proposal
    assert "later approved PROPOSAL-031 adds exactly one explicit disabled P23-4A Decision consumer" in proposal
    assert "PROPOSAL-029" in proposal_index
    assert "IMPLEMENTED_VERIFIED_DISABLED" in proposal_index
    assert "PROPOSAL-029-cycle-aware-bounded-target-position-laboratory.md" in docs_index
    assert "Later approved PROPOSAL-030 appended only one disabled AAPL test" in proposal
    assert "P30仅增加一项禁用AAPL测试配置和三条线性结果" in docs_index
    assert "P30 adds one disabled AAPL test configuration and three linear results" in project_state
    assert "P31 is the only explicit disabled Decision consumer" in project_state
    assert "六张P29表为空且无下游消费者" not in project_state


def test_proposal_030_records_approved_completed_local_validation_scope() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-030-aapl-p29-controlled-local-validation.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    assert "Status: `DRY_RUN`" in proposal
    assert "explicitly approved PROPOSAL-030" in proposal
    assert "4447da24-2d25-5fbd-a7fd-fb0c3e501249" in proposal
    assert "92a38cf4-3366-496d-ab18-7c9d01dfa1b6" in proposal
    assert "2116b50f-0a75-5476-8a7c-652b34a5cfe8" in proposal
    assert "7fca84f0-376f-5e86-9c99-a5081c8c85ef" in proposal
    assert "ac23677a-6d72-5257-a6b1-a2b5679e4be7" in proposal
    assert "`P_min` | `0.20`" in proposal
    assert "`s` | `0.05`" in proposal
    assert "`A` | `2.0`" in proposal
    assert "`B` | `4.0`" in proposal
    assert "All three known AAPL steps are expected to remain `LINEAR`" in proposal
    assert "P30-D1" in proposal and "P30-D8" in proposal
    assert "01d365bc-32b6-4ed8-b740-eab77a18206e" in proposal
    assert "02ca70ac-ad8f-495d-b7d9-50f609bd91db" in proposal
    assert "9cd2e18e-d07a-4e12-967d-37aeaf7e98c4" in proposal
    assert "a167b424-7b94-4be2-9f71-c96e502337e4" in proposal
    assert "eb386f12-6beb-4211-8933-ffe4b615bba6" in proposal
    assert "Every result is `VALID_LINEAR / LINEAR`" in proposal
    assert "formula `1`, configuration `1`, attempts `5`, results `3`, traces `3`, source links `18`" in proposal
    assert "no Market Data refresh" in proposal
    assert "Can it build or submit an order? No." in proposal
    assert "PROPOSAL-030" in proposal_index
    assert "approved `DRY_RUN`" in proposal_index
    assert "PROPOSAL-030-aapl-p29-controlled-local-validation.md" in docs_index


def test_proposal_031_is_implemented_disabled_and_preserves_decision_boundaries() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-031-cycle-target-decision-preview.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    assert "- Status: `IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "approved in full on 2026-08-11" in proposal
    assert "P31-D1" in proposal and "P31-D10" in proposal
    assert "preserve all existing Phase 5D public types and rows unchanged" in proposal
    assert "one Decision-owned pure exact-signed-difference kernel" in proposal
    assert "one explicit accepted P29 Result ID plus exact Run ID" in proposal
    assert "positive `INCREASE`, negative `DECREASE`, exact zero `HOLD`" in proposal
    assert "additive central SQLite v18→v19 with four P31 tables and zero backfill" in proposal
    assert "decision.cycle_target_adjustment_attempt@1" in proposal
    assert "Status: `PENDING`, `RUNNING`, `COMPLETED`, `INVALID_INPUT`, `FAILED`" in proposal
    assert "Status: `INTENT_CREATED`, `HOLD`" in proposal
    assert "`INTENT_CREATED`, `HOLD`, `INVALID_INPUT`, `FAILED`" not in proposal
    assert "invalid and failed operations preserve the attempt and Run messages" in proposal
    assert "no Phase 6A/Risk, cash, Backtesting, Accounting, Paper, Live or order consumer" in proposal
    assert "批准 PROPOSAL-031，采用推荐方案。" in proposal
    assert "All four P31 tables contain zero rows" in proposal
    assert "Deterministic recalculation replay" in proposal
    assert "market_history.schema-v18-to-v19.20260811T191208556475Z.sqlite3" in proposal
    assert "PROPOSAL-031" in proposal_index
    assert "`IMPLEMENTED_VERIFIED_DISABLED` P23-4A bridge" in proposal_index
    assert "PROPOSAL-031-cycle-target-decision-preview.md" in docs_index
    assert "DEC-017" in compass and "INTENT-041" in compass
    assert "P23-4A Cycle-Target Decision Preview" in compass
    assert "PROPOSAL-031 is approved, implemented and verified disabled" in compass
    assert "Implemented approved `PROPOSAL-031` P23-4A" in project_state
    assert "v19/120→v20/124" in project_state


def test_proposal_032_completed_the_bounded_p31_validation() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-032-aapl-p31-controlled-local-validation.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    assert "- Status: `DRY_RUN`" in proposal
    assert "P32-D1" in proposal and "P32-D8" in proposal
    assert "run read-only preflight for all three first" in proposal
    assert "any failure stops the entire validation before the first write" in proposal
    assert "9cd2e18e-d07a-4e12-967d-37aeaf7e98c4" in proposal
    assert "a167b424-7b94-4be2-9f71-c96e502337e4" in proposal
    assert "eb386f12-6beb-4211-8933-ffe4b615bba6" in proposal
    assert "`-1807.00189157667612249724698`" in proposal
    assert "`-2808.44497397660930460006057`" in proposal
    assert "`3337.76295311476456362242970`" in proposal
    assert "two `DECREASE` and one `INCREASE`" in proposal
    assert "stop before Risk" in proposal
    assert "algorithm_runs` | `54` | `57`" in proposal
    assert "P31 operation attempts | `0` | `3`" in proposal
    assert "批准 PROPOSAL-032，采用推荐方案执行三条本地验证。" in proposal
    assert "approved in full on 2026-08-11" in proposal
    assert "market_history.before-p32-validation.20260812T0041129668196Z.sqlite3" in proposal
    assert "80c98c9f-7146-4baf-8aff-368d1449df49" in proposal
    assert "270e400a-2ed0-4d30-aec2-cf568d2d559e" in proposal
    assert "7c4d1207-92d4-4e9b-b76a-2c755ec1d01b" in proposal
    assert "40e500b2-e263-4eeb-b2f1-d9da14451b9a" in proposal
    assert "2aa38bac-fe18-4bc1-bc94-d99b20fc6362" in proposal
    assert "b88b4752-cafd-47d4-ba27-1a81e1421927" in proposal
    assert "Fresh-process reload and deterministic recalculation replay matched" in proposal
    assert "Final counts are `57/107/55/270` and `3/3/3/3`" in proposal
    assert "PROPOSAL-032" in proposal_index
    assert "approved and completed `DRY_RUN`" in proposal_index
    assert "PROPOSAL-032-aapl-p31-controlled-local-validation.md" in docs_index
    assert "DEC-018" in compass and "INTENT-042" in compass
    assert "PROPOSAL-032 is approved and completed as a bounded `DRY_RUN`" in compass
    assert "Approved P32 created three exact independent AAPL validation results" in project_state
    assert "P33 is their only approved Risk boundary" in project_state
    assert "`PROPOSAL-032` 已获批准并完成`DRY_RUN`" in roadmap


def test_proposal_033_is_implemented_disabled_and_preserves_risk_authority() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-033-cycle-target-risk-manual-review-gate.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    assert "- Status: `IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "P33-D1" in proposal and "P33-D10" in proposal
    assert "compatible P31-specific sibling under the same Risk owner" in proposal
    assert "one private Risk-owned pure structural manual-review kernel" in proposal
    assert "one explicit accepted P31 Intent ID plus exact P31 Result/Run IDs" in proposal
    assert "SOURCE_CHAIN_INTEGRITY@1" in proposal
    assert "NON_EXECUTION_SAFETY_STATE@1" in proposal
    assert "NUMERICAL_RISK_POLICY_AVAILABILITY@1" in proposal
    assert "approved_notional_usd=None" in proposal
    assert "risk_approved_intent_id=None" in proposal
    assert "CYCLE_TARGET_RISK_REVIEW / NO_EXECUTION" in proposal
    assert "v19/120→v20/124 with four P33 tables and zero backfill" in proposal
    assert "no Phase 6B reuse, numerical Risk, daily count, freeze" in proposal
    assert "which authoritative event consumes a count" in proposal
    assert "Decision intent, Risk-reviewed candidate, planned order, submitted order or fill" in proposal
    assert "批准 PROPOSAL-033，采用推荐方案。" in proposal
    assert "no migration, code implementation or Risk run" in proposal
    assert "market_history.schema-v19-to-v20.20260812T015933497519Z.sqlite3" in proposal
    assert "all four P33 tables empty" in proposal
    assert "PROPOSAL-033" in proposal_index
    assert "`IMPLEMENTED_VERIFIED_DISABLED` P23-4B compatible Risk sibling" in proposal_index
    assert "PROPOSAL-033-cycle-target-risk-manual-review-gate.md" in docs_index
    assert "DEC-019" in compass and "INTENT-043" in compass
    assert "PROPOSAL-033 is implemented and verified disabled" in compass
    assert "Implemented approved `PROPOSAL-033`" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap


def test_proposal_034_records_completed_bounded_p33_validation() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-034-aapl-p33-controlled-local-validation.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    assert "- Status: `DRY_RUN`" in proposal
    assert "P34-D1" in proposal and "P34-D10" in proposal
    assert "all three source preflights and one current-safety precheck" in proposal
    assert "ALPACA_PAPER" in proposal
    assert "three independent `CYCLE_TARGET_RISK_REVIEW / NO_EXECUTION` Runs" in proposal
    assert "1807.00189157667612249724698" in proposal
    assert "2808.44497397660930460006057" in proposal
    assert "3337.76295311476456362242970" in proposal
    assert "`algorithm_runs` | `57` | `60`" in proposal
    assert "P33 rule results | `0` | `9`" in proposal
    assert "approved_notional_usd" in proposal and "risk_approved_intent_id" in proposal
    assert "If current safety is not exact" in proposal
    assert "批准 PROPOSAL-034，采用推荐方案执行三条本地 P33 验证。" in proposal
    assert "market_history.before-p34-validation.20260812T073041241799Z.sqlite3" in proposal
    assert "befe5720-7a2e-43aa-b90d-3084fa8eb149" in proposal
    assert "46179699-32a8-4451-8e7e-1b2163697956" in proposal
    assert "16bde342-bf0f-4850-9d61-62a3da3882c5" in proposal
    assert "Final Run/stage/symbol/binding/message counts are `60/113/58/279/289`" in proposal
    assert "P33 counts are `3/3/9/3`" in proposal
    assert "Deterministic retry of all three operation IDs created zero new rows" in proposal
    assert "PROPOSAL-034" in proposal_index
    assert "approved and completed bounded `DRY_RUN`" in proposal_index
    assert "PROPOSAL-034-aapl-p33-controlled-local-validation.md" in docs_index
    assert "DEC-020" in compass and "INTENT-044" in compass
    assert "PROPOSAL-034 is approved and completed as a bounded `DRY_RUN`" in compass
    assert "Approved P34 completed three exact local P33" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap


def test_proposal_035_records_approved_p23_4c1_and_defers_trade_count() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-035-versioned-frozen-asset-admission-and-daily-opportunity-semantics.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    assert "- Status: `IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "P35-D1" in proposal and "P35-D10" in proposal
    assert "Option A — recommended" in proposal
    assert "AssetTradingControlStatus@1" in proposal
    assert "`ELIGIBLE`" in proposal and "`FROZEN`" in proposal
    assert "Market Bar `trade_count`" in proposal
    assert "What must not consume a daily opportunity" in proposal
    assert "first positive fill consumes that opportunity" in proposal
    assert "P23-4C2 v1 should admit only an explicit per-symbol maximum of `1`" in proposal
    assert "v20/124→v21/130" in proposal
    assert "The user explicitly approved P35-D1–D10 and Option A" in proposal
    assert "ASSET_TRADING_CONTROL_CHANGE" in proposal
    assert "CYCLE_TARGET_ASSET_ADMISSION_REVIEW" in proposal
    assert "all six tables start empty" in proposal
    assert "market_history.schema-v20-to-v21.20260813T042448969415Z.sqlite3" in Path(
        "docs/modules/central-persistence.md"
    ).read_text(encoding="utf-8")
    assert "PROPOSAL-035" in proposal_index
    assert "`IMPLEMENTED_VERIFIED_DISABLED` for P23-4C1" in proposal_index
    assert "PROPOSAL-035-versioned-frozen-asset-admission" in docs_index
    assert "DEC-021" in compass and "INTENT-045" in compass
    assert "P23-4C1 Frozen-Asset Admission is `IMPLEMENTED_VERIFIED_DISABLED`" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap


def test_proposal_036_records_completed_bounded_p35_eligible_validation() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-036-aapl-p35-eligible-path-controlled-local-validation.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")

    assert "- Status: `DRY_RUN`" in proposal
    assert "P36-D1" in proposal and "P36-D10" in proposal
    assert "P36-D1–D10 approved and completed" in proposal
    assert "one first AAPL trading-control event with status `ELIGIBLE`" in proposal
    assert "1e18d4b2-bb93-581e-bed5-5d08bdece68b" in proposal
    assert "befe5720-7a2e-43aa-b90d-3084fa8eb149" in proposal
    assert "46179699-32a8-4451-8e7e-1b2163697956" in proposal
    assert "16bde342-bf0f-4850-9d61-62a3da3882c5" in proposal
    assert "`algorithm_runs` | `60` | `64`" in proposal
    assert "P35 admission rules | `0` | `9`" in proposal
    assert "Once the AAPL `ELIGIBLE` event is accepted" in proposal
    assert "P35_P33_SOURCE_VALID" in proposal
    assert "P35_TRADING_CONTROL_AVAILABLE" in proposal
    assert "P35_ELIGIBLE_MANUAL_REVIEW" in proposal
    assert "approved_notional_usd" in proposal and "risk_approved_intent_id" in proposal
    assert "\u6279\u51c6 PROPOSAL-036\uff0c\u91c7\u7528 P36-D1\u2013D10" in proposal
    assert "PROPOSAL-036" in proposal_index and "completed bounded `DRY_RUN`" in proposal_index
    assert "PROPOSAL-036-aapl-p35-eligible-path" in docs_index
    assert "DEC-022" in compass and "INTENT-046" in compass
    assert "edc6ee3e-8d73-4606-8bf3-0643d8c024b3" in proposal
    assert "4147db98-0e77-4eb0-ace6-6176df73864a" in proposal
    assert "market_history.before-p36-validation.20260814T062213721771Z.sqlite3" in proposal
    assert "64/120/62/286/292" in proposal
    assert "P37 1/2/1/1/3/0/3" in compass and "P39 1/1" in compass
    assert "Completed approved `PROPOSAL-036`" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap


def test_proposal_037_records_implemented_disabled_formal_mathematical_cycle_state() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-037-versioned-mathematical-cycle-state-promotion.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")

    assert "- Status: `IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "P37-D1–D12 explicitly approved for disabled implementation" in proposal
    assert "P37-D1" in proposal and "P37-D12" in proposal
    assert "asset_state.mathematical_cycle.p23_2b.v1" in proposal
    assert "EXACT_CUMULATIVE_P28_PROMOTION" in proposal
    assert "PROVISIONAL_NEW_CYCLE` → `COMMITTED_TO_NEW_CYCLE" in proposal
    assert "PROVISIONAL_NEW_CYCLE` → `DISCARDED_FOR_NEW_CYCLE" in proposal
    assert "OLD_DIRECTION_THROUGH_CONFIRMATION_CLOSE" in proposal
    assert "NEXT_EXPECTED_SESSION_START" in proposal
    assert "PRIOR_REVERSAL_EXTREME_REFERENCE" in proposal
    assert "v21/130→v22/137" in proposal
    assert "mathematical_cycle_state_definitions" in proposal
    assert "no automatic primary/active stream" in proposal
    assert "no runtime AAPL stream" in proposal
    assert "批准 PROPOSAL-037，采用 P37-D1–D12" in proposal
    assert "PROPOSAL-037" in proposal_index and "`IMPLEMENTED_VERIFIED_DISABLED`" in proposal_index
    assert "PROPOSAL-037-versioned-mathematical-cycle-state-promotion.md" in docs_index
    assert "ADR-0038-separate-mathematical-cycle-state.md" in Path(
        "docs/decisions/README.md"
    ).read_text(encoding="utf-8")
    persistence = Path("docs/modules/central-persistence.md").read_text(encoding="utf-8")
    assert "market_history.schema-v21-to-v22.20260814T192644633800Z.sqlite3" in persistence
    assert "v22/137" in persistence and "all seven P37 tables empty" in persistence
    assert "DEC-023" in compass and "INTENT-047" in compass
    assert "Main/origin commit `86c69d4` now publishes" in compass
    assert "Published validation commit `007bf39cdc896f64d4dd915be00ef00523a57822`" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap


def test_proposal_038_records_completed_bounded_aapl_p37_initialization() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-038-aapl-p37-mathematical-cycle-initialization-validation.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")

    assert "- Status: `DRY_RUN`" in proposal
    assert "P38-D1–D10 explicitly approved" in proposal
    assert "P38-D1" in proposal and "P38-D10" in proposal
    assert "86c69d48276c626bc77c33dffcbf5c54516e91b6" in proposal
    assert "4447da24-2d25-5fbd-a7fd-fb0c3e501249" in proposal
    assert "92a38cf4-3366-496d-ab18-7c9d01dfa1b6" in proposal
    assert "AAPL P23-2B research stream v1" in proposal
    assert "one open `DOWN` cycle" in proposal
    assert "P37 transitions | `0` | `0`" in proposal
    assert "validates initialization only, not a real AAPL reversal" in proposal
    assert "market_history.before-p38-validation.20260814T222041041676Z.sqlite3" in proposal
    assert "058e1979-fafa-5d1e-8dbc-b3eed1579b11" in proposal
    assert "f0bccf2c-ab66-5fc0-8427-27c1e344a5d2" in proposal
    assert "66/122/63/289/293" in proposal
    assert "1/2/1/1/3/0/3" in proposal
    assert "BUG-20260814-002" in proposal
    assert "approved `PROPOSAL-038`" in proposal
    assert "PROPOSAL-038" in proposal_index and "approved and completed bounded local `DRY_RUN`" in proposal_index
    assert "PROPOSAL-038-aapl-p37-mathematical-cycle-initialization-validation.md" in docs_index
    assert "DEC-024" in compass and "INTENT-048" in compass
    assert "After P38 was published at main/origin commit `47a8e27`" in compass
    assert "Approved PROPOSAL-038 P38-D1–D10 completed" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap


def test_proposal_039_records_implemented_disabled_explicit_p37_to_p29_link() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-039-explicit-mathematical-cycle-target-position-link.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    version_history = Path("docs/project/VERSION_HISTORY.md").read_text(encoding="utf-8")
    bug_log = Path("logs/BUG_LOG.md").read_text(encoding="utf-8")

    assert "- Status: `IMPLEMENTED_VERIFIED_DISABLED`" in proposal
    assert "P39-D1" in proposal and "P39-D12" in proposal
    assert "type-distinct explicit bridge, not a second target formula" in proposal
    assert "exact successful P37 operation ID, P37 Run ID, stream ID" in proposal
    assert "semantic equality before calling P29" in proposal
    assert "separately supplied deterministic target-operation ID" in proposal
    assert "v22/137 → v23/139" in proposal
    assert "mathematical_cycle_target_link_operations" in proposal
    assert "mathematical_cycle_target_position_links" in proposal
    assert "same P37 state and P29 inputs" in proposal
    assert "P38 AAPL `DOWN` initialization is a reversal or sell instruction" in proposal
    assert "disabled implementation and v22→v23 migration" in proposal
    assert "both P39 tables are zero" in proposal
    assert "批准 PROPOSAL-039，采用 P39-D1–D12" in proposal
    assert "PROPOSAL-039" in proposal_index and "`IMPLEMENTED_VERIFIED_DISABLED`" in proposal_index
    assert "PROPOSAL-006-historical-backtesting.md" in proposal_index
    assert "PROPOSAL-039-explicit-mathematical-cycle-target-position-link.md" in docs_index
    assert "DEC-025" in compass and "INTENT-049" in compass
    assert "published validation commit 007bf39cdc896f64d4dd915be00ef00523a57822" in compass
    assert "record completed PROPOSAL-040" in project_state
    assert "P39 `1/1`" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap
    assert "CHECKPOINT-20260814-013" in version_history
    assert "BUG-20260814-003" in bug_log


def test_proposal_040_records_completed_bounded_aapl_p39_validation() -> None:
    proposal = Path(
        "docs/proposals/PROPOSAL-040-aapl-p39-mathematical-cycle-target-link-validation.md"
    ).read_text(encoding="utf-8")
    proposal_index = Path("docs/proposals/README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    compass = Path("PROJECT_COMPASS.md").read_text(encoding="utf-8")
    project_state = Path("docs/project/PROJECT_STATE.md").read_text(encoding="utf-8")
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    version_history = Path("docs/project/VERSION_HISTORY.md").read_text(encoding="utf-8")
    edit_log = Path("logs/EDIT_LOG.md").read_text(encoding="utf-8")

    assert "- Status: `APPROVED / COMPLETED_DRY_RUN`" in proposal
    assert "explicitly approved `PROPOSAL-040` and P40-D1–D10" in proposal
    assert "P40-D1" in proposal and "P40-D10" in proposal
    assert "98ea64f73b869e1488ec2cf987734fbe88d341ed" in proposal
    assert "a934a4df-8869-54a6-8d54-eaa8a85046f9" in proposal
    assert "f0bccf2c-ab66-5fc0-8427-27c1e344a5d2" in proposal
    assert "3c2e3c34-e7f8-5179-b2fc-4282e57dfd2f" in proposal
    assert "4447da24-2d25-5fbd-a7fd-fb0c3e501249" in proposal
    assert "02ca70ac-ad8f-495d-b7d9-50f609bd91db@1" in proposal
    assert "`$100,000` capital / `$50,000` current position" in proposal
    assert "eb386f12-6beb-4211-8933-ffe4b615bba6" in proposal
    assert "`66/122/63/289/293`" in proposal
    assert "`1/1/5/3/3/18`" in proposal
    assert "| P39 operations | 0 | 1 | +1 |" in proposal
    assert "| P39 accepted links | 0 | 1 | +1 |" in proposal
    assert "Stop before P31, Decision, Risk" in proposal
    assert "批准 PROPOSAL-040，采用 P40-D1–D10" in proposal
    assert "approved and completed bounded local `DRY_RUN`" in proposal_index
    assert "PROPOSAL-040-aapl-p39-mathematical-cycle-target-link-validation.md" in docs_index
    assert "DEC-026" in compass and "INTENT-050" in compass
    assert "P39 Run `710f0030-af6f-48ad-af7b-2b58cfaba51e`" in compass
    assert "record completed PROPOSAL-040 and its bounded AAPL P39 local validation" in project_state
    assert "446A471ABEC1857AE502BBDA461E9704B74C3F2B6AC8A3E8ABD9B0CD4150EDA6" in project_state
    assert "Run/stage/symbol/binding/message is `68/126/65/294/293`" in project_state
    assert "P29 formula/configuration/operation/result/trace/source-link is `1/1/6/4/4/24`" in project_state
    assert "P39 operation/link is `1/1`" in project_state
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap
    assert "PLANNING-20260816-016" in version_history
    assert "VALIDATION-20260816-017" in version_history
    assert "CHECKPOINT-20260816-018" in version_history
    assert "EDIT-20260816-003" in edit_log
    assert "EDIT-20260816-004" in edit_log
    assert "007bf39cdc896f64d4dd915be00ef00523a57822" in proposal
    assert "05c63287-61b5-5878-b27b-5ed00c326ad9" in proposal
    assert "c22ce586-76b5-4a99-836b-cdb382c800de" in proposal
    assert "af98ea54-e142-454b-a543-0c0c3bd48c5f" in proposal
    assert "market_history.before-p40-validation.20260817T031119912252Z.sqlite3" in proposal
    assert "2056C3BBEB25F31A48C63193D804803EA18EB8C958E1679AB529CE88F7524F7D" in proposal
    assert "`68/126/65/294/293`" in proposal
    assert "`1/1/6/4/4/24`" in proposal
    assert "Final P39 operation/link: `1/1`" in proposal


def test_roadmap_records_completed_p26_through_p35() -> None:
    roadmap = Path("docs/project/ROADMAP.md").read_text(encoding="utf-8")
    assert "P26已完成一次另行批准的真实AAPL只读验证" in roadmap
    assert "PROPOSAL-027` P23-1F 已批准并完成" in roadmap
    assert "PROPOSAL-028` 的A/A1方向及完整实施包已由用户" in roadmap
    assert "PROPOSAL-028` 已批准、实现并验证" in roadmap
    assert "中央SQLite v17/110" in roadmap
    assert "PROPOSAL-029` 已批准、实现并验证" in roadmap
    assert "Schema v18/116" in roadmap
    assert "PROPOSAL-030` 已批准并完成 `DRY_RUN`" in roadmap
    assert "三条结果均为`VALID_LINEAR`" in roadmap
    assert "P30测试值不是默认值或AAPL投资建议" in roadmap
    assert "当前没有下一项已批准开发或验证工作" in roadmap
    assert "PROPOSAL-040 completed; next work unapproved; P23-4C2 pending" in roadmap
    assert "`PROPOSAL-031` 已批准并按P31-D1–D10实现" in roadmap
    assert "中央SQLite v19/120已验证" in roadmap
    assert "`PROPOSAL-032` 已获批准并完成`DRY_RUN`" in roadmap
    assert "两条`DECREASE`和一条`INCREASE`" in roadmap
    assert "重启重放、Run上下游、临时导出、逐表增量" in roadmap
    assert "`PROPOSAL-033` 已批准并按P33-D1–D10实现" in roadmap
    assert "中央SQLite v20/124和全部检查能力已验证" in roadmap
    assert "`PROPOSAL-034` 已获批准并完成`DRY_RUN`" in roadmap
    assert "三条结果均为`MANUAL_REVIEW_REQUIRED`" in roadmap
    assert "P33/P31/P29/P28 Run导航、幂等重试、逐表增量" in roadmap
    assert "PROPOSAL-035` 选项A与P35-D1–D10已经用户批准" in roadmap
    assert "中央SQLite已从v20/124增量迁移至v21/130" in roadmap
    assert "P23-4C2继续待定且未批准" in roadmap
    assert "中央SQLite v18已纳入已验证实现" in roadmap
    assert "中央SQLite v16已纳入已验证实现" not in roadmap
    assert "真实AAPL网络验证未执行" not in roadmap
    assert "真实AAPL历史研究仍需另一次明确验证指令" not in roadmap
    assert "仍等待用户明确批准" not in roadmap
