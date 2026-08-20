# Documentation Index

- [Shared visualization presentation](modules/visualization.md) — business-neutral responsive Plotly/QWebEngine rendering reused by Market History and Algorithm Control.

- [Historical Backtesting and Simulation](modules/backtesting.md)
- [Market Factor Layer](modules/market-factors.md)

- [Central SQLite persistence](modules/central-persistence.md) — shared physical Schema v23 database, independent Store contracts, migrations and immutable generic/specialized P23-1/P26/P23-1F/P23-2A/P23-2B/P23-3A/P23-3B/P23-4A/P23-4B/P23-4C1/Decision/Risk/Capital/State/Target evidence.
- [Unified Algorithm Run History](modules/run-history.md) — durable NO EXECUTION Run/Stage/binding/message/relationship contracts and Run History Explorer.
- [Research Capital Allocation](modules/capital-allocation.md) — explicit USD research cash basis, protected reserves, exact asset-cash conservation, Schema v4 history and NO EXECUTION management GUI.
- [Asset State](modules/asset-state.md) — user-defined symbolic graphs, one open cycle per symbol, manual transitions, deterministic replay and Schema v5 history; no automatic financial meaning.
- [Target Position Research](modules/target-position.md) — existing immutable bounded finite-knot/manual/linked previews plus disabled P23-3A exact-P28-step linear/finite-exponential targets, structured Decimal/IEEE traces and Schema v18 provenance; only explicit P23-4A Decision consumption is approved.
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
| P23-2A symmetric reversal observation | `proposals/PROPOSAL-028-symmetric-reversal-observation-laboratory.md` | 已批准并实现为DISABLED的同倍数、两日确认/下一交易日生效观察实验室；Schema v17/110与回放/历史GUI已完成，不修改正式状态且无交易消费者 |
| P23-3A cycle-aware target position | `proposals/PROPOSAL-029-cycle-aware-bounded-target-position-laboratory.md` | 已批准并`IMPLEMENTED_VERIFIED_DISABLED`：复用现有Target Position所有者，精确P28 Result/Run/Step→反向线性/有限指数/饱和目标仓位，Schema v18与既有页面检查器；P30仅增加一项禁用AAPL测试配置和三条线性结果，P31是唯一获批的显式禁用Decision消费者 |
| AAPL P29 controlled validation | `proposals/PROPOSAL-030-aapl-p29-controlled-local-validation.md` | 已批准并完成`DRY_RUN`：精确复用现有三步AAPL P28证据、无刷新、使用对称禁用无默认参数和独立假设USD上下文；三条结果均为`VALID_LINEAR`且重启回放一致，无下游消费者 |
| P23-4A cycle-target Decision preview | `proposals/PROPOSAL-031-cycle-target-decision-preview.md` | 已批准并`IMPLEMENTED_VERIFIED_DISABLED`：显式P29 Result/Run→只读预检→共享精确差额判断→独立零/一Intent，保留旧Phase 5D历史；Schema v19、Run History、导出和既有Decision页兄弟检查器已验证，P32已增加三条禁用验证结果；唯一Risk入口是仍禁用且无数值批准的P23-4B |
| AAPL P31 controlled local validation | `proposals/PROPOSAL-032-aapl-p31-controlled-local-validation.md` | 已批准并完成`DRY_RUN`：三条精确既有P29来源先全部通过无写入预检，再分别创建三个本地`NO_EXECUTION` P31 Run；结果为两条`DECREASE`、一条`INCREASE`，重载/重放/导出/数据库增量验证通过，不刷新数据、不接Risk且不改变代码或Schema |
| P23-4B cycle-target Risk manual-review gate | `proposals/PROPOSAL-033-cycle-target-risk-manual-review-gate.md` | 已批准并`IMPLEMENTED_VERIFIED_DISABLED`：显式P31 Intent/Result/Run→无写入预检→类型独立Risk证据，与旧Phase 6A共享私有结构门内核；Schema v20四张表保持为空，只能人工审查/阻止，不含数值Risk、次数、封存或交易下游 |
| AAPL P33 controlled local validation | `proposals/PROPOSAL-034-aapl-p33-controlled-local-validation.md` | 已批准并完成DRY_RUN：三条精确P32/P31来源全部通过无写入来源与安全预检，随后建立三条独立NO_EXECUTION P33人工审查历史；不改代码/Schema、不产生批准、不含次数/封存或下游 |
| P23-4C1 frozen-asset admission | `proposals/PROPOSAL-035-versioned-frozen-asset-admission-and-daily-opportunity-semantics.md` | 已批准并`IMPLEMENTED_VERIFIED_DISABLED`：Asset State保存不可变ELIGIBLE/FROZEN控制事件，Risk对显式精确P33与有效控制证据执行封存阻止；Schema v21六表零回填，既有页面支持检查/比较/导出/Run导航；P23-4C2每日次数继续待定 |
| AAPL P35 eligible-path validation | `proposals/PROPOSAL-036-aapl-p35-eligible-path-controlled-local-validation.md` | 已批准并完成DRY_RUN：一条明确AAPL ELIGIBLE首事件加三条精确P34/P33→P35本地人工审查结果；重载/重放/导出/GUI/Run导航/幂等与精确增量通过，不改代码/Schema、不产生交易权限 |
| P23-2B mathematical cycle state | `proposals/PROPOSAL-037-versioned-mathematical-cycle-state-promotion.md` | 已批准并`IMPLEMENTED_VERIFIED_DISABLED`：Asset State内的独立、版本化、可重放多命名数学周期流，只晋升显式精确累计P28证据；Schema v22七表零回填、Run与既有页只读检查已完成；不改人工状态/P35控制/P29–P35历史，未创建真实股票流或交易权限 |
| AAPL P37 initialization/replay validation | `proposals/PROPOSAL-038-aapl-p37-mathematical-cycle-initialization-validation.md` | 已批准并完成`DRY_RUN`：精确AAPL P28来源创建一个禁用定义和一个无默认命名流；一个开放`DOWN`周期、三个快照/来源链、零转换、重启重放、GUI/Run、幂等和精确增量均通过；不代表真实AAPL反转或交易授权 |
| Explicit P37 → P29 target link | `proposals/PROPOSAL-039-explicit-mathematical-cycle-target-position-link.md` | 已批准并`IMPLEMENTED_VERIFIED_DISABLED`：显式成功P37 operation/Run/stream/terminal snapshot经精确P28语义交叉核对后调用不变P29，保存双操作ID、类型独立连接、Run关系/工件；Schema v23迁移零回填，P40后来增加一条显式验证连接，但仍不新增公式、默认选择、Decision/Risk消费者或执行权限 |
| AAPL P39 controlled target-link validation | `proposals/PROPOSAL-040-aapl-p39-mathematical-cycle-target-link-validation.md` | 已批准并完成受控本地`DRY_RUN`：精确冻结的AAPL P37/P28证据、现有禁用P29配置和假设`$100,000/$50,000`上下文创建一条P39连接和一条新P29结果；与终端P30完全相等，重载/Run/GUI/Open Run/双层幂等/精确增量/数据库检查通过，止于P31/Decision/Risk之前 |
| AAPL P40 → P31 Decision validation | `proposals/PROPOSAL-041-aapl-p40-p31-decision-validation.md` | 已批准并完成受控本地`DRY_RUN`：精确P40 P29 Result/Run经既有禁用P31得到`INTENT_CREATED / INCREASE / 3337.76295311476456362242970 USD`；备份、重载、重放、导出、Run/GUI、幂等和逐表增量通过，不新增算法、Schema、P33/Risk或执行权限 |
| AAPL P41 → P33 structural Risk validation | `proposals/PROPOSAL-042-aapl-p41-p33-structural-risk-validation.md` | 已批准并完成有界本地DRY_RUN：精确P41 Intent/Result/Run经既有禁用P33，产生三条锁定结构规则并停在`MANUAL_REVIEW_REQUIRED`；重载/重放/oracle/导出/Run/GUI/幂等/增量通过，不新增模块/算法/Schema/GUI、数值Risk、P35或执行权限 |
| P23-2A architecture decision | `decisions/ADR-0033-symmetric-reversal-observation-laboratory.md` | 记录同倍数、前向冻结、确认/生效分离、六表持久化及严格无交易消费者边界 |
| P23-1F daily volatility profile | `proposals/PROPOSAL-027-per-stock-daily-volatility-profile.md` | 已批准的完整P26/R1 v1.0.0日常波动档案公式、Schema v16、GUI、验证与严格非交易边界 |
| Modules | `modules/README.md` | 新模块审批和文档模板 |
| Market history | `modules/market-history.md` | 股票历史数据浏览器、缓存、GUI、配置与测试 |
| Single-asset factors | `modules/factors.md` | 策略中立Factor合同、时间安全、注册器，以及已实现但锁定禁用且无交易消费者的P23-1 R1专用研究公式 |
| Trading decision | `modules/trading-decision.md` | 既有FactorSnapshot决策合同与类型独立的linked-target adjustment研究合同；均无执行 authority |
| Risk control | `modules/risk-control.md` | TradeIntent之后、Order Construction之前的保守风险合同，Phase 6A结构门及Phase 6B/6C/6D三条有序数值研究预览；候选金额仍未批准且不预留资金 |
| Application orchestration | `modules/analysis-decision-pipeline.md` | Factor → Decision → Risk、exact Standardized State → Target Position、exact P28 step → P23-3A Target、linked target → specialized Decision、Phase 6A–6D Risk研究、P23-1E-A最新交易日预览及P26单股票历史频谱研究的单向编排 |
| Algorithm run history | `modules/run-history.md` | Searchable Run IDs, ordered stages, exact version bindings, persistent Factor/Decision/Risk/P23-3A evidence, exact source relationships, migrations and read-only Explorer |
| Execution environments | `modules/execution-environments.md` | Paper与Live两个同级、空白、禁用的未来执行环境边界 |
| Portfolio accounting | `modules/portfolio-accounting.md` | 统一会计领域、派生快照、核对与只读Query边界 |
| Asset state | `modules/asset-state.md` | 版本化符号状态、交易周期、人工转换、时间线和确定性重放；不含自动状态公式 |
| Trading ledger | `modules/trading-ledger.md` | 追加式订单操作与成交/现金事实记录边界 |
| Algorithm control GUI | `modules/algorithm-control-gui.md` | Registry驱动的组件、参数、版本配置、依赖验证、NO EXECUTION预览、P23-3兄弟Target Position检查器和审计管理面 |
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
