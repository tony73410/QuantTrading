# Bug Log

本文件记录已确认的软件缺陷，只追加、不删除历史。状态变化通过新增更正记录或后续 Bug 条目说明；程序运行异常写入 `runtime/logs/error.log`，代码修改历史写入 `logs/EDIT_LOG.md`。

## BUG-20260713-001

### Title
加载期间修改数据范围会丢失新请求。

### Status
Fixed

### Severity
Medium

### Area
GUI / Threading

### Environment
Windows 11 10.0.26200；Python 3.14.5；PySide6 6.11.1。

### Reproduction steps
1. 启动一次需要等待的历史数据加载。
2. 在任务完成前切换日期范围、粒度、复权或 Feed。
3. 等待原任务完成。

### Expected behavior
当前任务结束后自动执行用户最后选择的数据请求，旧结果不应覆盖新选择。

### Actual behavior
`_schedule_reload()` 在 `_busy=True` 时直接返回；控件变化永久丢失，旧结果按旧参数显示。

### Error message
无错误提示。

### Technical exception
无异常；属于事件状态丢失。

### Location
`src/quant_trading/market_history/ui/history_panel.py`，`HistoryPanel._schedule_reload`、`_on_load_succeeded`。

### Root cause
加载状态只用于阻止并发任务，没有保存“忙碌期间发生了新请求”的意图。

### Fix
增加 `_reload_after_busy` 队列标志；忙碌期间发生数据控件变化或再次加载时记录意图，旧任务结束后自动加载最新控件值，并在新结果到达前保留原有有效图表。

### Files changed
- `src/quant_trading/market_history/ui/history_panel.py`
- `tests/unit/market_history/test_history_panel_roles.py`

### Validation
针对性 GUI 测试和完整 pytest。

### Regression test
`tests/unit/market_history/test_history_panel_roles.py::test_control_change_during_load_is_queued_instead_of_lost`

### Risk
队列只保留最后一次控件状态，不会为连续每次变化分别发起网络请求，这是刻意的合并行为。

### Rollback
移除 `_reload_after_busy` 及成功/失败回调中的后续加载逻辑；会恢复请求丢失问题。

### Related logs
修复前无错误日志；属于无异常状态 Bug。修复后后续加载具有独立 Request ID。

## BUG-20260713-002

### Title
GUI 主线程图表异常没有错误编号或用户可见诊断信息。

### Status
Fixed

### Severity
Medium

### Area
Chart / GUI / Logging

### Environment
Windows 11 10.0.26200；Python 3.14.5；Plotly 6.9.0；PySide6 6.11.1。

### Reproduction steps
1. 让 Chart Builder 或临时 Plotly HTML 创建抛出异常。
2. 触发数据加载或图表设置重绘。

### Expected behavior
写入带堆栈的 `error.log`，GUI 显示稳定错误编号与 Request ID，同时保留已有数据。

### Actual behavior
`_redraw_chart()` 没有异常边界；异步 WebEngine 加载失败也没有反馈，窗口可能停留空白或旧图。

### Error message
无统一提示。

### Technical exception
取决于原始 Chart/文件/WebEngine 失败；此前可从 Qt 主线程逸出。

### Location
`src/quant_trading/market_history/ui/history_panel.py`，`_PlotlyView.show_figure`、`_on_load_finished`、`HistoryPanel._redraw_chart`。

### Root cause
图表路径位于 GUI 主线程，未经过已有 Worker 异常映射路径。

### Fix
增加 `ChartError/QT-CHART-001`、图表同步异常捕获、WebEngine 失败 Signal、结构化堆栈日志和包含 Error Code/Request ID 的用户提示。

### Files changed
- `src/quant_trading/errors.py`
- `src/quant_trading/error_codes.py`
- `src/quant_trading/market_history/ui/history_panel.py`
- `tests/unit/market_history/test_history_panel_roles.py`

### Validation
注入 `RuntimeError`，验证 GUI 诊断文字和状态字段。

### Regression test
`tests/unit/market_history/test_history_panel_roles.py::test_chart_failure_shows_error_code_and_request_id`

### Risk
浏览器内部 JavaScript 在页面成功加载后的异步运行时错误仍受 Qt WebEngine 可观测能力限制。

### Rollback
移除 ChartError 边界和 render_failed Signal；会恢复静默空白风险。

### Related logs
修复后 `error_code=QT-CHART-001 operation=render_chart`。

## BUG-20260713-003

### Title
重复初始化运行日志会重复添加 Handler。

### Status
Fixed

### Severity
Low

### Area
Logging

### Environment
Windows 11；Python 3.14.5 标准库 logging。

### Reproduction steps
1. 在同一 Python 进程两次调用日志初始化。
2. 写入一条 Warning。

### Expected behavior
始终只有 app/error 两个 QuantTrade Handler，每条记录各写一次。

### Actual behavior
旧实现每次调用都向 root logger 追加 Handler，导致重复日志和未关闭文件句柄。

### Error message
无。

### Technical exception
无异常；表现为重复日志行。

### Location
旧 `src/quant_trading/market_history/app.py::configure_runtime_logging`。

### Root cause
初始化前没有识别并关闭项目自己创建的旧 Handler。

### Fix
统一 `configure_logging()` 为项目 Handler 加标记，重复配置前移除并关闭旧 Handler，再创建 `app.log` 与 `error.log`。

### Files changed
- `src/quant_trading/observability.py`
- `src/quant_trading/market_history/app.py`
- `tests/unit/test_observability.py`

### Validation
同一测试中连续初始化两次，断言项目 Handler 数量为 2 且敏感内容只以脱敏形式写入。

### Regression test
`tests/unit/test_observability.py::test_rotating_logs_are_idempotent_contextual_and_redacted`

### Risk
不会移除第三方或用户添加的非 QuantTrade Handler。

### Rollback
恢复旧日志初始化函数；会恢复重复写入风险。

### Related logs
`runtime/logs/app.log`、`runtime/logs/error.log`。

## BUG-20260713-004

### Title
Alpaca 异常响应格式会变成未分类后台异常。

### Status
Fixed

### Severity
Medium

### Area
API / Logging

### Environment
Python 3.14.5；alpaca-py 0.43.5。

### Reproduction steps
1. 使用 Fake Client 返回缺少时间戳/OHLC 字段的 Bar。
2. 调用 `fetch_bars()`。

### Expected behavior
映射为安全的行情响应错误，保留本地数据，并使用稳定错误编号。

### Actual behavior
转换阶段的 `AttributeError/TypeError/ValueError` 直接逸出 Provider，最终只能显示“未预期错误”。

### Error message
发生未预期错误，请查看运行日志。

### Technical exception
例如 `AttributeError` 或 `TypeError`。

### Location
`src/quant_trading/market_history/providers/alpaca_provider.py::fetch_bars`。

### Root cause
HTTP 调用异常已映射，但成功响应后的字段转换没有异常边界。

### Fix
将响应转换异常映射为 `ProviderError/QT-API-004`，保留原始 cause 和堆栈，并显示旧本地数据已保留。

### Files changed
- `src/quant_trading/market_history/providers/alpaca_provider.py`
- `tests/unit/market_history/test_alpaca_provider.py`

### Validation
使用畸形 Fake Bar 验证错误类型、编号和用户提示。

### Regression test
`tests/unit/market_history/test_alpaca_provider.py::test_malformed_response_is_mapped_instead_of_escaping_background_worker`

### Risk
只捕获明确的数据转换异常，不会吞掉 KeyboardInterrupt/SystemExit。

### Rollback
移除转换阶段异常映射；会恢复未分类后台错误。

### Related logs
修复后 `error_code=QT-API-004 operation=load_history`。

## BUG-20260713-005

### Title
关闭窗口时可能等待无法取消的底层 HTTP 请求。

### Status
Deferred

### Severity
Medium

### Area
Threading / API

### Environment
Windows 11；PySide6 6.11.1；alpaca-py 0.43.5。

### Reproduction steps
1. 启动一个网络层长期不返回的行情请求。
2. 请求进行中关闭窗口。

### Expected behavior
窗口在有限时间内关闭，后台请求安全取消或与 UI 生命周期隔离。

### Actual behavior
`closeEvent()` 调用无超时的 `QThreadPool.waitForDone()`；底层同步 SDK 请求没有安全取消接口时，关闭可能等待到请求返回。

### Error message
通常无错误提示，表现为关闭延迟。

### Technical exception
无；同步阻塞。

### Location
`src/quant_trading/market_history/ui/history_panel.py::closeEvent`。

### Root cause
同步 HTTP 调用与 Qt Worker 都没有协作取消令牌；强制杀死线程可能破坏 SQLite/SDK 状态，因此不能用不安全方式假装修复。

### Fix
Deferred。当前关闭会停止计时器、清除尚未开始的任务，并等待正在执行的操作安全结束。

### Files changed
- `KNOWN_ISSUES.md`
- `logs/BUG_LOG.md`

### Validation
代码路径审查；普通空闲关闭和有限 Fake Worker 由 GUI 测试覆盖。无限网络挂起未在自动测试中制造。

### Regression test
Not implemented；需要未来为 Provider 引入明确超时与协作取消设计。

### Risk
网络故障时窗口关闭可能延迟，但不会为快速退出而破坏数据库事务。

### Rollback
无修复可回滚。

### Related logs
请求开始记录可通过 Session ID/Request ID 检索；进程强制终止前可能没有完成日志。

## BUG-20260713-006

### Title
Qt 后台 Worker 日志丢失 Session ID。

### Status
Fixed

### Severity
Medium

### Area
Threading / Logging

### Environment
Windows 11；Python 3.14.5；PySide6 6.11.1。

### Reproduction steps
1. 启动 GUI 并加载 AAPL 本地缓存。
2. 使用 GUI 显示的 Request ID 搜索 `runtime/logs/app.log`。
3. 对比 GUI 和 Service 日志的 `session_id`。

### Expected behavior
同一次启动的 GUI 和后台 Service 日志具有同一个 Session ID。

### Actual behavior
GUI 行为显示 `SES-...`，Qt 线程池内的 Service 日志显示 `session_id=-`；Request ID 正常。

### Error message
无用户错误提示；影响诊断关联。

### Technical exception
无异常。

### Location
`src/quant_trading/market_history/ui/history_panel.py::_LoadWorker.run`；`src/quant_trading/observability.py`。

### Root cause
Python `ContextVar` 不会自动传播到 Qt `QThreadPool` 创建/复用的线程。

### Fix
Worker 创建时捕获当前 Session ID，运行时通过可恢复的 `session_context` 显式设置 Session，再进入 Request 上下文。

### Files changed
- `src/quant_trading/observability.py`
- `src/quant_trading/market_history/ui/history_panel.py`
- `tests/unit/market_history/test_history_panel_roles.py`

### Validation
直接执行 Worker 并在 operation 中读取 Session/Request Context；之后重新运行真实 GUI 缓存加载并搜索日志。

### Regression test
`tests/unit/market_history/test_history_panel_roles.py::test_background_worker_inherits_session_and_request_context`

### Risk
上下文只在 Worker 操作期间设置并在结束后恢复，避免污染 Qt 线程池复用线程。

### Rollback
移除 `session_context` 和 Worker 捕获字段；会恢复后台日志缺少 Session ID。

### Related logs
发现证据：`REQ-2A17C9C9558B` 的 Service 日志原为 `session_id=-`；修复后复验应显示与 GUI 相同的 `SES-...`。

### Verification update
2026-07-13 16:55:31 -07:00：实际 GUI 本地缓存加载复验通过。`REQ-B61A580A94F9` 的 GUI、Controller、Service、Store 与 Chart 日志均关联到同一个 `SES-5D86DC5EB9D9`；完整测试为 90 passed。

## BUG-20260713-007

### Title
图表加载后高度超过 WebView，底部年份坐标被挤出窗口。

### Status
Fixed

### Severity
Medium

### Area
Chart / GUI

### Environment
Windows 11；Python 3.14.5；PySide6/QWebEngine 6.11.1；Plotly 6.9.0。

### Reproduction steps
1. 启动股票历史数据浏览器并选择五年数据、成交量和范围滑块。
2. 加载 GOOGL 等股票，或在加载完成后改变窗口尺寸。
3. 观察图表底部年份坐标是否仍在窗口内。

### Expected behavior
Plotly 页面高度始终等于当前 WebView 可见高度；价格图、成交量、范围滑块和年份坐标均位于窗口内。

### Actual behavior
部分加载中页面沿用首次布局时计算的过大高度，价格图和成交量整体向下延伸，年份坐标落到窗口可见区域之外，看起来像 GUI 被自动放大。

### Error message
无错误对话框；视觉表现为底部坐标被裁掉。

### Technical exception
无 Python Exception。浏览器页面布局高度与 Qt WebView viewport 不一致。

### Location
`src/quant_trading/market_history/ui/history_panel.py::_PlotlyView`。

### Root cause
`plotly.io.to_html()` 生成的根图表使用百分比高度，但 HTML/body 没有明确绑定 QWebEngine viewport；首次加载、`Plotly.react` 和 Qt resize 后也没有统一调用 `Plotly.Plots.resize()`。因此页面可能保留加载瞬间的旧像素高度并产生纵向溢出。

### Fix
为 HTML、body 和图表根节点注入 100% viewport 高度、零 margin 和隐藏溢出的响应式样式；在首次页面完成、每次 `Plotly.react` 完成及 QWebEngine `resizeEvent` 后显式调用 Plotly resize。JavaScript 使用独立函数作用域，避免连续执行时 `const` 名称冲突。

### Files changed
- `src/quant_trading/market_history/ui/history_panel.py`
- `tests/unit/market_history/test_history_panel_roles.py`
- `docs/modules/market-history.md`
- `docs/project/PROJECT_STATE.md`
- `CHANGELOG.md`
- `logs/BUG_LOG.md`
- `logs/EDIT_LOG.md`

### Validation
使用真实 offscreen Qt WebEngine 加载离线 Plotly 页面，验证首次页面无纵向溢出；执行 `Plotly.react` 后数据正常变化；将 WebView 从 900×600 改为 900×450 后，图表高度与 `window.innerHeight` 误差不超过 1 像素，body 和图表底边均不超过 viewport。完整 pytest、compileall、pip check 和 diff 检查通过。

### Regression test
`tests/unit/market_history/test_history_panel_roles.py::test_plotly_bundle_loads_from_local_file_and_executes_javascript`

### Risk
页面隐藏自身纵向滚动条，图表必须依赖 Qt 外层窗口提供空间；这是期望行为，Plotly 内部缩放、拖动和范围滑块不受影响。

### Rollback
移除 `_RESPONSIVE_STYLE`、`_resize_plot()`、`resizeEvent()` 及 `Plotly.react` 后的 resize 调用，并撤销对应测试和文档；会恢复底部坐标可能被裁切的问题。

### Related logs
用户截图显示请求 `REQ-81383D39A63A` 与 `REQ-0C2F9A874A0C` 的不同布局结果；该问题无运行异常堆栈。

## BUG-20260713-008

### Title
Qt 窗口稳定前执行 Plotly resize，加载后仍需手动重新最大化。

### Status
Fixed

### Severity
Medium

### Area
Chart / GUI / Threading

### Environment
Windows 11；Python 3.14.5；PySide6/QWebEngine 6.11.1；Plotly 6.9.0。

### Reproduction steps
1. 在最大化的 GUI 中加载带成交量和范围滑块的多年数据。
2. 等待图表完成动态刷新。
3. 观察图表是否向下延伸；再切换一次非最大化/最大化状态。

### Expected behavior
图表在首次加载和任何窗口状态下都自动适配最终可见高度，不需要用户重新最大化。

### Actual behavior
上一版同步 resize 在 Qt `resizeEvent` 后立即执行，但 Chromium renderer 的 viewport 可能尚未收到最终尺寸；Plotly 仍按旧高度布局。用户再次最大化产生第二次 resize 后才恢复。

### Error message
无错误对话框；表现为图表底部和年份坐标超出屏幕。

### Technical exception
无 Python Exception；Qt 主窗口布局和 Chromium renderer viewport 的异步时序问题。

### Location
`src/quant_trading/market_history/ui/history_panel.py::_PlotlyView.resizeEvent`、`_on_load_finished`、`_react`。

### Root cause
`QTimer.singleShot(0, ...)` 只等待下一轮 Qt event loop，不能保证 Chromium renderer 已应用最终 viewport。上一版测试只检查稳定后的简单 Figure，没有确认浏览器尺寸观察器以及 K线、成交量、范围滑块组合在快速 resize 后的行为。

### Fix
增加 150ms 单次 Qt resize debounce，在窗口布局稳定后再调用 Plotly；页面加载完成后安装浏览器 `ResizeObserver`，由浏览器在 document viewport 实际改变时通过 `requestAnimationFrame` 同步 Plotly。动态 `Plotly.react` 后也启动延迟同步，连续 resize 只保留最后一次。

### Files changed
- `src/quant_trading/market_history/ui/history_panel.py`
- `tests/unit/market_history/test_history_panel_roles.py`
- `docs/modules/market-history.md`
- `docs/project/PROJECT_STATE.md`
- `CHANGELOG.md`
- `logs/BUG_LOG.md`
- `logs/EDIT_LOG.md`

### Validation
真实 offscreen QWebEngine 测试确认 `ResizeObserver` 已安装、Qt resize debounce 已激活；使用 50 根 K线、成交量子图和范围滑块执行 `Plotly.react`，随后将 WebView 从 900×600 快速改为 900×450，等待稳定后 body、图表底边均不超过 viewport，图表高度误差不超过 1 像素。完整测试和静态检查通过。

### Regression test
`tests/unit/market_history/test_history_panel_roles.py::test_plotly_bundle_loads_from_local_file_and_executes_javascript`

### Risk
窗口改变后图表可能在最多约 150ms 内完成最终重排；期间保留旧图，不阻塞 GUI，也不触发行情 API。

### Rollback
移除 `_plot_resize_timer` 和 `_install_resize_observer()`，恢复 resizeEvent 的立即调用；会恢复需要再次最大化才能校正尺寸的时序问题。

### Related logs
用户在 `BUG-20260713-007` 修复后继续报告实际显示器仍可复现；该视觉问题不产生 Error Code 或堆栈。
