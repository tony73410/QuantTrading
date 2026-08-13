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


def test_compass_verification_metadata_preserves_history_and_records_p34() -> None:
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
    assert "active SQLite is v20/124" in metadata
    assert "market_history.before-p32-validation.20260812T0041129668196Z.sqlite3" in metadata
    assert "54/101/52/261→57/107/55/270" in metadata
    assert "0/0/0/0→3/3/3/3" in metadata
    assert "40e500b2-e263-4eeb-b2f1-d9da14451b9a" in metadata
    assert "2aa38bac-fe18-4bc1-bc94-d99b20fc6362" in metadata
    assert "b88b4752-cafd-47d4-ba27-1a81e1421927" in metadata
    assert "market_history.before-p34-validation.20260812T073041241799Z.sqlite3" in metadata
    assert "current Run/stage/symbol/binding/message counts are 60/113/58/279/289" in metadata
    assert "P33 is 3/3/9/3" in metadata
    assert "all three P33 results are MANUAL_REVIEW_REQUIRED" in metadata
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
    assert "Approved PROPOSAL-031/032 provide three exact independent AAPL P31 Decision previews" in project_state
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
    assert "PROPOSAL-034 complete; next slice not approved" in roadmap


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
    assert "PROPOSAL-034 complete; next slice not approved" in roadmap


def test_roadmap_records_completed_p26_through_p34() -> None:
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
    assert "P30测试值也不是默认值或AAPL投资建议" in roadmap
    assert "当前没有下一项已批准开发或验证工作" in roadmap
    assert "PROPOSAL-034 complete; next slice not approved" in roadmap
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
    assert "每日1/2次上限与股票封存没有并入P33" in roadmap
    assert "中央SQLite v18已纳入已验证实现" in roadmap
    assert "中央SQLite v16已纳入已验证实现" not in roadmap
    assert "真实AAPL网络验证未执行" not in roadmap
    assert "真实AAPL历史研究仍需另一次明确验证指令" not in roadmap
    assert "仍等待用户明确批准" not in roadmap
