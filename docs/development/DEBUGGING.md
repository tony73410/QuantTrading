# Debugging Guide

本指南用于定位股票历史数据浏览器的问题。普通用户不需要阅读代码；只需保留错误编号、请求编号和截图。

## 用户发现错误时

1. 不要反复点击或删除本地数据库。
2. 记下弹窗中的 `错误编号`，例如 `QT-API-002`。
3. 记下 `请求编号`，例如 `REQ-...`。
4. 记录当时操作、股票代码、日期范围、时间粒度、复权和 Feed。
5. 截图弹窗和左侧状态区域。
6. 在项目目录找到 `runtime/logs/error.log`；如问题没有弹窗，也查看 `runtime/logs/app.log`。
7. 提供相关时间附近的日志行；不要发送 Alpaca Key、Secret、Authorization Header、密码或账户资料。

日志会自动轮转。`app.log` 和 `error.log` 单个最大 5 MB，各保留 5 个历史文件。`error.log` 保存 Warning 以上事件和堆栈；`app.log` 保存启动、关闭、缓存、API、数据库、图表和用户操作。

## Error Code 分类

| Prefix | Area | Examples |
|---|---|---|
| `QT-CFG` | 配置 | 缺少必要配置 |
| `QT-AUTH` | 凭据/权限 | 缺少、无效或无 Feed 权限 |
| `QT-API` | Alpaca Market Data | 连接、超时、限频、异常响应 |
| `QT-DATA` | 行情数据 | 无数据或完整性校验失败 |
| `QT-DB` | SQLite | 连接、查询或写入失败 |
| `QT-CACHE` | 缓存 Coverage | 覆盖信息不一致 |
| `QT-CHART` | Plotly/QWebEngine | 图表生成或加载失败 |
| `QT-UI` | GUI | 输入无效或操作冲突 |
| `QT-THREAD` | 后台任务 | Worker 未预期异常 |
| `QT-UNKNOWN` | 未分类 | 全局未处理异常 |

具体代码统一定义于 `src/quant_trading/error_codes.py`，不得在其他文件随意创造格式。

## 开发者排查流程

```text
Reproduce
→ Capture logs and Error Code / Request ID
→ Identify failing layer
→ Locate exception and stack
→ Determine root cause
→ Apply the smallest fix
→ Add a regression test
→ Run related tests
→ Run the complete test suite
→ Update logs/BUG_LOG.md
→ Append logs/EDIT_LOG.md
```

分层定位顺序：

```text
GUI
→ Controller
→ HistoricalDataService
→ SQLite Store / Alpaca Market Data Provider
→ Chart Builder / QWebEngine
```

同一次启动通过 `session_id` 关联；一次加载/刷新通过 `request_id` 关联。使用 PowerShell 查找：

```powershell
Select-String -Path runtime\logs\*.log* -Pattern "REQ-这里填请求编号"
Select-String -Path runtime\logs\error.log* -Pattern "QT-API-002"
```

## Bug 修复原则

- `logs/BUG_LOG.md` 同时记录已确认错误和具有具体失败机制的潜在缺陷，是唯一开发Bug来源。
- 先记录，再复现和修改；尚未确认时使用 `Suspected`/`Investigating`，无法复现时标为 `Cannot reproduce`，不能写成 Fixed。
- 修根本原因，不只隐藏弹窗或降低日志等级。
- 优先局部、可测试、可回滚的修改，不因小 Bug 重写模块。
- 每个可信候选或确认 Bug 使用 `BUG-YYYYMMDD-NNN` 写入 `logs/BUG_LOG.md`；纯理论担忧、功能建议和代码风格偏好不伪装成Bug。
- 每项修复写回归测试；确实无法自动测试时写明原因和剩余风险。
- 需要审批、影响数据/交易安全、会引发大范围重构或当前无法安全修复时，保留 `Deferred`，写明规避方法、验证计划和批准需求。
- API 失败必须保留既有 SQLite 数据，Coverage 只能在完整验证和事务成功后更新。
- Debug 模式只增加诊断信息，不得改变 Paper/Live、自动下单或人工确认安全设置。

## Debug 模式

普通模式默认：

```text
QUANT_TRADE_DEBUG=false
QUANT_TRADE_LOG_LEVEL=INFO
```

临时开发诊断：

```powershell
$env:QUANT_TRADE_DEBUG="true"
$env:QUANT_TRADE_LOG_LEVEL="DEBUG"
.\.venv\Scripts\python.exe -m quant_trading.market_history
```

Debug 模式仍会脱敏，不记录 Secret，也不会启用 Paper/Live 订单。

## 诊断命令

默认只做本地、只读或可撤销检查，不访问网络：

```powershell
.\.venv\Scripts\python.exe -m quant_trading.diagnostics
```

检查项目包括 Python、依赖、配置来源、运行目录写权限、SQLite 只读连接、逻辑 Schema 版本、`PRAGMA quick_check`、凭据是否完整和交易安全默认值。结果为 `PASS / WARNING / FAIL / SKIPPED`。

用户明确需要验证 Alpaca Market Data 时，执行一次只读 AAPL 日线请求：

```powershell
.\.venv\Scripts\python.exe -m quant_trading.diagnostics --network
```

该命令不写行情数据库、不访问账户、不提交订单、不显示 Key。普通自动测试永远不使用 `--network`。

## 三类日志的区别

- `runtime/logs/app.log` / `error.log`：程序实际运行事件，默认不提交 Git。
- `logs/BUG_LOG.md`：已发现错误与可信潜在缺陷的唯一开发历史，只追加并提交版本控制。
- `logs/EDIT_LOG.md`：每组代码与文档修改的事实记录，只追加并提交版本控制。
