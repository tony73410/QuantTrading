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
| `quant_trading.run_history` | Neutral NO EXECUTION research-run identity, lifecycle, ordered stages, exact bindings, parent/child/source relationships, messages and typed query views | `AlgorithmRunService`, `RunHistoryRepository`, `RunHistoryQueryService`, run/stage/detail/relationship models | stdlib only | Orchestration, Persistence adapters, Algorithm Control read-only GUI | `docs/modules/run-history.md` |
| `quant_trading.persistence` | Shared local SQLite Schema v13, versioned backup/migration, research queries, Run History repository and immutable Decision/Risk/Capital/Asset State/Target Position/standardized-state/link/target-adjustment/manual-review/exposure-cap/cash-floor/asset-cash evidence adapters | `CentralSQLiteDatabase`, existing repositories/query services, `SQLiteTargetPositionStore`, `SQLiteStandardizedPriceStateStore`, `SQLiteTargetAdjustmentDecisionStore`, `SQLiteTargetAdjustmentRiskStore`, `SQLiteExposureCapStore`, `SQLiteResearchCashFloorStore`, `SQLiteResearchAssetCashStore` | stdlib sqlite3, neutral Run History and public domain contracts | Market Store initialization; Orchestration/domain composition; typed research inspectors | `docs/modules/central-persistence.md` |
| `quant_trading.market_history` | 10/30 分钟、1 小时及日/周/月历史股票 Bar 获取、本地缓存、增量更新和桌面展示 | `HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController`, `python -m quant_trading.market_history` | Python stdlib, alpaca-py, pandas, Plotly, PySide6, shared presentation renderer | Desktop user | `docs/modules/market-history.md` |
| `quant_trading.visualization` | Business-neutral responsive Plotly/QWebEngine Figure rendering only | `PlotlyFigureView` | stdlib, Plotly, PySide6, shared ChartError | Market History and Algorithm Control presentation | `docs/modules/visualization.md` |
| `quant_trading.factors` | Single-asset Factor contracts plus disabled manual standardized-price-state research; owns typed history/exact-source evidence and exact structured normalization meaning; no production formula | Factor engine/snapshot/history contracts plus `StandardizedPriceStateEngine`, service and Store/query contracts | stdlib, public MarketBar/dimension models; neutral Run History for the approved specialized service | Orchestration, Persistence adapters, Algorithm Control or independent research caller | `docs/modules/factors.md`, `docs/modules/standardized-price-state.md` |
| `quant_trading.decision` | Public FactorSnapshot to generic non-executing DecisionResult/TradeIntent plus the isolated exact Phase 5D Target Adjustment Decision; owns immutable trace/history meaning; no production policy | generic Decision contracts plus `TargetAdjustmentDecisionService`, specialized result/intent and Store/query contracts | stdlib, Factor public contracts for generic decisions; neutral Run/link DTO contracts for the specialized path | Orchestration, Persistence adapters, Algorithm Control or independent decision caller | `docs/modules/trading-decision.md` |
| `quant_trading.risk` | Generic conservative Risk contracts/engine, isolated Phase 6A structural gate and disabled Phase 6B/6C/6D ordered numerical previews; no complete/production numerical approval policy | generic Risk contracts plus specialized target-adjustment, exposure-cap, cash-floor and research-asset-cash services with source-neutral rule/result/Store/query contracts | stdlib, safe application role enums and neutral Run identity | Orchestration, Persistence adapter, Algorithm Control inspector | `docs/modules/risk-control.md` |
| `quant_trading.orchestration` | Organizes approved cross-owner call order, including exact Standardized State → Target, linked Target → specialized Decision and specialized Decision intent → structural Risk review; contains no formulas or rule outcomes | existing pipelines/coordinators plus `TargetAdjustmentRiskReviewCoordinator` | public Factor/Decision/Risk/Target Position/Run contracts | Algorithm Control and future approved application services | `docs/modules/analysis-decision-pipeline.md` |
| `quant_trading.execution.paper` / `.live` | 两个同级、空白且禁用的未来执行环境边界 | None | None | None；尚无运行调用方 | `docs/modules/execution-environments.md` |
| `quant_trading.portfolio_accounting` | 统一Portfolio Accounting领域：Ledger追加事实，Accounting重放现金/净持仓，Reconciliation只报告差异，Queries提供只读模型 | `LedgerRepository`, `PortfolioAccountingService`, `AccountSnapshot`, `PositionSnapshot`, `ReconciliationService`, `PortfolioAccountingQueryService` | stdlib；内部仅依赖自身公共合同 | Risk只读Provider、Algorithm Control只读页签、未来Execution事件 | `docs/modules/portfolio-accounting.md`, `docs/modules/trading-ledger.md` |
| `quant_trading.capital_allocation` | Explicit user-entered research cash plans, protected reserve/asset buckets, exact conservation, append-only asset transfers and immutable snapshots | `CapitalAllocationService`, `CapitalAllocationStore`, `CapitalAllocationQueryService`, capital schema-v1 models | stdlib, shared errors, neutral Run History contracts | SQLite adapter and Algorithm Control owner page only; no runtime consumer | `docs/modules/capital-allocation.md` |
| `quant_trading.asset_state` | User-defined symbolic state graphs, one-open-cycle-per-symbol history, explicit manual transitions, immutable snapshots/attempts and deterministic replay | `AssetStateService`, `AssetStateStore`, `AssetStateQueryService`, typed schema-v1 commands/models/views | stdlib, shared errors, neutral Run History contracts | SQLite adapter and Algorithm Control owner page only; no runtime consumer | `docs/modules/asset-state.md` |
| `quant_trading.target_position` | Explicit bounded finite-knot definitions, exact manual previews and source-neutral linked-input/provenance contracts with unchanged curve mathematics | `TargetPositionService`, `LinkedTargetPositionService`, engine, Store/query and typed schema-v1 contracts | stdlib, shared errors, neutral Run History contracts | SQLite adapter, Phase 5C orchestration and Algorithm Control owner page only; no trading consumer | `docs/modules/target-position.md` |
| `quant_trading.algorithm_control` | Registry/ParameterSchema management, immutable Factor/Decision versions, safe previews/audit, typed inspectors, research owner pages and separate Target Adjustment Decision/Risk subtabs, including exact read-only Phase 6A–6D chain inspection | `AlgorithmControlController`, `AlgorithmControlPanel`, `RiskChainInspectionService`, `TargetAdjustmentRiskChainView`, typed panels, chart/export services, `python -m quant_trading.algorithm_control` | stdlib, PySide6, Plotly, shared renderer and approved public service/query contracts | Desktop user; local preview and explicit research management | `docs/modules/algorithm-control-gui.md` |
| `quant_trading.algorithm_control.idea_notebook` | Passive local idea notes only; never an algorithm, simulation, accounting, or execution input | `IdeaNote`, `IdeaNotebookService`, `IdeaNotebookPanel` | stdlib; PySide6 only in its panel | Algorithm Control GUI only | `docs/modules/idea-notebook.md` |
| `quant_trading.observability` / `quant_trading.diagnostics` | Error Code 上下文、脱敏轮转日志、异常 Hook 与只读安装诊断 | `configure_logging`, `request_context`, `python -m quant_trading.diagnostics` | Python stdlib；诊断只读复用 market-history 配置/Provider | Application / developer / user support | `docs/development/DEBUGGING.md` |
| `quant_trading.validation` | 统一ValidationResult/Severity/Error Code与fail-closed健康汇总；不拥有业务规则 | `ValidationIssue`, `ValidationResult`, `ValidationRegistry`, `HealthCheckResult` | stdlib, centralized ErrorCode, observability | diagnostics及未来模块自有validator | `docs/development/VALIDATION.md` |

## Verified module status inventory (2026-07-21)

| Area | Status | Evidence / boundary |
|---|---|---|
| Market Data | `IMPLEMENTED_VERIFIED` | Provider/Service/model tests、离线GUI smoke、数据合同与缓存流程 |
| Local Storage | `IMPLEMENTED_VERIFIED` | SQLite unit/integration、首次初始化与integrity=ok |
| GUI | `IMPLEMENTED_VERIFIED` | launcher/Market History/Algorithm Control offscreen启动关闭与GUI测试；物理显示QA仍open |
| Charting | `IMPLEMENTED_VERIFIED` | Market/Factor Plotly builders、共享renderer、UI测试与GUI构造；offscreen GPU回退不影响结果 |
| Configuration | `IMPLEMENTED_VERIFIED` | 有/无凭据、缺目录和默认安全设置验证 |
| Logging | `IMPLEMENTED_VERIFIED` | UTC结构化日志、exception hook与Secret脱敏测试/运行日志 |
| Diagnostics | `IMPLEMENTED_VERIFIED` | 本地只读命令成功；网络检查本次`SKIPPED` |
| Factor Layer | `PARTIALLY_IMPLEMENTED` | 合同/Engine/受限表达式及历史/精确版本比较已验证；无批准生产Factor或激活 |
| Trading Decision Layer | `PARTIALLY_IMPLEMENTED` | 通用合同/Engine/受限规则/trace及隔离的Phase 5D exact target-adjustment preview已验证；无生产Policy、Risk admission或订单 |
| Risk Layer | `PARTIALLY_IMPLEMENTED` | 合同/Engine/Fake规则已验证；无数值Risk政策或账户连接 |
| Execution Layer | `SCAFFOLD_ONLY` | Paper/Live空命名空间与架构测试；无Provider/OrderRequest |
| Algorithm Control GUI | `IMPLEMENTED_VERIFIED` | 本地版本/预览/审计、只读历史及独立Target Adjustment Decision子页签GUI测试；所有交易权限保持禁用 |
| Trading Ledger | `SCAFFOLD_ONLY` | typed模型和内存append/idempotency测试；无持久化/Broker ingestion |
| Portfolio Accounting | `SCAFFOLD_ONLY` | 内存现金/净多头replay及只读快照；无完整成本/P&L |
| Reconciliation | `SCAFFOLD_ONLY` | 内存比较与只报告差异；无Broker连接/自动修正 |
| Research Capital Allocation | `IMPLEMENTED_VERIFIED` | explicit USD basis, protected buckets, exact transfers/snapshots, Schema v4 reload and GUI; inactive/unconsumed |
| Research Asset State | `IMPLEMENTED_VERIFIED` | user-defined symbolic graphs, one open cycle per symbol, manual transitions, Schema v5 reload/replay and GUI; inactive/unconsumed |
| Research Target Position | `IMPLEMENTED_VERIFIED` | user-defined bounded finite-knot curves, exact manual USD previews, Schema v6 reload/traces and GUI; inactive/unconsumed |
| Manual Standardized Price State | `IMPLEMENTED_VERIFIED` | Factor-owned exact manual USD price/reference/positive-scale previews, Schema v7 reload/traces and GUI; disabled, with only explicit Phase 5C query consumption |
| Linked Standardized State → Target Position | `IMPLEMENTED_VERIFIED` | explicit exact source/curve selection, copied scalar/symbol/time, parent/child/source Runs, Schema v8 provenance and GUI; disabled with no trading consumer |
| Target Adjustment Decision Preview | `IMPLEMENTED_VERIFIED` | explicit accepted Phase 5C link selection, exact signed-difference mapping, specialized zero-or-one intent, Schema v9 provenance and Decision GUI; disabled with no Risk or trading consumer |
| Target Adjustment Risk Manual-Review Gate | `IMPLEMENTED_VERIFIED` | explicit Phase 5D intent, locked source/safety/policy-availability gates, manual-review/block-only result, Schema v10 provenance and Risk GUI; disabled with no numerical approval or downstream consumer |
| Single-Asset Exposure-Cap Preview | `IMPLEMENTED_VERIFIED_DISABLED` | explicit Phase 6A result and current immutable same-symbol cap version, locked exact `MAX_TARGET_EXPOSURE_USD@1`, Schema v11 provenance and existing Risk-page GUI; candidate remains unapproved/unconsumed |
| Research Asset Cash-Floor Preview | `IMPLEMENTED_VERIFIED_DISABLED` | explicit positive Phase 6B result and current immutable same-symbol floor version, exact Phase 5C hypothetical basis, locked order-2 `MIN_RESEARCH_ASSET_CASH_USD@1`, Schema v12 provenance and existing Risk-page GUI; candidate remains unapproved/unconsumed |
| Research Asset-Cash Availability Preview | `IMPLEMENTED_VERIFIED_DISABLED` | explicit positive Phase 6C result and explicit Phase 3A plan/exact latest conserved snapshot, locked order-3 `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1`, `research_cash_reserved=false`, Schema v13 provenance and existing Risk-page GUI; no Capital mutation or approval/consumer |
| Paper Trading | `NOT_IMPLEMENTED` | 只有空环境边界；无订单提交 |
| Live Trading | `NOT_IMPLEMENTED` | 空边界且全局disabled |
| Order Construction / Execution Provider | `PLANNED` | 文档方向/类型门；无实际代码或运行能力 |

内部依赖方向：`ui → controller → service → interfaces ← storage/providers`；`controller → charts`；Market History与Algorithm Control presentation可共同依赖无业务语义的`visualization` renderer。`storage`、`providers` 和 `charts` 彼此不依赖。

算法依赖方向：`MarketDataWindow → factors → FactorSnapshot → decision → TradeIntent → risk → RiskDecision`；`orchestration`只能按此顺序调用。Factors不知道Decision/Risk；Decision不知道Risk；Risk只使用公开上游合同，不导入具体Factor/Decision实现、Market History、SQLite、GUI、Alpaca或Execution。

`RiskApprovedTradeIntent`只是未来Order Construction的类型门，仍不是订单或执行授权。Paper/Live Execution仅存在空命名空间，没有接口或行为；Live与自动提交保持关闭。

Portfolio Accounting的事实流为`OrderEvent/TradeFill/CashMovement → Trading Ledger → Accounting → snapshots`。操作事件不改变财务状态；只有确认成交和有效现金事实参与重放。Risk和GUI是只读消费者，Broker仅为Reconciliation参考。

Capital Allocation is a separate research-planning flow: `explicit RESEARCH_INPUT → immutable plan/buckets → manual ASSET_CASH transfer → immutable snapshot/conservation → typed GUI/Run History`. It neither reads nor mutates Portfolio Accounting and has no Decision/Risk/Backtesting/Execution consumer.

Asset State is a separate manual research-history flow: `user-defined symbolic graph → explicit cycle start → manual allowed-edge transition → immutable snapshots/events → deterministic replay → typed GUI/Run History`. Labels carry no built-in financial meaning, and no Factor/Decision/Risk/Capital/Backtesting/Accounting/Execution consumer exists.

Manual Standardized Price State is a separate Factor-owned research flow: `explicit positive Decimal USD price/reference/scale → exact deviation/state → immutable structured evidence → typed GUI/Run History`. Phase 5C orchestration may read one exact selected result and pass its scalar/symbol/time into Target Position, but Factor publishes no generic FactorSnapshot, imports no Target code and has no automatic or trading consumer.

Target Adjustment Decision is a separate Decision-owned research flow: `explicit accepted Phase 5C link → exact persisted signed target difference → INCREASE/DECREASE/HOLD → specialized zero-or-one intent → typed GUI/Run History`. Its result/intent types cannot enter the existing Risk, Backtesting, Accounting or Execution paths.

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
