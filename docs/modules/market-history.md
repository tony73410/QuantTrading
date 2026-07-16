# Market History Module

## Purpose

提供独立桌面控制面板，浏览股票历史 OHLCV Bar，并通过本地 SQLite 缓存减少重复下载。该模块只处理市场数据，不提供投资建议或交易能力。

Alpaca 在本模块中仅承担 **Market Data Provider / 行情数据提供商** 职责；项目同时把 Alpaca 记录为计划主要券商，但未来 execution 必须是独立模块。图表中出现 Alpaca 行情不表示 Paper 或 Live 交易账户已连接。

## User capabilities

- 在窗口最左侧滚动浏览当前 SQLite 中至少有一条 Bar 的全部已下载股票；列表按代码排序，单击代码会同步股票输入框，并使用当前日期范围、粒度、复权与 Feed 自动加载图表。手工加载的新股票在成功写入本地缓存后会加入该列表。
- 输入股票代码，使用不区分大小写的本地常见美股代码自动补全，并选择粒度对应的快捷范围或自定义日期。首次查询点击“加载”；已有图表后切换时间范围或粒度会立即在后台自动加载新选择，不需再次点击。目录按 11 个 GICS 大类行业各收录 10 个常见代码；它只帮助输入，不覆盖全部上市公司、不限制其他代码，也不构成投资建议。
- 选择 10 分钟、30 分钟、1 小时、日线、周线或月线；Raw、拆股、分红或全部复权；IEX 或 SIP Feed。分钟/小时数据默认只显示纽约时间 09:30–16:00 的常规交易时段。
- 切换 Candlestick、折线和 OHLC；折线可选 Open/High/Low/Close/VWAP。
- 开关成交量、范围滑块和自动更新；执行普通加载、最新尾部更新或明确的 Force Refresh。
- 使用 Plotly 悬停、缩放、拖动、范围快捷按钮、范围滑块和重置视图；切换请求日期范围时重置旧缩放窗口，仅改变图表样式时保留当前视图；加载和调整窗口尺寸后图表高度跟随当前可见区域，避免底部年份坐标被挤出窗口。控制面板和状态栏在可见高度不足时在自身区域内纵向滚动，不得因刷新后的状态文字换行而把主窗口撑出屏幕。
- 没有 API 凭据时启动 GUI，并查看已有本地数据。
- 在状态区域查看“行情数据：Alpaca、主要券商：Alpaca、当前环境：Paper Trading、真实交易：未启用、自动下单：未启用、订单确认：需要人工确认”。

## Responsibilities

- 标准化股票、UTC 时间、粒度、复权和 Feed 请求。
- 在 GUI/Controller 边界将 Qt 下拉框返回的请求和图表字符串转换为明确领域枚举，拒绝不支持的选项。
- 通过官方 Alpaca SDK 获取历史股票 Bar，并映射错误、分页和有限重试。
- 使用 SQLite upsert Bar，维护 Coverage 和 Fetch History。
- 计算本地真正缺失区间和最新尾部重叠刷新区间。
- 在后台线程执行网络/数据库加载，向 GUI 返回统一 `DataResult`。
- 为每次加载生成 Request ID；已有结果时，快捷范围和粒度变化立即自动加载，自定义日期、复权和 Feed 变化经过短暂 debounce 后自动加载；加载期间发生的新数据选择会排队，并在当前任务结束后只使用最后选择自动重载。
- 从标准化 Bar 构建 Plotly 图表。
- 将完整离线 Plotly 页面写入自动清理的本地临时文件后交给 QWebEngine 加载，避免内嵌 `setHtml()` 页面大小限制；页面根容器绑定 WebView 可见高度，后续重绘使用 `Plotly.react`。Qt 端在布局稳定后执行延迟 resize，浏览器端使用 `ResizeObserver` 在 Chromium 实际收到 viewport 变化后再次同步，避免用户必须手动重新最大化窗口。

## Non-responsibilities

- 交易策略、技术指标策略、信号、回测、风险、仓位、订单、券商账户或实盘。
- WebSocket、逐笔成交、实时盘口、盘前/盘后专用视图或实时流式更新。
- 判断股票优劣、预测收益或提供投资建议。
- 管理 Alpaca Paper/Live 账户、持仓、订单、成交或交易权限。
- 登录、同步、抓取或自动控制 Fidelity；接收 Fidelity 用户名、密码、双重认证信息或 API Key。
- 生成订单、将订单标记为成交，或向 Alpaca、Fidelity及任何其他券商提交订单。

## Public interfaces

- `HistoricalDataRequest`：标准化 `[start, end)` 历史请求。
- `MarketBar`：带 UTC 时间和明确维度的 OHLCV 数据。
- `HistoricalMarketDataProvider` / `HistoricalDataStore`：可替换 Provider 与 Store Protocol；Store 的 `list_symbols()` 只读列出至少存在一条本地 Bar 的股票代码。
- `HistoricalDataService.load()`：本地优先加载、刷新和离线回退。
- `HistoryController`：GUI 参数转换、并发保护和图表入口。
- `python -m quant_trading.market_history` / `quant-history`：桌面启动入口。

## Inputs

股票代码、开始/结束日期、`Timeframe`、`Adjustment`、`DataFeed`、Force Refresh 标志、图表类型/字段和显示选项。当前 Alpaca 凭据只被 Market Data Provider 从环境变量读取；不存在 Fidelity 凭据输入。

## Outputs

- `DataResult`：Bar、来源、Coverage、实际补充区间、警告和最后成功更新时间。
- Plotly Figure 和 PySide6 桌面状态显示。
- SQLite 缓存与不含 Secret 的 `runtime/logs/app.log`、`runtime/logs/error.log` 轮转日志。

## Dependencies

- Python 3.11–3.14；当前验证 3.14.5。
- PySide6 6.x（含 Qt WebEngine）、Plotly 6.x、alpaca-py 0.x、pandas 2.2–3.x。
- Python 标准库：sqlite3、datetime、decimal、logging、threading。
- pytest 仅为开发/测试依赖。

依赖方向见 `docs/architecture/MODULE_MAP.md`。模块没有其他业务模块依赖。

## Side effects

- 首次启动创建 `runtime/data/market_history.sqlite3` 及其 SQLite 辅助文件。
- GUI 正常启动时创建/轮转 `runtime/logs/app.log` 和 `runtime/logs/error.log`（各 5 MB、保留 5 份）；旧 `market_history.log` 仅保留历史，不再写入。
- 首次图表初始化在操作系统临时目录创建自包含 Plotly HTML；QWebEngineView 销毁时自动删除，不进入 Git 或项目数据库。
- 仅在缓存缺失/过期、用户刷新或自动更新时调用 Alpaca Market Data REST API。
- 不访问 Trading、Account 或 Order API。

## GUI start

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m quant_trading.market_history
```

安装后也可执行 `.\.venv\Scripts\quant-history.exe`。

## Configuration

程序直接读取操作系统环境变量，不自动读取 `.env` 文件。`.env.example` 只提供变量名称和安全默认值。

```text
APCA_API_KEY_ID
APCA_API_SECRET_KEY
MARKET_HISTORY_CACHE_MAX_AGE_HOURS      default 24
MARKET_HISTORY_OVERLAP_BARS             default 5
MARKET_HISTORY_AUTO_REFRESH_MINUTES     default 5, minimum 1
QUANT_TRADE_DEBUG                       default false
QUANT_TRADE_LOG_LEVEL                   default INFO
```

当前代码仅将这两个变量用于访问 Alpaca Market Data。未来经批准的 Paper execution 可以使用明确配置的 Alpaca Paper 凭据，但“存在 Key”永远不等于允许订单提交，更不等于启用 Live。真实值不得写入仓库、`.env.example`、SQLite、Fetch History 或日志。缺少凭据时 Market Data Provider 不创建网络客户端，GUI 禁用行情刷新和自动更新，但“加载”仍可查询本地缓存。项目不读取任何 Fidelity 登录信息。

如果未来同时支持 Paper 和 Live，应使用明确分离的安全配置（例如单独的 Paper/Live 变量或密钥管理条目）、endpoint、状态和日志；当前不提前复制凭据体系。

## Brokerage and execution status

- Market data provider：Alpaca。
- Primary brokerage：Alpaca（计划角色，不代表账户已连接）。
- Execution environment：`ALPACA_PAPER`（默认目标；执行尚未实现）。
- Paper trading enabled：配置状态为开启，但当前没有账户/订单能力。
- Automatic order submission：关闭。
- Live trading：关闭。
- Manual confirmation：开启。
- Optional Fidelity：保留 `FIDELITY` / `MANUAL_FIDELITY` 兼容枚举，非默认、未连接、仅可作为未来手动选项。

当前完全没有订单或 execution 模块，因此不提前创建 `ExecutionProvider`、`AlpacaPaperExecutionProvider` 或 `AlpacaLiveExecutionProvider`。未来若获批实现，execution 必须独立于本行情模块，不得直接操作 SQLite 历史存储。Paper 与 Live 必须区分 endpoint、配置、GUI 状态、日志、订单记录和运行状态；测试只能使用 Fake/Mock Client。

未来 Live 至少需要独立显式配置、醒目 GUI 状态、额外用户确认、风险检查、订单金额/每日亏损/最大持仓限制和紧急停止，并再次获得用户批准。本次未实现或启用任何这些能力。Fidelity 自动登录、浏览器自动化、私有网页抓取及非官方逆向 API 始终不在当前范围。

## Timeframe meaning

- `10Min`：Alpaca 原生 10 分钟 Bar，过滤为纽约时间 09:30（含）至 16:00（不含）。单次最多查看 1 年。
- `30Min`：Alpaca 原生 30 分钟 Bar，使用相同常规时段过滤。单次最多查看 5 年。
- `1Hour`：请求 Alpaca 30 分钟 Bar，先过滤常规时段，再从 09:30 开盘起按小时聚合，避免 Alpaca 原生整点 1 小时 Bar 把 09:00 盘前交易混入第一根。最后一根通常为 15:30–16:00 的半小时尾 Bar。单次最多查看 5 年。
- `1Day`：Alpaca 原生日 Bar，不是 24 小时连续市场数据。
- `1Week`：Alpaca 原生周 Bar。
- `1Month`：Alpaca 原生月 Bar。

不同粒度分别缓存，不能混用 Coverage。10 分钟提供 1/3/6 个月、1 年和自定义快捷范围；30 分钟提供 3/6 个月、1/5 年和自定义；1 小时提供 6 个月、1/5 年和自定义；日/周/月提供 1/5/10 年和自定义。只有内部 `1Hour` 由 30 分钟数据按上述明确规则聚合；日线不会被自行聚合成周/月线。

## Adjustment meaning

- `raw`：原始价格，不处理公司行动。
- `split`：对拆股和反向拆股调整价格及成交量。
- `dividend`：对现金分红调整价格。
- `all`：应用 Alpaca 支持的全部相关调整。

不同复权方式分别缓存，不静默替换。数据含义和可用历史由 Alpaca API 决定。

## Feed and permissions

- `iex`：IEX 单一交易所数据，默认选择。
- `sip`：全美综合市场 Feed，通常取决于账户订阅和历史权限。

没有权限时显示明确错误，不改用其他 Feed。第一版不提供 OTC、BOATS、隔夜或其他 Provider。

## Database design

The existing `runtime/data/market_history.sqlite3` file is now the application's central physical SQLite database. Market History still owns only Bar/Coverage/Fetch History queries; the independent `quant_trading.persistence` adapter owns Factor-history SQL. Sharing one file does not permit either feature to call the other's private storage implementation. Schema version 1 adds `schema_migrations`, `factor_snapshots`, `factor_results`, and `factor_calculation_runs` without moving or rewriting existing Market rows.

默认路径：`runtime/data/market_history.sqlite3`，已被 `.gitignore` 排除。

### market_bars

唯一键：`symbol + timestamp_utc + timeframe + adjustment + feed`。重复下载通过 upsert 更新；价格和 VWAP 用十进制文本保存，数量用整数保存。常用范围查询有组合索引。

### data_coverage

保存每个 symbol/timeframe/adjustment/feed 已成功完成的 `[coverage_start_utc, coverage_end_utc)` 区间和更新时间。相邻或重叠区间在成功事务中合并；没有 Bar 的周末/假日区间仍可记录为成功覆盖。

### fetch_history

保存 request id、请求区间、维度、开始/结束时间、状态、行数和安全错误摘要。Bar、Coverage 和成功状态在一个事务中提交；失败不改变 Bar 或 Coverage。

## Cache and update behavior

### Load

先读取 Coverage。完整且未过期时只从本地返回；有前部、后部或中间缺口时分别请求缺失区间。最终始终重新从 SQLite 查询并返回。

### Refresh latest data

只重新获取请求尾部，默认重叠 5 根所选粒度的 Bar，并执行 upsert。它不删除更早历史。

### Force Refresh

重新请求当前选择的完整区间，但不先删除旧数据。只有新响应完整下载、通过验证并成功写入时才更新 Coverage；失败时继续保留旧数据。

### Staleness and Auto Refresh

包含最新时间的 Coverage 默认 24 小时后视为过期，Load 只刷新尾部。自动更新默认关闭，开启后默认每 5 分钟刷新尾部；图表拖动和显示设置不会触发 API。

## Failure modes

- 无效代码/无数据、缺少或无效凭据、Feed 权限、限频、网络超时、服务端错误、数据验证失败、SQLite 错误。
- 429、5xx 和临时连接错误最多尝试 3 次并指数退避；认证、权限和无效请求不反复重试。
- API 失败且本地有数据时返回 `Offline local cache` 和警告；无本地数据时显示通俗错误。
- 原始异常只进入不含 Secret 的运行日志，不直接显示给用户。

## Data validation

写入前检查 symbol/维度、带时区 UTC、严格时间排序、唯一键、请求范围、有限数值、OHLC 关系、非负 volume/trade count。异常价格不会被静默修正，也不会更新 Coverage。

即使请求结束边界允许延伸到当前时间之后，响应中的单条Bar也不得晚于验证时UTC；未来Bar以`DataValidationError`阻止，不写缓存、不进入Factor或图表。

## Clearing local data

第一版没有选择性删除 GUI。要清除全部历史缓存：先关闭应用，备份后删除 `runtime/data/market_history.sqlite3` 及同目录 SQLite `-wal`/`-shm` 辅助文件；下次启动会重新建库。此操作不可恢复，且之后重新加载会再次消耗 API 配额。

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m pip check
```

测试覆盖 Store、粒度隔离、Coverage、事务回滚、Service 缺口/粒度专属尾部刷新/离线回退、Provider 分钟映射/常规时段过滤/小时聚合/分页/重试、Chart、Controller、真实 Qt 下拉值转换、动态范围选项、端到端本地复用，以及 Alpaca/Paper/Live 安全默认值。所有自动 Provider 测试使用 Fake/Mock 或替换 SDK 底层 HTTP，不访问真实 Alpaca，不提交真实或模拟订单。

## Known limitations

- 只读诊断已用当前环境凭据验证 AAPL IEX Market Data 请求；SIP 或其他权限仍取决于用户订阅。
- 本地自动补全目录覆盖 11 个 GICS 大类行业，但不会自动同步上市、退市、代码或行业分类变化；列表之外的代码仍可自由输入。
- 只支持单股票和 10/30 分钟、1 小时、日/周/月 Bar；无更细分钟、盘前盘后专用模式、批量股票或选择性缓存删除。
- 常规交易时段过滤使用纽约时间 09:30–16:00 的固定窗口，能正确处理夏令时，但当前没有交易所日历依赖，因此无法识别提前收盘日；此类日期 13:00 后若供应商返回盘后 Bar，可能被保留。见 `KNOWN_ISSUES.md` 的 KI-0007。
- 图表数据转换为浏览器 JavaScript Number，用于展示而非精确财务计算。
- QWebEngine 在无 GPU/offscreen 环境可能报告图形上下文回退。
- 正在进行的底层 HTTP 调用无法安全中途终止；关闭窗口会停止计时器、清除排队任务并等待当前任务结束。

## Future extensions

其他行情 Provider 可实现 `HistoricalMarketDataProvider` 后注入 Service，无需修改 GUI、Store、Chart 或主要券商配置。实时行情需要单独设计明确的流式接口、订阅生命周期和安全规则，当前为 **Not implemented**，不得复用本模块暗中开启 WebSocket。

未来 Alpaca execution 必须使用独立接口和适配器，不能把 Market Data Client 扩展成混合数据/账户/订单客户端。Paper execution 为计划中的首选方向；Live execution 仅为未来扩展能力，必须经过接口、凭据、风险和真实资金安全审批。
