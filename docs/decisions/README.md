# Architecture Decision Records

- `ADR-0021-bounded-target-position-research.md`: accepted a separate disabled target-level owner with explicit manual USD inputs, bounded finite-knot Decimal interpolation, Schema v6 evidence and no Factor/State/Capital/Accounting/Decision/Risk/Execution consumer.

- `ADR-0020-manual-asset-state-history.md`: accepted a separate research state owner, user-defined symbolic graphs, one open cycle per symbol, manual transitions, deterministic replay, Schema v5 evidence and no financial/trading consumer.

- `ADR-0019-research-capital-allocation-conservation.md`: accepted a separate research planning owner, explicit cash basis, exact conserved/protected buckets, Schema v4 evidence and no dependency from factual Accounting or trading layers.

- `ADR-0018-factor-research-visualization.md`: accepted a business-neutral shared Plotly view, Factor-owned exact source-price evidence contracts, persistence-owned exact Bar join and explicit bounded export.

- `ADR-0017-factor-history-and-decision-trace.md`: accepted typed Factor-history queries, evaluation-time Decision condition/sizing traces and central SQLite Schema v3 while preserving Backtesting isolation and `NO_EXECUTION`.

- `ADR-0016-unified-algorithm-run-history.md`: accepted one neutral Run History lifecycle/query owner with central SQLite adapters and `NO_EXECUTION` research-only semantics.

- `ADR-0014-asset-market-factor-and-sizing.md`: accepted Asset/Market Factor separation and traceable Decision sizing.
- `ADR-0015-simulation-decision-journal.md`: accepted run-scoped daily evaluation evidence distinct from simulated fills and the operational Trading Ledger.

ADR 只用于影响项目长期结构的重要决定，不用于普通小改动。文件命名为 `ADR-NNNN-short-title.md`，编号递增。

## Lifecycle

1. 以 `Proposed` 记录问题、选项、建议和回滚方式。
2. 获得用户批准后改为 `Accepted`。
3. 已接受内容不得静默改写；改变决定时创建新 ADR，并将旧 ADR 标为 `Superseded` 且互相链接。
4. 未采用的提案标为 `Rejected`，保留决策背景。

## Required sections

`Status`、`Context`、`Options considered`、`Decision`、`Rationale`、`Consequences`、`Reversal`。

## Index

- [ADR-0021: Separate Bounded Target Position Research from Decision and Input Authorities](ADR-0021-bounded-target-position-research.md) — manual bounded target-level evidence, exact trace and no automatic upstream/downstream authority.

- [ADR-0020: Separate Manual Asset-State History from Trading Mathematics](ADR-0020-manual-asset-state-history.md) — exact definition/cycle identity, append-only manual transitions, deterministic replay and no automatic financial meaning.

- [ADR-0019: Separate Research Capital Allocation with Exact Conservation](ADR-0019-research-capital-allocation-conservation.md) — explicit research cash basis, protected reserves, zero-sum asset transfers, immutable evidence and no runtime consumer.

- [ADR-0012: Portfolio Accounting Domain with Separate Ledger and Accounting Modules](ADR-0012-portfolio-accounting-ledger.md) — one Portfolio domain, append-only fact authority, derived state, report-only reconciliation, and read-only consumers.

- [ADR-0011: Restricted Factor Authoring and Versioned Decision Selection](ADR-0011-restricted-factor-authoring.md) — GUI editing uses a restricted Factor-owned expression contract; versions are immutable/disabled and Decision selection is exact and non-executing.

- [ADR-0010: Separate Paper and Live Execution Boundaries](ADR-0010-paper-live-execution-boundaries.md) — one Execution owner with two empty, disabled sibling environment namespaces; no account/order behavior.

- [ADR-0009: Central SQLite Factor History](ADR-0009-central-sqlite-factor-history.md) — one physical local database, independent Store contracts, immutable Factor history and calculation-run audit.

- [ADR-0008: Change Admission and Conflict Prevention](ADR-0008-change-admission-and-conflict-prevention.md) — proposal-first admission, typed authority/contracts, disabled-by-default lifecycle and fail-closed Pipeline validation.

- `ADR-0001-project-governance.md` — Accepted — 建立语言无关治理基础与权限边界。
- `ADR-0002-market-history-stack.md` — Accepted — 股票历史数据浏览器的 Python、GUI、图表、Provider、存储和测试技术选择。
- `ADR-0003-project-compass.md` — Accepted — 以根目录 Compass 保存项目意图和当前语义，并强制 AI 前后自审。
- `ADR-0004-canonical-system-architecture.md` — Accepted — 以 `docs/architecture/OVERVIEW.md` 作为唯一主要架构来源，并用轻量架构测试保护依赖边界。
- `ADR-0005-two-stage-algorithm-architecture.md` — Accepted — 建立FactorSnapshot连接的单资产因子层与非执行交易决策层，并保留独立Risk/Execution边界。
- `ADR-0006-independent-risk-control-gate.md` — Accepted — 在TradeIntent与未来Order Construction之间建立只能保持/降低/阻止风险的独立可审计Risk Gate。
- `ADR-0007-algorithm-control-plane.md` — Accepted — 建立Registry/ParameterSchema驱动、版本化且NO EXECUTION的独立算法控制管理面。
