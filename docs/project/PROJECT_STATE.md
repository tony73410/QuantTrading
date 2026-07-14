# Project State

## Current phase

First approved user-facing module: stock historical data browser.

## Implemented capabilities

- 仓库级工作规则、文档索引、ADR 机制、编辑日志规范及目录职责说明。
- 需求解释协议：区分用户目标与建议方法，按风险等级处理歧义，并要求通俗汇报和持久记录重要假设。
- PySide6 桌面控制面板：覆盖 11 个 GICS 大类行业、共 110 个常见美股代码的本地前缀自动补全，以及粒度对应的快捷/自定义范围、10/30 分钟、1 小时、日/周/月、复权、Feed、K线/折线/OHLC、字段、成交量、范围滑块及更新控制；已有图表后切换时间范围或粒度会自动后台加载。
- Alpaca Market Data Provider（分钟/小时默认限纽约常规时段）、SQLite 本地缓存、Coverage/Fetch History、粒度隔离、缺失区间补齐、尾部重叠刷新、离线回退和 Plotly 交互图表。
- 应用角色明确分离：主要行情数据提供商和计划主要券商均为 Alpaca，默认目标环境为 `ALPACA_PAPER`。
- Paper execution、账户、持仓和订单能力均为 **Not implemented**；自动下单关闭、Live 关闭、人工确认开启。
- Fidelity 保留为非默认的可选手动兼容状态；未连接、未启用且不读取凭据。
- pytest 单元与集成测试；真实网络被禁止。
- 统一 Debug 基础设施：稳定 Error Code、Session ID/Request ID、用户友好诊断、Secret 脱敏、UTC 结构化 `app.log`/`error.log` 轮转日志、全局/Worker 异常记录和只读诊断命令。
- 交易能力：**Not implemented**。

## Active modules

- `quant_trading.market_history` — 股票历史数据浏览器；见 `docs/modules/market-history.md`。

## Public interfaces

- Python：`HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController` 及 Provider/Store Protocol。
- Desktop entry point：`quant-history` 或 `python -m quant_trading.market_history`。

## Current technology decisions

- Python 支持范围为 3.11–3.14；当前实际验证版本为 3.14.5。
- 历史数据模块采用 PySide6/QWebEngineView、Plotly、官方 `alpaca-py`、pandas、标准库 SQLite 和 pytest。
- 内部时间与数据库时间统一为 UTC；历史请求区间为 `[start, end)`。
- 价格字段以十进制文本保存到 SQLite；图表展示时转换为浮点数。
- 默认数据库为 `runtime/data/market_history.sqlite3`，运行日志为 `runtime/logs/app.log` 与 `runtime/logs/error.log`；这些运行产物不提交 Git。
- 安全边界默认为 DEVELOPMENT / BACKTEST / PAPER-TRADING ONLY。
- `MarketDataProviderType`、`BrokerageType` 与 `ExecutionEnvironment` 使用独立枚举；默认值分别为 `ALPACA`、`ALPACA` 和 `ALPACA_PAPER`。
- 当前 Alpaca 环境变量只用于 Market Data；Key 存在不会启用 Paper/Live 下单。项目不读取或保存 Fidelity 用户名、密码、双重认证信息或 API Key。
- 配置、正式源码、测试、脚本、运行产物和归档内容使用独立目录。
- Git 默认分支为 `main`；提交身份仅在本项目生效；远程 `origin` 指向 `https://github.com/tony73410/QuantTrading.git`。

## Pending decisions

- 是否配置 Alpaca Market Data 凭据以及可用 Feed 权限。
- 后续业务需求及其技术选择；本次决定不自动扩展到交易、策略或其他模块。
- 未来若提出 Paper 账户、订单或自动执行需求，必须先单独定义 execution 模块、订单模型、人工确认和风险边界并重新审批；当前没有此模块。
- Alpaca Live 的独立凭据/endpoint、风险限制、资金限制、每日亏损限制、最大持仓、额外确认和紧急停止方案均待未来明确批准。

## Known limitations

- 只读诊断已用现有凭据成功验证 AAPL IEX Market Data；SIP 等 Feed 仍取决于用户订阅权限。
- 未在实际物理显示器进行人工视觉验收；offscreen GUI 烟雾测试通过但产生 GPU 回退提示。
- 没有安装包分发、自动更新、选择性缓存删除或实时 WebSocket 行情。
- 本地股票代码建议目录不会自动同步上市、退市、代码或行业分类变化；列表之外的代码仍可自由输入。
- 正在执行的同步 Alpaca HTTP 请求无法安全中途取消，窗口关闭可能等待请求结束；见 KI-0006 / BUG-20260713-005。
- 分钟/小时常规时段使用固定 09:30–16:00 纽约时间窗口，当前不能识别提前收盘日；见 KI-0007。

## Next approved work

无。等待用户明确下一项需求；不得自行进入业务开发。

## Last verified date

2026-07-13 17:52:18 -07:00（分钟/小时历史数据、只读 Alpaca 验收与 109 项完整测试）
