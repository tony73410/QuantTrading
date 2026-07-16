# Project State

## Current phase

Governed stock historical data browser plus an independent Algorithm Control Center with a passive local Idea Notebook, immutable Factor/Decision authoring, non-destructive Factor lifecycle, local-only Factor preview, a Risk-gated dry run, and a read-only Portfolio & Ledger scaffold. Paper/Live Execution remain declaration-only; no active production algorithm, broker account connection, order, or execution behavior exists.

## Implemented capabilities

- Algorithm Idea Notebook is `IMPLEMENTED_VERIFIED` as an isolated local-only page: notes support title, plain text, tags, archive and restore, but cannot register or invoke Factor, Decision, Risk, Simulation, Portfolio Accounting or Execution behavior.

- Asset Factor is explicitly single-stock. Market Factor phase one provides immutable explicit-universe aggregation over exact Asset Factor versions with complete-input enforcement.
- Decision Sizing phase one provides fixed USD, cash/equity/position percentages, exit-all and restricted Decimal expressions over Asset/Market Factors plus read-only account/position fields. Risk contracts trace and constrain requested notional; no production Risk values were added.

- Historical Backtesting is `IMPLEMENTED_VERIFIED` for the approved research-only SMA20/50 baseline: all 110 locally cached symbols completed a one-year offline run, with isolated simulated trades, cash, holdings, equity curve, JSON results, GUI and CLI. Immutable records now reject inconsistent Decimal arithmetic, run identity, trace/journal evidence and result-file identity before display or persistence. It is not Paper Trading or production strategy evidence.
- User-named Simulation Strategies are implemented as immutable local versions that select exact buy/sell Decision versions and their exact Factor dependencies. Saved versions are selectable from Backtesting; the first-phase universe/allocation/fill/cost semantics remain fixed and execution authority remains false.

- QuantTrade主控制台：`python -m quant_trading`显示三个独立子GUI入口，并通过紧凑的可信目录直达Algorithm Control全部11个现有核心页签；子功能仍在独立进程及其所有者页面中运行，主菜单不包含业务/交易逻辑。
- Central SQLite schema version 1 reuses `runtime/data/market_history.sqlite3` for existing Market tables plus immutable `factor_snapshots`, typed `factor_results`, and append-preserving `factor_calculation_runs`. Exact semantic repeats reuse one result snapshot while retaining separate run records. No production Factor is active.

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

- `quant_trading.persistence` — shared SQLite connection/schema boundary and concrete Factor history adapter; see `docs/modules/central-persistence.md`.

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
| GUI | `IMPLEMENTED_VERIFIED` | 主Launcher、三个子GUI及Algorithm Control 11个核心直达入口的offscreen/GUI回归；物理显示QA仍未完成 |
| Charting | `IMPLEMENTED_VERIFIED` | Plotly builder与GUI集成测试 |
| Configuration | `IMPLEMENTED_VERIFIED` | 缺凭据/缺目录/默认安全角色验证 |
| Logging | `IMPLEMENTED_VERIFIED` | UTC轮转日志、异常hook、脱敏测试与实际错误堆栈 |
| Diagnostics | `IMPLEMENTED_VERIFIED` | 本地只读诊断运行通过；网络连接本次未验证 |
| Factor Layer | `PARTIALLY_IMPLEMENTED` | 公共合同、Engine、受限表达式和本地预览；无批准生产Factor |
| Trading Decision Layer | `PARTIALLY_IMPLEMENTED` | 公共合同、Engine、受限版本规则；无生产Policy/订单 |
| Risk Layer | `PARTIALLY_IMPLEMENTED` | 公共合同、Engine、保守Fake验证；无数值规则/账户连接 |
| Execution Layer | `SCAFFOLD_ONLY` | 空Paper/Live包和架构测试 |
| Algorithm Control GUI | `IMPLEMENTED_VERIFIED` | 本地版本、预览、审计和安全状态；无执行权限 |
| Algorithm Idea Notebook | `IMPLEMENTED_VERIFIED` | 独立JSON、服务与GUI回归测试；无任何业务模块输出 |
| Trading Ledger | `SCAFFOLD_ONLY` | 内存append-only/idempotency合同与测试 |
| Portfolio Accounting | `SCAFFOLD_ONLY` | 内存现金/净多头replay和只读快照 |
| Reconciliation | `SCAFFOLD_ONLY` | 内存差异报告；无Broker同步/自动修正 |
| Paper Trading | `NOT_IMPLEMENTED` | 无订单Provider或提交行为 |
| Live Trading | `NOT_IMPLEMENTED` | disabled；无连接、凭据或订单行为 |
| Order Construction / Execution Provider | `PLANNED` | 仅文档方向与Risk-approved类型门 |

当前没有模块标记为`IN_DEVELOPMENT`、`IMPLEMENTED_UNVERIFIED`、`BLOCKED`、`DEPRECATED`。局部能力受Open Decisions限制不等于模块状态`BLOCKED`；未完成交易模块按实际证据标记为`SCAFFOLD_ONLY`、`PLANNED`或`NOT_IMPLEMENTED`。

## Public interfaces

- Backtesting: `BacktestRequest`, `SimulatedTrade`, `EquityPoint`, `BacktestResult`, `DecisionJournalEntry`, `FactorTrace`, `ConditionTrace`, `JournalAction`, `JournalOutcome`; immutable contracts validate identity, UTC time and Decimal/arithmetic coherence, while the GUI exposes separate simulated-fill and daily-decision views. Implemented and verified for isolated research only.

- Persistence: `CentralSQLiteDatabase`, `FactorSnapshotStore`, `SQLiteFactorSnapshotStore`, `FactorCalculationRun`, `FactorCalculationStatus`.

- Python：`HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController` 及 Provider/Store Protocol。
- Desktop entry point：`quant-history` 或 `python -m quant_trading.market_history`。
- Factor：`FactorCalculator`, `SingleAssetFactorEngine`, `FactorResult`, `FactorSnapshot`, `FactorSnapshotCollection`。
- Decision：`TradingDecisionPolicy`, `TradingDecisionEngine`, `DecisionResult`, `TradeIntent`。
- Risk：`RiskPolicy`, `RiskEngine`, `RiskDecision`, `RiskApprovedTradeIntent`及中性上下文/Provider Protocol。
- Portfolio Accounting：`LedgerRepository`, `PortfolioAccountingService`, `AccountSnapshot`, `PositionSnapshot`, `PortfolioSnapshot`, `DailyPnLSnapshot`, `ReconciliationService`, `PortfolioAccountingQueryService`。
- Orchestration：`AnalysisDecisionPipeline`, `TradingEvaluationPipeline`。
- Algorithm Control：`AlgorithmComponentRegistry`, `ParameterSchema`, `ConfigurationService`, `AlgorithmControlController`, `AlgorithmControlPanel`；入口`quant-algorithm-control`或`python -m quant_trading.algorithm_control`。
- Algorithm Idea Notebook：`IdeaNote`, `IdeaNoteStatus`, `IdeaNoteStore`, `JsonIdeaNoteStore`, `IdeaNotebookService`, `IdeaNotebookPanel`；仅供Algorithm Control本地笔记使用。
- Factor authoring：`FactorDefinition`, `FactorDefinitionStore`, `SafeExpressionFactorCalculator`, `FactorDefinitionService`；见 `docs/modules/factor-authoring.md`。

- Change Admission public interfaces: `ChangeAdmissionService`, `ChangeProposal`, `ChangeImpactReport`, `ConflictAssessment`, `PipelineAdmissionResult`, `DataContractDeclaration`, `Capability`, and `FeatureState`; proposal workflow in `docs/proposals/README.md`.

## Current technology decisions

- The existing ignored `runtime/data/market_history.sqlite3` is the central physical SQLite file. Market and Factor persistence keep separate public Store contracts; schema initialization is additive and versioned. See ADR-0009.

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

- Factor persistence可由用户在本地预览中显式选择；结果写入中央SQLite，定义/生命周期/Decision版本写入被Git忽略的`runtime/algorithm_control/`。它不构成生产激活。

- 只读诊断已用现有凭据成功验证 AAPL IEX Market Data；SIP 等 Feed 仍取决于用户订阅权限。
- 未在实际物理显示器进行人工视觉验收；offscreen GUI 烟雾测试通过但产生 GPU 回退提示。
- 没有安装包分发、自动更新、选择性缓存删除或实时 WebSocket 行情。
- 本地股票代码建议目录不会自动同步上市、退市、代码或行业分类变化；列表之外的代码仍可自由输入。
- 正在执行的同步 Alpaca HTTP 请求无法安全中途取消，窗口关闭可能等待请求结束；见 KI-0006 / BUG-20260713-005。
- 分钟/小时常规时段使用固定 09:30–16:00 纽约时间窗口，当前不能识别提前收盘日；见 KI-0007。
- Factor/Decision/Risk已接入Algorithm Control的本地预览流程，但没有接入生产激活或执行流程。Factor结果可选持久化；Decision/Risk dry-run结果不持久化，也不是订单。
- 用户可保存多个禁用Factor和Decision版本。Pipeline Dry Run需要精确选择一个Decision版本和本地缓存数据；没有数值Risk规则时，任何交易意图都会停在人工审查状态。
- Risk的Account/Portfolio/OpenOrders Provider只有抽象Protocol；没有账户连接。Emergency de-risking当前只会暂停新Intent，自动平仓Not implemented。
- Portfolio Accounting仅使用内存Repository/Service；无持久化、Broker同步、市场估值或完整P&L。现有Decision/Risk trace-only Snapshot未被替换，未来运行接入需要显式adapter审查。
- Idea Notebook currently provides plain text, tags and archive/restore only. It has no search, attachments, cloud sync, encryption, proposal conversion, or algorithm activation path.

## Next approved work

`PROPOSAL-004`与`PROPOSAL-005`的非执行骨架已获批准并完成。`PROPOSAL-006`的隔离历史回测基线已实现并验证。Paper/Live Execution代码边界仍为空。完整会计、Paper执行、生产激活和Live均不得自行开始。当前发布检查点见 [`VERSION_HISTORY.md`](VERSION_HISTORY.md)。

## Last verified date

2026-07-16 (301 tests passed with one upstream warning; Main Launcher offscreen smoke exposed three applications and all eleven trusted Algorithm Control core shortcuts; the real `--page portfolio_ledger` entry parsed and exited cleanly with zero execution invocation; prior child-GUI, Backtesting-result, dependencies/compile/diagnostics/SQLite and isolated 110-symbol evidence remains recorded; network/account/order access was not used; Live and automatic submission remain disabled.)
