# Module Map

本文件是简要模块索引。系统结构、完整职责/非职责、依赖矩阵、数据流和架构不变量的唯一主要来源是 [`OVERVIEW.md`](OVERVIEW.md)。两者冲突时应报告漂移并以实际代码、Compass 与已批准决策核实，而不是静默合理化冲突。

## Active modules

| Module | Responsibility | Public entry points | Direct dependencies | Used by | Documentation |
|---|---|---|---|---|---|
| `quant_trading.market_history` | 10/30 分钟、1 小时及日/周/月历史股票 Bar 获取、本地缓存、增量更新和桌面展示 | `HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController`, `python -m quant_trading.market_history` | Python stdlib, alpaca-py, pandas, Plotly, PySide6 | Desktop user | `docs/modules/market-history.md` |
| `quant_trading.factors` | 将单资产、截至as-of可用的完整行情转换为版本化、策略中立FactorSnapshot；无正式公式 | `FactorCalculator`, `SingleAssetFactorEngine`, `FactorSnapshot` | stdlib, public MarketBar/dimension models | Orchestration or independent research caller | `docs/modules/factors.md` |
| `quant_trading.decision` | 消费公开FactorSnapshot并调用注入Policy，输出非执行DecisionResult/TradeIntent；无正式规则 | `TradingDecisionPolicy`, `TradingDecisionEngine`, `DecisionResult`, `TradeIntent` | stdlib, Factor public models/interfaces | Orchestration or independent decision caller | `docs/modules/trading-decision.md` |
| `quant_trading.risk` | 对TradeIntent执行独立、保守、可解释的执行前风险裁决；无具体数值规则 | `RiskPolicy`, `RiskEngine`, `RiskDecision`, `RiskApprovedTradeIntent` | stdlib, application role enum, public Factor/Decision models | Orchestration or independent risk caller | `docs/modules/risk-control.md` |
| `quant_trading.orchestration` | 仅组织Factor → Decision以及可选的Factor → Decision → Risk调用和上下文传递 | `AnalysisDecisionPipeline`, `TradingEvaluationPipeline` | public Factor/Decision/Risk engines/models | Future approved application service | `docs/modules/analysis-decision-pipeline.md` |
| `quant_trading.algorithm_control` | 通过Registry和ParameterSchema管理组件、版本配置、依赖验证、安全预览和审计 | `AlgorithmControlController`, `AlgorithmControlPanel`, `python -m quant_trading.algorithm_control` | stdlib, PySide6, public Factor/Decision/Risk result contracts | Desktop user / future composition root | `docs/modules/algorithm-control-gui.md` |
| `quant_trading.observability` / `quant_trading.diagnostics` | Error Code 上下文、脱敏轮转日志、异常 Hook 与只读安装诊断 | `configure_logging`, `request_context`, `python -m quant_trading.diagnostics` | Python stdlib；诊断只读复用 market-history 配置/Provider | Application / developer / user support | `docs/development/DEBUGGING.md` |

内部依赖方向：`ui → controller → service → interfaces ← storage/providers`；`controller → charts`。`storage`、`providers` 和 `charts` 彼此不依赖。

算法依赖方向：`MarketDataWindow → factors → FactorSnapshot → decision → TradeIntent → risk → RiskDecision`；`orchestration`只能按此顺序调用。Factors不知道Decision/Risk；Decision不知道Risk；Risk只使用公开上游合同，不导入具体Factor/Decision实现、Market History、SQLite、GUI、Alpaca或Execution。

`RiskApprovedTradeIntent`只是未来Order Construction的类型门，仍不是订单或执行授权。当前不存在Execution模块，Live与自动提交保持关闭。

算法控制中心是独立管理面，不在执行数据路径中；它不依赖具体Alpaca/SQLite/Execution实现，所有Preview均为NO EXECUTION。

应用级 `quant_trading.application_settings` 只声明角色与安全默认值：Alpaca 是 Market Data Provider 和 Primary Brokerage，默认目标环境为 `ALPACA_PAPER`，自动下单与 Live 均关闭，人工确认开启。它不连接账户、不提交订单，也不构成 execution 模块。

未来经批准的行情 Provider 可替换 `HistoricalMarketDataProvider`，无需改变券商角色；未来经批准的 Alpaca execution 模块必须独立于 `market_history`，不得反向依赖具体行情 Provider 或直接操作 SQLite 历史数据库。Fidelity/`MANUAL_FIDELITY` 仅为非默认兼容选项。

Admission subcomponents: `quant_trading.algorithm_control.admission_models`, `admission_service`, `capabilities`, and `contracts` own component identity, unique responsibility ownership, layer capability policy, versioned contract declarations, staged activation, and fail-closed Pipeline conflict checks. They contain no algorithm or execution behavior.

## How to update

每当模块获批并实现后，在此记录：模块名称、职责摘要、公共接口、直接依赖、主要调用方和对应 `docs/modules/<module-name>.md` 链接。该映射必须反映实际代码，不能提前列出假设模块。

公共接口或依赖方向变化属于审批事项，批准和实施后必须同步本文件及相关模块文档。
