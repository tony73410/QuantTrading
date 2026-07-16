# Quantitative Trading Project

本仓库包含项目治理基础和一个本地优先的桌面股票历史数据浏览器。浏览器使用 Alpaca Market Data 获取 10 分钟、30 分钟、1 小时、日、周、月 Bar，保存到本地 SQLite，并通过 Plotly 交互图表展示。分钟和小时图默认只显示纽约时间 09:30–16:00 的常规交易时段。

安全默认值为 **Alpaca Paper / Automatic submission: OFF / Live trading: OFF / Manual confirmation: REQUIRED**。项目现在仅预留了彼此分离的 Paper 与 Live 空白执行边界，没有账户、订单或券商客户端，因此程序不会提交模拟或真实订单。

## Main GUI / 主控制台

普通使用时只需要启动主控制台：

```powershell
.\.venv\Scripts\python.exe -m quant_trading
```

主控制台目前提供“股票历史数据浏览器”和“算法控制中心”两个按钮。点击后会打开独立窗口；关闭其中一个功能不会关闭其他窗口。未来新增的独立GUI功能必须同时在主控制台登记入口。

## Data and brokerage setup / 行情与券商设置

Alpaca is the project's primary market-data provider and planned primary brokerage. The default execution environment is Alpaca Paper Trading. Order execution is not implemented, automatic submission is disabled, and Alpaca Live Trading remains disabled.

本项目主要使用 Alpaca。Alpaca 负责向程序提供股票行情，并计划作为模拟交易及未来经批准的自动交易券商。当前默认环境是 Alpaca Paper Trading；`execution.paper`与`execution.live`目前只是同级空白边界，没有执行行为，所以程序既不会提交模拟订单，也不会提交真实资金订单。

真实交易默认关闭，不能因为配置了 `APCA_API_KEY_ID` 和 `APCA_API_SECRET_KEY` 就自动启用。当前代码只将这些变量用于 Market Data；未来 Paper Execution 必须经过独立实现和批准。Fidelity 被保留为可选的手动方式，非默认、未连接且未启用，项目不接受 Fidelity 登录凭据。

## Start here

1. 阅读 `PROJECT_COMPASS.md` 了解项目方向、当前真实能力、安全边界和仍待决定的问题。
2. 阅读 `AGENTS.md` 了解强制开发工作规则。
3. 阅读 `docs/architecture/OVERVIEW.md` 了解唯一主要架构、模块边界、依赖方向和变更影响规则。
4. 从 `docs/INDEX.md` 查找项目状态、决策和开发标准。
5. 查看 `docs/project/PROJECT_STATE.md` 确认详细实现状态。
6. 查看 `logs/EDIT_LOG.md` 追踪实际修改历史。

`PROJECT_COMPASS.md` 主要面向未来 AI 和开发者；它帮助防止项目方向随着不同开发会话漂移，不替代下面的普通使用说明。

重要的新组件或金融含义不会直接进入实现。开发前使用 [`docs/proposals/README.md`](docs/proposals/README.md) 进行归属、权限、公共合同、冲突、安全、测试和回滚审查；新组件默认关闭，代码完成不代表已经获得运行或交易权限。

## Stock history browser

要求 Python 3.11–3.14。Windows 开发环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m quant_trading.market_history
```

没有 Alpaca Market Data 凭据时 GUI 仍可启动并查看已有本地缓存，但不能下载新数据。凭据和可选缓存参数见 `.env.example`；程序直接读取操作系统环境变量，不会自动加载 `.env` 文件。

为避免一次加载过多数据，10 分钟图最多选择 1 年；30 分钟和 1 小时图最多选择 5 年。日、周、月图仍提供 1/5/10 年和自定义范围。切换粒度后，界面会自动更新可选范围；已有图表时会自动加载新选择，不需要再次点击“加载”。

详细行为、数据库和测试说明见 `docs/modules/market-history.md`。

现有 `runtime/data/market_history.sqlite3` 也是程序的中央本地数据库：除行情缓存外，Schema 已支持保存版本化因子快照、具体因子结果和每次计算记录。完全相同的重复计算不会复制结果，但运行记录仍会保留用于追踪。当前没有正式因子公式，因此普通GUI使用暂时不会产生因子记录。详见 `docs/modules/central-persistence.md`。

## Algorithm architecture status / 算法架构状态

项目已建立三个单向、可以用Fake分别测试的算法合同层：

```text
已完成且截至as-of可用的单资产行情
→ Single-Asset Factor Engine
→ FactorSnapshot
→ Trading Decision Engine
→ TradeIntent（只是意图，不是订单）
→ Risk Control Engine
→ RiskDecision（批准、降低、延迟或阻止；仍不是订单）
→ 停止：订单构建和执行尚未实现
```

目前没有生产激活的因子/Decision、仓位规则或数值Risk Policy。算法控制中心可以用本地缓存预览用户保存的Factor，编辑受限Decision规则，并运行停在Risk层的NO EXECUTION Dry Run；它不会访问券商或提交订单。Factor不知道Decision/Risk，Decision不知道Risk，Risk不能扩大原始意图或调用券商。Live和自动提交仍关闭。详细边界见 `docs/modules/factors.md`、`docs/modules/trading-decision.md` 和 `docs/modules/risk-control.md`。

## Algorithm Control Center / 算法控制中心

在“因子层”页面可以使用**受限表达式**创建或修改Factor。每次保存都会创建不可变新版本，并且默认不启用。它不是任意Python代码编辑器：只能使用界面列出的行情字段、数值参数、算术和聚合函数，不能访问文件、网络、数据库或券商。

在“交易决策层”页面，可以用精确Factor版本、数值比较条件、ALL/ANY组合和明确动作保存不可变Decision版本。新版本默认禁用，不包含股票数量、仓位或订单参数，也不会自动参与运行。

Factor定义、生命周期和Decision定义保存在忽略Git的 `runtime/algorithm_control/`。Factor页可以归档/弃用/恢复版本，并用本地SQLite行情预览；用户勾选保存结果时，Factor历史进入中央SQLite Store。Pipeline页可以运行Factor → Decision → Risk本地演练，但不会构造或提交订单。“执行控制”页只显示Paper/Live均未实现和关闭。详细说明见 [`docs/modules/factor-authoring.md`](docs/modules/factor-authoring.md)。

独立启动组件与配置管理窗口：

```powershell
.\.venv\Scripts\python.exe -m quant_trading.algorithm_control
```

它可以查看已注册的因子、交易决策和风险组件，管理 Draft / Saved / Active 配置版本，检查依赖并查看审计记录。当前没有正式因子公式、交易规则或数值风险规则，所以对应列表会如实为空，Pipeline Dry Run 会保持不可运行。四项系统安全不变量会以锁定状态显示。

这个窗口不会下载行情、读取账户或提交订单。所有预览都标为 **NO EXECUTION**；配置文件保存在 `runtime/algorithm_control/control_state.json`，与历史行情 SQLite 分开且不会提交 Git。

## Diagnostics and error reports / 诊断与错误报告

GUI 错误弹窗会显示稳定的 `Error Code` 和本次操作的 `Request ID`。程序每次启动还有独立 `Session ID`，可在轮转日志中串联 GUI、缓存、Alpaca、SQLite 和图表事件：

```text
runtime/logs/app.log
runtime/logs/error.log
```

运行本地诊断（默认不联网）：

```powershell
.\.venv\Scripts\python.exe -m quant_trading.diagnostics
```

明确需要只读验证 Alpaca Market Data 时：

```powershell
.\.venv\Scripts\python.exe -m quant_trading.diagnostics --network
```

不要发送 API Secret。出现问题时提供错误编号、请求编号、操作步骤和截图即可。完整流程见 `docs/development/DEBUGGING.md`。

本项目仍然不包含正式交易策略、买卖信号、回测、风险批准、订单、Alpaca 执行客户端、Fidelity 自动连接或实盘交易能力。
