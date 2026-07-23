# ADR-0028: Read Explicit Research Capital Asset Cash Without Creating a Cash Authority

- Status: Accepted and implemented disabled
- Date: 2026-07-22
- Related: PROPOSAL-021, PROPOSAL-020, PROPOSAL-012, ADR-0027, ADR-0019

## Context

Phase 6C leaves one positive manual-review candidate after two ordered numerical Risk previews. Phase 3A separately owns immutable, exactly conserved `RESEARCH_INPUT` capital plans with protected reserves and symbol-specific `ASSET_CASH` buckets. Those balances are planning evidence, not Portfolio Accounting, broker, settled or spendable cash. Connecting the two domains must not let Risk choose a plan, mutate Capital, reserve money or create a complete approval.

## Options considered

1. Read factual account, broker or Portfolio Accounting cash. Rejected because no approved persistent factual adapter or settlement semantics exists.
2. Let Risk deduct or reserve Phase 3A balances. Rejected because Capital owns those events and a preview is not a fill or accounting fact.
3. Explicitly select one current conserved research plan/snapshot and copy its same-symbol asset-cash evidence through orchestration. Accepted as the smallest traceable, reversible bridge.

## Decision

Add a type-distinct Phase 6D `TargetAdjustmentResearchAssetCashPreviewResult`. One preview explicitly names one positive Phase 6C `MANUAL_REVIEW_REQUIRED` result, one Phase 3A `RESEARCH_INPUT` USD plan and that plan's exact latest valid snapshot. Orchestration resolves public read-only Capital and Phase 6C contracts; Risk receives a source-neutral immutable DTO and never imports Capital Allocation.

Preserve the inherited `MAX_TARGET_EXPOSURE_USD@1` and `MIN_RESEARCH_ASSET_CASH_USD@1` results as order-1/order-2 references. Evaluate only `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1` at order 3. For `INCREASE`, the candidate is the lesser of the positive Phase 6C candidate and the selected same-symbol `ASSET_CASH` balance; exact equality passes and zero asset cash blocks. For long-only `DECREASE`, preserve the candidate and report a hypothetical increased asset-cash balance. Exact Decimal arithmetic has no rounding, tolerance, price, quantity, fee or settlement meaning.

Every positive output remains `MANUAL_REVIEW_REQUIRED`; a zero increase is `BLOCKED_BY_RESEARCH_ASSET_CASH`. Every result and rule stores `research_cash_reserved=false` and warns that repeated previews can reuse the same balance. Persist all attempts/results/order-3 rules/source links in central SQLite Schema v13 and expose them inside the existing Risk page and Run History. No Risk-approved object or downstream consumer is created.

## Rationale

The chosen adapter connects existing explicit planning evidence while preserving one owner for Capital mutation and one future owner for factual accounting. Exact IDs, latest-snapshot validation, copied conservation/bucket evidence and non-reservation disclosure make the limitation reproducible without overstating financial authority.

## Consequences

- QuantTrade has three ordered numerical research preview rules but still no complete or production Risk approval.
- Phase 3A remains the sole owner of plans, buckets, transfers and snapshots; Risk is read-only.
- A preview can preserve, reduce or block a candidate but cannot reserve cash, prevent another preview from reusing it, record a fill or change a balance.
- Central SQLite v13 adds four append-only evidence tables without definitions or backfill. The verified real v12→v13 migration preserved the prior 70 non-internal tables/216,055 rows, added four empty tables plus one migration row, and passed integrity/foreign-key checks.
- Portfolio Accounting, Backtesting, Paper, Live, orders and fills remain unchanged and cannot consume the result.

## Verification

Domain tests cover equality, preserve/reduce/zero-block and DECREASE paths, exact conservation, non-expansion and absent approval fields. Repository/integration tests cover restart reload, idempotency, source/latest-snapshot validation, no Capital mutation, durable failures, Run artifacts/relationships and v12→v13 backup/rollback. GUI and architecture tests prove explicit typed delegation, no GUI formula/SQL, Risk/Capital dependency separation and absence of trading consumers.

## Reversal

Disable the preview command and hide the existing Risk subtab while retaining Schema v13 evidence for audit. Physical downgrade requires stopping writers, preserving v13, restoring `market_history.schema-v12-to-v13.20260722T195926466864Z.sqlite3` and using matching v12 code. Code-only downgrade against a v13 database is unsupported.
