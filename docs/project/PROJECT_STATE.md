# Project State

## Current phase

Governed stock historical data browser plus an independent Algorithm Control Center with Phase 1–2B research observability, Phase 3A Research Capital Allocation, Phase 4A manual Asset State history and Phase 5A bounded Target Position research. Central Schema v6 preserves explicit conserved research cash, symbolic state history and exact manual target-level evidence. Portfolio Accounting remains an independent in-memory fact-replay scaffold. Paper/Live Execution remain declaration-only; no active production algorithm, broker account connection, order, or execution behavior exists.

## Implemented capabilities

- Algorithm Idea Notebook is `IMPLEMENTED_VERIFIED` as an isolated local-only page: notes support title, plain text, tags, archive and restore, but cannot register or invoke Factor, Decision, Risk, Simulation, Portfolio Accounting or Execution behavior.

- Asset Factor is explicitly single-stock. Market Factor phase one provides immutable explicit-universe aggregation over exact Asset Factor versions with complete-input enforcement.
- Decision Sizing phase one provides fixed USD, cash/equity/position percentages, exit-all and restricted Decimal expressions over Asset/Market Factors plus read-only account/position fields. Risk contracts trace and constrain requested notional; no production Risk values were added.

- Historical Backtesting is `IMPLEMENTED_VERIFIED` for the approved research-only SMA20/50 baseline: all 110 locally cached symbols completed a one-year offline run, with isolated simulated trades, cash, holdings, equity curve, JSON results, GUI and CLI. Immutable records now reject inconsistent Decimal arithmetic, run identity, trace/journal evidence and result-file identity before display or persistence. It is not Paper Trading or production strategy evidence.
- User-named Simulation Strategies are implemented as immutable local versions that select exact buy/sell Decision versions and their exact Factor dependencies. Saved versions are selectable from Backtesting; the first-phase universe/allocation/fill/cost semantics remain fixed and execution authority remains false.

- QuantTrade主控制台：`python -m quant_trading`显示三个独立子GUI入口，并通过紧凑的可信目录直达Algorithm Control全部15个现有核心页签，包括Capital Allocation、Asset State、Target Position和Run History Explorer；子功能仍在独立进程及其所有者页面中运行，主菜单不包含业务/交易逻辑。
- Central SQLite Schema v6 reuses `runtime/data/market_history.sqlite3` for independent Market/Run/Factor/Decision/Risk/Capital/State/Target evidence. Verified v1→v2→v3→v4→v5→v6 backups/migrations preserve 215,340 Market Bars plus 365 Fetch History rows. The v6 migration created no default Target Position definition, knot, preview or operation. No production Factor, capital, state or target consumer is active.
- Unified Run History is `IMPLEMENTED_VERIFIED` for local research previews: Factor Preview, Decision Preview and full Pipeline Dry Run store ordered stages, exact bindings, software/Session/Request identity, warnings/errors and typed artifacts; Run History Explorer is read-only and every run is `NO_EXECUTION`.
- Phase 2A Factor/Decision research inspection is `IMPLEMENTED_VERIFIED`: Factor history supports bounded filters over successful, invalid and failed attempts plus exact-version tabular comparison; restricted Decision evaluations persist condition and exact sizing-input traces; read-only GUI subtabs expose details and `Open Run`. Legacy rows without evidence remain `TRACE_NOT_CAPTURED` and are never reconstructed.
- Phase 2B Factor research visualization/export is `IMPLEMENTED_VERIFIED`: one exact Factor version is overlaid only with the stored Bar at its exact `source_data_end_utc` and exact dimensions; invalid/failed/missing or valid non-numeric evidence remains gaps/typed status markers without coercion; CSV/JSON copies preserve Decimal/UTC/ID/status evidence and require explicit overwrite. Market History and Algorithm Control share a presentation-only Plotly view. Schema v3 is unchanged.
- Phase 3A Research Capital Allocation is `IMPLEMENTED_VERIFIED` but disabled/unconsumed: user-entered `RESEARCH_INPUT` USD basis, exactly one protected locked reserve, one protected tactical reserve, unique asset cash buckets, exact Decimal conservation, manual asset-to-asset transfers, durable failures, Schema v4 restart reload, Allocation Runs, owner GUI and Launcher shortcut. It is not factual Accounting/broker cash and no downstream module reads it.
- Phase 4A Asset State is `IMPLEMENTED_VERIFIED` but disabled/unconsumed: immutable user-defined symbolic graphs, one open cycle per symbol, explicit manual transitions, start/close events, durable invalid/failed attempts, idempotent operation identity, Schema v5 restart reload, deterministic replay, State Runs, owner GUI and Launcher shortcut. Labels have no built-in financial meaning and no downstream module reads them.
- Phase 5A Target Position is `IMPLEMENTED_VERIFIED` but disabled/unconsumed: immutable user-defined monotone finite-knot curves, explicit manual scalar/USD basis/current value, exact Decimal clamp/interpolation, structured target/difference traces, durable invalid/failed attempts, Schema v6 restart reload, Target Position Runs, owner GUI/chart and Launcher shortcut. No upstream adapter or downstream module reads it.

- 仓库级工作规则、文档索引、ADR 机制、编辑日志规范及目录职责说明。
- 根目录 `PROJECT_COMPASS.md`：保存用户批准的 Stable Core、当前系统语义、Active Intent、Assumption Register、Open Decisions、漂移检测及 AI 实施前后审查规则；详见 ADR-0003。
- `docs/architecture/OVERVIEW.md` 是唯一主要架构来源：基于实际代码记录模块职责/非职责、公共接口、依赖矩阵、数据流、不变量、变更影响范围和已知漂移风险；详见 ADR-0004。
- 需求解释协议：区分用户目标与建议方法，按风险等级处理歧义，并要求通俗汇报和持久记录重要假设。
- PySide6 桌面控制面板：覆盖 11 个 GICS 大类行业、共 110 个常见美股代码的本地前缀自动补全，以及粒度对应的快捷/自定义范围、10/30 分钟、1 小时、日/周/月、复权、Feed、K线/折线/OHLC、字段、成交量、范围滑块及更新控制；已有图表后切换时间范围或粒度会自动后台加载。
- Alpaca Market Data Provider（分钟/小时默认限纽约常规时段）、SQLite 本地缓存、Coverage/Fetch History、粒度隔离、缺失区间补齐、尾部重叠刷新、离线回退和 Plotly 交互图表。
- 应用角色明确分离：主要行情数据提供商和计划主要券商均为 Alpaca，默认目标环境为 `ALPACA_PAPER`。
- `quant_trading.execution.paper`与`.live`已建立为同级空白、禁用的环境边界；Paper/Live账户、持仓、订单和执行能力仍为 **Not implemented**，自动下单关闭、Live关闭、人工确认开启。
- Fidelity 保留为非默认的可选手动兼容状态；未连接、未启用且不读取凭据。
- pytest 单元、集成与架构测试；架构测试使用标准库 AST 检查循环/非法跨层 import，真实网络被禁止。
- 统一 Debug 基础设施：稳定 Error Code、Session ID/Request ID、用户友好诊断、Secret 脱敏、UTC 结构化 `app.log`/`error.log` 轮转日志、全局/Worker 异常记录和只读诊断命令。
- 统一Validation/Health基础：模块自有规则返回共享Severity/Status/Issue合同；注册器异常记录`QT-INTEGRITY-001`并fail closed；本地diagnostics汇总`HEALTHY/DEGRADED/BLOCKED/CRITICAL/UNKNOWN`，其中BLOCKED/CRITICAL/UNKNOWN不允许自动执行。
- `logs/BUG_LOG.md` 是编辑、测试、审查和运行中发现的确认错误与可信潜在缺陷的唯一开发历史；未来任务必须报告发现/修复/延期状态，Fixed必须有真实验证证据。
- 三层算法基础：`quant_trading.factors`输出版本化、策略中立FactorSnapshot；`quant_trading.decision`只消费公开FactorSnapshot并输出不可变、非执行TradeIntent；`quant_trading.risk`独立裁决并输出RiskDecision，只能保持/降低/阻止风险；`quant_trading.orchestration`组织本地数据、Factor、Decision和Risk调用顺序。当前没有生产激活的算法或数值Risk Policy。
- 独立算法控制中心：Registry驱动元数据与通用参数界面；Factor支持归档/弃用/恢复及本地SQLite数据预览，Decision支持受限数值比较规则的不可变版本，Pipeline支持NO EXECUTION Risk dry run，Execution页只读显示Paper/Live均未实现。所有用户组件默认禁用。
- Scheme A Factor authoring：GUI可保存受限表达式为不可变Factor版本、归档/弃用/恢复版本并用本地缓存预览；Decision GUI保存精确Factor版本、比较符、阈值和明确动作的禁用规则版本。不能执行任意Python，不包含数量/仓位，也不会自动产生订单。
- 交易能力：**Not implemented**；Execution目录只声明环境边界，不提供任何公共接口或运行路径。
- Portfolio Accounting：一个统一领域内分离append-only Trading Ledger、Accounting replay、report-only Reconciliation和read-only Queries。当前仅内存实现现金/确认成交净多头数量重放；完整成本基础、估值和P&L未实现。

- Change Admission / Conflict Prevention is implemented in `quant_trading.algorithm_control`: typed component ownership, capabilities and public-contract declarations; disabled-by-default activation evidence; registration conflict checks; fail-closed pre-run Pipeline validation; and a read-only GUI Conflict Center. No production algorithm was activated.

## Active modules

- `quant_trading.run_history` — neutral top-level Run lifecycle, ordered stage/binding/message and typed query contracts; see `docs/modules/run-history.md`.
- `quant_trading.persistence` — shared SQLite Schema v6/migration boundary plus Run History, Factor, Decision, Risk, Capital Allocation, Asset State and Target Position evidence/query adapters; see `docs/modules/central-persistence.md`.
- `quant_trading.capital_allocation` — explicit research plans, protected buckets, exact conserved transfers/snapshots and public Store/query contracts; see `docs/modules/capital-allocation.md`.
- `quant_trading.asset_state` — immutable symbolic definitions, per-symbol cycles, manual transitions, snapshots, attempts and replay contracts; see `docs/modules/asset-state.md`.
- `quant_trading.target_position` — immutable bounded curve definitions, exact manual previews, structured traces, attempts and query contracts; see `docs/modules/target-position.md`.
- `quant_trading.visualization` — business-neutral responsive Plotly/QWebEngine Figure renderer used by Market History and Algorithm Control; see `docs/modules/visualization.md`.

- `quant_trading.market_history` — 股票历史数据浏览器；见 `docs/modules/market-history.md`。
- `quant_trading.factors` — 单资产因子合同、注册器和无公式引擎；见 `docs/modules/factors.md`。
- `quant_trading.decision` — 非执行交易决策合同、注册器和无规则引擎；见 `docs/modules/trading-decision.md`。
- `quant_trading.risk` — 独立风险合同、注册器、保守组合引擎和Risk-approved类型门；见 `docs/modules/risk-control.md`。
- `quant_trading.orchestration` — Factor → Decision及Factor → Decision → Risk接口级编排；见 `docs/modules/analysis-decision-pipeline.md`。
- `quant_trading.portfolio_accounting` — Trading Ledger事实、Accounting派生状态、Reconciliation和Query合同/内存骨架；见 `docs/modules/portfolio-accounting.md`、`docs/modules/trading-ledger.md`。
- `quant_trading.execution.paper` / `.live` — 空白、禁用且互相隔离的未来模拟/真实执行边界；见 `docs/modules/execution-environments.md`。
- `quant_trading.algorithm_control` — 组件元数据、版本配置、验证、安全预览、审计与独立桌面GUI；见 `docs/modules/algorithm-control-gui.md`。
- `quant_trading.algorithm_control.idea_notebook` — 被动本地笔记模型/Store/Service及GUI页面；见 `docs/modules/idea-notebook.md`。

## Module status inventory

| Area | Status | Current evidence |
|---|---|---|
| Market Data | `IMPLEMENTED_VERIFIED` | 模型/Provider/Service/GUI单元与集成测试、离线启动和本地加载 |
| Local Storage | `IMPLEMENTED_VERIFIED` | SQLite schema/store测试、首次/既有数据库初始化、integrity check |
| GUI | `IMPLEMENTED_VERIFIED` | 主Launcher、三个子GUI及Algorithm Control 15个核心直达入口的offscreen/GUI回归；物理显示QA仍未完成 |
| Charting | `IMPLEMENTED_VERIFIED` | Market/Factor Plotly builders、共享renderer、精确缺失gap与GUI集成测试 |
| Configuration | `IMPLEMENTED_VERIFIED` | 缺凭据/缺目录/默认安全角色验证 |
| Logging | `IMPLEMENTED_VERIFIED` | UTC轮转日志、异常hook、脱敏测试与实际错误堆栈 |
| Diagnostics | `IMPLEMENTED_VERIFIED` | 本地只读诊断运行通过；网络连接本次未验证 |
| Factor Layer | `PARTIALLY_IMPLEMENTED` | 公共合同、Engine、受限表达式和本地预览；无批准生产Factor |
| Trading Decision Layer | `PARTIALLY_IMPLEMENTED` | 公共合同、Engine、受限版本规则；无生产Policy/订单 |
| Risk Layer | `PARTIALLY_IMPLEMENTED` | 公共合同、Engine、保守Fake验证；无数值规则/账户连接 |
| Execution Layer | `SCAFFOLD_ONLY` | 空Paper/Live包和架构测试 |
| Algorithm Control GUI | `IMPLEMENTED_VERIFIED` | 本地版本、预览、审计、研究历史、Capital Allocation、Asset State与Target Position owner pages；无执行权限 |
| Algorithm Idea Notebook | `IMPLEMENTED_VERIFIED` | 独立JSON、服务与GUI回归测试；无任何业务模块输出 |
| Trading Ledger | `SCAFFOLD_ONLY` | 内存append-only/idempotency合同与测试 |
| Portfolio Accounting | `SCAFFOLD_ONLY` | 内存现金/净多头replay和只读快照 |
| Reconciliation | `SCAFFOLD_ONLY` | 内存差异报告；无Broker同步/自动修正 |
| Research Capital Allocation | `IMPLEMENTED_VERIFIED` | 显式研究现金、受保护资金桶、精确守恒、Schema v4重载和GUI；inactive/unconsumed |
| Research Asset State | `IMPLEMENTED_VERIFIED` | 用户定义图、每股单一开放周期、人工转换、Schema v5重载与确定性重放；inactive/unconsumed |
| Research Target Position | `IMPLEMENTED_VERIFIED` | 用户定义单调有限节点曲线、显式人工USD研究输入、Schema v6重载与精确结构化轨迹；inactive/unconsumed |
| Paper Trading | `NOT_IMPLEMENTED` | 无订单Provider或提交行为 |
| Live Trading | `NOT_IMPLEMENTED` | disabled；无连接、凭据或订单行为 |
| Order Construction / Execution Provider | `PLANNED` | 仅文档方向与Risk-approved类型门 |

当前没有模块标记为`IN_DEVELOPMENT`、`IMPLEMENTED_UNVERIFIED`、`BLOCKED`、`DEPRECATED`。局部能力受Open Decisions限制不等于模块状态`BLOCKED`；未完成交易模块按实际证据标记为`SCAFFOLD_ONLY`、`PLANNED`或`NOT_IMPLEMENTED`。

## Public interfaces

- Backtesting: `BacktestRequest`, `SimulatedTrade`, `EquityPoint`, `BacktestResult`, `DecisionJournalEntry`, `FactorTrace`, `ConditionTrace`, `JournalAction`, `JournalOutcome`; immutable contracts validate identity, UTC time and Decimal/arithmetic coherence, while the GUI exposes separate simulated-fill and daily-decision views. Implemented and verified for isolated research only.

- Run History/Persistence: `AlgorithmRunService`, `RunHistoryRepository`, `RunHistoryQueryService`, `CentralSQLiteDatabase`, `SQLiteRunHistoryRepository`, `FactorSnapshotStore`, `SQLiteFactorSnapshotStore`, `SQLiteAlgorithmResultStore`, `SQLiteResearchHistoryQueryService`, `SQLiteCapitalAllocationStore`, `SQLiteAssetStateStore`, `SQLiteTargetPositionStore`, `FactorCalculationRun`, `FactorCalculationStatus`.
- Capital Allocation: `CapitalAllocationService`, `CapitalAllocationStore`, `CapitalAllocationQueryService`, `CapitalPlan`, `CapitalSnapshot`, `CapitalAllocationTransferEvent`, `CapitalConservationResult`, `CapitalOperationAttempt` and typed commands/list/detail views.
- Asset State: `AssetStateService`, `AssetStateStore`, `AssetStateQueryService`, `AssetStateMachineDefinition`, `TradingCycle`, `AssetStateTransitionEvent`, `AssetStateSnapshot`, `AssetStateOperationAttempt`, `StateReplayResult` and typed commands/queries.
- Target Position: `TargetPositionService`, `TargetPositionEngine`, `TargetPositionStore`, `TargetPositionQueryService`, `TargetPositionCurveDefinition`, `TargetPositionResult`, `TargetPositionCalculationTrace`, `TargetPositionOperationAttempt` and typed commands/queries.

- Python：`HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController` 及 Provider/Store Protocol。
- Desktop entry point：`quant-history` 或 `python -m quant_trading.market_history`。
- Factor：`FactorCalculator`, `SingleAssetFactorEngine`, `FactorResult`, `FactorSnapshot`, `FactorSnapshotCollection`, `FactorHistoryQueryService`, `FactorVisualizationQueryService`及历史/精确版本/源价格证据合同。
- Decision：`TradingDecisionPolicy`, `TradingDecisionEngine`, `DecisionResult`, `TradeIntent`, `DecisionConditionTrace`, `DecisionSizingInputTrace`, `DecisionHistoryQueryService`及历史详情合同。
- Risk：`RiskPolicy`, `RiskEngine`, `RiskDecision`, `RiskApprovedTradeIntent`及中性上下文/Provider Protocol。
- Portfolio Accounting：`LedgerRepository`, `PortfolioAccountingService`, `AccountSnapshot`, `PositionSnapshot`, `PortfolioSnapshot`, `DailyPnLSnapshot`, `ReconciliationService`, `PortfolioAccountingQueryService`。
- Orchestration：`AnalysisDecisionPipeline`, `TradingEvaluationPipeline`。
- Algorithm Control：`AlgorithmComponentRegistry`, `ParameterSchema`, `ConfigurationService`, `AlgorithmControlController`, `AlgorithmControlPanel`；入口`quant-algorithm-control`或`python -m quant_trading.algorithm_control`。
- Algorithm Idea Notebook：`IdeaNote`, `IdeaNoteStatus`, `IdeaNoteStore`, `JsonIdeaNoteStore`, `IdeaNotebookService`, `IdeaNotebookPanel`；仅供Algorithm Control本地笔记使用。
- Factor authoring：`FactorDefinition`, `FactorDefinitionStore`, `SafeExpressionFactorCalculator`, `FactorDefinitionService`；见 `docs/modules/factor-authoring.md`。

- Change Admission public interfaces: `ChangeAdmissionService`, `ChangeProposal`, `ChangeImpactReport`, `ConflictAssessment`, `PipelineAdmissionResult`, `DataContractDeclaration`, `Capability`, and `FeatureState`; proposal workflow in `docs/proposals/README.md`.

## Current technology decisions

- The existing ignored `runtime/data/market_history.sqlite3` is the central physical SQLite file. Market, Run History, Factor, Decision, Risk, Capital Allocation, Asset State and Target Position persistence keep separate public contracts; schema initialization is additive and versioned. Schema v2 is defined by PROPOSAL-009/ADR-0016, Schema v3 by PROPOSAL-010/ADR-0017, exact Bar visualization by PROPOSAL-011/ADR-0018, Schema v4 by PROPOSAL-012/ADR-0019, Schema v5 by PROPOSAL-013/ADR-0020, and Schema v6 bounded target research by PROPOSAL-014/ADR-0021.

- Python 支持范围为 3.11–3.14；当前实际验证版本为 3.14.5。
- 历史数据模块采用 PySide6/QWebEngineView、Plotly、官方 `alpaca-py`、pandas、标准库 SQLite 和 pytest。
- 内部时间与数据库时间统一为 UTC；历史请求区间为 `[start, end)`。
- 价格字段以十进制文本保存到 SQLite；图表展示时转换为浮点数。
- 默认数据库为 `runtime/data/market_history.sqlite3`，运行日志为 `runtime/logs/app.log` 与 `runtime/logs/error.log`；这些运行产物不提交 Git。
- 算法控制状态独立保存在`runtime/algorithm_control/control_state.json`，使用原子替换、不可变版本和审计记录；不保存凭据，也不与行情SQLite混合。
- 算法Idea笔记独立保存在`runtime/algorithm_control/idea_notes.json`；它不属于组件状态、Factor/Decision定义、Simulation结果或交易记录，且不得保存Secret。
- 安全边界默认为 DEVELOPMENT / BACKTEST / PAPER-TRADING ONLY。
- `MarketDataProviderType`、`BrokerageType` 与 `ExecutionEnvironment` 使用独立枚举；默认值分别为 `ALPACA`、`ALPACA` 和 `ALPACA_PAPER`。
- 当前 Alpaca 环境变量只用于 Market Data；Key 存在不会启用 Paper/Live 下单。项目不读取或保存 Fidelity 用户名、密码、双重认证信息或 API Key。
- 配置、正式源码、测试、脚本、运行产物和归档内容使用独立目录。
- 当前依赖方向经代码与自动检查验证为 `UI → Controller → Service → Protocols ← Provider/Store`，Controller 另依赖 Chart Builder；`app.py` 是唯一具体组装入口。
- 算法依赖方向为 `MarketDataWindow → factors → FactorSnapshot → decision → TradeIntent → risk → RiskDecision`；上游不反向依赖下游，Risk不依赖具体Factor/Decision实现、Market History、SQLite、GUI、Alpaca或Execution。
- Git 默认分支为 `main`；提交身份仅在本项目生效；远程 `origin` 指向 `https://github.com/tony73410/QuantTrading.git`。

## Pending decisions

- 当前环境曾完成 Alpaca IEX 只读验证；其他电脑/进程是否配置凭据以及 SIP 等 Feed 权限仍取决于本地环境和账户订阅，不能从仓库推断。
- 自动本地数据保留与清理目标已由用户提出，但具体期限、不可逆删除、Coverage同步和持久化结构方案尚未批准；当前 **Not implemented**，见 Compass DEC-001 / INTENT-005。
- 后续业务需求及其技术选择；本次决定不自动扩展到交易、策略或其他模块。
- Market History本地预览采用“Bar时间戳加粒度时长后才可用”的保守近似，并过滤`as_of_utc`之后的数据；它不是经交易日历验证的回测语义。精确映射仍待决定，见Compass DEC-005。
- 复权历史对未来Factor/回测的point-in-time语义尚未批准；当前合同只记录Adjustment，不声明其可用于无前视偏差回测，见Compass DEC-006。
- 用户可通过受限表达式保存自己的Factor定义；这些定义默认禁用。任何Factor的金融含义/正式激活、Decision Policy、阈值、仓位/组合语义仍待用户逐项批准。
- 最大仓位/订单、现金、Buying Power、亏损、回撤、集中度、杠杆、保证金和紧急自动降仓规则/数值均待用户逐项批准；当前Risk无生产规则，见Compass DEC-007。
- 未来若提出 Paper 账户、订单或自动执行需求，必须在现有 `execution.paper` 空边界内单独定义合同、订单模型、人工确认和风险边界并重新审批；当前没有相关行为。
- 会计成本基础、交易日/时区、结算现金、手续费、股息、公司行为、做空、保证金、多币种、税务、Daily P&L与Broker冲突处理均为Open Decisions；当前不声明口径。
- Alpaca Live 的独立凭据/endpoint、风险限制、资金限制、每日亏损限制、最大持仓、额外确认和紧急停止方案均待未来明确批准。

## Known limitations

- Tracked local previews persist Factor evidence by default so Decision/Risk rows retain a durable input reference. Definitions/lifecycle/Decision versions remain under ignored `runtime/algorithm_control/`; results and Run evidence use central SQLite. Neither persistence path constitutes production activation.

- 只读诊断已用现有凭据成功验证 AAPL IEX Market Data；SIP 等 Feed 仍取决于用户订阅权限。
- 未在实际物理显示器进行人工视觉验收；offscreen GUI 烟雾测试通过但产生 GPU 回退提示。
- 没有安装包分发、自动更新、选择性缓存删除或实时 WebSocket 行情。
- 本地股票代码建议目录不会自动同步上市、退市、代码或行业分类变化；列表之外的代码仍可自由输入。
- 正在执行的同步 Alpaca HTTP 请求无法安全中途取消，窗口关闭可能等待请求结束；见 KI-0006 / BUG-20260713-005。
- 分钟/小时常规时段使用固定 09:30–16:00 纽约时间窗口，当前不能识别提前收盘日；见 KI-0007。
- Factor/Decision/Risk已接入Algorithm Control的本地预览流程和统一Run History，但没有接入生产激活或执行流程。Factor/Decision/Risk dry-run结果会作为研究证据持久化；TradeIntent和RiskDecision都不是订单。
- Schema-v2 Decision rows remain readable as `TRACE_NOT_CAPTURED`; Phase 2A does not infer or backfill condition outcomes. Phase 2B charts only one exact Factor version and exact stored source field; cross-version chart overlays/ranking, Decision export and recomputation replay remain unimplemented. Phase 5A Target Position is a separate manual-only research branch, not a Factor/Decision integration.
- 用户可保存多个禁用Factor和Decision版本。Pipeline Dry Run需要精确选择一个Decision版本和本地缓存数据；没有数值Risk规则时，任何交易意图都会停在人工审查状态。
- Risk的Account/Portfolio/OpenOrders Provider只有抽象Protocol；没有账户连接。Emergency de-risking当前只会暂停新Intent，自动平仓Not implemented。
- Portfolio Accounting仅使用内存Repository/Service；无持久化、Broker同步、市场估值或完整P&L。现有Decision/Risk trace-only Snapshot未被替换，未来运行接入需要显式adapter审查。
- Capital Allocation、Asset State和Target Position都没有Active选择或自动消费者。Target Position只接受人工scalar/USD输入。行业层级、动态权重、储备借贷、自动状态公式/阈值/饱和重置、标准化状态、Capital/Accounting adapter、hysteresis、TradeIntent转换均未实现。
- Idea Notebook currently provides plain text, tags and archive/restore only. It has no search, attachments, cloud sync, encryption, proposal conversion, or algorithm activation path.

## Implementation checkpoint — 2026-07-20

- Phase 1、2A、2B、3A、4A和5A均按PROPOSAL-009/010/011/012/013/014批准边界实施；Phase 5A只计算显式人工研究目标，不进入Decision/Risk/Execution链。
- 中央SQLite已从v5事务式迁移到Schema v6，备份`market_history.schema-v5-to-v6.20260720T221057524713Z.sqlite3`有效；迁移前后保留215,340条Market Bars和365条Fetch History，双方`integrity_check=ok`且无外键错误。所有新Target Position表为0行，没有默认定义/节点/预览/操作。
- 所有Capital与Asset State运行均为`NO_EXECUTION`。Paper/Live包仍为空，自动提交和Live仍关闭；未使用网络、账户或订单权限。
- 确认并修复`BUG-20260720-001/002/003`：Capital Store完整快照校验、Asset State幂等/原始请求保存和Store跨对象证据校验均有回归覆盖。
- 当前Phase 1–5A工作构成本记录所在Git提交的已验证发布检查点；Git提交保存精确修订标识，项目包版本仍为`0.1.0`。本次交付只发布既有获批研究能力，不授予后续开发、运行激活或交易权限。

## Next approved work

`PROPOSAL-014` Phase 5A is implemented and verified as disabled/unconsumed manual research. No further development slice is currently approved. Standardized-state formulas, automatic Factor/State inputs, Capital/Accounting adapters, hysteresis, target-to-Decision conversion, numerical Risk, full Backtesting consumption, accounting persistence, Paper execution, production activation and Live require separate scope and approval. Paper/Live Execution boundaries remain empty.

## Last verified date

2026-07-20 (full suite 375 passed with one upstream warning; final architecture suite 45 passed; compileall and pip dependency integrity passed; diff whitespace status is recorded in EDIT-20260720-006; Target Position domain/SQLite/Run/GUI/chart/Launcher paths passed; central SQLite Schema v6 and verified v5 backup preserve 215,340 Market Bars and 365 Fetch History rows with integrity/FK checks clean and zero default Target Position rows; Main Launcher exposes three applications and fifteen trusted shortcuts; network/account/order access was not used; Live and automatic submission remain disabled.)
