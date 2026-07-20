# Changelog

本文件只记录用户可见或版本层面重要的变化，采用倒序维护。内部小改动应只进入 `logs/EDIT_LOG.md`。

## Unreleased

- Added approved Phase 5A **bounded Target Position research**: users can save immutable monotone finite-knot curves with explicit min/neutral/max fractions, run exact manual scalar/USD-basis/current-position previews, inspect Decimal endpoint/interpolation traces, reload successful/invalid/failed attempts and open the related `NO_EXECUTION` Run. Central SQLite Schema v6, Target Position Laboratory/chart and the fifteenth trusted Launcher shortcut are included. The verified real v5→v6 migration preserved 215,340 Market Bars and 365 Fetch History rows and created no default curve/result. No standardized-state formula, automatic Factor/Asset State input, Capital/Accounting adapter, hysteresis, TradeIntent, numerical Risk, Backtesting consumer, Paper, Live or order capability was added.

- Added approved Phase 4A **Asset State and Trading Cycle history**: users can save immutable symbolic state graphs with no built-in financial meaning, start one open research cycle per stock, record explicit allowed manual transitions, close a cycle, reload it after restart and verify deterministic replay. Successful, invalid and failed operations persist under `NO_EXECUTION` Runs in central SQLite Schema v5 and are inspectable through the new Asset State Monitor, `Open Run` and Launcher shortcut. The verified real v4→v5 migration preserved 215,340 Market Bars and 365 Fetch History rows and created no default state definition, stock, cycle or event. No automatic state formula, Target Position, Capital/Accounting consumer, Decision, numerical Risk, Backtesting integration, Paper, Live or order capability was added.
- Fixed Phase 4A operation idempotency/request evidence so a conflicting retry cannot displace the original terminal result and exact transition notes/unknown requested cycle IDs survive reload (`BUG-20260720-002`).
- Fixed the Asset State SQLite boundary to reject completed definition/cycle/transition evidence that does not exactly match its typed operation inputs, Run/stage, graph, predecessor and snapshot chain (`BUG-20260720-003`).

- Added approved Phase 3A **Research Capital Allocation and conservation**: an isolated planning domain accepts only an explicit user-entered USD basis, exactly one protected locked reserve, one protected tactical reserve and zero or more unique stock-cash buckets; accepted transfers are manual asset-cash-to-asset-cash, exact-Decimal, non-overdrawing and zero-sum. Immutable plans, attempts, transfers and snapshots persist in central SQLite Schema v4 under `NO_EXECUTION` Allocation Runs and are inspectable through the new Algorithm Control owner page, `Open Run` and Launcher shortcut. The verified real v3→v4 migration preserved 215,340 Market Bars and 365 Fetch History rows and created no default capital record. No Accounting fact, strategy formula, numerical Risk, Target Position, Backtesting consumer, Paper, Live or order capability was added.
- Fixed the new Capital SQLite Store boundary so a grand-total-conserved but structurally incomplete bucket snapshot, or a transfer snapshot without the exact source/destination delta, is rejected transactionally (`BUG-20260720-001`).

- Added Phase 2B **exact Factor research visualization and export**: one persisted Factor version can be shown against only its exact final source-Bar field with separate axes, explicit invalid/failed/missing or valid non-numeric gaps, typed status/audit details and no value coercion; current bounded records can be copied to atomic CSV/JSON files with exact Decimal strings and overwrite confirmation. Market History and Algorithm Control now reuse one presentation-only Plotly/QWebEngine view. Central SQLite remains Schema v3; no Target Position, Decision export, numerical Risk, Backtesting/accounting integration, Paper, Live or order capability was added.

- Added Phase 2A **Factor/Decision research inspection**: bounded Factor-history filters, exact-version tabular comparison, durable Decision condition and exact sizing-input traces, read-only inspector subtabs with `Open Run`, and an additive central SQLite v2→v3 migration with verified backup/rollback evidence. Legacy uncaptured traces remain explicit; no Target Position, chart/export, formula, numerical Risk, accounting persistence, Paper or Live capability was added.

- Added Phase 1 unified **Run History**: every local Factor/Decision/Risk preview receives a durable `NO_EXECUTION` Run ID with ordered stages, exact version/software bindings, structured warnings/errors and reloadable results. Central SQLite migrated additively from v1 to v2 with a verified pre-migration backup, and Algorithm Control plus the Main Launcher now expose a read-only Run History Explorer. No trading formula, numerical Risk, Portfolio Accounting persistence, Paper or Live capability was added.

- Added a compact **核心功能直达** directory to the primary GUI. It opens all twelve existing Algorithm Control pages directly through trusted static page IDs while keeping feature logic in the owning window and trading authority unchanged.

- Added an isolated **算法 Idea 笔记** page to Algorithm Control for local plain-text ideas, tags, archive and restore. Notes cannot register or invoke Factors, Decisions, Simulation, accounting, Paper, Live, or automatic submission.

- Corrected isolated simulation state and audit accuracy: partial sells now preserve remaining shares, requested notional is distinct from whole-share executed gross, Market Factor inputs reject duplicates/mixed timestamps, and saved-strategy Market Factor traces retain exact versions without cross-run cache leakage.

- Added a detailed **Daily Decision Journal** to Backtesting & Simulation. Every valid trading day and symbol now retains market data, Factor values, Decision-condition results, sizing evidence, non-trade reasons and simulated before/after state; the GUI provides filtering and a read-only inspector separate from the fill table.

- Split Factor authoring into explicit single-stock Asset Factor and Market/Macro Factor pages, and added traceable Decision sizing modes with percentage sliders and read-only account/position references. All new behavior remains disabled/research-only.

- Added user-named, locally saved and versioned Simulation Strategies. Backtesting can select an exact saved strategy before entering dates and simulated starting cash; saved strategies remain research-only and cannot submit orders.

- Added a user-visible **Backtesting & Simulation** launcher entry and isolated research GUI/CLI for the approved SMA20/50 historical baseline. Simulation never connects to broker accounts or submits Paper/Live orders.

- Stabilized validation and GUI error handling: future-dated Market Bars are blocked before caching/downstream use, Decision condition buttons no longer pass Qt checked state as domain data, and local diagnostics now report a unified fail-closed system health status. No trading capability or accounting completion was added.

- Added a read-only `Portfolio & Ledger` tab and an implemented-disabled in-memory Portfolio Accounting architecture scaffold: typed append-only ledger facts, deterministic cash/net-long-quantity replay, immutable account/position contracts, and report-only reconciliation. No broker connection, order submission, Live capability, or production-grade cost/P&L convention was added.

- Added a simple primary QuantTrade desktop launcher with buttons for the historical-data browser and Algorithm Control Center. Each feature opens independently; the launcher contains no market, algorithm, account or order logic.
- Implemented the approved six-phase algorithm workbench as disabled, local-only behavior: non-destructive Factor lifecycle, cached-data Factor preview with optional central-SQLite history, immutable restricted Decision rules, Risk-gated dry run, and read-only Paper/Live execution status. No order path, production activation, numerical Risk limit, or Live capability was added.

### Added

- Added safe GUI Factor authoring with a restricted numeric expression language, immutable disabled-by-default definition versions, and exact Factor-version selection in Decision configuration. This does not add a production Decision rule, activate a Factor, or enable any order path.

- Added empty, disabled `execution.paper` and `execution.live` sibling package boundaries so future simulation work can remain isolated from real-money execution. No account, order, broker client, Paper submission or Live capability was added.

- Added a versioned central SQLite schema and independent Factor-history Store. Meaningful Factor snapshots/results are preserved, exact repeats are deduplicated, and every calculation run remains auditable. No Factor formula or trading behavior was added.

- Added proposal-first Change Admission, typed component ownership/capability/public-contract declarations, disabled-by-default activation stages, fail-closed Pipeline validation, and a GUI Conflict Center. This adds no trading algorithm or order capability.

- 增加独立算法控制中心：通过Registry和通用ParameterSchema展示Factor/Decision/Risk组件，管理Draft/Saved/Active不可变配置版本、依赖验证、锁定安全不变量和审计记录；所有后台预览均为NO EXECUTION，未添加正式算法或订单功能。
- 在TradeIntent与未来Order Construction之间建立独立Risk Control层：支持可解释的批准、拒绝、缩减、延迟、人工审查和股票/系统暂停合同，保守合并多个Fake规则并从类型上阻止原始TradeIntent直接进入未来执行；未加入任何具体风险数值或订单路径。
- 建立相互独立的单资产Factor层与非执行Trading Decision层：通过版本化FactorSnapshot单向通信，提供注册器、合同级引擎、Fake编排和依赖测试；没有加入任何正式公式、交易规则或订单路径。
- 将 `logs/BUG_LOG.md` 扩展为已发现错误与可信潜在缺陷的唯一只追加记录，并建立“先记录、验证、能安全修复则修复、否则透明延期”的强制开发流程。
- 将 `docs/architecture/OVERVIEW.md` 建立为唯一主要架构来源，记录实际模块职责、依赖矩阵、数据流、架构不变量、变更影响范围和漂移风险，并增加无第三方依赖的架构边界测试。
- 增加根目录 `PROJECT_COMPASS.md`，将用户控制权、稳定项目原则、当前语义、意图/假设/开放决定、漂移检测和 AI 实施前后自审建立为长期治理机制。
- 将 Alpaca 明确为主要行情数据提供商和计划主要券商，默认目标环境为 Paper Trading；GUI 显示 Live/自动提交关闭且需要人工确认。
- 实现本地优先的股票历史数据桌面浏览器，支持 Alpaca 日/周/月 Bar、SQLite 增量缓存和 Plotly 交互图表。
- 增加 10 分钟、30 分钟和从 09:30 起聚合的 1 小时历史图；分钟/小时默认限于常规交易时段，并按粒度限制单次范围以控制数据量。
- 增加 PySide6 后台加载控制面板、无凭据离线启动、普通刷新、尾部更新、强制刷新和可选自动更新。
- 将股票代码本地前缀自动补全扩展为覆盖 11 个 GICS 大类行业的 110 个常见美股代码，不访问网络且不限制手动输入。
- 增加 174 项默认不访问真实网络的单元、集成与架构测试，以及 Python 项目依赖清单和安全环境变量示例；真实网络只保留为用户主动运行的只读诊断或明确的只读验收。
- 增加统一 Error Code、Session/Request ID、Secret 脱敏轮转日志、全局异常记录、BUG_LOG、Debug 流程和只读诊断命令。
- 建立语言无关的仓库治理、文档入口、变更追踪和安全边界。
- 建立需求解释协议，要求区分用户目标与建议方法，并按行为和交易风险处理歧义。
- 初始化本地 Git 仓库、`main` 默认分支、项目级提交身份和 GitHub `origin`，并建立首次治理基线提交。

### Fixed

- 修复 PySide6 下拉框将时间粒度、复权和 Feed 作为普通字符串传入，导致首次加载在 SQLite 查询前异常的问题。
- 修复离线 Plotly JavaScript 页面超过 QWebEngine `setHtml()` 可加载大小后只显示白色的问题。
- 修复图表类型和折线字段仍以 Qt 字符串进入 Chart Builder，导致数据加载后停留在初始提示的问题。
- 修复从一年切换到五年等日期范围后仍沿用旧缩放坐标、导致已加载数据看似消失的问题。
- 修复加载期间修改数据选项会丢失新请求、图表主线程异常缺少诊断、重复日志 Handler 和 Alpaca 畸形响应未分类的问题。
- 修复图表加载、最大化或窗口尺寸变化后 Plotly/Chromium viewport 异步更新造成页面保留过大高度、底部年份坐标被挤出可见区域的问题。
- 已有图表时，选择 1/5/10 年会立即在后台自动加载新范围，无需再次点击“加载”；快速连续修改仍只执行最后选择。

### Trading behavior

- Alpaca Paper 是默认目标环境，但执行模块尚未实现；自动提交和 Alpaca Live 保持关闭，人工确认保持开启。Fidelity 只保留为非默认、未连接的可选手动方式。

### Intraday validation

- 新增分钟/小时粒度、请求范围上限、Alpaca 参数映射、纽约常规时段过滤、09:30 小时聚合、SQLite 粒度隔离、尾部重叠刷新和 GUI 动态范围测试。
- 使用现有环境凭据只读请求一个已结束交易日的 AAPL IEX 行情：10 分钟 39 行、30 分钟 13 行、1 小时 7 行；未访问账户或订单，未输出凭据。
- 完整测试 109 passed，保留 1 个上游 `websockets.legacy` 弃用警告；compileall、pip check 和 diff 检查通过。
