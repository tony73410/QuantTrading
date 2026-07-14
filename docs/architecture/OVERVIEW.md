# Architecture Overview

当前实现一个独立的 `quant_trading.market_history` 模块，并保留既有目录边界：

- `src/`：正式 Python 程序代码；当前包含股票历史数据模块。
- `tests/`：unit 与 integration 测试，全部隔离真实 Alpaca 网络。
- `config/`：非敏感配置；不得包含业务逻辑。
- `scripts/`：开发、维护或运维辅助入口；不得承载正式业务逻辑。
- `runtime/`：运行生成内容，默认不进入版本控制。
- `archive/`：仅供历史参考，正式程序不得导入。
- `docs/`：当前状态、架构、模块、决策和开发规则。
- `logs/EDIT_LOG.md`：只追加的开发编辑记录，不是程序运行日志。

## Implemented data flow

```text
PySide6 GUI
  → HistoryController
    → HistoricalDataService
      ├→ SQLiteHistoricalDataStore
      └→ AlpacaHistoricalMarketDataProvider

DataResult
  → PlotlyChartBuilder
    → QWebEngineView
```

`quant_trading.observability` 是横切诊断层：应用启动生成 Session ID，GUI 每次加载生成 Request ID，日志 Context 贯穿 Controller、Service、Store、Provider 与 Chart。它不改变这些模块的依赖方向或业务职责，也不接触订单。`quant_trading.diagnostics` 复用公开配置和 Market Data Provider 进行只读健康检查，默认跳过网络。

GUI 不直接访问 SQLite 或 Alpaca；Chart Builder 不读取数据库；Provider 不决定缓存。未来架构继续由已批准需求逐步形成。

## Market data, brokerage, and execution boundary

```text
Alpaca Market Data
  → local SQLite market database
    → charts / analysis / future approved strategy work
      → Alpaca Execution (Planned; separate module)
        → Alpaca Paper (default target; not implemented)

Alpaca Live (future only; disabled)
```

`MarketDataProviderType.ALPACA`、`BrokerageType.ALPACA` 与 `ExecutionEnvironment.ALPACA_PAPER` 是三个独立概念。应用设置同时规定自动提交关闭、Live 关闭、人工确认开启。当前没有 execution 模块、订单模型或 Alpaca Trading Client；Paper 只是默认目标环境，不代表已连接或可下单。

未来 `AlpacaExecutionProvider` 必须独立于 `AlpacaHistoricalMarketDataProvider`，不得读取本地历史数据库或承担行情存储。Paper 与 Live 必须使用清晰分离的 endpoint、配置、状态和日志；Live 还需风险限制、额外确认及紧急停止机制并重新审批。Fidelity 仅保留为可选的 `MANUAL_FIDELITY` 兼容状态，非默认、未连接、未启用。
