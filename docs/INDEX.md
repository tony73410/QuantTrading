# Documentation Index

- [Shared visualization presentation](modules/visualization.md) — business-neutral responsive Plotly/QWebEngine rendering reused by Market History and Algorithm Control.

- [Historical Backtesting and Simulation](modules/backtesting.md)
- [Market Factor Layer](modules/market-factors.md)

- [Central SQLite persistence](modules/central-persistence.md) — shared physical Schema v8 database, independent Store contracts, migrations and immutable algorithm/link evidence.
- [Unified Algorithm Run History](modules/run-history.md) — durable NO EXECUTION Run/Stage/binding/message/relationship contracts and Run History Explorer.
- [Research Capital Allocation](modules/capital-allocation.md) — explicit USD research cash basis, protected reserves, exact asset-cash conservation, Schema v4 history and NO EXECUTION management GUI.
- [Asset State](modules/asset-state.md) — user-defined symbolic graphs, one open cycle per symbol, manual transitions, deterministic replay and Schema v5 history; no automatic financial meaning.
- [Target Position Research](modules/target-position.md) — immutable bounded finite-knot curves, manual and exact linked-source previews, structured Decimal traces and Schema v8 provenance; disabled with no trading consumer.
- [Manual Standardized Price State](modules/standardized-price-state.md) — Factor-owned exact manual USD price/reference/positive-scale normalization and Schema v7 history; Phase 5C may read one explicitly selected result without recalculation.

- [Change proposals](proposals/README.md) — canonical pre-implementation admission, conflict, activation, migration and rollback process.
- [Proposal template](proposals/PROPOSAL_TEMPLATE.md) — required identity, ownership, capability, contract, financial/safety and impact fields.

| Area | Entry | Purpose |
|---|---|---|
| Safe Factor authoring | `modules/factor-authoring.md` | Restricted expressions, immutable disabled Factor versions, and exact Decision Factor-version selection |
| Project compass | `../PROJECT_COMPASS.md` | AI 项目方向、当前语义、安全不变量、意图/假设和前后自审中心入口 |
| Current project | `project/PROJECT_STATE.md` | 当前阶段、能力、决策与限制 |
| Version checkpoints | `project/VERSION_HISTORY.md` | 已发布版本的行为、编辑目的、验证证据、当前关注目标与回滚摘要 |
| Direction | `project/ROADMAP.md` | 仅记录已批准或明确待决的阶段 |
| Terms | `project/GLOSSARY.md` | 项目统一术语 |
| Canonical architecture | `architecture/OVERVIEW.md` | 唯一主要架构来源：模块职责、依赖方向、数据流、不变量与扩展规则 |
| Module map | `architecture/MODULE_MAP.md` | 实际模块与文档的简要索引；不替代主要架构文件 |
| Dependencies | `architecture/DEPENDENCY_RULES.md` | 仓库级通用依赖原则；具体矩阵以主要架构文件为准 |
| Decisions | `decisions/README.md` | ADR 规则与索引 |
| Modules | `modules/README.md` | 新模块审批和文档模板 |
| Market history | `modules/market-history.md` | 股票历史数据浏览器、缓存、GUI、配置与测试 |
| Single-asset factors | `modules/factors.md` | 策略中立Factor合同、时间安全、注册器、无公式引擎与边界 |
| Trading decision | `modules/trading-decision.md` | 只消费FactorSnapshot的非执行决策合同、注册器、无规则引擎与边界 |
| Risk control | `modules/risk-control.md` | TradeIntent之后、Order Construction之前的保守风险合同、优先级和无数值规则引擎 |
| Application orchestration | `modules/analysis-decision-pipeline.md` | Factor → Decision → Risk及exact Standardized State → Target Position的单向编排和Execution停止边界 |
| Algorithm run history | `modules/run-history.md` | Searchable Run IDs, ordered stages, exact version bindings, persistent Factor/Decision/Risk evidence, Decision traces, migrations and read-only Explorer |
| Execution environments | `modules/execution-environments.md` | Paper与Live两个同级、空白、禁用的未来执行环境边界 |
| Portfolio accounting | `modules/portfolio-accounting.md` | 统一会计领域、派生快照、核对与只读Query边界 |
| Asset state | `modules/asset-state.md` | 版本化符号状态、交易周期、人工转换、时间线和确定性重放；不含自动状态公式 |
| Trading ledger | `modules/trading-ledger.md` | 追加式订单操作与成交/现金事实记录边界 |
| Algorithm control GUI | `modules/algorithm-control-gui.md` | Registry驱动的组件、参数、版本配置、依赖验证、NO EXECUTION预览和审计管理面 |
| Algorithm Idea Notebook | `modules/idea-notebook.md` | Algorithm Control内的本地纯文本想法记录；与Factor、Decision、Backtesting和Execution隔离 |
| Workflow | `development/WORKFLOW.md` | 每次任务的执行流程 |
| Debugging | `development/DEBUGGING.md` | 错误编号、日志、诊断命令和标准排查流程 |
| Validation and health | `development/VALIDATION.md` | 统一验证结果、错误严重度、Fail-Closed汇总和模块验证所有权 |
| Discovered bugs | `../logs/BUG_LOG.md` | 编辑、测试、审查和运行中发现的确认错误与可信潜在缺陷历史 |
| Current known issues | `../KNOWN_ISSUES.md` | 当前仍影响用户的问题、证据和临时规避方法摘要 |
| Requirement interpretation | `development/REQUIREMENT_INTERPRETATION.md` | 将日常表达转为准确、安全、可验证的需求 |
| Code | `development/CODING_STANDARDS.md` | 技术栈无关编码标准 |
| Tests | `development/TESTING_STANDARDS.md` | 行为验证要求 |
| Documentation | `development/DOCUMENTATION_STANDARDS.md` | 文档同步和状态标记规则 |

修改历史见根目录 `CHANGELOG.md` 和 `logs/EDIT_LOG.md`；前者面向重要变化，后者是只追加的开发事实记录。
