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

- `ADR-0001-project-governance.md` — Accepted — 建立语言无关治理基础与权限边界。
- `ADR-0002-market-history-stack.md` — Accepted — 股票历史数据浏览器的 Python、GUI、图表、Provider、存储和测试技术选择。
