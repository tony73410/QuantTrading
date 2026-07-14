# Development Workflow

## 0. Classify the task

Choose the lowest safe execution mode before broad inspection and report:

```text
Task mode:
Primary module:
Expected files changed:
Tests to run:
Documents to update:
```

| Mode | Use when | Inspection and validation | Documentation |
|---|---|---|---|
| FAST | Small, local, low-risk, normally one module | Directly relevant files and tests only | `EDIT_LOG` only unless behavior truly changes |
| STANDARD | Normal work within an existing module boundary | Compass and architecture summary; owner/direct dependencies; targeted unit/integration tests | affected module documentation and `EDIT_LOG` |
| DEEP | Major layer, contract, dependency, schema, broker/execution, Risk authority, order or Live change | full impact/permission review, migration/rollback plan, broad tests | Compass, canonical architecture and ADR where appropriate, plus affected documents/logs |

Do not use DEEP by habit. A local task does not justify a full-project audit. If a FAST/STANDARD task uncovers serious architecture, permission, contract, migration, financial-semantics or trading-safety conflict, stop and recommend DEEP escalation before expanding the task.

## 1. Inspect

阅读根 `PROJECT_COMPASS.md`、`AGENTS.md`、主要架构、文档索引、项目状态、相关模块/ADR、代码、最近相关编辑记录与 `logs/BUG_LOG.md`；确认 Stable Core、相关 Active Intent、Assumption Register、Open Decisions和已知缺陷；运行 `git status`（若已初始化），识别并保护用户未提交修改。涉及 Alpaca 时分别检查 Market Data、Paper Execution 和 Live Execution 角色，不得因存在 API Key 推断订单授权。

## 2. Restate

按照 `REQUIREMENT_INTERPRETATION.md` 区分用户目标、用户建议的方法、专业解释和推荐实现。简述需求、包含范围、不包含范围、必要假设和验收条件；对 Level C/D 歧义说明不同选择的实际后果，Level D 在用户明确选择前不得实施有风险行为。

## 3. Impact analysis

列出涉及文件/模块、接口、依赖、配置、数据和交易安全影响；判断是否触发审批。任何 Alpaca Live、自动订单提交、风险限制或执行接口变化都必须单独识别。

## 4. Plan

给出小步计划并完成简短 Pre-Implementation Compass Audit，说明真实目标、适用原则、必须保持的行为、假设、金融语义影响、审批需求和完成证据。触发审批事项时，按 `AGENTS.md` 的七项说明模板停止并等待批准。

## 5. Implement

进行最小、局部、可解释的修改；保持现有风格，不清理或重构无关内容，不覆盖用户工作。编辑过程中发现具有具体位置、现象、失败机制或证据的错误/潜在缺陷时，先分配Bug ID并记录；确认且可安全局部处理时修复根因，否则记录验证计划、规避方法和延期/审批原因。

## 6. Validate

运行最相关测试及必要的格式、类型、静态分析、接口兼容和 diff 检查。每个Bug修复应有回归测试；只有真实证据允许标记Fixed。交易相关配置还必须验证默认 Paper、Live 关闭、自动提交关闭、人工确认开启，以及测试不访问真实账户或提交订单。失败必须如实区分新引入与既有问题。

## 7. Document

同步受影响的模块文档、项目状态、必要的 Compass Evolving State/CHANGELOG/ADR。发现/调查/修复状态写入 `logs/BUG_LOG.md`，当前仍影响用户的问题摘要到 `KNOWN_ISSUES.md`，代码与文档修改追加到 `logs/EDIT_LOG.md`。仅在项目含义、默认值、架构、能力状态、重要假设、外部服务角色或安全边界变化时更新 Compass，避免无意义重复。

## 8. Report

报告 Summary、Files added/modified/deleted/renamed、Tests/checks executed、Results、Behavior/interface/dependency impact、Documentation updated、Known risks、Rollback method、Suggested commit message，并提供有依据的 Post-Implementation `Compass audit` 与 Bug discovery audit（发现/修复/延期ID；没有则明确说明）。

原则：一个任务，一组相关改动，一个清晰目的。
