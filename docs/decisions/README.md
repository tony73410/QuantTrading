# Architecture Decision Records

ADR 只用于影响项目长期结构的重要决定，不用于普通小改动。文件命名为 `ADR-NNNN-short-title.md`，编号递增。

## Lifecycle

1. 以 `Proposed` 记录问题、选项、建议和回滚方式。
2. 获得用户批准后改为 `Accepted`。
3. 已接受内容不得静默改写；改变决定时创建新 ADR，并将旧 ADR 标为 `Superseded` 且互相链接。
4. 未采用的提案标为 `Rejected`，保留决策背景。

## Required sections

`Status`、`Context`、`Options considered`、`Decision`、`Rationale`、`Consequences`、`Reversal`。

## Index

- [ADR-0008: Change Admission and Conflict Prevention](ADR-0008-change-admission-and-conflict-prevention.md) — proposal-first admission, typed authority/contracts, disabled-by-default lifecycle and fail-closed Pipeline validation.

- `ADR-0001-project-governance.md` — Accepted — 建立语言无关治理基础与权限边界。
- `ADR-0002-market-history-stack.md` — Accepted — 股票历史数据浏览器的 Python、GUI、图表、Provider、存储和测试技术选择。
- `ADR-0003-project-compass.md` — Accepted — 以根目录 Compass 保存项目意图和当前语义，并强制 AI 前后自审。
- `ADR-0004-canonical-system-architecture.md` — Accepted — 以 `docs/architecture/OVERVIEW.md` 作为唯一主要架构来源，并用轻量架构测试保护依赖边界。
- `ADR-0005-two-stage-algorithm-architecture.md` — Accepted — 建立FactorSnapshot连接的单资产因子层与非执行交易决策层，并保留独立Risk/Execution边界。
- `ADR-0006-independent-risk-control-gate.md` — Accepted — 在TradeIntent与未来Order Construction之间建立只能保持/降低/阻止风险的独立可审计Risk Gate。
- `ADR-0007-algorithm-control-plane.md` — Accepted — 建立Registry/ParameterSchema驱动、版本化且NO EXECUTION的独立算法控制管理面。
