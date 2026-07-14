# Quantitative Trading Project

本仓库包含项目治理基础和一个本地优先的桌面股票历史数据浏览器。浏览器使用 Alpaca Market Data 获取 10 分钟、30 分钟、1 小时、日、周、月 Bar，保存到本地 SQLite，并通过 Plotly 交互图表展示。分钟和小时图默认只显示纽约时间 09:30–16:00 的常规交易时段。

安全默认值为 **Alpaca Paper / Automatic submission: OFF / Live trading: OFF / Manual confirmation: REQUIRED**。当前尚未实现执行模块，因此程序不会提交模拟或真实订单。

## Data and brokerage setup / 行情与券商设置

Alpaca is the project's primary market-data provider and planned primary brokerage. The default execution environment is Alpaca Paper Trading. Order execution is not implemented, automatic submission is disabled, and Alpaca Live Trading remains disabled.

本项目主要使用 Alpaca。Alpaca 负责向程序提供股票行情，并计划作为模拟交易及未来经批准的自动交易券商。当前默认环境是 Alpaca Paper Trading，但执行模块尚未实现，所以程序既不会提交模拟订单，也不会提交真实资金订单。

真实交易默认关闭，不能因为配置了 `APCA_API_KEY_ID` 和 `APCA_API_SECRET_KEY` 就自动启用。当前代码只将这些变量用于 Market Data；未来 Paper Execution 必须经过独立实现和批准。Fidelity 被保留为可选的手动方式，非默认、未连接且未启用，项目不接受 Fidelity 登录凭据。

## Start here

1. 阅读 `AGENTS.md` 了解强制工作规则。
2. 从 `docs/INDEX.md` 查找项目状态、架构、决策和开发标准。
3. 查看 `docs/project/PROJECT_STATE.md` 确认已实现内容和待决事项。
4. 查看 `logs/EDIT_LOG.md` 追踪实际修改历史。

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

本项目仍然不包含交易策略、买卖信号、回测、订单、Alpaca 执行客户端、Fidelity 自动连接或实盘交易能力。
