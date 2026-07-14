# Module Map

## Active modules

| Module | Responsibility | Public entry points | Direct dependencies | Used by | Documentation |
|---|---|---|---|---|---|
| `quant_trading.market_history` | 10/30 分钟、1 小时及日/周/月历史股票 Bar 获取、本地缓存、增量更新和桌面展示 | `HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController`, `python -m quant_trading.market_history` | Python stdlib, alpaca-py, pandas, Plotly, PySide6 | Desktop user | `docs/modules/market-history.md` |
| `quant_trading.observability` / `quant_trading.diagnostics` | Error Code 上下文、脱敏轮转日志、异常 Hook 与只读安装诊断 | `configure_logging`, `request_context`, `python -m quant_trading.diagnostics` | Python stdlib；诊断只读复用 market-history 配置/Provider | Application / developer / user support | `docs/development/DEBUGGING.md` |

内部依赖方向：`ui → controller → service → interfaces ← storage/providers`；`controller → charts`。`storage`、`providers` 和 `charts` 彼此不依赖。

应用级 `quant_trading.application_settings` 只声明角色与安全默认值：Alpaca 是 Market Data Provider 和 Primary Brokerage，默认目标环境为 `ALPACA_PAPER`，自动下单与 Live 均关闭，人工确认开启。它不连接账户、不提交订单，也不构成 execution 模块。

未来经批准的行情 Provider 可替换 `HistoricalMarketDataProvider`，无需改变券商角色；未来经批准的 Alpaca execution 模块必须独立于 `market_history`，不得反向依赖具体行情 Provider 或直接操作 SQLite 历史数据库。Fidelity/`MANUAL_FIDELITY` 仅为非默认兼容选项。

## How to update

每当模块获批并实现后，在此记录：模块名称、职责摘要、公共接口、直接依赖、主要调用方和对应 `docs/modules/<module-name>.md` 链接。该映射必须反映实际代码，不能提前列出假设模块。

公共接口或依赖方向变化属于审批事项，批准和实施后必须同步本文件及相关模块文档。
