# Module Map

本文件是简要模块索引。系统结构、完整职责/非职责、依赖矩阵、数据流和架构不变量的唯一主要来源是 [`OVERVIEW.md`](OVERVIEW.md)。两者冲突时应报告漂移并以实际代码、Compass 与已批准决策核实，而不是静默合理化冲突。

## Active modules

| `quant_trading.factors` Asset Factor | One-symbol standardized bars to immutable Factor result | existing Factor contracts/engine/editor | Market Data contracts only | Decision/Market Factor | `docs/modules/factors.md` |
| `quant_trading.factors.market` | Exact Asset Factor collection to cross-symbol Market Factor | `MarketFactorDefinition`, `MarketFactorResult`, calculator | public Asset Factor results only | Decision/Risk research context | `docs/modules/market-factors.md` |

| `quant_trading.backtesting` | Isolated historical research replay, simulated fills, cash/equity and result queries | `BacktestRequest`, `BacktestResult`, `HistoricalBacktestService`, `HistoricalBarSource`, GUI/CLI | public Market History models through a read-only port; concrete SQLite only in app composition | Research user | `docs/modules/backtesting.md` |
| `SimulationStrategyDefinition` | User-named immutable research composition of exact buy/sell Decision versions | strategy service/store, `DefinitionSignalProvider`, Algorithm Control page | exact Factor/Decision public definitions; execution authority forbidden | Algorithm Control and Backtesting | `docs/modules/backtesting.md` |

| Module | Responsibility | Public entry points | Direct dependencies | Used by | Documentation |
|---|---|---|---|---|---|
| `quant_trading.launcher` | QuantTrade主要桌面入口，以静态可信目录启动三个独立GUI进程，并直达Algorithm Control现有核心页签 | `LaunchTarget`, `DEFAULT_CORE_SHORTCUTS`, `MainLauncherWindow`, `python -m quant_trading`, `quant-trade` | stdlib, PySide6, observability；功能模块名/参数仅作为静态字符串 | Desktop user | `docs/modules/main-launcher.md` |
| `quant_trading.persistence` | Shared local SQLite connection/schema versioning plus immutable Factor snapshot/result and calculation-run storage | `CentralSQLiteDatabase`, `SQLiteFactorSnapshotStore` implementing `FactorSnapshotStore` | stdlib sqlite3, public Market/Factor models | Market Store initialization; optional Orchestration injection | `docs/modules/central-persistence.md` |
| `quant_trading.market_history` | 10/30 分钟、1 小时及日/周/月历史股票 Bar 获取、本地缓存、增量更新和桌面展示 | `HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController`, `python -m quant_trading.market_history` | Python stdlib, alpaca-py, pandas, Plotly, PySide6 | Desktop user | `docs/modules/market-history.md` |
| `quant_trading.factors` | 将单资产、截至as-of可用的完整行情转换为版本化、策略中立FactorSnapshot；无正式公式 | `FactorCalculator`, `SingleAssetFactorEngine`, `FactorSnapshot` | stdlib, public MarketBar/dimension models | Orchestration or independent research caller | `docs/modules/factors.md` |
| `quant_trading.decision` | 消费公开FactorSnapshot并调用注入Policy，输出非执行DecisionResult/TradeIntent；无正式规则 | `TradingDecisionPolicy`, `TradingDecisionEngine`, `DecisionResult`, `TradeIntent` | stdlib, Factor public models/interfaces | Orchestration or independent decision caller | `docs/modules/trading-decision.md` |
| `quant_trading.risk` | 对TradeIntent执行独立、保守、可解释的执行前风险裁决；无具体数值规则 | `RiskPolicy`, `RiskEngine`, `RiskDecision`, `RiskApprovedTradeIntent` | stdlib, application role enum, public Factor/Decision models | Orchestration or independent risk caller | `docs/modules/risk-control.md` |
| `quant_trading.orchestration` | 仅组织Factor → Decision以及可选的Factor → Decision → Risk调用和上下文传递 | `AnalysisDecisionPipeline`, `TradingEvaluationPipeline` | public Factor/Decision/Risk engines/models | Future approved application service | `docs/modules/analysis-decision-pipeline.md` |
| `quant_trading.execution.paper` / `.live` | 两个同级、空白且禁用的未来执行环境边界 | None | None | None；尚无运行调用方 | `docs/modules/execution-environments.md` |
| `quant_trading.portfolio_accounting` | 统一Portfolio Accounting领域：Ledger追加事实，Accounting重放现金/净持仓，Reconciliation只报告差异，Queries提供只读模型 | `LedgerRepository`, `PortfolioAccountingService`, `AccountSnapshot`, `PositionSnapshot`, `ReconciliationService`, `PortfolioAccountingQueryService` | stdlib；内部仅依赖自身公共合同 | Risk只读Provider、Algorithm Control只读页签、未来Execution事件 | `docs/modules/portfolio-accounting.md`, `docs/modules/trading-ledger.md` |
| `quant_trading.algorithm_control` | 通过Registry和ParameterSchema管理组件、Factor生命周期、Factor/Decision不可变版本、安全预览请求和审计 | `AlgorithmControlController`, `AlgorithmControlPanel`, `python -m quant_trading.algorithm_control` | stdlib, PySide6, public Factor/Decision/Risk contracts | Desktop user; local preview composition | `docs/modules/algorithm-control-gui.md` |
| `quant_trading.algorithm_control.idea_notebook` | Passive local idea notes only; never an algorithm, simulation, accounting, or execution input | `IdeaNote`, `IdeaNotebookService`, `IdeaNotebookPanel` | stdlib; PySide6 only in its panel | Algorithm Control GUI only | `docs/modules/idea-notebook.md` |
| `quant_trading.observability` / `quant_trading.diagnostics` | Error Code 上下文、脱敏轮转日志、异常 Hook 与只读安装诊断 | `configure_logging`, `request_context`, `python -m quant_trading.diagnostics` | Python stdlib；诊断只读复用 market-history 配置/Provider | Application / developer / user support | `docs/development/DEBUGGING.md` |
| `quant_trading.validation` | 统一ValidationResult/Severity/Error Code与fail-closed健康汇总；不拥有业务规则 | `ValidationIssue`, `ValidationResult`, `ValidationRegistry`, `HealthCheckResult` | stdlib, centralized ErrorCode, observability | diagnostics及未来模块自有validator | `docs/development/VALIDATION.md` |

## Verified module status inventory (2026-07-16)

| Area | Status | Evidence / boundary |
|---|---|---|
| Market Data | `IMPLEMENTED_VERIFIED` | Provider/Service/model tests、离线GUI smoke、数据合同与缓存流程 |
| Local Storage | `IMPLEMENTED_VERIFIED` | SQLite unit/integration、首次初始化与integrity=ok |
| GUI | `IMPLEMENTED_VERIFIED` | launcher/Market History/Algorithm Control offscreen启动关闭与GUI测试；物理显示QA仍open |
| Charting | `IMPLEMENTED_VERIFIED` | Plotly builder/UI测试与GUI构造；offscreen GPU回退不影响结果 |
| Configuration | `IMPLEMENTED_VERIFIED` | 有/无凭据、缺目录和默认安全设置验证 |
| Logging | `IMPLEMENTED_VERIFIED` | UTC结构化日志、exception hook与Secret脱敏测试/运行日志 |
| Diagnostics | `IMPLEMENTED_VERIFIED` | 本地只读命令成功；网络检查本次`SKIPPED` |
| Factor Layer | `PARTIALLY_IMPLEMENTED` | 合同/Engine/受限表达式已验证；无批准生产Factor或激活 |
| Trading Decision Layer | `PARTIALLY_IMPLEMENTED` | 合同/Engine/受限规则已验证；无生产Policy/仓位/订单 |
| Risk Layer | `PARTIALLY_IMPLEMENTED` | 合同/Engine/Fake规则已验证；无数值Risk政策或账户连接 |
| Execution Layer | `SCAFFOLD_ONLY` | Paper/Live空命名空间与架构测试；无Provider/OrderRequest |
| Algorithm Control GUI | `IMPLEMENTED_VERIFIED` | 本地版本/预览/审计GUI及测试；所有组件默认禁用 |
| Trading Ledger | `SCAFFOLD_ONLY` | typed模型和内存append/idempotency测试；无持久化/Broker ingestion |
| Portfolio Accounting | `SCAFFOLD_ONLY` | 内存现金/净多头replay及只读快照；无完整成本/P&L |
| Reconciliation | `SCAFFOLD_ONLY` | 内存比较与只报告差异；无Broker连接/自动修正 |
| Paper Trading | `NOT_IMPLEMENTED` | 只有空环境边界；无订单提交 |
| Live Trading | `NOT_IMPLEMENTED` | 空边界且全局disabled |
| Order Construction / Execution Provider | `PLANNED` | 文档方向/类型门；无实际代码或运行能力 |

内部依赖方向：`ui → controller → service → interfaces ← storage/providers`；`controller → charts`。`storage`、`providers` 和 `charts` 彼此不依赖。

算法依赖方向：`MarketDataWindow → factors → FactorSnapshot → decision → TradeIntent → risk → RiskDecision`；`orchestration`只能按此顺序调用。Factors不知道Decision/Risk；Decision不知道Risk；Risk只使用公开上游合同，不导入具体Factor/Decision实现、Market History、SQLite、GUI、Alpaca或Execution。

`RiskApprovedTradeIntent`只是未来Order Construction的类型门，仍不是订单或执行授权。Paper/Live Execution仅存在空命名空间，没有接口或行为；Live与自动提交保持关闭。

Portfolio Accounting的事实流为`OrderEvent/TradeFill/CashMovement → Trading Ledger → Accounting → snapshots`。操作事件不改变财务状态；只有确认成交和有效现金事实参与重放。Risk和GUI是只读消费者，Broker仅为Reconciliation参考。

算法控制中心是独立管理面，不在执行数据路径中；GUI不依赖具体Alpaca/SQLite/Execution实现。应用编排通过公开Store合同提供本地Factor预览和Factor → Decision → Risk Dry Run，所有Preview均为NO EXECUTION。

应用级 `quant_trading.application_settings` 只声明角色与安全默认值：Alpaca 是 Market Data Provider 和 Primary Brokerage，默认目标环境为 `ALPACA_PAPER`，自动下单与 Live 均关闭，人工确认开启。它不连接账户、不提交订单，也不构成 execution 模块。

未来经批准的行情 Provider 可替换 `HistoricalMarketDataProvider`，无需改变券商角色；未来经批准的 Alpaca execution 内容必须放入正确的Paper或Live边界、独立于 `market_history`，且不得反向依赖具体行情 Provider 或直接操作 SQLite 历史数据库。Fidelity/`MANUAL_FIDELITY` 仅为非默认兼容选项。

Admission subcomponents: `quant_trading.algorithm_control.admission_models`, `admission_service`, `capabilities`, and `contracts` own component identity, unique responsibility ownership, layer capability policy, versioned contract declarations, staged activation, and fail-closed Pipeline conflict checks. They contain no algorithm or execution behavior.

Scheme A extension: `quant_trading.factors.definitions` and `expression_language` own immutable Factor-definition/restricted-language contracts; `expression` owns calculation. Algorithm Control owns editing, lifecycle metadata, atomic definition persistence and disabled registration. `quant_trading.decision.definitions` and `rule_policy` own restricted, immutable Decision rules; orchestration owns local-only evaluation and optional Factor-history persistence. No selection, save or preview grants trading authority. See `docs/modules/factor-authoring.md`, `docs/modules/trading-decision.md` and PROPOSAL-004.

Execution Control is read-only metadata: it reports both sibling Paper/Live boundaries as Not implemented and disabled. The execution packages remain declaration-only and contain no runtime Provider or order path.

## Historical Simulation evidence

Historical Simulation owns a separate research-only `DecisionJournalEntry` stream: every valid Daily bar/symbol receives an evaluation with Factor/Decision/sizing evidence, while only eligible BUY/SELL evaluations create simulated fills. This stream never enters the operational Trading Ledger or Portfolio Accounting.

## How to update

每当模块获批并实现后，在此记录：模块名称、职责摘要、公共接口、直接依赖、主要调用方和对应 `docs/modules/<module-name>.md` 链接。该映射必须反映实际代码，不能提前列出假设模块。

公共接口或依赖方向变化属于审批事项，批准和实施后必须同步本文件及相关模块文档。
