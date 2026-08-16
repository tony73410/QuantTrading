# Bug Log — Discovered Errors and Potential Defects

本文件是 QuantTrade 在开发、编辑、测试、审查和实际运行过程中发现的**错误与可信潜在缺陷的唯一开发记录**。已确认和暂未确认的问题都必须进入本文件；旧记录只追加、不删除、不改写成“从未发生”。状态变化通过条目内追加 Verification update 或新的更正记录说明。

程序运行异常写入 `runtime/logs/error.log`，代码修改事实写入 `logs/EDIT_LOG.md`，当前仍影响用户的问题还应在 `KNOWN_ISSUES.md` 保留简要状态和规避方法。这三个文件不得互相替代。

## Mandatory discovery workflow

未来每次代码或重要配置编辑都必须执行：

1. **Discover**：检查相关代码、测试、运行日志、异常路径和用户操作是否暴露错误或可信风险。
2. **Record first**：一旦问题具有具体位置、现象、失败机制或可验证证据，立即分配 `BUG-YYYYMMDD-NNN` 并记录；不得因为尚未复现就隐瞒。
3. **Classify honestly**：未确认使用 `Suspected` 或 `Investigating`；已复现使用 `Open`；不得把猜测写成已确认事实。
4. **Fix when safe and in scope**：能够确认且可用小范围、非破坏性方式修复时，修复根因并增加回归测试。
5. **Defer transparently**：无法复现、需要审批、存在数据/交易风险、会扩大当前任务或无法安全修复时，不得猜测性改代码；记录原因、影响、临时规避方法、验证计划和所需决定。
6. **Verify**：只有取得真实测试或运行证据后才可标记 `Fixed`。修复失败或证据不足必须保持未解决状态。
7. **Report**：任务最终报告列出本次发现的 Bug ID；若没有发现，也明确写“未发现新的可信缺陷”，不得编造条目。

模糊的代码风格偏好、尚未批准的功能、纯理论且没有具体失败机制的担忧，不应伪装成 Bug。它们应进入架构风险、Open Decision 或建议列表。只要存在具体失败机制，即使暂时不能复现，也应以 `Suspected` 记录。

## Status definitions

| Status | Meaning |
|---|---|
| `Suspected` | 有具体风险机制或证据，但尚未复现或确认。 |
| `Investigating` | 正在收集复现、日志或根因证据。 |
| `Open` | 已确认，尚未修复。 |
| `Fixed` | 根因已修复并有真实验证证据。 |
| `Cannot reproduce` | 按记录环境和步骤暂时无法复现；保留证据与后续触发条件。 |
| `Deferred` | 已确认或可信，但当前无法安全修复、需要批准或超出合理范围。 |
| `Rejected` | 经验证不是程序错误；必须保留为什么排除的证据。 |

## Required entry fields

每个新条目至少包含：Title、Status、Severity、Area、Discovery context、Environment、Reproduction steps、Expected behavior、Actual or potential behavior、Evidence、Error message、Technical exception、Location、Root cause or hypothesis、Fix or proposed fix、Files changed、Validation、Regression test、Risk、Workaround、Rollback、Related logs 和 Approval needs。无法填写的字段写 `Unknown`、`Not reproduced` 或 `Not implemented`，不得猜测。

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

## BUG-20260714-001

### Title
Orchestration构造函数使用不可解析的`callable[...]`类型注解。

### Status
Fixed

### Severity
Low

### Area
Interface / Typing

### Discovery context
本次建立Analysis Decision Pipeline后进行源码审查时发现，尚未进入主分支。

### Environment
Windows 11；Python 3.14.5。

### Reproduction steps
1. 对`AnalysisDecisionPipeline.__init__`调用`typing.get_type_hints()`。
2. 解析`collection_id_factory`注解。

### Expected behavior
公共接口注解可由Python类型工具正常解析。

### Actual or potential behavior
内置函数`callable`被错误当作可下标类型，延迟注解解析时可能抛出`TypeError`。

### Evidence
源码写成`callable[[], UUID]`；`callable`不是`collections.abc.Callable`。

### Error message
Potential `TypeError: 'builtin_function_or_method' object is not subscriptable`。

### Technical exception
未在用户运行路径触发；通过接口审查定位。

### Location
`src/quant_trading/orchestration/analysis_decision_pipeline.py::AnalysisDecisionPipeline.__init__`。

### Root cause or hypothesis
类型名大小写和导入来源写错。

### Fix or proposed fix
导入并使用`collections.abc.Callable[[], UUID]`。

### Files changed
- `src/quant_trading/orchestration/analysis_decision_pipeline.py`
- `tests/integration/test_analysis_decision_pipeline.py`

### Validation
注解解析回归测试通过；完整测试133 passed。

### Regression test
`tests/integration/test_analysis_decision_pipeline.py::test_pipeline_public_annotations_are_resolvable`

### Risk
仅影响类型/反射工具，不改变运行算法语义。

### Workaround
Not needed after fix。

### Rollback
撤销修复会恢复不可解析注解，不建议单独回滚。

### Related logs
无运行日志；开发期静态发现。

### Approval needs
无需额外审批；属于本次新接口的局部修复。

## BUG-20260714-002

### Title
Factor/Decision新合同未拒绝NaN、Infinity和无效Market Bar数值。

### Status
Fixed

### Severity
Medium

### Area
Data / Factor / Decision

### Discovery context
审查新数据模型的失败路径时发现，Decimal允许NaN/Infinity，初版合同只检查缺失状态和confidence范围。

### Environment
Windows 11；Python 3.14.5。

### Reproduction steps
1. 构造`FactorResult(status=VALID, value=Decimal('NaN'))`；或
2. 构造含负成交量/无效OHLC的`MarketDataWindow`；或
3. 构造含`Infinity` exposure或`NaN` confidence的`TradeIntent`。

### Expected behavior
非有限数值和无效Bar必须在进入Factor/Decision计算前被受控拒绝。

### Actual or potential behavior
初版模型可能接受非有限值，或在NaN比较时产生非预期Decimal异常，使错误数值传播到决策合同。

### Evidence
模型初版缺少`Decimal.is_finite()`和Factor窗口OHLC/count校验。

### Error message
初版可能无错误，或在比较NaN时产生`decimal.InvalidOperation`。

### Technical exception
合同验证缺失；未进入任何真实交易路径。

### Location
`src/quant_trading/factors/models.py`；`src/quant_trading/decision/models.py`。

### Root cause or hypothesis
只验证了None/状态关系，没有覆盖Decimal特殊值及Factor边界的基础Bar完整性。

### Fix or proposed fix
Factor/Decision参数、Factor值、confidence/exposure统一拒绝非有限Decimal；Factor窗口重新验证有限OHLC/VWAP、价格区间和非负计数；VALID Decision必须包含明确Intent。

### Files changed
- `src/quant_trading/factors/models.py`
- `src/quant_trading/decision/models.py`
- `tests/unit/factors/test_factor_engine.py`
- `tests/unit/decision/test_decision_engine.py`

### Validation
针对性非有限值/无效Bar/空VALID Decision测试通过；完整测试133 passed。

### Regression test
- `test_factor_contract_rejects_nonfinite_values_and_invalid_market_prices`
- `test_trade_intent_rejects_nonfinite_exposure_and_confidence`
- `test_valid_decision_cannot_silently_omit_all_intents`

### Risk
新合同现在更严格；没有既有调用方或持久化数据需要兼容。

### Workaround
Not needed after fix。

### Rollback
撤销验证会允许不安全数值重新进入合同，不建议单独回滚。

### Related logs
无运行日志；开发期合同审查发现。

### Approval needs
无需额外审批；属于用户明确要求的数据验证和安全边界。

## BUG-20260714-003

### Title
Glossary的Timeframe说明遗漏已实现的分钟和小时粒度。

### Status
Fixed

### Severity
Low

### Area
Documentation

### Discovery context
为FactorSnapshot补充统一术语时检查现有Glossary发现。

### Environment
Repository documentation at base commit plus uncommitted governance changes。

### Reproduction steps
1. 阅读`docs/project/GLOSSARY.md`的Timeframe条目。
2. 对比`Timeframe`枚举和当前GUI。

### Expected behavior
文档列出10/30分钟、1小时、日、周、月当前支持粒度。

### Actual or potential behavior
旧条目只声明日、周、月，可能误导开发者认为Intraday未实现。

### Evidence
`market_history.models.Timeframe`与测试明确包含三种Intraday粒度。

### Error message
无。

### Technical exception
无；文档状态错误。

### Location
`docs/project/GLOSSARY.md`。

### Root cause or hypothesis
Intraday功能完成后Glossary未同步。

### Fix or proposed fix
更新Timeframe条目并增加Factor、FactorSnapshot、TradeIntent和前视偏差术语。

### Files changed
- `docs/project/GLOSSARY.md`

### Validation
文档与实际枚举、MODULE_MAP及测试状态人工核对；完整测试133 passed。

### Regression test
Not implemented；属于文档一致性检查。

### Risk
无运行风险。

### Workaround
Not needed after fix。

### Rollback
撤销会恢复错误的当前状态说明。

### Related logs
无运行日志。

### Approval needs
无需额外审批；低风险事实修正。

## BUG-20260714-004

### Title
新增替换Factor实现测试时Fake Policy返回语句被放入错误类。

### Status
Fixed

### Severity
Low

### Area
Tests

### Discovery context
编辑`test_analysis_decision_pipeline.py`后、运行测试前立即完整读取文件时发现。

### Environment
Windows 11；Python 3.14.5；pytest 9.1.1。

### Reproduction steps
1. 查看补丁后的`FakePolicy.evaluate`。
2. 发现只构造Intent但不返回DecisionResult，返回语句位于`AlternativeFakeFactor.calculate`的不可达代码之后。

### Expected behavior
Fake Policy返回可验证的DecisionResult；Alternative Fake只替换Factor版本和值。

### Actual or potential behavior
若不修复，Pipeline测试会得到Policy错误结果，无法证明替换Factor实现的独立性。

### Evidence
补丁后源码人工复读显示错误缩进和不可达return。

### Error message
尚未运行失败版本；预期会导致决策状态`POLICY_ERROR`或断言失败。

### Technical exception
测试夹具结构错误。

### Location
`tests/integration/test_analysis_decision_pipeline.py`。

### Root cause or hypothesis
基于过于宽泛的补丁上下文插入新测试类，命中了Fake Policy方法内部位置。

### Fix or proposed fix
将DecisionResult返回恢复到`FakePolicy.evaluate`，删除Alternative Fake中的不可达代码，并重新运行目标/完整测试。

### Files changed
- `tests/integration/test_analysis_decision_pipeline.py`

### Validation
目标Factor/Decision/Pipeline/Architecture测试24 passed；完整测试133 passed。

### Regression test
`test_replacing_factor_implementation_does_not_change_decision_policy`

### Risk
只影响测试证据，不影响正式运行路径。

### Workaround
Not needed after fix。

### Rollback
撤销修复会破坏Fake Policy测试合同。

### Related logs
无运行日志；开发期自审发现。

### Approval needs
无需额外审批；本次测试的局部修复。

### Verification update — BUG-20260714-002

2026-07-14 13:07:19 -07:00：继续审查运行时类型边界后，补充拒绝float exposure/confidence、float Factor value、字符串FactorStatus和字符串`BUY` action。类型注解不会在运行时自动验证，这些输入现在统一转为受控合同错误。针对性测试24 passed；完整测试133 passed，1个既有上游弃用警告。

## BUG-20260714-005

### Title
初版Risk-approved类型门未完整阻止无动作或与原始Intent不一致的批准对象。

### Status
Fixed

### Severity
High

### Area
Risk / Contract / Execution gate

### Discovery context
本次建立RiskDecision和未来Execution类型门后，对可独立构造的数据合同进行失败路径审查时发现。

### Environment
Windows 11；Python 3.14.5；pytest 9.1.1。

### Reproduction steps
1. 独立构造`APPROVED_WITH_REDUCTION`，在原Intent没有目标值时填写新的approved值；或
2. 将与RiskDecision不一致的TradeIntent包装为Risk-approved对象；或
3. 将`HOLD`/`NO_DECISION`且没有批准敞口的Intent包装为未来Order Construction输入。

### Expected behavior
Risk只能保持或降低原Intent；风险批准类型门必须保留源Intent身份/提案，并拒绝没有可执行变化的意图。

### Actual or potential behavior
初版Engine路径会阻止规则扩大风险，但独立构造的合同和类型门缺少全部交叉验证，未来调用方可能错误地把无动作或不一致对象视为已通过风险审查。

### Evidence
初版`RiskDecision.__post_init__`未覆盖original值为None但approved值非None的情况；`RiskApprovedTradeIntent`只核对ID、symbol和批准状态。

### Error message
初版可能不报错。

### Technical exception
合同验证缺失；当前无Execution模块，因此未进入任何账户或订单路径。

### Location
`src/quant_trading/risk/models.py::RiskDecision.__post_init__`；`RiskApprovedTradeIntent.__post_init__`；`RiskEngine._preflight`。

### Root cause or hypothesis
初版把主要安全验证放在Engine规则合并路径，未同时把不变量固化在可独立构造的公共输出合同中。

### Fix or proposed fix
RiskDecision拒绝发明目标/数量和任何扩大/反转；Risk-approved对象核对完整源提案并拒绝HOLD/NO_DECISION或无批准敞口；Risk Engine同时拒绝时间或Factor引用不一致的Intent。

### Files changed
- `src/quant_trading/risk/models.py`
- `src/quant_trading/risk/engine.py`
- `tests/unit/risk/test_risk_engine.py`

### Validation
风险增加、不可变源Intent、不一致ID/as-of、无动作类型门测试通过；完整测试151 passed。

### Regression test
- `test_rule_that_attempts_to_increase_risk_fails_closed`
- `test_trade_intent_is_immutable_and_risk_output_preserves_source`
- `test_risk_rejects_intent_with_mismatched_as_of`
- `test_risk_approved_gate_rejects_hold_or_no_exposure`

### Risk
合同更严格；当前没有既有Risk调用方、持久化记录或Execution需要兼容。

### Workaround
Not needed after fix。

### Rollback
不建议单独撤销；撤销会恢复未来可绕过类型门的潜在路径。

### Related logs
无运行错误；开发期合同审查发现。

### Approval needs
无需额外审批；属于用户明确要求的“不增加风险”和Execution Gate安全不变量。

## BUG-20260714-006

### Title
初版Risk Engine没有为所有裁决返回路径统一写入审计日志。

### Status
Fixed

### Severity
Medium

### Area
Risk / Logging / Audit

### Discovery context
对照用户要求的Risk审计字段检查新Engine时发现，初版只记录Policy异常，没有记录成功、拒绝、缩减和预检查拦截。

### Environment
Windows 11；Python 3.14.5；Python标准logging。

### Reproduction steps
1. 使用Fake approve或系统暂停上下文调用`RiskEngine.evaluate`。
2. 检查`quant_trading.risk.engine`日志。

### Expected behavior
每次Risk review记录RiskDecision ID、Intent ID、symbol、原始/批准值、原因、Policy/配置版本、环境和人工审查状态。

### Actual or potential behavior
初版成功或正常阻止路径没有统一日志，未来难以回答“算法原本想做什么、风险为什么修改、最终允许多少”。

### Evidence
初版只有`logger.exception`的Policy失败分支，没有统一完成日志函数。

### Error message
无异常；缺少审计事件。

### Technical exception
无。

### Location
`src/quant_trading/risk/engine.py::RiskEngine.evaluate`。

### Root cause or hypothesis
先完成合同/组合逻辑后，尚未将所有早退和正常返回汇合到统一审计记录。

### Fix or proposed fix
增加`_log_decision`并在预检查、无规则和组合结果的所有返回路径调用；日志只包含安全标识/版本/数值，不包含凭据或账户敏感信息。

### Files changed
- `src/quant_trading/risk/engine.py`
- `tests/unit/risk/test_risk_engine.py`

### Validation
日志回归测试验证Decision/Intent ID、Paper环境和配置版本；完整测试151 passed。

### Regression test
`test_every_risk_review_writes_traceable_audit_log`

### Risk
每次风险评估增加一条INFO日志；现有轮转日志控制文件增长，且无Secret字段。

### Workaround
Not needed after fix。

### Rollback
移除统一日志会失去关键风险审计证据，不建议单独回滚。

### Related logs
未来运行记录位于`runtime/logs/app.log`；自动测试使用捕获Logger，不写真实账户数据。

### Approval needs
无需额外审批；日志属于本次明确要求的Risk审计能力。

## BUG-20260714-007

### Title
算法组件“已实现/已配置”与“获准启用”没有独立生命周期门。

### Status
Fixed

### Severity
High

### Area
Configuration / Safety / Algorithm Control

### Environment
Windows 11；Python 3.14.5；PySide6；pytest 9.1.1。

### Reproduction steps
1. 注册一个非锁定的测试算法组件。
2. 创建Draft并将`enabled`设为true。
3. 在旧实现中保存并Apply该配置，不提供Unit、Integration、Dry Run、Paper或人工批准证据。

### Expected behavior
代码实现、注册、配置保存和运行/交易授权必须是不同状态；新组件默认关闭，只能按证据逐级进入Preview、Dry Run、Paper和Active。

### Actual behavior
原Algorithm Control仅使用`enabled`布尔值和Draft/Saved/Active配置状态，无法表达或强制“实现但禁用”“仅预览”“Dry Run”“Paper验证”“Live资格”。一个配置可在没有激活证据时被标记启用；当前没有生产算法或Execution，因此没有订单或资金影响。

### Error message
旧实现不报错。

### Technical exception
无异常；属于权限和状态建模缺口。

### Location
`src/quant_trading/algorithm_control/models.py`、`configuration_service.py`、`validation_service.py`。

### Root cause
配置版本状态被误用来同时表达实现状态、功能启用状态和运行授权，缺少独立`FeatureState`、激活证据与运行前Admission检查。

### Fix
加入独立功能生命周期和`ActivationEvidence`；新组件默认`REGISTERED`/disabled；禁止跳级；注册时验证所有权/能力/合同；Pipeline运行前检查缺失阶段、多个Primary、锁定安全和Live/自动提交状态；GUI显示Conflict Center。

### Files changed
- `src/quant_trading/algorithm_control/admission_models.py`
- `src/quant_trading/algorithm_control/admission_service.py`
- `src/quant_trading/algorithm_control/configuration_service.py`
- `src/quant_trading/algorithm_control/models.py`
- `src/quant_trading/algorithm_control/validation_service.py`
- `tests/unit/algorithm_control/test_change_admission.py`
- `tests/unit/algorithm_control/test_configuration_service.py`

### Validation
缺少证据、跳过阶段、越权能力、多个Decision Primary和缺少Pipeline阶段均有回归测试；完整测试结果记录于EDIT-20260714-026。

### Regression test
- `test_implemented_component_cannot_be_enabled_without_activation_evidence`
- `test_activation_requires_evidence_and_cannot_skip_stages`
- `test_component_defaults_to_registered_and_cannot_gain_another_layers_capability`
- `test_opposing_decision_policies_block_pipeline_instead_of_being_combined`

### Risk
旧的控制状态JSON仍可读取；缺少新字段时按已有Active/enabled状态保守转换。当前仅四项锁定系统安全记录，不存在生产算法配置迁移。

### Workaround
Not needed after fix。

### Rollback
可撤销本次Admission扩展并恢复旧控制配置模型，但会重新产生实现与授权混淆风险；不建议在未来启用算法前单独回滚此安全门。

### Related logs
开发期自审发现；没有运行时账户或订单日志。

### Approval needs
无需额外审批；修复属于用户明确要求的“实现状态与激活状态分离”和默认关闭安全边界。

## BUG-20260714-008

### Title
Concrete Factor SQLite adapter initially crossed the pure Factor-layer boundary.

### Status
Fixed

### Severity
Medium

### Area
Architecture / Database

### Environment
Windows 11; Python 3.14.5; pytest 9.1.1.

### Reproduction steps
1. Place the concrete `sqlite3` Factor Store under `quant_trading.factors.storage`.
2. Run `python -m pytest tests/architecture -q`.

### Expected behavior
The strategy-neutral Factor package must not import or contain concrete SQLite infrastructure; it should expose only a public Store Protocol.

### Actual behavior
The first implementation placed `sqlite_store.py` inside the Factor package, and the architecture test reported `quant_trading.factors.storage.sqlite_store imports forbidden sqlite3`.

### Error message
Architecture test assertion listing the forbidden `sqlite3` import.

### Technical exception
`AssertionError` from `test_documented_layer_boundaries_are_not_crossed`.

### Location
Initial task implementation in `src/quant_trading/factors/storage/sqlite_store.py`.

### Root cause
The public Factor Store contract and its concrete infrastructure adapter were initially treated as one package responsibility.

### Fix
Kept `FactorSnapshotStore` and typed calculation-run records in the Factor public contract, moved the concrete adapter to `quant_trading.persistence.factor_sqlite_store`, and added persistence-layer forbidden dependency checks.

### Files changed
- `src/quant_trading/factors/interfaces.py`
- `src/quant_trading/persistence/factor_sqlite_store.py`
- `tests/architecture/test_dependency_boundaries.py`

### Validation
The previously failing architecture suite passed after the move; the final complete result is recorded in EDIT-20260714-028.

### Regression test
`test_documented_layer_boundaries_are_not_crossed`

### Risk
Low after correction. The infrastructure adapter may depend on public Factor models, but Factor calculation cannot depend back on persistence.

### Workaround
Not needed after fix.

### Rollback
Do not move the adapter back into `quant_trading.factors`; disable optional Store injection if Factor persistence must be rolled back.

### Related logs
Development-time architecture test output; no runtime user data or secret involved.

### Approval needs
No additional approval; this is the minimal correction required to preserve the approved module boundary.

## BUG-20260714-009

### Title
Factor management wrapper initially removed an existing GUI inspection surface.

### Status
Fixed

### Severity
Low

### Area
GUI / Compatibility

### Environment
Windows 11; Python 3.14.5; PySide6 6.x; pytest 9.1.1; offscreen Qt platform.

### Reproduction steps
1. Wrap the existing Factor `ComponentPanel` in the new authoring tab container.
2. Run `python -m pytest tests/unit/algorithm_control/test_parameter_editor.py -q`.
3. The existing smoke test accesses `panel.factor_page.list`.

### Expected behavior
Adding the authoring tab should preserve the existing Factor component-list inspection surface used by smoke diagnostics and tests.

### Actual behavior
The initial wrapper exposed the nested panel only as `components`, so `factor_page.list` raised `AttributeError`.

### Error message
`AttributeError: 'FactorManagementPanel' object has no attribute 'list'`

### Technical exception
`AttributeError` in `test_control_panel_shows_empty_algorithm_layers_and_locked_risk_invariants`.

### Location
`src/quant_trading/algorithm_control/ui/factor_authoring_panel.py`, `FactorManagementPanel.__init__`.

### Root cause
The new two-tab wrapper did not forward the small pre-existing list surface when replacing the page object.

### Fix
Expose `FactorManagementPanel.list` as the contained component panel's list widget. No algorithm, configuration or trading behavior changed.

### Files changed
- `src/quant_trading/algorithm_control/ui/factor_authoring_panel.py`
- `tests/unit/algorithm_control/test_parameter_editor.py`

### Validation
The originally failing Algorithm Control test passed, targeted tests passed, and the complete suite passed 216 tests.

### Regression test
`test_control_panel_shows_empty_algorithm_layers_and_locked_risk_invariants`

### Risk
Low. The alias is read-only structural compatibility for inspection; GUI state remains owned by the contained panel.

### Workaround
Not needed after fix.

### Rollback
If the wrapper is removed, restore the original `ComponentPanel` as `factor_page`. Do not remove the alias while the wrapper remains unless callers are migrated through an approved interface change.

### Related logs
Development-time pytest failure only; no runtime request, credential, network or order activity.

### Approval needs
No additional approval; this is a minimal regression fix within the approved GUI extension.

## BUG-20260715-001

### Title
Algorithm preview composition initially imported the concrete Market History SQLite Store across the application boundary.

### Status
Fixed

### Severity
Medium

### Area
Architecture / Database

### Environment
Windows 11; Python 3.14.5; pytest 9.1.1.

### Reproduction steps
1. Compose the new local Factor preview directly inside Algorithm Control.
2. Run the architecture test suite.
3. Observe the forbidden concrete Store import.

### Expected behavior
GUI/control code issues typed preview requests; application orchestration obtains local storage through a narrow public factory/Store contract.

### Actual behavior
The first implementation imported the concrete SQLite history adapter across the protected boundary.

### Error message
Architecture dependency assertion failed.

### Technical exception
Pytest assertion in the documented layer-boundary architecture test.

### Location
`src/quant_trading/orchestration/algorithm_preview_composition.py`; corrected through `src/quant_trading/market_history/local_store_factory.py`.

### Root cause
Infrastructure assembly was initially placed too close to the GUI composition root.

### Fix
Move concrete Store creation behind a narrow Market History factory and keep the GUI dependent only on the preview service contract.

### Files changed
- `src/quant_trading/market_history/local_store_factory.py`
- `src/quant_trading/orchestration/algorithm_preview_composition.py`
- `src/quant_trading/algorithm_control/app.py`

### Validation
Architecture tests and full suite passed: 223 tests.

### Regression test
`test_control_center_does_not_import_broker_or_execution_provider`; `test_documented_layer_boundaries_are_not_crossed`.

### Risk
Low after fix; no database schema or data changed.

### Rollback
Remove the local preview composition as a unit; do not restore the forbidden direct GUI/Store dependency.

### Related logs
Development-time pytest only; no runtime network, credential or order activity.

## BUG-20260715-002

### Title
Initial Phase 5 implementation added runtime execution-gate code to declaration-only Execution boundaries.

### Status
Fixed

### Severity
High

### Area
Architecture / Execution safety

### Environment
Windows 11; Python 3.14.5; pytest 9.1.1.

### Reproduction steps
1. Add a runtime gate/model under `quant_trading.execution` while Paper/Live are approved only as empty boundaries.
2. Run execution-boundary architecture tests.

### Expected behavior
Phase 5 may expose read-only status metadata but must not create an execution runtime or order path.

### Actual behavior
The initial draft crossed the declaration-only boundary even though it did not submit orders.

### Error message
Execution-boundary architecture assertion failed.

### Technical exception
Pytest assertion detecting runtime content in the protected execution package.

### Location
Initial uncommitted `quant_trading.execution` gate/model draft; corrected in `algorithm_control/system_components.py` and `ui/execution_control_panel.py`.

### Root cause
“Execution control surface” was initially interpreted as requiring a runtime gate rather than a status-only management view.

### Fix
Delete the uncommitted runtime execution draft, retain empty Paper/Live packages, and represent both environments using disabled component metadata plus a read-only GUI.

### Files changed
- `src/quant_trading/algorithm_control/system_components.py`
- `src/quant_trading/algorithm_control/ui/execution_control_panel.py`
- `src/quant_trading/algorithm_control/ui/main_panel.py`

### Validation
`test_execution_boundaries_contain_no_runtime_implementation` and all 223 tests passed.

### Regression test
`test_execution_control_metadata_is_declaration_only_and_disabled`.

### Risk
Resolved. Execution, Paper submission, automatic submission and Live remain unavailable.

### Rollback
Remove the read-only metadata/page; the empty execution boundaries remain unchanged.

### Related logs
Development-time architecture test only; no account, network or order activity.

## BUG-20260715-003

### Title
Pipeline Dry Run button could remain disabled after Decision choices were populated.

### Status
Fixed

### Severity
Low

### Area
GUI

### Environment
Windows 11; Python 3.14.5; PySide6 6.x.

### Reproduction steps
1. Open Algorithm Control with at least one saved Decision definition.
2. Refresh the component catalog.
3. Inspect the Pipeline Dry Run button.

### Expected behavior
The button becomes available after the exact Decision-version list contains an item.

### Actual behavior
Its enabled state was calculated before the list was repopulated.

### Error message
None; stale UI state.

### Technical exception
None.

### Location
`src/quant_trading/algorithm_control/ui/main_panel.py`, refresh flow.

### Root cause
Refresh operations occurred in the wrong order.

### Fix
Set the enabled state only after repopulating the Decision combo box.

### Files changed
- `src/quant_trading/algorithm_control/ui/main_panel.py`

### Validation
GUI unit tests, offscreen eight-tab smoke test and full suite passed.

### Regression test
Covered by Algorithm Control panel smoke and Decision authoring tests.

### Risk
Low; affects only button availability, not financial behavior.

### Rollback
Revert the refresh-order change.

### Related logs
No runtime error code; found during code review.

## BUG-20260715-004

### Title
Decision management wrapper initially removed the existing `factor_choices` compatibility surface.

### Status
Fixed

### Severity
Low

### Area
GUI / Compatibility

### Environment
Windows 11; Python 3.14.5; pytest 9.1.1.

### Reproduction steps
1. Wrap the existing Decision component page with the new authoring page.
2. Run the existing Algorithm Control GUI test.

### Expected behavior
Existing callers can still inspect the exact Factor-choice widget.

### Actual behavior
The wrapper initially exposed only the nested panel, causing `AttributeError`.

### Error message
`AttributeError: 'DecisionManagementPanel' object has no attribute 'factor_choices'`

### Technical exception
AttributeError in the existing GUI regression test.

### Location
`src/quant_trading/algorithm_control/ui/decision_authoring_panel.py`.

### Root cause
The wrapper did not forward a small pre-existing inspection surface.

### Fix
Expose a compatibility alias to the contained component panel's `factor_choices` widget.

### Files changed
- `src/quant_trading/algorithm_control/ui/decision_authoring_panel.py`
- `tests/unit/algorithm_control/test_parameter_editor.py`

### Validation
The originally failing test and the complete 223-test suite passed.

### Regression test
`test_control_panel_shows_empty_algorithm_layers_and_locked_risk_invariants`.

### Risk
Low; read-only compatibility only.

### Rollback
Remove the wrapper entirely or migrate callers before removing the alias.

### Related logs
Development-time pytest only; no runtime request or trading activity.

## BUG-20260715-005

### Title
Successful IEX requests can cover a wider requested interval than the returned Bar history.

### Status
Deferred

### Severity
Medium

### Area
API / Cache / Data coverage

### Environment
Windows 11; Python 3.14.5; `alpaca-py`; SQLite central database; Alpaca IEX Market Data; Raw adjustment.

### Reproduction steps
1. Request approximately 2016-07-15 through 2026-07-15 for a mature US stock using IEX.
2. Allow the normal local-first service to finish successfully and update Coverage.
3. Query the earliest stored Bar for that symbol and compare it with the requested start.

### Expected behavior
The interface should clearly distinguish a successfully queried interval from the actual earliest and latest Bar returned by the selected Feed.

### Actual behavior
The batch completed successfully, but most selected stocks had actual daily IEX Bars beginning around 2020-07-27. Coverage can still represent the full successfully queried request interval, so a user may interpret “covered” as ten years of actual Bars.

### Error message
None. This is a data-availability and coverage-semantics mismatch, not a request exception.

### Technical exception
None.

### Location
`src/quant_trading/market_history/service.py` missing-range and successful-fetch flow; `src/quant_trading/market_history/storage/sqlite_store.py` Coverage persistence; status presentation in the Market History GUI.

### Root cause
Coverage intentionally records successfully queried time intervals so weekends, holidays and genuine no-data periods are not requested forever. Alpaca IEX can return less historical depth than the requested interval, and the current provider response does not supply a separate authoritative “history unavailable before” boundary. Treating all no-Bar periods as missing would instead cause repeated empty downloads.

### Fix
Deferred. No safe local fix was applied because changing Coverage semantics without provider availability metadata or an approved trading calendar could cause repeated API calls and alter cache behavior. The limitation is documented, and bulk-download verification now reports actual Bar bounds separately from requested bounds.

### Files changed
- `KNOWN_ISSUES.md`
- `logs/BUG_LOG.md`
- `logs/EDIT_LOG.md`

### Validation
The 110-symbol batch completed 330 of 330 Raw/IEX Daily/Weekly/Monthly combinations. Actual aggregate Bar bounds were inspected separately; SQLite integrity returned `ok`, and duplicate unique-key count was zero.

### Regression test
Not added because production behavior was not changed. A future fix needs tests that distinguish requested Coverage, actual Bar coverage and permanently unavailable provider history without retry loops.

### Risk
Users may believe ten years were downloaded when the selected IEX Feed returned fewer years. Changing the current behavior prematurely could create unnecessary repeated downloads.

### Rollback
Remove only the new documentation entries if they are incorrect; no source or schema change was made for this deferred issue.

### Related logs
2026-07-15 bulk Market Data operation; runtime logs under `runtime/logs/`. No credential values, account requests or order operations were recorded.

## BUG-20260715-006

### Title
Factor版本行看似已选中，但生命周期操作认为没有选中版本。

### Status
Fixed

### Severity
Medium

### Area
Algorithm Control GUI / Factor authoring

### Environment
Windows 11；PySide6桌面界面；算法控制中心“因子层 → 创建/修改Factor”。

### Reproduction steps
1. 在左侧选择一个Factor版本并将其归档。
2. 列表刷新后保留或重新显示该行的视觉高亮。
3. 点击“恢复为可用”。

### Expected behavior
视觉高亮的版本应成为内部选中版本，并可在填写修改原因后执行恢复。

### Actual behavior
右侧表单为空，点击“恢复为可用”后提示“请先在左侧选择一个已保存的Factor版本”，即视觉选择与内部`_selected_id`不同步。

### Error message
“请选择版本：请先在左侧选择一个已保存的Factor版本。”

### Technical exception
无异常；这是GUI选择状态同步缺陷。

### Location
`src/quant_trading/algorithm_control/ui/factor_authoring_panel.py`中的`reload()`、`clear_form()`、`currentRowChanged`连接和`_set_lifecycle()`选择检查。

### Root cause
当前只监听`QListWidget.currentRowChanged`。清除选择或重载后，列表行号仍可能保持为0；用户再次点击同一行只改变视觉选择而不改变current row，因此不会重新调用`_load_selected()`，`_selected_id`仍为`None`。

### Fix
`clear_form()`现在同时将列表current row重置为`-1`，并监听`itemSelectionChanged`重新加载真实选择；再次选择同一行时，视觉选择、右侧表单和内部`_selected_id`保持同步。

### Files changed
- `KNOWN_ISSUES.md`
- `logs/BUG_LOG.md`
- `logs/EDIT_LOG.md`
- `src/quant_trading/algorithm_control/ui/factor_authoring_panel.py`
- `tests/unit/algorithm_control/test_parameter_editor.py`

### Validation
`.venv\Scripts\python.exe -m pytest -q tests\unit\algorithm_control\test_parameter_editor.py tests\unit\algorithm_control\test_factor_definition_authoring.py tests\architecture\test_dependency_boundaries.py`：19 passed。

### Regression test
新增`test_factor_selection_can_be_reloaded_and_archived_version_restored`，覆盖表单清空后重选同一行、归档和恢复为可用。

### Risk
用户无法可靠恢复、归档或弃用当前视觉高亮的Factor版本；不涉及订单、实盘或交易语义变化。

### Rollback
撤销选择同步连接、current row重置及对应回归测试；不需要迁移数据或配置。

### Related logs
用户于2026-07-15提供的GUI截图；无账户、订单或交易活动。

## BUG-20260715-007

### Title
刷新后的状态内容提高窗口最低高度，导致历史数据浏览器向下延伸出屏幕。

### Status
Fixed

### Severity
Medium

### Area
Market History GUI / Qt layout

### Environment
Windows 11；PySide6/QWebEngine；最大化的股票历史数据浏览器；带已下载股票列表、控制面板、状态和Plotly图表的三栏布局。

### Reproduction steps
1. 启动股票历史数据浏览器并最大化窗口。
2. 加载股票或点击“更新最新数据”。
3. 状态区域填入范围、Coverage、更新时间、来源和请求编号等内容。
4. 观察窗口内容向下延伸，底部超出显示器可见范围。

### Expected behavior
刷新不得改变主窗口的可见高度；高度不足时，左侧控制和状态区域应在自身范围内滚动，图表继续适配剩余可见空间。

### Actual behavior
状态值刷新并换行后，左侧完整内容的size hint成为Qt布局最低高度，主窗口被向下撑大；控件并未消失，而是落到屏幕外。

### Error message
无错误对话框或Python异常。

### Technical exception
无；这是Qt widget minimum-size propagation造成的布局缺陷。

### Location
`src/quant_trading/market_history/ui/history_panel.py::HistoryPanel._build_ui`中的控制/状态栏布局。

### Root cause
控制面板、18行状态、进度条和可换行消息直接作为`QSplitter`子部件。刷新后较长状态文本增加子部件minimum size hint，Qt只能通过提高整个窗口最低高度满足布局。此前`BUG-20260713-007/008`修复的是Plotly HTML相对WebView viewport的溢出和异步resize时序，没有约束Qt左侧栏的最低高度，因此没有覆盖本问题。

### Fix
使用可调整内容大小的`QScrollArea`承载控制面板和状态栏，关闭横向滚动并将纵向size policy设为`Ignored`、最低高度设为0。内容过高时仅在该栏出现纵向滚动条，不再把主窗口撑出屏幕；既有Plotly响应式resize逻辑保持不变。

### Files changed
- `src/quant_trading/market_history/ui/history_panel.py`
- `tests/unit/market_history/test_history_panel_roles.py`
- `docs/modules/market-history.md`
- `KNOWN_ISSUES.md`
- `logs/BUG_LOG.md`
- `logs/EDIT_LOG.md`

### Validation
- 定向布局回归：2 passed。
- Market History单元/集成和架构检查：117 passed，1个既有上游`websockets.legacy`弃用警告。
- `git diff --check`在最终审查中执行。

### Regression test
`test_status_refresh_cannot_expand_window_beyond_requested_height`构造长Coverage和刷新消息，验证窗口高度不变、minimum size hint不超过请求高度且控制栏产生自身纵向滚动范围。

### Risk
小屏幕或较大字体下，控制/状态栏需要滚动才能查看底部内容；这比窗口内容落到屏幕外可控。行情、图表数据、缓存、数据库和交易安全语义不变。

### Rollback
移除`controls_scroll`并把原`left`部件直接放回Splitter；会恢复刷新后窗口最低高度可能超过屏幕的问题。无需配置或数据迁移。

### Related logs
用户于2026-07-15提供刷新前后整窗截图；关联历史问题`BUG-20260713-007`与`BUG-20260713-008`。

## BUG-20260715-008

### Title
Algorithm Control点击“添加条件”时将Qt按钮布尔参数误作DecisionCondition并触发未处理异常。

### Status
Fixed

### Severity
Medium

### Area
Algorithm Control GUI / Decision authoring

### Reproduction steps
1. 启动Algorithm Control Center。
2. 打开Decision创建/修改页。
3. 点击“添加条件”。
4. 观察error.log中的未处理主线程异常。

### Expected behavior
新增一行空条件编辑器，不产生异常。

### Actual behavior
Qt `QPushButton.clicked(bool)`将`False`传给`_add_condition(existing)`；函数将其作为`DecisionCondition`读取字段并抛出`AttributeError`。

### Error message
`AttributeError: 'bool' object has no attribute 'factor_component_id'`

### Technical location
`src/quant_trading/algorithm_control/ui/decision_authoring_panel.py::DecisionAuthoringPanel.__init__/_add_condition`，日志堆栈指向第165行附近。

### Root cause
按钮signal直接连接了一个带可选业务对象参数的slot，Qt信号布尔参数与该slot签名发生语义冲突。

### Fix
按钮连接改为显式无参lambda，并由`_add_blank_condition()`适配后再调用保留业务对象参数的`_add_condition()`。Qt checked状态不再可能进入DecisionCondition参数。

### Regression test
`test_add_condition_button_adds_an_empty_row_without_passing_qt_checked_state`以offscreen Qt发出bool overload，验证只调用blank adapter并新增一行。

### Validation
基线日志`runtime/logs/error.log`在2026-07-15T18:55:00Z保存了可复现堆栈；修改前全套251 tests未覆盖按钮点击路径。修复后定向Decision authoring测试通过；最终全套259 passed，见`EDIT-20260715-009`。

### Risk
用户无法可靠在GUI创建Decision条件；异常由全局hook记录，但本次没有订单或执行路径。

### Rollback
撤销无参adapter和对应测试即可；会恢复Qt信号参数进入业务slot的风险，无数据或配置迁移。

## BUG-20260715-009

### Title
Market Data验证允许请求区间内的未来Bar通过。

### Status
Fixed

### Severity
High

### Area
Market History / data integrity

### Reproduction steps
1. 创建结束时间为当前时间之后、但不超过当前时间加一天的合法`HistoricalDataRequest`。
2. 创建timestamp同样位于未来且落入该请求区间的`MarketBar`。
3. 调用`validate_market_bars`。

### Expected behavior
未来Bar应被`QT-DATA-002`对应的数据合同阻止，不能进入缓存、Factor或后续流程。

### Actual behavior
当前实现只检查`request.start_time <= timestamp < request.end_time`，因此未来Bar可通过。

### Error message
无；错误数据被接受。

### Technical location
`src/quant_trading/market_history/models.py::validate_market_bars`。

### Root cause
请求边界验证与point-in-time完整性验证被混为一体；合法的未来结束边界不能证明其中每条Bar已经发生。

### Fix
`validate_market_bars`在一次验证开始时固定当前UTC上界，逐条拒绝晚于该上界的Bar；不排序、不改写、不写入缓存。

### Regression test
`test_future_market_bar_is_rejected_even_when_inside_request_range`证明请求区间内的未来Bar也必须触发`DataValidationError`。

### Validation
修复前该测试明确失败（DID NOT RAISE）；修复后Market模型/配置定向测试通过。最终全套259 passed，见`EDIT-20260715-009`。

### Risk
未来时间戳可能造成前视数据进入图表、缓存或算法输入。当前没有订单执行，但这是后续交易安全阻断缺口。

### Rollback
撤销未来UTC上界检查和回归测试即可；会恢复前视数据缺口，无配置/Schema/数据迁移。

## BUG-20260715-010

### Title
盘中常规时段过滤使用固定09:30–16:00，无法识别交易所提前收盘日。

### Status
Deferred

### Severity
Medium

### Area
Market History / session filtering

### Reproduction steps
1. 选择包含美股提前收盘日的分钟或小时数据。
2. Provider返回该日13:00–16:00纽约时间的扩展/盘后Bar。
3. 当前固定常规时段过滤仍将其视为16:00前数据。

### Expected behavior
常规时段过滤应按适用交易所日历识别该交易日的真实收盘时间。

### Actual behavior
当前实现只使用`America/New_York`固定09:30–16:00窗口，无法区分提前收盘日。

### Error message
无；属于数据会话分类偏差。

### Technical location
Market History Provider的盘中常规时段过滤；当前项目没有交易所日历合同或依赖。

### Root cause
精确交易日历来源、市场适用范围和新依赖尚未获用户批准，现有代码只能使用固定时间窗口。

### Fix
Deferred。需要先批准交易所日历来源/依赖和适用市场语义；本次稳定性任务禁止新增依赖或扩展市场规则。

### Regression test
未添加实现测试；修复时应使用已知提前收盘日Fake calendar覆盖13:00边界。本次只确认现有文档与代码限制。

### Validation
对应`KI-0007`；本次未访问网络，未能使用Provider样本重新确认具体日期。问题不标记Fixed。

### Risk
提前收盘日的盘后Bar可能被显示为常规时段，并可能污染依赖该分类的研究输入。当前没有生产交易或执行。

### Rollback
本条仅补充现有Deferred事实记录，无代码可回滚；未来若结论变化，应追加状态更新，不删除历史。
# BUG-20260715-011

### Title
Backtesting tests collided with an existing same-named pytest module

### Status
Fixed

### Severity
Low

### Area
Test collection

### Reproduction steps
Run `.venv\Scripts\python.exe -m pytest` after adding `tests/unit/backtesting/test_service.py`.

### Expected behavior
The complete suite collects both module-specific service test files.

### Actual behavior
Pytest stopped with an `import file mismatch` against `tests/unit/market_history/test_service.py`.

### Error message
`import file mismatch: imported module 'test_service' ...`

### Technical location
`tests/unit/backtesting/`

### Root cause
The new test directory had no package marker, so two files named `test_service.py` shared a top-level import name.

### Fix
Added `tests/unit/backtesting/__init__.py`.

### Regression test
Complete-suite collection and execution.

### Validation
Pending final full-suite rerun in EDIT_LOG record.

### Risk
Test-only packaging; no runtime or financial behavior impact.

### Rollback
Remove the package marker only if the colliding test module is also renamed.
### Verification update — 2026-07-15

BUG-20260715-011 is verified Fixed: the final complete suite collected 263 tests and passed all 263.
## BUG-20260715-012

### Title
Algorithm Control tab-count regression after adding Simulation Strategies

### Status
Fixed

### Severity
Low

### Area
Algorithm Control GUI tests

### Reproduction steps
Run the targeted Algorithm Control tests after registering the approved Simulation Strategies page.

### Expected behavior
The control-center entry test recognizes every trusted page, including Simulation Strategies.

### Actual behavior
The test expected 9 tabs while the approved GUI now contains 10.

### Error message
`assert 10 == 9`

### Technical location
`tests/unit/algorithm_control/test_parameter_editor.py`

### Root cause
The new visible page was added without updating the existing GUI-entry regression assertion.

### Fix
Updated the count and added an explicit Simulation Strategies label assertion.

### Regression test
Targeted Algorithm Control suite and final full suite.

### Validation
Pending final validation in EDIT_LOG.

### Risk
Test-only correction; no financial behavior impact.

### Rollback
Revert the assertion only if the approved GUI page is also removed.
### Verification update — 2026-07-15

BUG-20260715-012 is verified Fixed: targeted Algorithm Control/Backtesting/architecture tests passed 74/74 and the final complete suite passed 267/267.
## BUG-20260715-013

### Title
Algorithm Control entry-count test did not include the approved Market Factor page

### Status
Fixed

### Severity
Low

### Area
Algorithm Control GUI tests

### Reproduction steps
Run `tests/unit/algorithm_control` after adding the approved Market Factor page.

### Expected behavior
The entry test recognizes separate Asset Factor and Market Factor pages.

### Actual behavior
The test expected 10 tabs but the approved UI contains 11.

### Error message
`assert 11 == 10`

### Root cause
The visible-entry regression assertion was not yet synchronized with the approved new page.

### Fix and regression test
Updated the count and added explicit labels for `单只股票因子` and `市场/宏观因子`; targeted and full-suite validation follow.

### Risk and rollback
Test-only correction. Revert only if the approved Market Factor page is removed.
## BUG-20260715-014

### Title
Approved Market Factor contract was absent from architecture allowlist

### Status
Fixed

### Severity
Low

### Area
Architecture and GUI regression tests

### Reproduction steps
Run Algorithm Control and architecture tests after introducing `quant_trading.factors.market`.

### Expected behavior
The new public Market Factor contract is permitted while private/reverse Factor dependencies remain forbidden, and GUI entries are located by stable labels.

### Actual behavior
The architecture allowlist rejected the new public module and a legacy fixed tab index pointed to Execution Control.

### Root cause
Tests encoded the pre-change public-contract list and tab ordering.

### Fix and regression test
Added only `quant_trading.factors.market` to the public allowlist and replaced the fragile tab index with a label assertion. Targeted and full validation follow.

### Risk and rollback
No production behavior change. Revert together with the Market Factor public contract/page.
### Verification update — 2026-07-15

BUG-20260715-013 and BUG-20260715-014 are verified Fixed. Targeted architecture/Factor/Decision/Algorithm Control/Backtesting/Risk tests passed 95/95 before final additions; the final complete suite passed 277/277.
## BUG-20260715-015

### Title
Decision Journal initially rejected legacy signal-provider simulations

### Status
Fixed

### Severity
Low

### Area
Research Backtesting compatibility

### Reproduction steps
Run the existing sizing-provider regression after adding the daily journal.

### Expected behavior
Existing providers continue to simulate; first-party providers additionally expose complete daily evidence.

### Actual behavior and error message
A valid fill raised `ValueError: signal is missing its decision journal evaluation`.

### Technical location and root cause
`backtesting.service.HistoricalBacktestService._completed_entry`; optional trace evidence was initially treated as mandatory.

### Fix and regression test
Fill enrichment is conditional for legacy `signals()` providers. Existing sizing-provider and full Backtesting suites cover compatibility.

### Validation, risk and rollback
Fixed in targeted validation; final evidence is in EDIT_LOG. Low risk and no financial behavior change. Reverting restores the compatibility failure.

## BUG-20260715-016

### Title
Definition strategy condition trace referenced a method-local type outside its scope

### Status
Fixed

### Severity
Low

### Area
Research Backtesting decision trace

### Reproduction steps
Run a saved Simulation Strategy after enabling condition trace capture.

### Expected behavior
Every daily saved-strategy evaluation constructs condition evidence.

### Actual behavior and error message
`NameError: ConditionTrace is not defined`.

### Technical location and root cause
`backtesting.strategies.DefinitionSignalProvider._matches`; the type was imported inside another method.

### Fix and regression test
Moved trace contracts to module scope. Saved Asset/Market strategy tests and daily-journal tests cover the path.

### Validation, risk and rollback
Fixed in targeted validation; final evidence is in EDIT_LOG. Low risk, isolated to research trace construction.

## BUG-20260715-017

### Title
Non-filled simulation signals remained labeled pending in the Decision Journal

### Status
Fixed

### Severity
Medium

### Area
Simulation audit semantics

### Reproduction steps
Run the one-year 110-symbol baseline and count journal outcomes after fills complete.

### Expected behavior
Every matched signal ends as FILLED or BLOCKED with an explicit reason.

### Actual behavior and error message
591 non-filled signals remained `pending_next_bar`; there was no exception, but the persisted audit status was misleading.

### Technical location and root cause
`backtesting.service.HistoricalBacktestService.run`; only successful fill enrichment updated the initial pending outcome.

### Fix and regression test
No-position sells, already-held buys, missing sizing amounts and sub-one-share amounts now become BLOCKED with explicit reasons. Tests assert no pending outcome remains after a completed run.

### Validation, risk and rollback
Final one-year and full-suite verification is recorded in EDIT_LOG. The change affects research reporting only and does not create or alter an operational order.

### Verification update — 2026-07-15
BUG-20260715-015, BUG-20260715-016 and BUG-20260715-017 are verified Fixed: targeted tests passed 12/12, the final complete suite passed 279/279, and the final 27,610-entry run contained zero pending outcomes.

## BUG-20260715-018

### Title
Partial simulated sell cleared the entire position

### Status
Investigating

### Severity
High

### Area
Historical simulation portfolio state

### Reproduction steps
Start with a simulated long position, emit a SELL using fixed notional smaller than the position value, and inspect the next journal/ending market value.

### Expected behavior
Only the simulated filled quantity is removed; the remaining quantity stays in the isolated position state.

### Actual behavior
Cash increases by the partial fill amount, but `positions[symbol]` is set to zero.

### Technical location and root cause
`src/quant_trading/backtesting/service.py`, sell processing in `HistoricalBacktestService.run`; the fill quantity replaced the original quantity variable and the position was unconditionally cleared.

### Fix, regression test and validation
Pending a failing regression test and minimal state-update correction.

### Risk and rollback
High for research-result correctness, none for real accounts because Backtesting is isolated. Rollback would restore the known incorrect partial-sell behavior.

## BUG-20260715-019

### Title
Decision Journal recorded executed gross as requested notional

### Status
Investigating

### Severity
Medium

### Area
Simulation audit trail

### Reproduction steps
Use a requested notional that does not divide exactly by the next-bar price and inspect `requested_notional` versus `approved_notional`.

### Expected behavior
Requested notional preserves the sizing result; approved/executed amount reflects whole-share rounding.

### Actual behavior
Both fields contain the executed gross amount.

### Technical location and root cause
`src/quant_trading/backtesting/service.py`; `_completed_entry` receives `gross` in the requested-notional argument.

### Fix, regression test and validation
Pending a failing regression test and explicit separation of requested and executed values.

### Risk and rollback
Medium for audit accuracy; no execution authority or account effect.

## BUG-20260715-020

### Title
Saved-strategy Market Factor trace did not preserve its real version

### Status
Investigating

### Severity
Medium

### Area
Simulation Decision Journal

### Reproduction steps
Run a saved strategy with a versioned Market Factor and inspect the daily Market Factor trace.

### Expected behavior
The trace identifies the exact saved Market Factor version and symbol universe.

### Actual behavior
The trace reports the literal string `exact` as its version.

### Technical location and root cause
`backtesting.strategies.DefinitionSignalProvider`; prepared market data retained only sizing name/value references, discarding definition trace metadata.

### Fix, regression test and validation
Pending preservation of a separate typed Market Factor trace cache and an exact-version assertion.

### Risk and rollback
Medium audit-accuracy risk only; no order or account path.

## BUG-20260715-021

### Title
Reusable saved-strategy provider retained Market Factor values across prepares

### Status
Investigating

### Severity
Medium

### Area
Backtesting strategy preparation

### Reproduction steps
Reuse one `DefinitionSignalProvider` for two different bar sets/date ranges and inspect its prepared Market Factor references.

### Expected behavior
Each run derives Market Factors only from that run's bars.

### Actual behavior
The internal date cache is not cleared by `prepare()`.

### Technical location and root cause
`backtesting.strategies.DefinitionSignalProvider.prepare`; run-scoped derived state was stored on the provider without reset.

### Fix, regression test and validation
Pending explicit cache reset and repeat-run regression coverage.

### Risk and rollback
Medium research-correctness risk when callers reuse a provider; no operational effect.

## BUG-20260715-022

### Title
Backtest domain service depended on concrete SQLite storage

### Status
Investigating

### Severity
Low

### Area
Architecture drift

### Reproduction steps
Inspect imports in `backtesting.service`.

### Expected behavior
The domain service consumes a narrow read-only historical-bar port; only the application composition root imports SQLite.

### Actual behavior
The service type annotation imports `SQLiteHistoricalDataStore` directly despite already supporting Fakes structurally.

### Technical location and root cause
`src/quant_trading/backtesting/service.py`; initial implementation annotated the first concrete store rather than declaring its actual narrow dependency.

### Fix, regression test and validation
Pending an additive Backtesting-owned Protocol and architecture assertion.

### Risk and rollback
Low current runtime risk, medium future coupling risk. Rollback restores concrete coupling without data migration.

## BUG-20260715-023

### Title
Market Factor aggregation could silently accept duplicate or mismatched-as-of inputs

### Status
Investigating

### Severity
High

### Area
Market Factor input integrity

### Reproduction steps
Pass two results for one required symbol, or pass required symbols whose Factor timestamps differ from the requested Market Factor as-of time.

### Expected behavior
The immutable universe must contain exactly one valid, same-as-of result per symbol; invalid collections fail closed.

### Actual behavior
A dictionary comprehension silently keeps the last duplicate and no as-of equality check is performed.

### Technical location and root cause
`src/quant_trading/factors/market.py`, `MarketFactorCalculator.calculate`; set equality alone does not prove one-to-one or temporal consistency.

### Fix, regression test and validation
Pending explicit cardinality/duplicate/as-of validation with invalid-input regression tests.

### Risk and rollback
High for research Factor correctness; no direct execution or account effect. Rollback restores acceptance of ambiguous input.

## BUG-20260715-024

### Title
Backtest market-data validation swallowed unexpected programming exceptions

### Status
Investigating

### Severity
Medium

### Area
Backtesting error boundary

### Reproduction steps
Cause the validation call itself to raise an exception other than its declared `DataValidationError`.

### Expected behavior
Known bad symbol data is skipped; unexpected implementation failures abort and remain visible.

### Actual behavior
`except Exception` labels every failure as invalid market data and continues.

### Technical location and root cause
`HistoricalBacktestService.run`; the exception boundary was broader than the Market Data validation contract.

### Fix, regression test and validation
Pending narrowing to `DataValidationError` and a regression that unexpected errors propagate.

### Risk and rollback
Medium diagnostic/correctness risk; narrowing may expose latent errors instead of silently producing a partial research run.

## BUG-20260715-025

### Title
Canonical status documents contradicted implemented Backtesting and research sizing

### Status
Investigating

### Severity
Medium

### Area
Project architecture documentation

### Reproduction steps
Compare current Backtesting/Sizing code and tests with Compass B1/B16/B17, architecture Overview status, Project State verification footer and related module limitations.

### Expected behavior
Canonical documents distinguish implemented research-only capabilities from unimplemented production activation/rules.

### Actual behavior
Several older paragraphs still state that backtests and position sizing are not implemented and cite the prior 259-test baseline.

### Technical location and root cause
`PROJECT_COMPASS.md`, `docs/architecture/OVERVIEW.md`, `docs/project/PROJECT_STATE.md` and two module documents; later approved phases updated additive sections without superseding all old status statements.

### Fix, regression test and validation
Pending minimal factual corrections and a consistency search after final verification.

### Risk and rollback
Medium architecture-drift risk because future work may duplicate or bypass existing owners. Documentation-only rollback would restore known contradictions.

### Stabilization verification update — 2026-07-15/16

BUG-20260715-018 through BUG-20260715-025 are verified **Fixed**.

- 018: partial sells retain `position_before - filled_quantity`; regression verifies 100 → 70 shares.
- 019: a USD 305 request at USD 10 records requested `305` and executed/approved `300`.
- 020: saved Market Factor traces retain version `1` and locked source symbols.
- 021: `prepare()` resets all run-scoped Market Factor references/traces.
- 022: `HistoricalBacktestService` depends on `HistoricalBarSource`; concrete SQLite remains in the app composition root.
- 023: duplicate-symbol and mixed-as-of Market Factor collections return `INVALID_INPUT`.
- 024: only declared `DataValidationError` is converted to a skipped symbol; unexpected exceptions propagate.
- 025: canonical status documents now distinguish implemented research Backtesting/sizing from unimplemented production activation.

Targeted Factor/Backtesting/architecture validation passed 40/40. The final complete suite passed 283/283 with one existing upstream deprecation warning. A 110/110-symbol one-year run and four GUI/import/diagnostic smokes passed. No issue from this set remains open in `KNOWN_ISSUES.md`.

## BUG-20260716-001

### Title
Backtest results accepted inconsistent run identity and terminal totals

### Status
Investigating

### Severity
High

### Area
Backtesting public contracts

### Reproduction steps
Construct a `BacktestResult` whose `run_id` differs from `request.run_id`, whose completion precedes its start, or whose ending equity differs from cash plus market value.

### Expected behavior
Run identity, chronology and terminal Decimal totals are validated before a result can be persisted or shown in the GUI.

### Actual behavior
Only result timestamp timezone presence is validated; mutually inconsistent result data is accepted.

### Error message
No error is raised.

### Technical location
`src/quant_trading/backtesting/models.py`, `BacktestResult.__post_init__`.

### Root cause
The initial additive result contract normalized timestamps but did not encode its cross-field invariants.

### Fix
Pending minimal invariant checks in the immutable public model.

### Regression test
Pending tests for mismatched run identity, invalid chronology and inconsistent ending totals.

### Validation
Pending targeted and complete test suites.

### Risk
Corrupt research evidence can be stored under a plausible result object; no operational account or order path is affected.

### Rollback
Remove the additive contract checks; no data migration is required.

## BUG-20260716-002

### Title
Simulated financial records accepted invalid Decimal and arithmetic relationships

### Status
Investigating

### Severity
High

### Area
Backtesting trade and equity contracts

### Reproduction steps
Construct a `SimulatedTrade` with `gross_amount != quantity * price`, the wrong cash-effect sign, a naive fill timestamp, or a non-finite Decimal; construct an `EquityPoint` whose total differs from cash plus market value.

### Expected behavior
Invalid research financial records fail at the model boundary.

### Actual behavior
The immutable dataclasses accept all of these inconsistent values.

### Error message
No error is raised.

### Technical location
`src/quant_trading/backtesting/models.py`, `SimulatedTrade` and `EquityPoint`.

### Root cause
The simulation service generated valid values, but the public records relied on the producer instead of defending their own contract.

### Fix
Pending finite-Decimal, UTC, text and arithmetic validation that mirrors the isolated simulation semantics.

### Regression test
Pending direct model tests for valid normalization and invalid arithmetic.

### Validation
Pending targeted and complete test suites.

### Risk
Persisted trade history or GUI totals could be internally false even though the service normally emits valid records.

### Rollback
Remove the additive model validation; no stored result rewrite is required.

## BUG-20260716-003

### Title
Backtest JSON repository could overwrite or return the wrong run identity

### Status
Investigating

### Severity
Medium

### Area
Backtesting result persistence

### Reproduction steps
Save twice with the same run ID, or place a valid result for run B in the JSON path named for run A and call `get(A)`.

### Expected behavior
Saved research runs are immutable by ID, and `get(run_id)` verifies that the decoded result has the requested identity.

### Actual behavior
`save` silently replaces the existing JSON and `get` returns whatever identity the file contains.

### Error message
No error is raised.

### Technical location
`src/quant_trading/backtesting/repository.py`, `JsonBacktestResultRepository.save/get`.

### Root cause
Atomic replacement was implemented without a create-only guard or read identity assertion.

### Fix
Pending explicit overwrite rejection and requested-ID verification.

### Regression test
Pending repository tests for duplicate save and wrong-file identity.

### Validation
Pending targeted and complete test suites.

### Risk
A research audit record can be lost or misattributed; operational Ledger and account data remain isolated.

### Rollback
Remove the two repository guards; no schema or migration reversal is needed.

## BUG-20260716-004

### Title
Daily decision-journal contracts accepted malformed or incomplete evidence

### Status
Investigating

### Severity
Medium

### Area
Backtesting decision journal

### Reproduction steps
Construct a journal entry with invalid OHLC data, non-finite Decimal values, an empty symbol, a naive trace timestamp, or `FILLED` outcome without the complete trade/cash/position evidence.

### Expected behavior
The detailed daily audit record validates its market evidence and requires a coherent financial evidence set for simulated fills.

### Actual behavior
Only the entry timestamp timezone and symbol casing are checked; malformed evidence is accepted.

### Error message
No error is raised.

### Technical location
`src/quant_trading/backtesting/models.py`, `FactorTrace`, `ConditionTrace` and `DecisionJournalEntry`.

### Root cause
The first journal phase prioritized additive trace capture and did not complete defensive validation on the new immutable contracts.

### Fix
Pending localized trace, OHLC, optional-Decimal and filled-evidence validation.

### Regression test
Pending direct contract tests plus an existing full backtest compatibility check.

### Validation
Pending targeted and complete test suites.

### Risk
The GUI can present detailed but internally invalid research evidence; operational Ledger, Risk and Execution remain isolated.

### Rollback
Remove the additive journal validations; no persistence schema migration is involved.

## BUG-20260716-005

### Title
Launcher documentation understated the registered GUI catalog

### Status
Investigating

### Severity
Low

### Area
GUI discoverability documentation

### Reproduction steps
Compare `DEFAULT_LAUNCH_TARGETS` and launcher tests with Project State and the Main Launcher module test description.

### Expected behavior
Current-state documentation lists Market History, Algorithm Control and Backtesting as the three trusted child GUI targets.

### Actual behavior
One Project State sentence and one module-test sentence still claim that only two child entries exist.

### Error message
Not applicable; this is a factual documentation defect.

### Technical location
`docs/project/PROJECT_STATE.md` and `docs/modules/main-launcher.md`.

### Root cause
The Backtesting target was added to the code and public-interface section without updating two older count statements.

### Fix
Pending minimal factual corrections; no launcher code change is needed.

### Regression test
Existing launcher tests enumerate and verify the three target IDs; final offscreen smoke covers the launcher plus all three child applications.

### Validation
Pending final documentation consistency search.

### Risk
Low runtime risk, but users and future maintainers may overlook the Backtesting GUI.

### Rollback
Revert the two documentation sentences only.

### Verification update — 2026-07-16

BUG-20260716-001 through BUG-20260716-005 are verified **Fixed**.

- 001: `BacktestResult` now rejects mismatched request/run identity, reversed chronology, inconsistent terminal Decimal totals/return, invalid curve identity and duplicate or cross-run evidence.
- 002: `SimulatedTrade` and `EquityPoint` now enforce finite Decimal values, UTC fills and exact gross/cash/equity relationships.
- 003: result files are create-only by run ID; `get` and `list_results` verify decoded identity against the requested ID or filename.
- 004: Factor/condition traces and daily journal entries validate identity, UTC, finite values, OHLCV and complete filled-trade evidence.
- 005: Project State and Main Launcher documentation now match the three registered child GUI targets.

The new regression module passed 11/11; targeted Backtesting/architecture validation passed 26/26; the complete suite passed 294/294 with one existing upstream warning. All seven pre-existing saved result files decoded successfully under the stricter contracts. New isolated run `1b7651ca-52bc-486a-89e5-5cdb851992e5` completed 110/110 symbols with 43 fills, 27,720 journal entries, zero pending outcomes and ending equity `1665427.225`. Four GUI entry smokes, dependency/compile/diagnostics/SQLite checks and the no-trading-capability source search passed. No issue from this set remains open in `KNOWN_ISSUES.md`.

## BUG-20260716-006

### Title
Idea Notebook save confirmation was immediately overwritten

### Status
Investigating

### Severity
Low

### Area
Algorithm Control Idea Notebook GUI

### Reproduction steps
Create a valid note through `IdeaNotebookPanel._save()` and inspect the status label after the table reload selects the saved row.

### Expected behavior
The page confirms that the note was saved and that no algorithm or trading workflow was triggered.

### Actual behavior
The selection-change callback replaces the confirmation with the generic current-note identifier.

### Error message
No exception; the GUI regression assertion failed on the visible status text.

### Technical location
`src/quant_trading/algorithm_control/ui/idea_notebook_panel.py`, `_save()` and reload/selection ordering.

### Root cause
The success message was set before `reload()`, whose row-selection signal updated the same label.

### Fix
Pending setting the operation result after the reload completes.

### Regression test
`tests/unit/algorithm_control/test_idea_notebook.py::test_gui_saves_and_archives_a_passive_note`.

### Validation
Pre-fix targeted result: 1 failed, 15 passed.

### Risk
Low presentation risk; saved content is correct and no algorithm, account or execution path is involved.

### Rollback
Revert the status-order change only.

### Verification update — 2026-07-16

BUG-20260716-006 is verified **Fixed**. The success/status message is now assigned after table reload and selection signals complete, so save/archive confirmation remains visible. The regression first reproduced the defect (`1 failed, 15 passed`), then passed in the targeted set (`16 passed`). The final complete suite passed 298/298 with one existing upstream deprecation warning, and the offscreen Algorithm Control smoke constructed 12 pages, saved/reloaded one isolated temporary note, and invoked no execution path.

## BUG-20260716-007

### Title
Main launcher could not directly locate existing core Algorithm Control pages

### Status
Investigating

### Severity
Low

### Area
Main GUI navigation and discoverability

### Reproduction steps
Open `python -m quant_trading` and try to navigate directly to Idea Notebook, Asset Factor, Market Factor, Decision, Risk, Execution status, Portfolio & Ledger, Simulation Strategies, Pipeline, Conflict Center or Audit.

### Expected behavior
The main GUI provides a compact, trusted route to every existing user-facing core page while backend-only modules remain internal.

### Actual behavior
The launcher exposes only the three standalone applications. Users must know that eleven core pages are nested inside Algorithm Control and then find the tab manually.

### Error message
Not applicable; this is a confirmed navigation/discoverability gap.

### Technical location
`src/quant_trading/launcher/app.py`, `src/quant_trading/algorithm_control/app.py`, and `src/quant_trading/algorithm_control/ui/main_panel.py`.

### Root cause
The trusted launch catalog can store only a module name and Algorithm Control has no stable startup-page selector.

### Fix
Pending additive trusted arguments, a compact core-page shortcut catalog, and an Algorithm Control page-selection boundary. No business logic will move into the launcher.

### Regression test
Pending Launcher command/GUI coverage and Algorithm Control page-selection coverage.

### Validation
Pending targeted, complete and offscreen GUI tests.

### Risk
Low runtime risk, but users may overlook existing safety, accounting, strategy and audit pages. Adding navigation must not create arbitrary command execution or duplicate feature logic.

### Rollback
Remove shortcut metadata/startup-page selection and retain the existing three standalone application entries.

## BUG-20260716-008

### Title
Algorithm Control page-map patch retained an obsolete loop colon

### Status
Investigating

### Severity
Low

### Area
Algorithm Control GUI startup navigation

### Reproduction steps
Compile or import `src/quant_trading/algorithm_control/ui/main_panel.py` immediately after the page-map edit.

### Expected behavior
The page metadata is assigned as a tuple and then iterated by the following explicit loop.

### Actual behavior
The tuple assignment ended with `):`, retaining the colon from the replaced inline `for` loop and producing invalid Python syntax.

### Error message
`SyntaxError` at the page tuple terminator.

### Technical location
`src/quant_trading/algorithm_control/ui/main_panel.py`, `AlgorithmControlPanel.__init__` page-map construction.

### Root cause
The patch replaced the old `for ... in (...)` header with a `pages = (...)` assignment but did not remove the old loop colon.

### Fix
Pending removal of the obsolete colon before compile and regression tests.

### Regression test
Existing Algorithm Control import/GUI tests plus final `compileall` and full suite.

### Validation
Pending.

### Risk
If left unfixed, Algorithm Control and direct shortcuts cannot start. The defect was found by immediate source inspection before execution.

### Rollback
Revert the page-map edit or remove the single obsolete colon.

### Verification update — 2026-07-16

BUG-20260716-007 and BUG-20260716-008 are verified **Fixed**.

- 007: the Main Launcher retains its three standalone applications and now exposes all eleven existing Algorithm Control core pages through a compact static shortcut catalog. Each shortcut starts the owner process with one reviewed `--page` ID; no feature logic or arbitrary user argument enters the launcher.
- 008: the obsolete tuple colon was removed before runtime testing. `compileall`, Algorithm Control imports and GUI construction now pass.

Targeted Launcher/Algorithm Control/architecture validation passed 30/30. The complete suite passed 301/301 with one existing upstream warning. The offscreen Main GUI smoke selected `portfolio_ledger`, verified the detached command, and the real Algorithm Control entry parsed that page and exited 0 with `execution_invocations=0`. No issue from this set remains open in `KNOWN_ISSUES.md`.

## BUG-20260716-009

### Title
Staged snapshot contained six whitespace integrity defects

### Status
Investigating

### Severity
Low

### Area
Documentation and Algorithm Control source formatting

### Reproduction steps
Stage the approved working tree and run `git diff --cached --check`.

### Expected behavior
The staged snapshot has no trailing whitespace or extra blank line at end of file.

### Actual behavior
One ADR status line and four Proposal metadata lines contain trailing spaces; `factor_workbench_panel.py` has one extra blank line at EOF.

### Error message
`trailing whitespace` and `new blank line at EOF`.

### Technical location
`docs/decisions/ADR-0015-simulation-decision-journal.md`, `docs/proposals/PROPOSAL-008-simulation-decision-journal.md`, and `src/quant_trading/algorithm_control/ui/factor_workbench_panel.py`.

### Root cause
Earlier Markdown hard-break formatting and an extra terminal newline were not caught until the complete staged snapshot was checked.

### Fix
Pending removal of whitespace only; no content or runtime behavior change.

### Regression test
Final `git diff --cached --check`.

### Validation
Pending restage and staged-snapshot integrity check.

### Risk
No runtime risk; committing a known dirty diff would reduce repository quality and can fail future hooks.

### Rollback
Not applicable beyond restoring the insignificant whitespace.

### Verification update — 2026-07-16

BUG-20260716-009 is verified **Fixed**. The five trailing-space locations and one extra EOF line were removed without changing text meaning or Python behavior. The complete staged snapshot will be restaged and rechecked before commit.

## BUG-20260716-010

### Title
Canonical governance documents contain duplicate identifiers and stale verification metadata

### Status
Deferred

### Severity
Medium

### Area
Project governance and canonical architecture documentation

### Reproduction steps
1. Inspect `PROJECT_COMPASS.md` section B11 and find two unrelated rows identified as `INTENT-017`.
2. Inspect `docs/architecture/OVERVIEW.md` under Architecture Invariants and observe invariant numbering restart at 24 and 25 after item 28.
3. Compare the Compass `last_verified_commit_or_working_tree_state` value with `git status`, `git rev-parse HEAD`, and `origin/main`.

### Expected behavior
Intent IDs and invariant references are unique and stable, and verification metadata accurately describes the evidenced repository state.

### Actual behavior
Portfolio Accounting and Main Launcher share the same Active Intent ID, two architecture invariants share earlier numbers, and the Compass still describes the current tree as uncommitted although HEAD `5a32cf6` is clean and matches `origin/main`.

### Error message
Not applicable; this is a canonical-document integrity defect.

### Technical location
`PROJECT_COMPASS.md` metadata and B11 Active Intent Ledger; `docs/architecture/OVERVIEW.md` Architecture Invariants.

### Root cause
Later governance and launcher additions appended identifiers and evidence text without a final uniqueness/current-state consistency pass.

### Fix
Deferred because changing canonical identifiers and verification metadata should be performed as a focused governance correction with cross-reference checks. Preserve the earlier Portfolio Accounting intent ID and assign the launcher a new unique ID; renumber only the duplicated architecture list items; refresh the verification evidence from the actual clean commit.

### Regression test
Pending a documentation-integrity check for unique `INTENT-NNN` identifiers, monotonic invariant numbering, and a manual evidence review of mutable Git-state metadata.

### Validation
The observability-framework inventory independently confirmed a clean worktree at `5a32cf6`, matching `origin/main`. Existing persistence/pipeline/preview/backtesting/architecture verification passed 54/54. No runtime code was changed.

### Risk
Future proposals and audit reports can cite an ambiguous intent or invariant, and maintainers may incorrectly believe the verified repository contains uncommitted work. Trading behavior is not directly affected.

### Workaround
Until corrected, refer to the Portfolio Accounting and Main Launcher intents by their full titles and evidence links rather than `INTENT-017` alone, and cite architecture invariant text rather than the duplicated numeric label.

### Rollback
Remove only this appended Bug Log record and the matching Known Issues summary if the evidence is disproved; do not rewrite prior Bug Log history.

### Resolution update — 2026-07-16

**Status: Fixed.** The user explicitly approved this correction with Phase 1 Run History. Portfolio Accounting remains `INTENT-017`; the Main Launcher is uniquely `INTENT-019`; the new approved Run History intent is `INTENT-020`. Canonical architecture invariants are now monotonic and unique through item 34. Compass verification metadata now describes the current uncommitted Phase 1 worktree, 312-test result, Schema v2 migration evidence, and unchanged execution safety state.

Regression coverage is implemented in `tests/architecture/test_governance_document_integrity.py`: it checks unique Active Intent IDs, a complete monotonic invariant sequence, and rejects the stale 301-test Compass metadata. The full suite passed 312 tests with one pre-existing upstream deprecation warning. No financial, Risk, account, order, Paper or Live behavior changed.

## BUG-20260716-011

### Title
Compass explicitly denied the already verified research Backtesting capability

### Status
Fixed

### Severity
Medium

### Area
Canonical governance documentation

### Reproduction steps
1. Read `PROJECT_COMPASS.md` B1 and confirm isolated historical Backtesting is `Implemented and verified for research`.
2. Read B6 and observe the blanket statement that the current application does not implement a `backtest`.

### Expected behavior
Canonical capability and non-capability statements distinguish implemented isolated research Backtesting from unimplemented production trading strategy/execution behavior.

### Actual behavior
The two sections contradicted each other, allowing a future audit to deny a verified research capability or misread the safety boundary.

### Error message
Not applicable; this was a canonical-document integrity contradiction.

### Technical location
`PROJECT_COMPASS.md`, sections B1 and B6.

### Root cause
The B6 non-capability sentence predated the approved isolated Backtesting implementation and was not narrowed when that research capability became verified.

### Fix
Replaced the blanket denial with an explicit denial of production strategy/signal/advice/profit-guarantee capability while stating that isolated research-only Backtesting exists without production or execution authority.

### Regression test
`tests/architecture/test_governance_document_integrity.py::test_compass_does_not_deny_verified_research_backtesting` rejects the stale sentence and requires the truthful research-only qualification.

### Validation
The targeted governance/Run History/dependency suite passed 22 tests. The complete suite passed 320 tests with one existing upstream `websockets.legacy` deprecation warning.

### Risk
Documentation-only; no formula, simulation result, Risk rule, account, order, Paper or Live behavior changed. If left unresolved, future change admission and status reports could use inconsistent canonical evidence.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the contradiction was confirmed, locally fixed and regression-tested in the same approved task.

### Rollback
Revert the Compass wording and regression assertion only, although doing so knowingly restores the contradiction.

## BUG-20260716-012

### Title
Proposal index described actively persisted local Factor history as inactive

### Status
Fixed

### Severity
Low

### Area
Change-admission governance index

### Reproduction steps
1. Read `docs/proposals/README.md` entry for PROPOSAL-001.
2. Compare its statement that implementation remains inactive with implemented PROPOSAL-009/010 and the verified local preview persistence path.

### Expected behavior
The proposal index distinguishes active local `NO_EXECUTION` evidence persistence from unapproved production Factor activation.

### Actual behavior
The entry used “inactive” for the whole implementation, contradicting the implemented local preview Store while attempting to describe only the production-activation boundary.

### Technical location
`docs/proposals/README.md`, PROPOSAL-001 index entry.

### Root cause
The early proposal summary was not updated after later approved proposals activated persistence for explicit local research previews without activating production Factors.

### Fix
Updated the index to state that PROPOSAL-009/010 extend the original storage decision for active local `NO_EXECUTION` evidence while production activation remains unapproved.

### Regression test
`tests/architecture/test_governance_document_integrity.py::test_proposal_index_does_not_claim_local_factor_history_is_inactive` rejects the stale blanket claim.

### Validation
Pending the focused governance test at the time of this record; the proposal task will append final evidence to its Edit Log entry.

### Risk
Documentation-only. The stale description could cause a future proposal to create duplicate storage or falsely claim the preview path was unused. No database, Factor formula, Risk, account, order, Paper or Live behavior changed.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the contradiction was fixed locally in the same task.

### Rollback
Revert the single proposal-index sentence and regression assertion, although doing so restores the documented contradiction.

### Verification update — 2026-07-16

The focused governance suite passed 5 tests, including the new proposal-index regression. `git diff --check` passed with only existing Windows LF→CRLF notices. BUG-20260716-012 remains **Fixed**; no current Known Issue was created.

## BUG-20260716-013

### Title
Qt combo boxes returned plain strings for typed Factor history dimensions

### Status
Fixed

### Severity
Medium

### Area
Algorithm Control Factor history query boundary

### Reproduction steps
1. Select an exact Timeframe, Adjustment, Feed or PriceField in the Factor History panel.
2. Request the exact Factor/source-price chart.
3. Observe that Qt may return the `StrEnum` item data as a plain `str`.
4. The downstream chart or SQLite adapter then attempts to read `.value` from that string.

### Expected behavior
The GUI Controller boundary reconstructs the declared enum type before creating a typed query contract.

### Actual behavior
Raw `QComboBox.currentData()` values were passed directly, causing `'str' object has no attribute 'value'` in the new chart path and leaving the analogous persisted history-filter path unsafe.

### Error message
`'str' object has no attribute 'value'`

### Technical location
`src/quant_trading/algorithm_control/ui/factor_history_panel.py`

### Root cause
The UI assumed PySide6 would preserve Python `StrEnum` instances through QVariant storage. PySide6 is permitted to expose their string representation instead.

### Fix
Normalize every optional or required combo value back through its exact enum constructor at the GUI boundary before building Factor history, comparison or visualization queries.

### Regression test
`tests/unit/algorithm_control/test_research_history_panels.py::test_factor_history_panel_renders_exact_chart_and_exports_current_records` drives real combo selections through the chart and export workflow.

### Validation
Pending the focused GUI suite at the time of this record; final evidence is recorded in the Phase 2B Edit Log entry.

### Risk
Local read-only research UI only. No Factor calculation, price transformation, Decision, Risk, account, order, Paper or Live behavior changed.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the issue was confirmed and fixed with a regression test in the same approved task.

### Rollback
Revert the enum-normalization helper and its call sites, which would knowingly restore the query failure.

## BUG-20260716-014

### Title
Factor export no-overwrite guard had a time-of-check/time-of-use race

### Status
Fixed

### Severity
Low

### Area
Factor history export filesystem boundary

### Reproduction steps
1. Start a new export to a path that does not yet exist with `overwrite=False`.
2. Create the target path from another process after the initial existence check but before the final filesystem replacement.
3. Observe that unconditional `os.replace()` can replace the newly created file.

### Expected behavior
An export without explicit overwrite approval must atomically create a new file or fail if the name is already occupied at the final filesystem operation.

### Actual behavior
The initial guard rejected an already existing path, but the final operation still used replace semantics and left a narrow race window.

### Technical location
`src/quant_trading/algorithm_control/factor_history_export.py`

### Root cause
The temporary file was correctly written in the destination directory, but the same final operation was used for both explicit-overwrite and create-only modes.

### Fix
Use `os.replace()` only after explicit overwrite approval. Create-only export uses a same-filesystem hard link from the completed temporary file to the target; link creation is atomic and fails if the target exists, after which the temporary name is removed.

### Regression test
`tests/unit/algorithm_control/test_factor_history_export.py::test_create_only_export_does_not_overwrite_a_racing_target` creates the destination inside the final link call and verifies the competing content remains unchanged.

### Validation
Pending the final focused/full suite at the time of this record; final evidence is recorded in EDIT-20260716-009.

### Risk
Local user-selected export files only. Central SQLite, Factor/Decision/Risk calculations, accounts, orders, Paper and Live are unaffected.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the race was fixed with a deterministic regression test in the same approved task.

### Rollback
Reverting to unconditional replace would knowingly weaken the explicit no-overwrite guarantee. Removing export entirely is the feature-level rollback.

### Verification update — 2026-07-16

BUG-20260716-013 and BUG-20260716-014 remain **Fixed**. The complete suite passed 332 tests with one existing upstream warning; the focused architecture/research/GUI suite passed 64 tests and the export suite passed 4 tests. Compileall, dependency integrity and diff whitespace checks passed. Neither issue requires a current Known Issue entry.

## BUG-20260716-015

### Title
Valid non-numeric Factor values looked like successfully plotted numeric evidence

### Status
Fixed

### Severity
Low

### Area
Factor history chart presentation

### Reproduction steps
1. Persist a `VALID` Factor result whose public typed value is `bool` or `str`.
2. Open the exact Factor history chart.
3. Observe that the numeric line correctly has a gap but the status marker used the same green color as a plotted numeric point and omitted the original value.

### Expected behavior
The presentation must not coerce a valid non-numeric Factor into a browser number and must make the reason for the numeric-line gap explicit.

### Actual behavior
The line omitted the point, but the status track could imply complete numeric evidence.

### Technical location
`src/quant_trading/algorithm_control/factor_history_chart.py`

### Root cause
Status color considered calculation/result/source availability but not whether the Factor's declared typed value was numerically plottable.

### Fix
Keep the numeric gap, display the original typed Factor value in status hover, and use a separate non-numeric color. No boolean/string-to-number conversion is introduced.

### Regression test
`tests/unit/algorithm_control/test_factor_history_chart.py::test_chart_keeps_invalid_factor_and_missing_price_as_explicit_gaps` includes a valid boolean result and verifies its gap, source-price continuity, typed hover value and distinct status color.

### Validation
Pending the final focused/full suite; final evidence is appended below and recorded in EDIT-20260716-009.

### Risk
Presentation-only. Persisted evidence and all Factor/Decision/Risk calculations remain unchanged; no financial or execution meaning is added.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the issue was fixed with regression coverage in the same approved task.

### Rollback
Revert the status hover/color change only; doing so would knowingly restore an ambiguous chart marker.

### Verification update — 2026-07-16

BUG-20260716-015 remains **Fixed**. Its focused chart/export suite passed 5 tests, and the complete suite then passed 332 tests with one existing upstream warning. No current Known Issue was created.

## BUG-20260720-001

### Title
Capital SQLite Store could accept a total-conserved initial snapshot that omitted a plan bucket

### Status
Fixed

### Severity
Medium

### Area
Capital Allocation persistence boundary

### Reproduction steps
1. Construct a valid typed capital plan with locked reserve, tactical reserve and two asset-cash buckets.
2. Construct a separately valid snapshot whose total still equals the research cash basis, but omit one asset bucket and add its amount to another bucket.
3. Call the public SQLite Store directly instead of the coordinating service.

### Expected behavior
Persistence must reject any snapshot that does not contain every plan bucket exactly once with matching type, symbol and currency. Transfer snapshots must retain that complete set and apply only the exact source debit/destination credit while leaving all other buckets unchanged.

### Actual behavior
The domain objects independently verified exact totals, but the Store previously checked only top-level plan/snapshot/operation identity. A caller outside the normal service path could therefore persist structurally incomplete bucket evidence whose grand total was still zero-difference.

### Technical location
`src/quant_trading/persistence/capital_allocation_sqlite_store.py`

### Root cause
Conservation of the grand total and completeness of the per-bucket state were validated separately, without a Store-boundary cross-object comparison.

### Fix
The Store now requires the initial snapshot to exactly match all plan bucket definitions and initial balances. Transfer persistence reloads the current complete bucket set inside the same `BEGIN IMMEDIATE` transaction and requires the next snapshot to preserve every bucket, cash basis and currency, apply exactly one source debit and destination credit, keep every other balance unchanged and remain non-negative.

### Regression test
`tests/unit/capital_allocation/test_sqlite_capital_allocation.py::test_sqlite_store_rejects_a_conserved_snapshot_with_a_missing_plan_bucket`

### Validation
The focused Capital Allocation domain, SQLite, GUI-boundary and architecture suite passed 15 tests after the fix. Final full-suite evidence is recorded in the PROPOSAL-012 implementation Edit Log entry.

### Risk
The fix is fail-closed and affects only research capital-plan persistence. It adds no Portfolio Accounting facts, Risk rule, Decision logic, order, Paper or Live behavior.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the issue was fixed with regression coverage during the approved implementation.

### Rollback
Revert the Store cross-object validation and its regression test, which would knowingly restore the persistence-boundary gap; feature-level rollback is to leave the Capital Allocation composition disabled and restore the pre-v4 database backup.

## BUG-20260720-002

### Title
Asset State idempotency lookup and operation evidence could lose the original completed request

### Status
Fixed

### Severity
Medium

### Area
Asset State persistence and idempotency boundary

### Reproduction steps
1. Complete an Asset State operation with one `operation_id`.
2. Submit the same ID with different canonical content so the conflict attempt is durably recorded.
3. Query the operation ID again, or inspect a transition note / an unknown requested cycle ID.

### Expected behavior
The first completed operation remains the idempotent source of truth. Same ID plus identical payload returns that result; changed content is rejected without displacing it. Every canonical request field, including transition note and unresolved requested cycle ID, remains auditable.

### Actual behavior
The initial Store lookup could select a later conflicting row instead of the completed operation. Transition note was absent from the canonical/persisted input, and an unknown requested cycle ID could be lost because only a resolved cycle foreign key was retained.

### Technical location
`src/quant_trading/asset_state/models.py`, `src/quant_trading/asset_state/service.py`, `src/quant_trading/persistence/asset_state_sqlite_store.py`, central Schema v5 operation table

### Root cause
Attempt history and idempotent operation identity were represented by the same lookup ordering, and not every user request field had an independent durable column/input contract.

### Fix
Completed operations are selected before conflict attempts and then by original row order. Transition note participates in canonical identity and persists with the attempt. `requested_cycle_id` is stored independently from the optional resolved cycle foreign key, preserving invalid requests without fabricating a valid reference.

### Regression test
`tests/unit/asset_state/test_sqlite_asset_state.py::test_operation_idempotency_preserves_original_result_and_records_conflict` and the unknown-cycle invalid-attempt assertion.

### Validation
The Asset State focused suite passed 8 tests after the fix; the complete implementation suite subsequently passed 362 tests with one existing upstream warning before documentation-only final checks.

### Risk
Fail-closed local research-history correction only. No transition is inferred, no financial meaning is added, and Decision/Risk/Capital/Accounting/Backtesting/Execution are unaffected.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the defect was fixed with regression coverage during the approved implementation.

### Rollback
Revert the idempotency/evidence changes only while leaving Asset State disabled, which would knowingly restore the audit gap; feature rollback restores the verified Schema v4 backup with writers stopped.

## BUG-20260720-003

### Title
Asset State SQLite Store initially trusted completed cross-object evidence supplied by the service

### Status
Fixed

### Severity
High

### Area
Asset State transactional persistence boundary

### Reproduction steps
1. Build individually valid Asset State definition/operation/snapshot objects.
2. Alter a completed definition operation so its structured graph input no longer matches the accepted definition.
3. Call the public Store directly, bypassing normal service coordination.

### Expected behavior
Persistence must independently reject any completed operation whose exact definition, Run/stage, predecessor, edge, event, snapshot or structured input evidence is inconsistent. The failed attempt must remain durable while no accepted state fact is committed.

### Actual behavior
The initial adapter relied on service validation and could accept individually valid but mutually inconsistent completed objects at its public boundary.

### Technical location
`src/quant_trading/persistence/asset_state_sqlite_store.py`

### Root cause
Object-level validation did not prove cross-object identity and provenance at the transaction boundary, which is callable independently of the coordinating service.

### Fix
The Store now revalidates completed definition inputs against the exact typed definition; exact local Run/stage identity; start/transition/close operation evidence; current predecessor; definition graph/allowed edge; resulting snapshot and event/transition relationships in one transaction. Inconsistent accepted facts roll back, and the service persists only a failed attempt in a separate terminal Run.

### Regression test
`tests/unit/asset_state/test_sqlite_asset_state.py::test_store_rejects_inconsistent_completed_definition_evidence`

### Validation
The focused Asset State suite passed 8 tests after the fix; the complete implementation suite subsequently passed 362 tests with one existing upstream warning before documentation-only final checks.

### Risk
The fix strengthens fail-closed research persistence. It cannot create or advance state, and it adds no formula, financial rule, account, order, Paper or Live behavior.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the defect was fixed with a deterministic Store-boundary regression during the approved task.

### Rollback
Revert the transactional cross-object checks only while disabling the Asset State composition, which would knowingly restore the Store-boundary defect; database rollback is restoration of the verified Schema v4 backup with writers stopped.

## BUG-20260720-004

### Title
Target Position GUI passed a Qt-coerced string where the typed direction enum was required

### Status
Fixed

### Severity
Medium

### Area
Target Position Laboratory controller boundary

### Reproduction steps
1. Open the Target Position Laboratory.
2. Enter a valid finite-knot definition and click Save.
3. Observe that Qt returns the `StrEnum` item data as its string value.

### Expected behavior
The GUI converts presentation data into the exact typed command contract and delegates the definition to `TargetPositionService`.

### Actual behavior
The initial implementation passed the Qt string directly, so `CreateTargetPositionDefinitionCommand` rejected the otherwise valid request before a Run/attempt could be created.

### Technical location
`src/quant_trading/algorithm_control/ui/target_position_panel.py`

### Root cause
PySide's QVariant conversion did not preserve the Python `StrEnum` object stored as combo-box item data.

### Fix
The GUI now explicitly reconstructs `TargetPositionDirection` at its typed controller boundary before constructing the command.

### Regression test
`tests/unit/algorithm_control/test_target_position_panel.py::test_panel_saves_definition_previews_and_opens_exact_run`

### Validation
The Target Position GUI/domain/repository/architecture focused suite passed after the fix; final suite evidence is recorded in `EDIT-20260720-006`.

### Risk
Local research input conversion only. The fix adds no curve default, consumer, TradeIntent, Risk or execution behavior.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because it was fixed with deterministic GUI regression coverage during the approved implementation.

### Rollback
Revert the explicit enum reconstruction and keep the Target Position write surface disabled, which would knowingly restore the inability to save definitions through the GUI.

## BUG-20260720-005

### Title
Target Position SQLite Store initially trusted completed cross-object evidence supplied by the service

### Status
Fixed

### Severity
High

### Area
Target Position transactional persistence boundary

### Reproduction steps
1. Build individually valid Target Position definition/result and completed operation objects.
2. Change the operation's raw definition name, knot input or preview input so it no longer matches the accepted object.
3. Call the public SQLite Store directly, bypassing normal service coordination.

### Expected behavior
Persistence independently rejects mutually inconsistent completed evidence and rolls back the accepted definition/result.

### Actual behavior
The initial adapter checked primary IDs and Run/stage identity but did not compare every raw operation input to the accepted definition/result.

### Technical location
`src/quant_trading/persistence/target_position_sqlite_store.py`

### Root cause
Object-level validation was not sufficient to prove cross-object provenance at the independently callable Store boundary.

### Fix
Definition persistence now compares name/reason/direction/bounds/predecessor/creator and every parsed knot to the accepted definition. Preview persistence compares exact definition, manual Decimal inputs, `as_of`, evidence, actor and reason to the accepted result. Any mismatch rolls back transactionally; the service then stores only a failed attempt under its terminal Run.

### Regression test
`tests/unit/target_position/test_target_position.py::test_sqlite_store_rejects_inconsistent_completed_definition_evidence`

### Validation
The focused repository suite passed 7 tests after the fix; final suite evidence is recorded in `EDIT-20260720-006`.

### Risk
Fail-closed local research persistence only. The fix cannot create a definition/result and adds no financial or execution authority.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the defect was fixed with Store-boundary regression coverage during the approved implementation.

### Rollback
Revert the cross-object validation only while disabling Target Position composition, which would knowingly restore the audit-integrity gap; feature rollback restores the verified Schema v5 backup with writers stopped.

## BUG-20260720-006

### Title
Target Position chart initially omitted the current-position fraction marker required by the approved inspector contract

### Status
Fixed

### Severity
Medium

### Area
Target Position typed result and presentation adapter

### Reproduction steps
1. Persist a valid manual Target Position preview with non-zero research capital basis.
2. Open the result in Target Position Laboratory.
3. Inspect the curve chart and calculation detail.

### Expected behavior
The inspector shows both the persisted target fraction/value and the current position fraction/value, with separate current and target markers.

### Actual behavior
The first implementation displayed current USD in the table but exposed only the target marker/fraction on the curve.

### Technical location
`src/quant_trading/target_position/models.py`, `src/quant_trading/algorithm_control/target_position_chart.py`, `src/quant_trading/algorithm_control/ui/target_position_panel.py`

### Root cause
The approved current-position display requirement was not mapped to a typed read-model property during the initial GUI implementation.

### Fix
`TargetPositionResult.current_position_fraction` now derives an exact read-only ratio from the two persisted manual inputs in the domain model; zero basis explicitly returns unavailable. The chart and structured detail consume that typed value and render distinct persisted-target and derived-current markers. No GUI business calculation or Schema change was added.

### Regression test
`tests/unit/target_position/test_target_position.py::test_definition_interpolation_and_run_evidence_survive_restart`, `tests/unit/algorithm_control/test_target_position_chart.py::test_chart_uses_exact_persisted_knots_without_calculation`, and the Target Position panel test.

### Validation
Focused Target Position domain/chart/GUI tests passed after the fix; final suite evidence is recorded in `EDIT-20260720-006`.

### Risk
Read-only presentation completeness only. It neither changes the target result nor creates a TradeIntent, Risk result or order.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because it was fixed with domain/chart/GUI regression coverage during the approved implementation.

### Rollback
Revert the derived read-model property and marker only, which would knowingly restore the inspector omission while leaving stored canonical inputs/results unchanged.

## BUG-20260720-007

### Title
Standardized-state SQLite adapter initially queried a non-existent Run-stage column

### Status
Fixed

### Severity
High

### Area
Phase 5B standardized-state persistence and Run provenance validation

### Reproduction steps
1. Initialize a temporary central Schema v7 database.
2. Use `StandardizedPriceStateService` to save a valid manual definition.
3. Observe the Store validating its terminal Run/stage before inserting the operation.

### Expected behavior
The Store validates the exact `STANDARDIZED_STATE_PREVIEW` Run and `STANDARDIZED_STATE` stage, then transactionally persists the accepted definition and completed operation.

### Actual behavior
The first implementation queried `algorithm_run_stages.name`, but the canonical Schema v2 contract names that column `stage_name`. SQLite raised `OperationalError`, so the accepted definition and even the attempted failure record could not be persisted.

### Technical location
`src/quant_trading/persistence/standardized_state_sqlite_store.py`

### Root cause
The new adapter duplicated a stage lookup and used the domain property name instead of the established SQL column name.

### Fix
The provenance query now selects and validates `s.stage_name`. The exact Run ID, stage ID, run type, stage name and `NO_EXECUTION` mode remain fail-closed.

### Regression test
`tests/unit/factors/test_standardized_state.py::test_definition_preview_trace_run_and_restart_are_exact` and the standardized-state GUI/repository suite exercise successful plus durable invalid/failed operations through the same check.

### Validation
The immediate focused rerun passed 8 tests; broader and final suite evidence is recorded in `EDIT-20260720-009`.

### Risk
Local research persistence only. The fix restores approved append-only evidence and cannot create an estimator, target, trade, Risk approval or order.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because it was fixed with regression coverage before Phase 5B handoff.

### Rollback
Disable standardized-state composition and revert Phase 5B code while retaining Schema v7 history; reverting only this fix would knowingly make all new writes fail.

## BUG-20260721-008

### Title
Standardized-state Run History artifact used a mojibake empty-value placeholder

### Status
Fixed

### Severity
Low

### Area
Run History presentation adapter

### Reproduction steps
1. Open a Standardized State definition-save or preview Run in Run History Explorer.
2. Inspect an artifact whose optional definition name or symbol is absent.
3. Observe the fallback text in the artifact summary.

### Expected behavior
Missing optional values render with the normal em-dash placeholder `—`.

### Actual behavior
The adapter embedded the mojibake text `â€”`, which could be displayed literally.

### Technical location
`src/quant_trading/persistence/run_sqlite_store.py`

### Root cause
The Phase 5B artifact summary string was written with incorrectly decoded source text while adjacent structured fields used the correct placeholder helper.

### Fix
Replace both corrupted fallback literals with the canonical em dash. No persisted evidence, calculation, schema, financial meaning or Run identity changes.

### Regression test
The linked Target Position integration test reloads the exact source Run artifact and asserts that no artifact summary contains the mojibake sequence.

### Validation
The linked integration regression, complete suite (**401 passed**) and final architecture/governance suite (**54 passed**) succeeded; full evidence is recorded in `EDIT-20260720-011`.

### Risk
Read-only presentation text only. The fix cannot change a Factor value, Target Position, cash, holding, Risk result or order.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the deterministic local fix is included with regression coverage in the current approved implementation.

### Rollback
Reverting the two literal replacements would knowingly restore the visible artifact-summary corruption without affecting stored evidence.

## BUG-20260721-009

### Title
Compass governance regression still asserted the Phase 5B verification checkpoint after Phase 5C completion

### Status
Fixed

### Severity
Low

### Area
Architecture/governance test metadata

### Reproduction steps
1. Complete the approved Phase 5C implementation and update the Compass verification metadata to Schema v8.
2. Run `pytest tests/architecture -q`.
3. Observe the governance test still requiring the former Phase 5B/Schema v7 metadata strings.

### Expected behavior
The regression protects the current Phase 5C exact-link checkpoint, Schema v8 migration evidence and zero default linked rows.

### Actual behavior
The stale assertion rejected truthful current metadata even though the full behavior suite had passed.

### Technical location
`tests/architecture/test_governance_document_integrity.py`

### Root cause
The implementation updated the governed metadata after the earlier test pass but did not update the checkpoint-specific assertion in the same edit step.

### Fix
Rename the test for Phase 5C and assert the current exact-adapter, Schema v8, v7→v8 backup/migration and zero-default-linked-row evidence strings.

### Regression test
The corrected governance test is itself the regression and remains part of the complete architecture suite.

### Validation
The final architecture/governance rerun and complete suite results are recorded in `EDIT-20260720-011`.

### Risk
Documentation/test consistency only. No runtime, persistence, financial calculation, GUI behavior or trading authority changed.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the deterministic local fix was completed immediately.

### Rollback
Reverting the assertion would knowingly make the governance suite reject the current truthful Phase 5C checkpoint.

## BUG-20260722-001

### Title
Run History limitations incorrectly said Phase 5D had no Risk consumer after Phase 6A–6C existed

### Status
Fixed

### Severity
Low

### Area
Run History module documentation

### Reproduction steps
1. Read the Run History known-limitations section after the verified Phase 6A–6C implementations.
2. Compare it with the same document's current orchestration list and persisted source relationships.
3. Observe that the limitation still says Phase 5D has no current Risk consumer.

### Expected behavior
The document states that Phase 5D is consumed only by the disabled specialized Risk research chain and still has no complete approval or trading consumer.

### Actual behavior
One stale sentence described the pre-Phase-6A state and contradicted verified code, tests and adjacent documentation.

### Technical location
`docs/modules/run-history.md`

### Root cause
The known-limitations sentence was not advanced when the specialized Phase 6A and later ordered previews were documented.

### Fix
Replace the stale sentence with the exact disabled Phase 6A→6B→6C→6D consumer boundary and preserve the absence of complete Risk approval, Backtesting, Accounting and Execution consumers.

### Regression test
Governance/document integrity and full-suite validation cover the current canonical phase and document references; the implementation edit record captures the corrected statement.

### Validation
Final Phase 6D documentation and full-suite validation are recorded in the corresponding implementation Edit Log entry.

### Risk
Documentation accuracy only. No runtime contract, formula, persisted row or trading authority changed.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the deterministic local documentation fix is included immediately.

### Rollback
Reverting the sentence would knowingly restore a contradiction about the current specialized Risk consumer chain.

## BUG-20260722-002

### Title
Phase 6D source validation did not explicitly require complete Capital plan/snapshot bucket identity

### Status
Fixed

### Severity
Medium

### Area
Phase 6D orchestration and SQLite cross-object validation

### Reproduction steps
1. Create a valid research Capital Plan with multiple asset-cash buckets and a conserved snapshot.
2. Outside the supported Capital service, delete one asset balance and move its amount to another existing plan asset bucket so the stored snapshot total remains conserved.
3. Request a Phase 6D preview for an unaffected symbol.

### Expected behavior
Phase 6D fails closed because the latest snapshot no longer contains exactly the full bucket identity defined by its Capital Plan.

### Actual behavior
The initial implementation verified that every present balance belonged to the plan and revalidated the selected reserves/same-symbol bucket, but did not explicitly compare the complete plan and snapshot bucket-ID sets.

### Technical location
`src/quant_trading/orchestration/target_adjustment_research_asset_cash_preview.py`, `src/quant_trading/persistence/research_asset_cash_sqlite_store.py`

### Root cause
Subset membership plus exact conservation was treated as sufficient even though a malicious/manual database edit can redistribute a missing bucket's amount into another existing plan bucket.

### Fix
Require exact equality between all plan bucket IDs and all snapshot balance bucket IDs both during orchestration resolution and again inside the result-persistence transaction.

### Regression test
The Phase 6D SQLite integration suite tampers a latest snapshot while preserving its total and asserts a durable `INVALID_INPUT` attempt with no accepted result.

### Validation
Targeted and full-suite evidence is recorded in the Phase 6D implementation Edit Log entry.

### Risk
Research evidence integrity only; supported Capital service writes were already complete. The fix is fail-closed and cannot change a candidate, Capital balance, factual account or order.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the deterministic local fix and regression test are included immediately.

### Rollback
Reverting the two equality checks would knowingly restore acceptance of semantically incomplete tampered snapshots.

## BUG-20260722-003

### Title
Phase 6D could accept a conserved Capital snapshot whose protected reserve balance was tampered

### Status
Fixed

### Severity
Medium

### Area
Phase 6D orchestration and SQLite cross-object validation

### Reproduction steps
1. Create a valid Phase 3A research Capital Plan with locked reserve, tactical reserve and asset-cash buckets.
2. Outside the supported Capital service, reduce the latest snapshot's locked-reserve balance and add the same amount to an asset-cash balance, preserving every bucket ID and the exact total.
3. Request a Phase 6D preview against that plan/latest snapshot.

### Expected behavior
Phase 6D fails closed because protected reserve balances must remain equal to their immutable plan definitions, and every snapshot balance must retain the plan bucket's type, currency and symbol identity.

### Actual behavior
The Phase 6D coordinator and transactional Store checked exact bucket-ID coverage, total conservation and the selected locked/tactical/asset evidence, but did not compare protected reserve balances or every balance's metadata to the immutable plan bucket definitions.

### Technical location
`src/quant_trading/orchestration/target_adjustment_research_asset_cash_preview.py`, `src/quant_trading/persistence/research_asset_cash_sqlite_store.py`

### Root cause
The earlier complete-bucket fix treated exact IDs plus total conservation as complete plan/snapshot identity. That does not detect redistribution out of a protected reserve or metadata tampering while IDs and totals remain unchanged.

### Fix
Validate every snapshot balance's bucket type, currency and symbol against its immutable plan definition, and require locked/tactical reserve balances to equal their initial plan balances, both during orchestration and again inside the result-persistence transaction.

### Regression test
SQLite regressions preserve IDs and total while moving one USD from the locked reserve to the selected asset-cash bucket. The coordinator path requires durable `INVALID_INPUT` with no accepted result, and a separate transaction-level check rejects a source captured before the tamper.

### Validation
The focused Phase 6D repository suite passed 7 tests; the complete suite passed 498 tests and the architecture/governance suite passed 80 tests. No real database row was modified.

### Risk
Research evidence integrity only. Supported Phase 3A transfers already forbid reserve mutation. The fix must fail closed without changing a candidate, factual account, order or trading authority.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the deterministic local fix and regression tests completed in this task.

### Rollback
Reverting the definition/balance identity checks would knowingly restore acceptance of tampered protected reserves.

## BUG-20260722-004

### Title
Compass next-direction checkpoint still named PROPOSAL-020 after PROPOSAL-021 completion

### Status
Fixed

### Severity
Low

### Area
Project governance documentation

### Reproduction steps
1. Read `PROJECT_COMPASS.md` B17 after the verified Phase 6D implementation.
2. Compare the current phase and approved-capability sections with the next-direction paragraph.
3. Observe that the paragraph says `PROPOSAL-020 is complete` although PROPOSAL-021 is the latest completed proposal.

### Expected behavior
The checkpoint names PROPOSAL-021 as complete and accurately states that no later development slice is approved.

### Actual behavior
One stale proposal number remained from the Phase 6C checkpoint.

### Technical location
`PROJECT_COMPASS.md` B17

### Root cause
The Phase 6D semantic update advanced the phase description and exclusions but missed the proposal identifier in one next-direction sentence.

### Fix
Replace only the stale identifier and keep the no-further-approved-work boundary unchanged.

### Regression test
The governance document-integrity suite now requires the Phase 6D/PROPOSAL-021 checkpoint and rejects the stale Phase 6C sentence.

### Validation
The architecture/governance suite passed 80 tests and the complete suite passed 498 tests.

### Risk
Documentation accuracy only; no runtime, database, financial formula or trading authority is affected.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the deterministic correction completed in this task.

### Rollback
Reverting the correction would knowingly restore a false project checkpoint.

## BUG-20260722-005

### Title
Offscreen Plotly queued-data test did not reliably start hidden QWebEngine navigation

### Status
Fixed

### Severity
Low

### Area
Market History shared Plotly/QWebEngine presentation test

### Reproduction steps
1. Run the complete pytest suite in the current Phase 6D working tree.
2. Observe `test_plotly_applies_data_queued_while_initial_page_is_loading` wait ten seconds for the initial page load.
3. In the observed run, `loadFinished` was not received and `loaded` remained empty.

### Expected behavior
The offscreen QWebEngine page loads and the test observes one successful `loadFinished` event before checking queued Plotly data.

### Actual behavior
One complete-suite run reported `loaded == []`; 497 other tests passed. No Risk/Capital code path calls this presentation component.

### Technical location
`tests/unit/market_history/test_history_panel_roles.py::test_plotly_applies_data_queued_while_initial_page_is_loading`

### Root cause
The queued-load test created a `QWebEngineView` but never resized or showed it. The adjacent normal Plotly test uses the real QWidget lifecycle and passed; the hidden offscreen view did not reliably start navigation, so neither `loadFinished` nor the later JavaScript callback arrived.

### Fix
Resize and show the view before starting the queued-load scenario, matching the adjacent production-like WebEngine test. The original ten-second limits, queued-data behavior and assertions remain unchanged; production code was not modified.

### Regression test
The formerly failing exact test passed in isolation after the lifecycle correction.

### Validation
The second complete-suite run passed all 498 tests with only the existing `KI-0005` upstream warning.

### Risk
Potential test reliability or GUI-load timing issue only. No evidence currently shows a production behavior regression, financial calculation change or trading impact.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the deterministic test-lifecycle correction completed and the full suite passed.

### Rollback
Reverting the test lifecycle correction would restore the deterministic offscreen timeout without changing production behavior.

## BUG-20260722-006

### Title
Initial Phase 6D date-query field placement could break positional limit callers

### Status
Fixed

### Severity
Low

### Area
Risk public read-query compatibility

### Reproduction steps
1. Construct `ResearchAssetCashResultQuery` using the pre-PROPOSAL-022 eighth positional argument for `limit`.
2. Observe that the initial additive field order interpreted that value as `as_of_from_utc`.

### Expected behavior
The approved optional UTC bounds are backward-compatible; an existing positional `limit` argument keeps its meaning.

### Actual behavior
During implementation review, the two new optional date fields were initially placed before `limit`.

### Technical location
`quant_trading.risk.research_asset_cash_models.ResearchAssetCashResultQuery`

### Root cause
The first draft preserved keyword construction compatibility but did not preserve dataclass positional field order.

### Fix
Keep `limit` in its existing eighth position and append `as_of_from_utc` / `as_of_to_utc` after it.

### Regression test
The Phase 6D repository test constructs the query with the original positional `limit` position and verifies the value remains `123`.

### Validation
Targeted Risk-chain and Phase 6D tests pass after the correction; final full-suite evidence is recorded in the corresponding Edit Log entry.

### Risk
Read-query construction compatibility only. The draft was corrected before task completion; no database row, financial result or trading behavior was affected.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the compatibility defect was corrected in the same implementation task.

### Rollback
Reverting the field-order correction would restore the positional-constructor incompatibility.

## BUG-20260722-007

### Title
Initial Risk-chain subtab parameter placement could reinterpret a positional parent

### Status
Fixed

### Severity
Low

### Area
Algorithm Control GUI composition compatibility

### Reproduction steps
1. Construct the existing `RiskManagementPanel` using its previous sixth positional `parent` argument.
2. In the initial Phase 6E draft, that value occupied the newly inserted `risk_chain_panel` position instead.

### Expected behavior
Existing positional construction keeps the same parent semantics; the additive explorer is supplied explicitly by keyword.

### Actual behavior
The first draft inserted the optional explorer argument before `parent`.

### Technical location
`quant_trading.algorithm_control.ui.target_adjustment_risk_panel.RiskManagementPanel`

### Root cause
The additive composition parameter was initially inserted into the existing positional portion of the constructor.

### Fix
Retain `parent` in its prior position, make `risk_chain_panel` keyword-only, and pass it by keyword from `AlgorithmControlPanel`.

### Regression test
Existing Algorithm Control construction tests plus the Phase 6E GUI suite exercise both default/no-service composition and explicit explorer wiring.

### Validation
Targeted Algorithm Control and final complete-suite evidence are recorded in EDIT-20260722-006.

### Risk
GUI constructor compatibility only. The draft was corrected before task completion; no persisted data, calculation or trading behavior was affected.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the compatibility issue was corrected in the same implementation task.

### Rollback
Reverting the signature correction would restore positional-parent incompatibility.

## BUG-20260722-008

### Title
Plotly load-finished callback was not registered as a native Qt slot

### Status
Fixed

### Severity
Low

### Area
Shared Plotly/QWebEngine presentation lifecycle

### Reproduction steps
1. Run the complete suite after the Phase 6E compatibility regression was added.
2. Observe the queued-data Plotly test receive `loadFinished=True` but then time out waiting for the queued `Plotly.react` result.
3. Qt reports `AttributeError: Slot 'PlotlyFigureView::_on_load_finished(bool)' not found.`

### Expected behavior
The internal load-finished callback is present in the Qt meta-object, applies the latest queued figure after initial navigation and allows later JavaScript callbacks to complete.

### Actual behavior
The callback was connected as an undecorated Python method. Under one long full-suite QWebEngine lifecycle it was not found as a Qt slot, so the queued figure was not applied and the JavaScript callback did not return.

### Technical location
`quant_trading.visualization.plotly_view.PlotlyFigureView._on_load_finished`

### Root cause
The cross-language signal callback relied on PySide's dynamic method connection instead of declaring the stable `bool` slot in the Qt meta-object.

### Fix
Decorate `_on_load_finished` with `@Slot(bool)` and assert its Qt meta-object registration in the production-like Plotly test.

### Regression test
Both the full local-file Plotly/resize-observer test and queued-during-load test pass together; the former verifies `indexOfSlot("_on_load_finished(bool)") >= 0`.

### Validation
The two exact Plotly tests pass after the correction. Final complete-suite evidence is recorded in EDIT-20260722-006.

### Risk
Presentation callback/lifecycle only. No chart data meaning, financial formula, database or trading behavior changed.

### Known Issues disposition
Not added to `KNOWN_ISSUES.md` because the meta-object registration defect was confirmed and fixed locally. This supersedes the incomplete lifecycle-only explanation in BUG-20260722-005.

### Rollback
Reverting the slot declaration would restore reliance on the unstable dynamic callback registration.

## BUG-20260722-009

### Title
Read-only diagnostics reported every current central database as Schema v1

### Status
Fixed

### Severity
Medium

### Area
Diagnostics / central SQLite observability

### Reproduction steps
1. Run `python -m quant_trading.diagnostics` against the verified central Schema v13 database.
2. Observe the successful `sqlite_schema` result.

### Expected behavior
The diagnostic reports the actual migration version, compares it with the application-supported version and verifies the tables required by that version.

### Actual behavior
The diagnostic reports `central_sqlite_v1` and checks only the seven Phase-1 tables even though the database and application are at Schema v13.

### Technical location
`quant_trading.diagnostics._database_checks`

### Root cause
Diagnostics retained a private Phase-1 table list and literal label instead of reading the schema version and current schema contract owned by central persistence.

### Fix
Added the persistence-owned `CentralSchemaInspection` / `inspect_central_schema` contract. Diagnostics now reads exact migration history, compares it with the supported version, verifies the complete required table set and reports `PRAGMA foreign_key_check` separately. A healthy current database reports `central_sqlite_v13; tables=74`.

### Regression test
`test_diagnostics_are_read_only_safe_and_skip_network_by_default` verifies the supported version/table message and foreign-key result. `test_diagnostics_fail_when_current_schema_is_missing_a_required_table` drops one late v13 table in a temporary database and requires `sqlite_schema=FAIL` plus blocked health.

### Validation
The exact diagnostics/persistence suite passed 10 tests; the final complete suite passed 512 tests with only existing KI-0005. The real database read-only diagnostic reports v13, 74 tables, physical integrity `ok` and foreign keys `ok`.

### Risk
The database is not modified by diagnostics, but the false success label can mislead operators and hide missing post-v1 tables until a feature query fails.

### Known Issues disposition
Not added because the deterministic defect is fixed and fully covered.

### Rollback
Reverting the diagnostic integration would restore the false v1 label and post-v1 schema blind spot; no database rollback is involved.

## BUG-20260722-010

### Title
Central SQLite initialization accepted a current-version database missing later business tables

### Status
Fixed

### Severity
High

### Area
Central SQLite schema validation

### Reproduction steps
1. Initialize a temporary central database to Schema v13.
2. Drop `target_adjustment_research_asset_cash_rule_results` while leaving all migration rows intact.
3. Call `CentralSQLiteDatabase.initialize()` again.

### Expected behavior
Initialization fails closed because the current Schema v13 contract is incomplete.

### Actual behavior
Initialization completes successfully; the migration version remains 13 and the required table remains absent.

### Technical location
`quant_trading.persistence.sqlite_database.CentralSQLiteDatabase._validate_after_migration`

### Root cause
Post-initialization validation checks SQLite integrity, foreign keys and pre-existing row counts, but it does not compare `sqlite_master` with the complete table set defined by migrations.

### Fix
Derive the expected logical table set through any supported version from the persistence-owned migrations. Existing databases are checked for contiguous migration history and all tables required at their current version before any forward migration; the final current contract is checked again after migration. Missing/gapped databases fail closed and are not automatically repaired, deleted or overwritten.

### Regression test
Three central-persistence regressions require rejection of a current v13 database missing a late table, rejection of an incomplete v1 database before any v2+ migration, and rejection of a current database with a migration-history gap. The old-schema test verifies that `algorithm_runs` was never added after preflight failure.

### Validation
The exact diagnostics/persistence suite passed 10 tests; the final complete suite passed 512 tests and the architecture/governance suite passed 83. The real database was inspected read-only and is complete; no migration or business row was created.

### Risk
A locally damaged or manually altered database can pass startup validation and fail later inside a feature repository. The proposed fix changes only fail-closed validation; it does not migrate, repair or delete user data.

### Known Issues disposition
Not added because the deterministic defect is fixed and fully covered.

### Rollback
Code rollback removes the stricter fail-closed check but does not downgrade or change Schema v13. Reverting is not recommended because it would knowingly accept incomplete logical schemas again.

## BUG-20260722-011

### Title
Whole-program verification summary dropped the protected Phase 6E no-write-path phrase

### Status
Fixed

### Severity
Low

### Area
Compass verification metadata / governance test

### Reproduction steps
1. Replace the prior Phase 6E-only `last_verified_commit_or_working_tree_state` with the whole-program sweep summary.
2. Run `tests/architecture/test_governance_document_integrity.py`.
3. Observe the exact Phase 6E assertion fail because `no persistent write path changed` is no longer present.

### Expected behavior
The broader verification summary retains the still-true Phase 6E no-persistent-write-path statement required by canonical governance evidence.

### Actual behavior
The summary retained Schema v13 and execution-safety facts but omitted that exact protected statement.

### Technical location
`PROJECT_COMPASS.md` YAML metadata and `test_compass_verification_metadata_describes_current_phase_six_e_work`.

### Root cause
The diagnostic-sweep summary replaced rather than extended the existing Phase 6E evidence sentence.

### Fix
Restored the accurate Phase 6E phrase inside the broader whole-program verification summary without removing the new v13 schema-validation evidence.

### Regression test
The existing governance test requires the exact Phase 6E identity, Schema v13 and no-persistent-write-path statements in Compass metadata.

### Validation
Final governance/diagnostics/persistence validation passed 93 tests after the correction.

### Risk
Documentation/test compatibility only. No runtime, database, financial result or trading authority is affected.

### Known Issues disposition
Not added because the deterministic documentation regression was fixed immediately.

### Rollback
Reverting the one-line metadata correction would knowingly restore the governance failure and incomplete verification statement.

## BUG-20260731-001

### Title
Alpaca plural corporate-action category was falsely classified as unsupported

### Status
Fixed and verified

### Severity
Medium

### Area
Market History / read-only Alpaca corporate-action evidence

### Reproduction steps
1. Use the approved read-only validation to request AAPL corporate actions for 2026-01-01 through 2026-07-30.
2. Observe Alpaca return two cash-dividend events whose category is `cash_dividends`.
3. Convert them with `AlpacaCorporateActionProvider`.

### Expected behavior
The provider-specific plural category is normalized to the project-owned canonical `cash_dividend` action type and remains supported evidence. Dividend evidence is preserved but does not dividend-adjust the Factor price series.

### Actual behavior
Both events retain `cash_dividends` and are marked unsupported, which would fail closed and unnecessarily block a P23-1 evidence bundle.

### Technical location
`quant_trading.market_history.providers.alpaca_corporate_actions.AlpacaCorporateActionProvider._convert_event`

### Root cause
The initial adapter compared the returned provider string only with singular SDK enum values and did not normalize Alpaca response-group plural names.

### Fix
Added an explicit, closed provider-to-domain action-type mapping for singular and Alpaca response-group plural categories. Unknown categories remain unsupported.

### Regression test
`tests/unit/market_history/test_research_evidence.py` covers plural cash-dividend normalization.

### Validation
The deterministic provider tests and the approved read-only AAPL corporate-action request both passed. The second live response contained two `cash_dividend` events, both supported; no account, position, order or fill client was used.

### Risk
Research availability only. The defect cannot submit trades or alter accounts, but it would incorrectly reject otherwise valid Daily evidence.

### Known Issues disposition
Not added because the confirmed defect was fixed, covered and revalidated in the same implementation task.

### Rollback
Reverting the closed mapping would restore false rejection of supported Alpaca corporate-action evidence and is not recommended.

## BUG-20260731-002

### Title
Short-window spectral segment points used window-local instead of bundle source ordinals

### Status
Fixed and verified

### Severity
Medium

### Area
Factor / P23-1 spectral source lineage

### Reproduction steps
1. Calculate W60, W120 and W250 from one 250-observation frozen bundle.
2. Inspect `SpectralSeriesPoint.source_ordinal` for the W60 leading segment.
3. Observe values 1..40 instead of the exact source observation ordinals 191..230.

### Expected behavior
Every non-padding series point identifies the exact `ResearchBarObservation.ordinal` in the frozen bundle, while segment start/end indexes separately retain window-local calculation bounds.

### Actual behavior
Segment points identify only their location inside the selected window. Numerical FFT inputs and results remain correct, but persisted source navigation for W60/W120 is inaccurate.

### Technical location
`quant_trading.factors.spectral_engine.SpectralVolatilityEngine._spectrum`

### Root cause
One integer was reused for two distinct meanings: window-local segment start and bundle-level source observation ordinal.

### Fix
Passed the exact first bundle observation ordinal separately from the window-local segment bound and preserved zero-padding as null lineage.

### Regression test
`tests/unit/factors/test_spectral_volatility.py` requires W60 to reference exact bundle ordinals 191 through 250, including 191 through 230 for its leading 40-observation segment.

### Validation
The targeted P23-1 suite and full project suite passed; stored numerical values are unchanged while the source links now identify the correct frozen observations.

### Risk
Audit/replay lineage only; calculated prices, power, periods and statuses are unchanged. No downstream trading consumer exists.

### Known Issues disposition
Not added because the lineage defect was fixed and covered in the same implementation task.

### Rollback
Reverting the ordinal separation would knowingly make W60/W120 audit lineage inaccurate.

## BUG-20260731-003

### Title
Initial P23-1 engine did not enforce recognized evaluation session and adjustment reconciliation

### Status
Fixed and verified

### Severity
High

### Area
Market History evidence validation / P23-1 Factor input gate

### Reproduction steps
1. Build a bundle whose `as_of_utc` falls on a weekend, or label later-captured evidence as `POINT_IN_TIME_OBSERVED`.
2. Alternatively provide raw/split prices whose ratio changes without a matching frozen split event.
3. Calculate the P23-1 windows.

### Expected behavior
An evaluation date must be a completed recognized XNYS session; point-in-time labels must agree with observed timestamps; `UNVERIFIED_ADJUSTMENT` is invalid; raw/split ratios must be piecewise consistent with frozen forward/reverse splits; dividends remain unadjusted warnings; unsupported reorganizations invalidate only crossing windows.

### Actual behavior
The initial implementation accepted a weekend as-of and did not yet evaluate adjustment ratios. It also rejected an unsupported action globally in the bundle builder instead of preserving the event and assigning the exact per-window status.

### Technical location
`quant_trading.market_history.research_evidence.SpectralMarketEvidenceBuilder` and `quant_trading.factors.spectral_engine.SpectralVolatilityEngine`

### Root cause
The first implementation slice established typed provenance before all approved R1 validation gates were connected to the per-window engine path.

### Fix
Added closed evidence-mode/time checks, completed-recognized-session validation, common-feed validation, exact Decimal raw/split ratio reconciliation, dividend warnings and per-window unsupported-action invalidation.

### Regression test
`tests/unit/factors/test_spectral_volatility.py` covers weekend/unrecognized as-of, unverified adjustment, valid and invalid split reconciliation, dividend warnings and unsupported actions that invalidate only crossing windows.

### Validation
The direct numerical, market-evidence, repository and full project suites passed, including deterministic holiday/early-close/temporary-closure fixtures.

### Risk
Research correctness and reproducibility. No Decision, Risk, account or execution consumer exists, but invalid evidence could otherwise be presented as valid research.

### Known Issues disposition
Not added because the high-severity evidence gate was completed fail-closed and verified before handoff.

### Rollback
Reverting these gates would allow invalid or non-reproducible market evidence to appear valid and is not recommended.

## BUG-20260731-004

### Title
Adding test package markers broke existing top-level conftest imports

### Status
Fixed and verified

### Severity
Low

### Area
Test organization

### Reproduction steps
1. Add `__init__.py` under `tests/` and `tests/unit/` to support a new relative fixture import.
2. Run the full pytest suite.
3. Observe eight existing Market History tests fail collection because their established `from conftest import ...` import no longer resolves as before.

### Expected behavior
New P23-1 test helpers do not change the import context of existing tests.

### Actual behavior
Package markers changed test-module import semantics before any production test ran.

### Technical location
New test package marker files and P23-1 test helper imports.

### Fix
Removed the package markers, exposed only the dedicated Factor test-helper directory through pytest's test-only `pythonpath`, and retained plain helper imports.

### Regression test
The full suite exercises the established Market History `conftest` imports together with the new P23-1 tests.

### Validation
The final full project suite passed 531 tests with one pre-existing upstream WebSocket deprecation warning.

### Risk
Test collection only; no runtime, database, financial or trading behavior is affected.

### Known Issues disposition
Not added because the collection regression was fixed and the complete suite passed.

### Rollback
Re-adding the package markers would restore the collection failure and is not recommended.

## BUG-20260802-001

### Title
Retrospective spectral evidence is still filtered by historical observation time

### Status
Open — confirmed during PROPOSAL-025 pre-implementation audit

### Severity
High

### Area
P23-1 spectral Factor evidence admission

### Reproduction steps
1. Build a valid `RETROSPECTIVE_ADJUSTED` P23-1 evidence bundle for a completed historical XNYS session.
2. Preserve the truthful Bar `first_observed_at_utc` later than the historical evaluation close, as required for newly fetched history.
3. Run `SpectralVolatilityEngine.calculate`.
4. Observe that `_window` unconditionally requires `available_at_utc < as_of_utc`, so every retrospectively fetched observation is excluded and the windows cannot calculate.

### Expected behavior
`POINT_IN_TIME_OBSERVED` uses only observations available before the historical as-of. Explicitly labeled `RETROSPECTIVE_ADJUSTED` research may use the frozen later-observed Bars while retaining their real observation times and the retrospective warning. It must not be represented as point-in-time/backtest-safe.

### Actual behavior
Both evidence modes use the point-in-time availability filter. A truthful weekend or later-date manual preview over freshly fetched data therefore becomes unusable even though the approved retrospective mode exists specifically to preserve and label that research case.

### Technical location
`src/quant_trading/factors/spectral_engine.py`, `SpectralVolatilityEngine._window`.

### Planned fix
Make the observation-admission predicate explicitly mode-dependent without changing any spectral formula, window size or missing-session rule. Add a regression test proving that the same late-observed input is rejected for `POINT_IN_TIME_OBSERVED` and admitted only when explicitly labeled `RETROSPECTIVE_ADJUSTED`.

### Risk
Research correctness and availability semantics. The current behavior blocks the approved manual runner; an over-broad fix could introduce look-ahead into point-in-time results. The fix must retain the strict point-in-time gate and retrospective warning.

### Known Issues disposition
Not added while the approved PROPOSAL-025 implementation is actively fixing and validating the defect. Add to `KNOWN_ISSUES.md` if it remains unresolved at handoff.

### Rollback
Not applicable until a fix is implemented.

### Verification update — 2026-08-02 (BUG-20260802-001/002/003)

All three PROPOSAL-025 defects are verified **Fixed**:

- `BUG-20260802-001`: `SpectralVolatilityEngine` now keeps strict availability admission for `POINT_IN_TIME_OBSERVED` while admitting truthfully later-observed frozen Bars only for explicit `RETROSPECTIVE_ADJUSTED` evidence. Regression: `test_retrospective_mode_admits_truthfully_late_evidence_only_with_label`.
- `BUG-20260802-002`: `SpectralVolatilityService` now persists the exact non-point-in-time evidence mode in operation warnings and Run messages. Regression: `test_retrospective_warning_is_persisted_and_visible_in_run_messages` plus coordinator reload assertions.
- `BUG-20260802-003`: the concrete Market History factory remains in `quant_trading.market_history.composition`, is no longer imported through the lightweight package root, and Algorithm Control imports the explicit composition module. Regression: `test_algorithm_control_app_imports_in_a_fresh_process`.

The P25 targeted suite passed 29 tests; the final full suite passed 547 tests with one pre-existing upstream WebSocket warning. Compilation passed. The single approved end-to-end AAPL read-only validation completed after the cold-start fix and reloaded its exact Run/operation from a fresh process; SQLite reported `integrity_check=ok` and zero foreign-key violations. No Trading client/account/position/order/fill operation occurred. None of these bugs remains a current Known Issue.

Rollback: restore strict rejection of the P23-1E-A runner as a whole while retaining immutable stored definitions/Runs/results for inspection. Do not weaken point-in-time admission, remove the retrospective warning, or restore the eager package-root composition export.

## BUG-20260802-003

### Title
Exporting the Market History composition factory from the package root creates a cold-start import cycle

### Status
Open — confirmed before the approved external validation made any network request

### Severity
High

### Area
P23-1E-A application composition and package boundaries

### Reproduction steps
1. Import the Algorithm Control application in a fresh Python process after adding the P25 Market History composition factory to `quant_trading.market_history.__init__`.
2. Observe `market_history.__init__ → composition → storage → persistence → decision → factors → market_history`.
3. Import fails because `quant_trading.decision` is only partially initialized.

### Expected behavior
All formal application modules import successfully from a clean process. Market History may own its concrete composition factory without forcing every import of the lightweight public Market History models through Persistence and Decision.

### Actual behavior
The package-root re-export eagerly imports the concrete composition path and creates a cycle. The approved AAPL validation stopped at import time; no provider/client request, AAPL Run or result was created.

### Technical location
`src/quant_trading/market_history/__init__.py` package-root export and the Algorithm Control import of that export.

### Planned fix
Keep the concrete factory in `quant_trading.market_history.composition`, remove it from the lightweight package root and import the explicit composition module only from the Algorithm Control composition root. Add a fresh-subprocess import regression test.

### Risk
Application startup availability. No financial, database, Market Data or trading behavior occurred before failure.

### Known Issues disposition
Not added while the current task is actively fixing and validating it. Add to `KNOWN_ISSUES.md` if unresolved at handoff.

### Rollback
Remove the P25 application composition until the cycle is fixed; retaining the eager root export is unsafe.

## BUG-20260802-002

### Title
Retrospective spectral mode marks warning status without preserving its warning code

### Status
Open — confirmed during PROPOSAL-025 GUI integration

### Severity
Medium

### Area
P23-1 spectral operation and Run observability

### Reproduction steps
1. Run `SpectralVolatilityService.preview` with a valid `RETROSPECTIVE_ADJUSTED` bundle.
2. Observe that the Market Data stage and operation status become warning-bearing.
3. Reload the operation and inspect `operation.warnings` and Run messages.

### Expected behavior
The exact `RETROSPECTIVE_ADJUSTED` warning is preserved in the immutable operation warning array and Run messages so restart/replay/export does not rely on interpreting status or another field indirectly.

### Actual behavior
The service uses the evidence mode when choosing warning status but constructs the stored warning tuple only from window warnings/statuses. A valid retrospective operation can therefore be `COMPLETED_WITH_WARNINGS` with no explicit retrospective warning string.

### Technical location
`src/quant_trading/factors/spectral_service.py`, successful preview warning construction.

### Planned fix
Add the non-point-in-time evidence mode as an explicit operation/Run warning before window warnings and add service/repository regression assertions.

### Risk
Audit clarity only; no calculation, state, position, Risk or execution behavior changes. Omitting the warning could still cause a user to overstate historical point-in-time validity.

### Known Issues disposition
Not added while the current approved implementation is actively fixing it. Add to `KNOWN_ISSUES.md` if unresolved at handoff.

### Rollback
Not applicable until a fix is implemented.

### Final verification update — 2026-08-02

`BUG-20260802-001`, `BUG-20260802-002` and `BUG-20260802-003` are all **Fixed** with the regression and full-suite evidence recorded in the earlier consolidated verification update. This later append is authoritative over each original `Open` discovery status. No current Known Issue remains from these three defects.

## BUG-20260806-001

### Title
Roadmap still says the separately approved AAPL P26 validation was not executed

### Status
Fixed during PROPOSAL-027 proposal creation; validation pending at this append

### Severity
Low

### Area
Project governance documentation

### Reproduction steps
1. Open `docs/project/ROADMAP.md` after the 2026-08-06 AAPL P26 validation.
2. Read `Proposed next — awaiting approval` and the P26 item in `Pending user decisions`.
3. Observe that both still say the real AAPL historical validation was not executed or still required a separate instruction.
4. Compare with the completed study, Project State, Compass, PROPOSAL-026 and `EDIT-20260806-002` evidence.

### Expected behavior
The Roadmap must distinguish completed P26 implementation/validation from the next unapproved P27 proposal and must not ask again for an already completed validation.

### Actual behavior
The Roadmap retained pre-validation wording even though the authoritative validation records show 40 of 40 completed-with-warnings points and exact restart reload.

### Technical location
`docs/project/ROADMAP.md`, the `Proposed next` and `Pending user decisions` sections.

### Fix
Replace the stale P26 proposal/validation wording with the completed AAPL evidence and record PROPOSAL-027 as the actual proposed next slice. Add a governance regression assertion that the Roadmap contains the completed-validation truth and does not retain the stale phrase.

### Risk
Documentation only. The stale text could cause an unnecessary second external-data request or confuse completed evidence with unapproved next work; no calculation, database, financial or trading behavior changed.

### Known Issues disposition
Not added because the stale statements are corrected in the current task and will be covered by a governance test. Add only if validation fails or another current contradictory source remains.

### Rollback
Revert only the P27 proposal references while retaining the corrected P26 validation truth. Do not restore the false “validation not executed” statement.

### Verification update — 2026-08-06

The focused governance document suite passed 8 tests and the complete architecture suite passed 89 tests. The regression requires the Roadmap to record the completed P26 AAPL validation, identify PROPOSAL-027 as proposed/awaiting approval and reject both stale validation-not-executed phrases. `BUG-20260806-001` is verified **Fixed** and is not a current Known Issue.

## BUG-20260806-002

### Title
PROPOSAL-027 documentation impact references a nonexistent schema document

### Status
Open — confirmed during approved implementation pre-audit

### Severity
Low

### Area
Proposal/documentation governance

### Reproduction steps
1. Open the approved `PROPOSAL-027` documentation-impact section.
2. Follow the listed `docs/persistence/SCHEMA.md` update target.
3. Observe that the repository has no `docs/persistence` directory or `SCHEMA.md`; central schema ownership is documented in `docs/modules/central-persistence.md`.

### Expected behavior
An approved implementation plan must reference the existing canonical schema owner document or explicitly approve a new document boundary.

### Actual behavior
The proposal names a nonexistent file even though the existing central-persistence module document already owns schema-version/table/migration/rollback details.

### Technical location
`docs/proposals/PROPOSAL-027-per-stock-daily-volatility-profile.md`, `Documentation impact`.

### Planned fix
Replace the nonexistent target with `docs/modules/central-persistence.md`, update that existing owner document for Schema v16, and add/extend governance assertions so the proposal does not reintroduce the nonexistent path.

### Risk
Documentation only. Creating an unnecessary new documentation directory would duplicate schema ownership and increase drift risk; runtime and financial behavior are unaffected.

### Known Issues disposition
Not added while the approved implementation is actively correcting and verifying the reference. Add only if unresolved at handoff.

### Rollback
Retain the existing central-persistence document as the canonical schema record. Do not create a second schema source merely to satisfy the stale proposal path.

## BUG-20260806-003

### Title
Algorithm Control Factor-contract architecture allowlist omitted the approved P23-1F public modules

### Status
Fixed during PROPOSAL-027 implementation; full-suite revalidation pending at this append

### Severity
Low

### Area
Architecture regression tests

### Reproduction steps
1. Implement the approved P23-1F public models, interfaces and service and compose them in Algorithm Control.
2. Run `tests/architecture/test_dependency_boundaries.py::test_algorithm_control_uses_only_public_factor_authoring_contracts`.
3. Observe that the static allowlist rejects all three new public Factor modules even though the separately added P27 boundary test accepts the same dependency direction.

### Expected behavior
The architecture suite should recognize the approved P23-1F public models/interfaces/service while continuing to reject imports of its private engine or concrete persistence adapter.

### Actual behavior
The general Algorithm Control allowlist stopped at the P26 public modules, so the full suite failed despite the new P27-specific boundary tests passing.

### Fix
Add only `daily_volatility_profile_models`, `daily_volatility_profile_interfaces` and `daily_volatility_profile_service` to the existing public Factor allowlist. The engine, SQLite store and every financial/execution owner remain forbidden.

### Risk and rollback
Test-governance only; runtime and financial behavior are unchanged. Revert the three allowlist entries together with the P27 feature if the approved component is rolled back.

### Final verification update — 2026-08-06

The focused dependency test and complete architecture suite now pass; the exhaustive grouped suite covers all 565 collected tests with no failures. `BUG-20260806-003` is verified **Fixed** and is not a current Known Issue.

### BUG-20260806-002 final verification update — 2026-08-06

The P27 proposal now references `docs/modules/central-persistence.md` as the canonical schema owner, no `docs/persistence/SCHEMA.md` was created, and governance regression tests require this condition. `BUG-20260806-002` is verified **Fixed** and is not a current Known Issue.

## BUG-20260810-001

### Title
P28 end-of-range confirmation was initially reported as a day-1 pending candidate

### Status
Fixed during PROPOSAL-028 implementation

### Severity
Medium

### Area
Asset State / P23-2 reversal-observation engine

### Reproduction and cause
During the first synthetic engine run, a two-session reversal that confirmed on the final available session had no next activation session in the bounded source. The draft evaluator used `activation_session is not None` as the proxy for confirmation. A valid confirmation at the source end therefore appeared as `VALID_WITH_PENDING_CANDIDATE` even though a `REVERSAL_CONFIRMED` event had occurred.

### Expected behavior
Day 2 confirmation and day 3 activation are separate facts. If the source ends on day 2, the durable status must be `CONFIRMED_AWAITING_ACTIVATION`; the evaluator must not invent day 3.

### Fix and regression evidence
The internal candidate now keeps an explicit `confirmed` flag independent of the optional next-session activation date. Synthetic regression tests cover day-1 pending, source-end day-2 confirmation and day-3 activation. The focused P28 domain/persistence suite passes 6 tests.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the defect was found before P28 release, fixed locally and covered by regression tests. Rolling back P28 removes the affected draft evaluator; do not restore the conflated confirmation/activation representation.

## BUG-20260810-002

### Title
P28 history refresh supplied eleven values to a nine-column table

### Status
Fixed during PROPOSAL-028 implementation; final regression verification pending at this append

### Severity
Low

### Area
Algorithm Control / Asset State / P23-2 history GUI

### Reproduction and cause
Populate the reversal-observation history and inspect `ReversalObservationPanel.reload()`. The row tuple repeated P27 Result and Run ID after the intended nine values, so the loop attempted columns 9 and 10 on a table configured with columns 0 through 8. Qt did not expose the duplicated values, which made the mismatch easy to miss.

### Expected behavior
Each history row supplies exactly the nine values named by the table headers, and every visible cell maps to the intended typed field.

### Fix and regression plan
Remove the duplicate pair and extend the GUI regression to require exactly nine columns and populated cells only within that schema.

### Known Issues disposition and rollback
Not added while the local fix and verification are in the same approved implementation. Reverting the fix would restore an internal presentation mismatch but would not change stored evidence or trading behavior.

## BUG-20260810-003

### Title
P28 public Market Evidence accepted empty, non-chronological or internally impossible availability sequences

### Status
Fixed during PROPOSAL-028 implementation; final regression verification pending at this append

### Severity
Medium

### Area
Asset State / P23-2 public evidence contract

### Reproduction and cause
Construct `ReversalObservationMarketEvidence` directly with no evaluated sessions or with duplicate-free expected sessions in descending order. The DTO accepted both because it checked tuple equality and duplicates but not non-empty strict chronology. `ReversalObservationPriceObservation` also accepted `available_at_utc` earlier than `first_observed_at_utc`. The normal GUI coordinator independently rejected or never produced these cases, but the public domain contract did not fail closed for another caller or replay source.

### Expected behavior
P23-2 requires at least one evaluated completed session, a strictly increasing sequence after the seed and an availability timestamp no earlier than both official close and first observation.

### Fix and regression plan
Strengthen the immutable DTO invariants and add unit tests for empty, reordered and impossible-timestamp evidence. Existing valid engine, persistence and replay fixtures must remain unchanged.

### Known Issues disposition and rollback
Not added while the approved implementation is correcting and verifying the contract. Reverting would reopen a misleading research-result path but still would not grant execution authority.

### BUG-20260810-002 final investigation correction — 2026-08-10

Direct UTF-8 source reinspection showed that `ReversalObservationPanel.reload()` already supplied exactly nine values for the nine headers; the apparent repeated pair came from the earlier combined inspection output rather than the file. No GUI source change was required or made for this report. The existing GUI test and final focused/full reruns cover the nine-column table. Treat BUG-20260810-002 as **Closed — cannot reproduce in source**, not Fixed; it is not a Known Issue.

### PROPOSAL-028 final Bug verification update — 2026-08-10

- `BUG-20260810-001` is verified **Fixed**: source-end day-2 confirmation remains distinct from next-session activation and the regression passes.
- `BUG-20260810-003` is verified **Fixed**: immutable source evidence now rejects empty/reordered session sequences, pre-close first observation and availability earlier than source evidence; the new boundary regression and all existing P28 paths pass.
- `BUG-20260810-002` remains **Closed — cannot reproduce**, as corrected above.
- Final complete verification passed **578 tests**. None of these items is added to `KNOWN_ISSUES.md`.

## BUG-20260810-004

### Title
Repeated read-only spectral evidence refresh created a new version-1 calendar-mapping ID and failed persistence

### Status
Confirmed during the approved PROPOSAL-028 AAPL validation; fix and regression verification in progress

### Severity
Medium

### Area
Market History / P23-1 evidence preparation and central SQLite persistence

### Reproduction and cause
Run a second `FETCH_AND_FREEZE_READ_ONLY` spectral preview for AAPL after a version-1 AAPL/XNYS mapping already exists. Evidence preparation created a fresh random mapping ID while still labelling it mapping version 1. Central SQLite correctly enforces one `(symbol, mapping_version)` row, so `INSERT OR IGNORE` retained the original mapping. The subsequent immutable source link referenced the new, non-persisted ID and failed its foreign key.

### Expected behavior
A repeated read-only evidence refresh must reuse the already frozen compatible version-1 symbol/calendar mapping, persist the new evidence graph atomically, and remain fully reloadable. It must not silently create a second identity for the same mapping version.

### Actual impact
The Alpaca Market Data read succeeded and generic Raw/Split bars were cached, but the new spectral evidence graph was rolled back. The Factor Run `55f3146d-991b-4446-bb20-178c3db33b25` durably records the failed prerequisite. No P28 result, account access, order or execution occurred.

### Planned fix and regression
Resolve a compatible mapping from prior frozen spectral evidence before building the next bundle; create mapping version 1 only when none exists. Add a repeated-refresh regression that proves the same mapping identity is reused and the second graph reloads without foreign-key errors. Re-run the approved AAPL validation after the focused tests pass.

### Known Issues disposition and rollback
This issue currently blocks the approved P28 real-data validation and is therefore summarized in `KNOWN_ISSUES.md` until the repair and rerun are verified. Rollback removes only the mapping-reuse helper and its regression; it must not alter existing frozen evidence or cached Market Data.

## BUG-20260810-005

### Title
P28 seed preflight relied on refreshable Market Bar cache instead of the frozen P27 source observation

### Status
Confirmed during the approved PROPOSAL-028 AAPL validation; fix and regression verification in progress

### Severity
Medium

### Area
Asset State / P23-2 research evidence orchestration

### Reproduction and cause
Freeze a valid P27 result whose exact inclusive source bundle contains the 2026-08-05 AAPL close, then refresh the overlapping Raw/Split Market History range before P28. The generic Market Bar cache updates `fetched_at_utc`; P28 used that mutable cache timestamp to prove seed availability and therefore rejected the seed as if it had not existed when P27 was created.

### Expected behavior
The P28 seed must come from P27's exact immutable spectral source observation, including its Raw/Split close fingerprints and original evidence timestamps. Only sessions after the seed should come from the newly frozen forward Market History evidence.

### Actual impact
The local P28 preflight stopped before creating a definition or result. No account, position, order or execution boundary was accessed.

### Planned fix and regression
Resolve the seed from the exact P27 source bundle, fail closed unless its session and availability match P27, and continue using local frozen post-seed bars for evaluated sessions. Add a regression where generic seed-cache timestamps are newer than P27 but the exact frozen P27 seed remains valid.

### Known Issues disposition and rollback
This issue currently blocks validation and is summarized as `KI-0015` until the focused repair and real-data rerun pass. Rollback restores the older cache-dependent preflight and is not recommended because it makes reproducibility depend on later cache refreshes.

### BUG-20260810-004 final verification update — 2026-08-10

The preparation service now reuses the latest compatible frozen symbol/calendar mapping regardless of its positive version number, while the SQLite exact-bundle query resolves one requested symbol/as-of/feed/mode directly. The regression explicitly reuses a P26-style mapping version `20250710`; 14 focused Market History/P23-1 persistence tests pass. The repaired read-only refresh persisted operation `af2cc617-5172-4915-a2cf-15db574378c5` / Run `4df2d227-6f57-40a6-bf1d-a6fc2c4099b2` with mapping `b49c78da-ae3d-5648-bccb-5b98c65a3ead`. `BUG-20260810-004` is **Fixed** and `KI-0014` is resolved.

### BUG-20260810-005 final verification update — 2026-08-10

P28 now chooses the latest compatible immutable spectral observation that was available by P27 creation, rejects conflicting frozen evidence and uses its original Raw/Split fingerprints, closes and availability timestamps as the seed. The regression deliberately refreshes the generic seed-cache timestamp after P27 while preserving the earlier frozen seed; the exact preflight still succeeds. The combined P28/source regression set passed 23 tests, and the real AAPL result reloaded and recalculated exactly. `BUG-20260810-005` is **Fixed** and `KI-0015` is resolved.

## BUG-20260810-006

### Title
Implemented PROPOSAL-028 still ended with a stale pre-approval instruction

### Status
Fixed during the approved AAPL validation documentation update

### Severity
Low

### Area
Governance documentation

### Reproduction and cause
Read the final sentence of the already `IMPLEMENTED_VERIFIED_DISABLED` PROPOSAL-028. A proposal-template instruction still said not to mark or implement the proposal until approval, even though the approval record and implementation evidence directly above showed that the user had approved it.

### Fix and verification
Replace the stale sentence with the current boundary: the package is approved and implemented but remains disabled, has no multiplier default and grants no formal-state or trading authority. Governance assertions continue to require the approved/disabled status and the exact validation evidence.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the contradiction was corrected in the same documentation pass. Rolling back would restore conflicting governance instructions and is not recommended.

## BUG-20260810-007

### Title
P28 validation metadata update temporarily dropped the P27 local-source checkpoint phrase

### Status
Fixed during final governance verification

### Severity
Low

### Area
Compass verification metadata / governance regression

### Reproduction and cause
Run `test_compass_verification_metadata_describes_current_p23_2_work` after replacing the older “no P28 validation” metadata. The new text preserved the exact P27 result ID but omitted the explicit `local-only AAPL reuse` wording required to keep the P26→P27 source checkpoint visible.

### Fix and verification
Restore the truthful prior local-only P26/P27 checkpoint alongside the new P28 validation evidence. The focused governance test is rerun before the full suite.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this was a change-local documentation regression corrected before handoff. Reverting would reduce provenance clarity but would not change runtime behavior.

### P28 validation final regression summary — 2026-08-10

The complete repository suite passed **579 tests** after the fixes for `BUG-20260810-004`, `BUG-20260810-005`, `BUG-20260810-006` and `BUG-20260810-007`. Python compilation, dependency consistency, diff hygiene and the forbidden P28-consumer scan also passed. No new unresolved Bug or Known Issue was found in the final audit.

## BUG-20260810-008

### Title
Compass P23-2A capability row retained the pre-validation “no real-symbol validation” boundary

### Status
Fixed during final P28 validation consistency scan

### Severity
Low

### Area
Compass evolving capability inventory

### Reproduction and cause
Read the P23-2A capability row after the approved AAPL validation. The current phase, verification metadata and Project State correctly record the real-symbol validation, but the shorter capability row still contains the earlier pre-validation phrase `no default, real-symbol validation or financial consumer`.

### Expected behavior and planned fix
The row must say that one separately approved AAPL validation exists while still making clear that it did not create a default or financial consumer. Add a governance assertion so the obsolete phrase cannot return.

### Known Issues disposition and rollback
Not added because this change-local documentation inconsistency was fixed and verified in the same pass. Reverting would restore contradictory governance evidence without changing runtime behavior.

### Final verification
The capability row now records the separately approved AAPL validation while retaining the no-default/no-financial-consumer boundary. The governance regression rejects the obsolete phrase and the focused governance suite passes **9 tests**. No Known Issue remains.

## BUG-20260810-009

### Title
Governance assertions still required the P27 publication and pre-P29 “no next work” wording

### Status
Fixed during CHECKPOINT-20260810-006 pre-publication verification

### Severity
Low

### Area
Governance document integrity tests

### Reproduction and cause
After updating Compass to the authorized P28 publication checkpoint and recording that the user approved proposal-only P29 creation, run `tests/architecture/test_governance_document_integrity.py`. Two assertions still require `PROPOSAL-027` in current publication metadata and the exact sentence `No further implementation slice is currently approved` in Next Direction.

### Expected behavior and planned fix
The regression should require current P28/CHECKPOINT-006 evidence, retain the exact P27 source-result checkpoint, recognize proposal-only P29 authorization and explicitly require that P29 implementation remains unapproved. It must not weaken the no-runtime/no-trading boundary.

### Known Issues disposition and rollback
Not added because this change-local test expectation was corrected and verified before publication. Reverting only the assertion update would make truthful publication metadata fail without improving safety.

### Final verification
The test now requires `CHECKPOINT-20260810-006`, current P28 evidence, the exact P27 source result, proposal-only P29 authorization and the explicit no-P29-implementation boundary. The focused governance suite passes **9 tests** and the complete architecture suite passes **92 tests**.

## BUG-20260810-010

### Title
P29 proposal metadata compression again removed exact P27/P28 checkpoint phrases

### Status
Fixed during PROPOSAL-029 proposal-only self-audit

### Severity
Low

### Area
Compass current verification metadata

### Reproduction and cause
Compare the P29-updated `last_verified_commit_or_working_tree_state` with the existing governance assertions. The shortened publication text kept the correct IDs and meaning but replaced the exact phrases `local-only AAPL reuse`, `one separately approved read-only AAPL validation`, `VALID_NO_REVERSAL result ...` and the explicit no-Trading-access sentence. Those phrases are deliberate provenance checkpoints protected after BUG-20260810-007.

### Expected behavior and planned fix
Restore the exact P26→P27→P28 provenance wording while appending the P29 proposal-only working-tree state. Keep the regression assertions and add P29-specific assertions rather than weakening P28 evidence.

### Known Issues disposition and rollback
Not added because this change-local documentation recurrence was corrected and verified in the same proposal pass. Reverting the correction would reduce provenance clarity but would not alter runtime behavior.

### Final verification
Compass again preserves the exact P26→P27→P28 checkpoint phrases and appends P29 only as proposal/governance working-tree state. The focused governance suite passes **10 tests** and the complete architecture suite passes **93 tests** without weakening any P28 assertion.

## BUG-20260810-011

### Title
P29 SQLite Run Stage validation queried a nonexistent `name` column

### Status
Fixed during PROPOSAL-029 implementation

### Severity
Medium

### Area
P23-3 cycle target-position persistence / Run History integrity validation

### Reproduction and cause
Save the first P29 formula definition through `CycleTargetPositionService`. The P29 SQLite store validates the associated Run Stage with `SELECT run_id, name FROM algorithm_run_stages`, while the central schema names that column `stage_name`. SQLite raises `OperationalError`, so the immutable definition and its operation attempt cannot be persisted.

### Expected behavior and planned fix
Validate against the canonical `stage_name` column and retain the existing exact Run type, execution mode, Run ID and stage-name checks. The P29 SQLite integration test is the regression test.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the defect was found before P29 handoff and is being corrected in the same implementation. Reverting the fix would make all P29 definition/configuration/result persistence unusable but would not affect previously published modules.

### Final verification
The Store now validates the canonical `algorithm_run_stages.stage_name` column while retaining exact Run type, execution mode, Run ID and stage-name checks. P29 immutable formula/configuration/result persistence, restart reload and replay integration tests pass; the affected-module suite passes 142 tests, the architecture suite passes 94 tests and the complete repository suite passes 591 tests.

## BUG-20260810-012

### Title
P29 preview failure finalization could overwrite a completed source Stage

### Status
Fixed during PROPOSAL-029 implementation

### Severity
Medium

### Area
P23-3 Run lifecycle / failure audit fidelity

### Reproduction and cause
Let exact P28 source validation complete the P29 `STATE` Stage, then make creation of the `TARGET_POSITION` Stage fail. The exception handler currently falls back to the local `STATE` Stage object. Because that object still represents its originally returned running state, failure finalization can attempt to mark the already completed persisted source Stage as failed.

### Expected behavior and planned fix
Track whether the source Stage was durably completed. Source-validation failures must fail `STATE`; failures after that completion but before a target Stage exists must leave `STATE` completed and fail only the Run; failures after target Stage creation must fail `TARGET_POSITION`. Add focused lifecycle tests for the first two cases.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because P29 is not yet handed off and the defect is being corrected before active use. Reverting would affect only P29 failure-history fidelity, not calculations or earlier modules.

### Final verification
The service now tracks durable completion of the source `STATE` Stage. Source-validation failure fails `STATE`; a failure while starting `TARGET_POSITION` after source completion leaves `STATE` completed and fails only the Run; later target failures attach to `TARGET_POSITION`. Focused lifecycle regression tests pass within the 142-test affected-module suite and the complete 591-test repository suite.

## BUG-20260810-013

### Title
Roadmap pending-decision summary still identified central SQLite as Schema v16

### Status
Fixed during PROPOSAL-030 proposal-only synchronization

### Severity
Low

### Area
Project governance / Roadmap current-state accuracy

### Reproduction and cause
Read `docs/project/ROADMAP.md` after the verified P29 v17→v18 migration. The current pending-decision summary still says that the approved dependencies and central SQLite v16 are implemented, even though Project State, Compass, canonical architecture and the active database now consistently report Schema v18/116. The sentence was not advanced when later additive P28/P29 migrations were documented.

### Expected behavior and planned fix
Update only the stale current-schema reference to v18 and preserve the historical v16/v17 migration statements elsewhere. Add a governance assertion that the P30-era Roadmap current pending summary names central SQLite v18.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this is a documentation-only current-state drift being corrected in the same proposal pass. Reverting the correction would not change runtime data but would again mislead users and future agents about the active schema.

### Final verification
The Roadmap current pending-decision summary now names central SQLite v18 while preserving the historical v16/v17 statements in their proper checkpoints. The focused governance suite passes 11 tests and the complete architecture suite passes 95 tests.

## BUG-20260810-014

### Title
P30 Compass metadata append removed the protected exact P29 empty-data phrase

### Status
Fixed during PROPOSAL-030 proposal-only self-audit

### Severity
Low

### Area
Compass current verification metadata

### Reproduction and cause
Run `tests/architecture/test_governance_document_integrity.py` after appending the proposal-only P30 statement to `last_verified_commit_or_working_tree_state`. The metadata still says the six P29 tables are empty and that P30 creates no formula/configuration/Run/result/database row, but the rewrite dropped the exact protected phrase `no real P29 definition/configuration/result` established by the P29 implementation checkpoint.

### Expected behavior and planned fix
Restore the exact P29 phrase while retaining the P30 proposal-only/no-data statement. Keep the regression assertion unchanged and add P30-specific assertions separately.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the metadata regression was found and corrected before handoff and did not alter runtime or database state. Reverting the correction would reduce checkpoint precision without changing behavior.

### Final verification
Compass again preserves the exact `no real P29 definition/configuration/result` phrase and separately states that P30 created no formula/configuration/Run/result/database row. The original assertion was not weakened; the focused governance suite passes 11 tests and the complete architecture suite passes 95 tests.

## BUG-20260810-015

### Title
Publication checkpoint metadata dropped the protected P28 Schema-v17 evidence

### Status
Fixed during P29/P30 publication checkpoint

### Severity
Low

### Area
Compass publication metadata / governance regression

### Reproduction and cause
Run `tests/architecture/test_governance_document_integrity.py` after replacing the pre-publication Compass verification sentence with the P29/P30 feature commit identity. The new metadata retains P28 Result/Run provenance and the older checkpoint commit but omits the exact `v17/110` migration evidence protected by the governance test. The publication rewrite compressed historical P28 context too aggressively.

### Expected behavior and planned fix
Restore the explicit P28 central SQLite `v16/104→v17/110` migration evidence while retaining the new P29/P30 feature commit `7ad1e1f`, Schema-v18 and validation evidence. Keep the existing regression assertion; rerun the focused governance suite before the checkpoint commit.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this is a documentation-only regression discovered before publication handoff and can be corrected locally without runtime impact. Reverting only the faulty checkpoint metadata would also restore the phrase but lose the truthful current feature-commit state.

### Final verification

Compass v82 now retains the exact P28 `P23-2A`, `v16/104→v17/110`, separately approved read-only AAPL validation, no-Trading-access and `DISABLED/execution_allowed=false/live_allowed=false` phrases while separately recording feature commit `7ad1e1f` and P29/P30 evidence. The protected governance suite passes all 11 tests without weakening an assertion.

## BUG-20260810-016

### Title
Canonical P23-3A architecture still denied the completed P30 validation rows

### Status
Fixed during next-slice inspection

### Severity
Low

### Area
Canonical architecture / P23-3A current persistence state

### Reproduction and cause
Read the P23-3A `Side effects / configuration` row in `docs/architecture/OVERVIEW.md` after completed PROPOSAL-030. It still says there is no real P29 row, although P30 intentionally and immutably created one disabled formula, one disabled AAPL configuration, five attempts, three results/traces and eighteen source links. P30 correctly changed no architecture, so the earlier implementation-era empty-data sentence was not synchronized when validation evidence was appended.

### Expected behavior and planned fix
Keep the architecture and safety meaning unchanged while replacing only the stale empty-data claim with the exact bounded P30 validation state: no automatic/default selection, only approved disabled local validation evidence, and no downstream consumer. Add an architecture regression assertion and update the architecture metadata version/date.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this is a documentation-only current-state defect discovered before selecting the next development slice and can be corrected immediately. Reverting the correction would not change runtime behavior but would again misrepresent the authoritative architecture state.

### Final verification

Canonical architecture v38 now records the exact bounded P30 state: only the approved disabled local formula/configuration and three results exist; there is no automatic/default selection, schedule or downstream consumer, and all evidence remains non-executable. A focused architecture/governance suite passes 16 tests, the complete architecture suite passes 96 tests, and a regression assertion rejects the obsolete `real P29 row or schedule` phrase.

## BUG-20260811-001

### Title
Current P23-3A project/index/proposal summaries still claimed P29 validation data was absent

### Status
Fixed during PROPOSAL-031 proposal-only synchronization

### Severity
Low

### Area
Project State / documentation index / P29 proposal current-status summary

### Reproduction and cause
After completed PROPOSAL-030, read the P23-3A capability rows in `docs/project/PROJECT_STATE.md`, the P29 entry in `docs/INDEX.md`, and the opening current-status paragraph in PROPOSAL-029. Several statements still say there is no real P29 version/result or that all six P29 tables are empty. Those statements were true immediately after P29 implementation but were not converted to historical wording after the approved P30 disabled validation appended one formula, one AAPL configuration and three results.

### Expected behavior and planned fix
Preserve historical migration/implementation statements such as “began empty,” but update current summaries to name the bounded P30 disabled validation evidence and continue to state that no default, production parameter or P23-4 consumer exists. Add governance regression coverage across Project State, INDEX and the P29 proposal.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this is a documentation-only current-state synchronization defect that can be repaired before P31 proposal creation. Runtime, database and trading safety are unaffected.

### Final verification
Project State, Documentation Index and the P29 proposal now distinguish the historical zero-backfill implementation checkpoint from the current bounded P30 evidence: one disabled AAPL test configuration and three linear results, with no default or downstream consumer. The focused governance/boundary suite passes **17 tests** and the complete architecture suite passes **97 tests**.

## BUG-20260811-002

### Title
P31 Compass synchronization briefly transcribed the protected P28 validation Result ID incorrectly

### Status
Fixed during PROPOSAL-031 proposal-only synchronization

### Severity
Low

### Area
Compass verification metadata / immutable evidence identity

### Reproduction and cause
Inspect `last_verified_commit_or_working_tree_state` immediately after the first Compass-v83 proposal-only patch. The P28 validation Result ID was accidentally changed from `4447da24-2d25-5fbd-a7fd-fb0c3e501249` to a mixed identifier while editing the long metadata line. This was a local documentation transcription error; no runtime record, database row or source code changed.

### Expected behavior and planned fix
Restore the exact already-verified P28 Result ID and retain the existing governance regression assertion that protects it. Run the focused governance and complete architecture suites before handoff.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because it was detected immediately in the uncommitted proposal-only working tree and can be corrected before handoff. Reverting only the incorrect Compass patch would also restore the ID but would lose the truthful P31 proposal-only status.

### Final verification
Compass v83 again records the exact protected Result ID `4447da24-2d25-5fbd-a7fd-fb0c3e501249`. The existing exact-ID assertion was retained unchanged; the focused governance/boundary suite passes **17 tests** and the complete architecture suite passes **97 tests**.

## BUG-20260811-003

### Title
PROPOSAL-031 mixed failed operation states into the accepted Decision Result contract

### Status
Fixed during PROPOSAL-031 contract self-review

### Severity
Low

### Area
P31 proposed Decision contracts / persistence semantics

### Reproduction and cause
Read the proposed `decision.cycle_target_adjustment_result@1` status list. It includes `INVALID_INPUT` and `FAILED`, while the immediately following missing-value rule says failed attempts have no accepted result. The intended four-table design separates durable operation attempts from accepted results, but the first draft mixed those two lifecycles in one status list.

### Expected behavior and planned fix
Make the operation-attempt contract explicitly own `PENDING`, `RUNNING`, `COMPLETED`, `INVALID_INPUT` and `FAILED`. Restrict accepted Decision Result status to `INTENT_CREATED` or `HOLD`; failed/invalid operations preserve attempt and Run messages but create no accepted result, intent or source link. Add exact governance assertions before handoff.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this is an unapproved proposal-only contract inconsistency detected before implementation. No runtime code or data exists. Reverting the correction would reintroduce ambiguity into a future persistence implementation.

### Final verification
PROPOSAL-031 now defines a separate attempt contract with `PENDING/RUNNING/COMPLETED/INVALID_INPUT/FAILED`, while accepted Decision Results allow only `INTENT_CREATED/HOLD`; invalid and failed attempts create no result, intent or source link. Exact governance assertions protect this separation. The focused governance/boundary suite passes **17 tests** and the complete architecture suite passes **97 tests**.

## BUG-20260811-004

### Title
P31 conflict failure could reject its own durable operation evidence when the preview Run already had a valid P29 parent

### Status
Fixed during PROPOSAL-031 implementation

### Severity
Medium

### Area
P31 preview orchestration / SQLite Run-context validation

### Reproduction and cause
Submit a second P31 command with an existing operation ID but a different fingerprint while both commands name a valid P29 source Result and Run. The coordinator can legitimately create the new failed preview Run with that P29 Run as its parent before detecting the operation conflict. The first store draft required every unresolved failure to have no parent, so it would reject the failed operation evidence instead of durably recording the conflict.

### Expected behavior and planned fix
For an unresolved failed operation, accept either no parent (when the source could not be resolved) or the explicitly requested P29 source Run (when source identity was already sufficient to establish lineage). Continue to require an exact P29 parent for every completed operation and never create an accepted result, intent or source link for the failure. Add a regression test covering the conflicting command and its persisted failed attempt.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this defect existed only in the uncommitted P31 implementation and was corrected before P31 handoff. Rollback is removal of the uncommitted P31 slice; no existing Phase-5D/P29 behavior or central-database row is affected.

### Final verification
The Store now accepts a failed P31 Run with either no parent when source resolution failed or the exact requested P29 parent when that lineage was already established; completed operations still require the exact resolved parent. The conflict integration test proves the failed attempt persists with no accepted result/intent/source link, and the focused P31 suite passes.

## BUG-20260811-005

### Title
P31 source-integrity validation compared equivalent P29 timestamps as different text formats

### Status
Fixed during PROPOSAL-031 implementation

### Severity
Medium

### Area
P31 SQLite immutable-source validation

### Reproduction and cause
Create a valid P29 result whose UTC timestamps have zero microseconds, then submit it to P31. P29 persists Python `datetime.isoformat()` text such as `2026-08-10T20:00:00+00:00`; the first P31 validator formatted the same instant with forced microseconds, such as `2026-08-10T20:00:00.000000+00:00`. A raw string comparison therefore rejected valid immutable evidence and also prevented the derived failed attempt from being stored.

### Expected behavior and planned fix
Compare persisted timestamps as timezone-aware UTC instants while continuing exact text comparison for identifiers, versions, fingerprints and Decimal evidence. Add the completed-chain/reload integration regression that exposed the defect; no tolerance, rounding or financial arithmetic changes are permitted.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this affected only the uncommitted P31 implementation and was fixed before handoff. No central P31 runtime row has been created.

### Final verification
P31 source validation now parses both persisted values as aware datetimes, normalizes them to UTC and compares instants; all identifiers, versions, fingerprints and Decimal evidence remain exact. The complete temporary P28→P29→P31 chain, restart reload and deterministic replay tests pass, while the migrated central P31 tables remain empty.

## BUG-20260811-006

### Title
Run History dependency boundary allowlist omitted the approved P31 Decision engine and replay service

### Status
Fixed during PROPOSAL-031 final architecture verification

### Severity
Low

### Area
Architecture regression tests / Decision dependency boundary

### Reproduction and cause
Run the complete architecture suite after adding P31. `test_only_approved_factor_service_depends_on_neutral_run_history` still listed only the two Phase 5D Decision files permitted to import the neutral `SoftwareIdentity`. P31's engine needs the same immutable software identity and its read-only replay reconstructs that exact identity, so the stale allowlist rejected an approved dependency even though neither file imports a repository, SQLite or concrete Run implementation.

### Fix and verification
Add only `cycle_target_adjustment_engine.py`, `cycle_target_adjustment_service.py` and `cycle_target_adjustment_replay.py` to the explicit Decision allowlist; the first rerun exposed that the service also receives the same immutable software identity, and the allowlist was completed accordingly. All other Decision files remain forbidden from importing Run History, and P31-specific architecture tests continue to forbid concrete Target Position, Persistence, Risk and Execution dependencies. The complete architecture suite is rerun after this correction.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this was an uncommitted test-maintenance defect corrected before handoff. Rollback would restore a false negative without changing runtime behavior.

### Final verification
The complete architecture suite passes **102 tests** after the exact three-file allowlist correction. The complete repository suite passes **613 tests** with one pre-existing third-party deprecation warning.

## BUG-20260811-007

### Title
Main Algorithm Control composition passed P31 dependencies to the wrong owner page

### Status
Fixed during PROPOSAL-031 complete-suite verification

### Severity
High

### Area
Algorithm Control application composition / full-panel startup

### Reproduction and cause
Construct `AlgorithmControlPanel` without optional research services, as the existing main-controller tests do. The first P31 integration patch passed `cycle_target_adjustment_preview`, its query service and P29 queries into `StandardizedPriceStatePanel`, which does not own or accept them, instead of `DecisionManagementPanel`. Startup raised `TypeError` before the control center could render. The isolated P31 panel test did not exercise full main-panel construction.

### Fix and verification
Remove all P31 arguments from the Standardized State constructor and pass them only to the existing Decision owner page, whose public constructor already declares them. The three pre-existing full-panel tests are retained as regression coverage, the focused GUI suite and complete repository suite are rerun, and no business logic is moved into GUI composition.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the defect existed only in the uncommitted P31 working tree and was fixed before handoff. Reverting the P31 GUI composition is the local rollback; no database or financial semantics are involved.

### Final verification
The five focused main-panel/P31 GUI tests pass, and the complete repository rerun passes **613 tests** with one pre-existing third-party deprecation warning. Full Algorithm Control construction with absent optional P31 services now succeeds, while the P31 inspector remains owned by the Decision page.

## BUG-20260811-008

### Title
P29 governance assertion still required the pre-P31 no-consumer sentence

### Status
Fixed during PROPOSAL-031 final documentation verification

### Severity
Low

### Area
Governance regression tests / Project State

### Reproduction and cause
After synchronizing Project State to say P31 is the only approved explicit disabled P29 Decision consumer, rerun the focused governance suite. The older P29 assertion still required the exact pre-P31 sentence that P30 had three results and no consumer, producing a false failure even though the new statement is more restrictive and truthful.

### Fix and verification
Require Project State to preserve the P30 one-configuration/three-result evidence and explicitly name P31 as the only disabled Decision consumer, with no default or Risk consumer. The focused governance suite is rerun; runtime code and financial semantics are unchanged.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this uncommitted test-maintenance defect was fixed before handoff. Rollback would restore a false pre-P31 current-state requirement.

### Final verification
The focused governance/P31/Target boundary suite passes **22 tests** after the assertion is updated. `git diff --check` remains clean apart from informational line-ending notices.

## BUG-20260811-009

### Title
P33 completion persistence initially did not revalidate the exact P29 configuration fingerprint

### Status
Fixed during PROPOSAL-033 implementation verification

### Severity
High

### Area
P23-4B Risk persistence / exact P31→P29 provenance validation

### Reproduction and cause
Create an otherwise valid P31 source, then alter the referenced `cycle_target_asset_configurations.constraint_fingerprint` before a P33 review is committed. The first uncommitted P33 Store revision revalidated the P31 intent/result/source link and P29 result but did not compare the immutable P29 configuration row itself. A tampered configuration could therefore have retained a matching copied fingerprint in P31 evidence and reached durable P33 result insertion without direct configuration-row proof.

### Fix and verification
`SQLiteCycleTargetRiskStore` now requires the exact P29 configuration row and compares its version, formula identity/version, symbol, constraint fingerprint, schema and non-execution flags inside the same `BEGIN IMMEDIATE` transaction as P33 persistence. A regression test tampers only that configuration fingerprint and verifies fail-closed `FAILED` evidence with no accepted P33 result. The complete suite is rerun after this fix.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this defect existed only in the uncommitted P33 implementation and was fixed before handoff. Reverting the validation would weaken exact provenance and is not an acceptable operational rollback; the safe rollback is to disable P33 composition while retaining Schema-v20 evidence.

### Final verification

The affected P33/Phase-6A/architecture set passes **16 tests**, and the final complete repository rerun passes **627 tests** with one pre-existing third-party deprecation warning. Python compilation and diff hygiene also pass.

## BUG-20260812-010

### Title
Governance regression tests fixed the Roadmap at the pre-P35 heading

### Status
Fixed during PROPOSAL-035 proposal verification

### Severity
Low

### Area
Governance documentation integrity tests / Roadmap proposal progression

### Reproduction and cause
Create proposal-only PROPOSAL-035 and truthfully change the Roadmap next-direction heading from `PROPOSAL-034 complete; next slice not approved` to `PROPOSAL-035 proposed; user decision required`, then run `tests/architecture/test_governance_document_integrity.py`. Three assertions still required the old literal heading, so they rejected the new proposal state even though P35 remained explicitly unapproved and no runtime behavior changed.

### Fix and verification
Update the three historical progression assertions to require the new unapproved-P35 heading, and add a dedicated P35 governance test that proves proposal-only status, P35-D1–D10 presence, exact overlap warnings, no preview-as-trade counting, future logical-action/first-fill semantics, proposed-not-applied v21 migration, cross-document references and the explicit lack of implementation approval.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the stale assertion existed only against the uncommitted P35 documentation change and was corrected before handoff. Reverting P35 documentation should also revert the matching assertion update; no product or database rollback is involved.

### Final verification
The focused governance suite passes **16 tests**, including the new P35 proposal-only assertion. `git diff --check` passes with informational Windows LF→CRLF notices only. No runtime code or database behavior changed.

## BUG-20260812-011

### Title
Initial P35 SQLite inserts and GUI enum handling could fail before saving evidence

### Status
Fixed during PROPOSAL-035 implementation

### Severity
Medium

### Area
P23-4C1 Persistence / Algorithm Control GUI

### Reproduction and cause
Exercise the first uncommitted P35 Store and panel revisions. The initial SQL used placeholder counts that did not match the approved v21 column lists, and the first panel test double did not model Qt combo-box enum data consistently. A valid control/admission request could therefore fail in persistence or during GUI command construction instead of producing the required terminal evidence.

### Fix and verification
Align every INSERT placeholder/value count with the six v21 table contracts, deserialize Qt combo data through the typed enum contract, and cover completed/failed persistence plus both panels. Focused Store/GUI tests and the exhaustive repository shards pass.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because both defects existed only in the uncommitted implementation and are fixed with regression coverage. Safe rollback disables P35 composition while retaining any v21 audit evidence; reverting the fixes alone is unsafe.

## BUG-20260812-012

### Title
P35 GUI regenerated a different command after successful no-write preflight

### Status
Fixed during PROPOSAL-035 implementation

### Severity
High

### Area
P23-4C1 Algorithm Control GUI / exact preflight identity

### Reproduction and cause
Run a successful Trading Control or Asset Admission preflight and then press the write/review button. Both first panel revisions called `_command()` again, generating a new operation ID, request ID and timestamp; admission could also resolve a different effective control event. The visible preflight therefore did not prove the exact command submitted for persistence.

### Fix and verification
Cache the exact typed command accepted by preflight, invalidate it on every source/status/reason edit, and submit that same object once. GUI tests assert object identity across preflight→save/review, and architecture tests continue to prove the panels contain no business or SQL logic.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the defect was fixed before handoff. Reverting this change would violate the approved exact-preflight contract and is not a safe rollback.

## BUG-20260812-013

### Title
P35 first control event could be retroactively effective at client request time

### Status
Fixed during PROPOSAL-035 implementation

### Severity
High

### Area
P23-4C1 Asset State effective-time semantics

### Reproduction and cause
Construct a valid command whose aware `requested_at_utc` is earlier than the actual accepted operation time. The first service revision made an immediate freeze or first explicit status effective at the supplied request timestamp. A caller could therefore make a newly accepted control appear effective in historical queries, contrary to the approved no-backdating rule.

### Fix and verification
The coordinator now freezes exact calendar evidence at an injected accepted time; the service requires accepted time to be no earlier than the request, makes immediate/first events effective at accepted time, and delays only `FROZEN→ELIGIBLE` to the next XNYS open. Regression coverage proves an old request does not affect the symbol before acceptance.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md`; this uncommitted defect is fixed. Reverting would change financial safety meaning and is not an acceptable local rollback.

## BUG-20260812-014

### Title
P35 invalid control caught at rule two could not form a valid blocked result

### Status
Fixed during PROPOSAL-035 implementation

### Severity
High

### Area
P23-4C1 Risk result invariant

### Reproduction and cause
Evaluate an otherwise valid exact P33 source with a mismatched or invalid trading-control DTO. The engine correctly stopped on `ASSET_TRADING_CONTROL_AVAILABILITY`, but the first result invariant allowed `BLOCKED_INVALID_SOURCE` only after rule one. Result construction raised instead of returning durable fail-closed Risk evidence.

### Fix and verification
Permit `BLOCKED_INVALID_SOURCE` only at locked rule prefix length one or two, while retaining exact rule identity/order enforcement. Dedicated Risk tests cover invalid P33 at rule one, invalid control at rule two, missing control, frozen both directions and eligible manual review.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because the issue was fixed before handoff. The safe rollback is to disable P35, not weaken the invariant or bypass Risk.

## BUG-20260812-015

### Title
Missing P33 admission could reference a nonexistent parent Run and lose durable failure evidence

### Status
Fixed during PROPOSAL-035 implementation

### Severity
High

### Area
P23-4C1 Orchestration / Run History / Persistence

### Reproduction and cause
Request P35 review with nonexistent P33 Result/Run IDs. The first coordinator revision started the P35 Run with the requested nonexistent P33 Run as its database parent. The Run foreign key could fail before the approved invalid attempt was recorded.

### Fix and verification
Only a successfully resolved exact P33 source becomes the parent Run. Unresolved IDs remain immutable requested fields on a parentless failed P35 Run, and the Store validates that accepted operations have the exact P33 parent while failed operations do not claim one. Regression coverage proves the invalid attempt and failed Run survive reload with no accepted result.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md`; fixed before handoff. Reverting would break the durable-failure acceptance criterion.

## BUG-20260812-016

### Title
Failed-v21 migration test incorrectly expected the restored database to remain v21

### Status
Fixed during PROPOSAL-035 verification

### Severity
Low

### Area
Central SQLite migration regression test

### Reproduction and cause
Inject invalid v21 DDL while migrating a complete v20 fixture. The migration correctly restores the verified pre-migration database at v20, but the first new assertion expected `MAX(schema_migrations.version)=21`, falsely reporting the correct rollback as a failure.

### Fix and verification
Require restored version 20, absence of the v21 result table and `integrity_check=ok`. The corrected migration test passes along with additive v20→v21 backup/zero-backfill tests and active/backup read-only verification.

### Known Issues disposition and rollback
Not added to `KNOWN_ISSUES.md` because this was an uncommitted test expectation defect. It changed no runtime data or financial meaning.
## BUG-20260813-001

### Title
Published P35 feature commit was still described as an uncommitted working tree

### Status
Fixed during next-direction preflight

### Severity
Low

### Area
Project governance / checkpoint metadata

### Reproduction and cause

After commit `b147e60` was pushed to `origin/main`, `PROJECT_COMPASS.md` and `docs/proposals/README.md` still described CHECKPOINT-20260812-007 at `828f956` as the published baseline and P35 as an uncommitted working-tree implementation. The feature implementation record intentionally preceded publication, but no follow-up checkpoint metadata had yet replaced that transient wording.

### Resolution and regression evidence

Updated Compass metadata and narrative, Proposal status, Project State and append-only Version History to identify `b147e60` as the published P35 feature commit while preserving P23-4C2 and runtime-validation exclusions. Governance integrity tests and `git diff --check` are required before the correction is considered complete.

## BUG-20260813-002

### Title
Run History module migration summary stopped at Schema v19 after v20/v21 were implemented

### Status
Fixed during PROPOSAL-036 documentation synchronization

### Severity
Low

### Area
Run History module documentation

### Reproduction and cause

Read `docs/modules/run-history.md` after the published P35 implementation. Its Migration and rollback summary still called v1→v19 the current additive chain even though the same repository and Central Persistence documentation establish Schema v20 for P23-4B and v21 for P23-4C1. This was stale documentation; runtime migration code and active SQLite were already correct.

### Resolution and regression evidence

Updated the current chain to v1→v21 and named P23-4B v20 and P23-4C1 v21. Governance integrity and diff checks cover the synchronized documentation. No source code, Schema, database row, public contract or trading behavior changed.

### Known Issues disposition and rollback

Not added to `KNOWN_ISSUES.md` because the documentation defect was fixed in the same handoff. Rollback is a documentation-only revert, though it would reintroduce the stale version statement.

## BUG-20260814-001

### Title
P37 missing-source failures could not be persisted durably

### Status
Fixed during PROPOSAL-037 implementation

### Severity
Medium

### Area
P23-2B mathematical-cycle persistence and orchestration

### Reproduction and cause

Request promotion with an unknown exact P28 Result/Run identity. The coordinator correctly fails closed before changing mathematical-cycle state, but the first v22 operation-table design also declared foreign keys from the *requested* source IDs to accepted P28 rows. SQLite therefore rejected the failure-attempt insert itself, so the invalid request could not satisfy the approved requirement that failures remain searchable after restart.

### Resolution and regression evidence

Removed foreign keys only from the requested-source fields on `mathematical_cycle_state_operations`. Accepted source facts remain foreign-key constrained in snapshots, transition events and source links. Added a parentless durable source-failure path that records an `INVALID_INPUT`/`NO_EXECUTION` Run and failed operation without creating a definition, stream, cycle, snapshot, transition or source link. Repository integration tests verify restart reload, zero state mutation and exact Run linkage for an unknown P28 source.

### Known Issues disposition and rollback

Not added to `KNOWN_ISSUES.md` because the defect was found and fixed before P37 handoff and never affected the active database: all seven P37 tables remain empty. A normal code/schema-definition revert of the uncommitted P37 implementation is sufficient; do not restore or discard existing P36 evidence.

## BUG-20260814-002

### Title
P37 promotion source warning was absent from Run History messages

### Status
Confirmed during approved PROPOSAL-038 runtime validation; local fix in progress

### Severity
Medium

### Area
P23-2B mathematical-cycle application service / Run History observability

### Reproduction and cause

Promote the exact persisted AAPL P28 Result/Run containing the approved `LOCAL_ONLY` warning. The P37 operation correctly stores the warning and its stage/Run correctly finish `COMPLETED_WITH_WARNINGS`, but `MathematicalCycleStateService.promote` did not call the public Run History message API. The resulting Run therefore reported `warning_count=0`, and the approved P38 `algorithm_run_messages +1` delta did not hold. P28 already records the same class of warning through the public API; the omission is local to P37.

### Required resolution and safety boundary

Record every accepted P37 source warning as a stage-scoped Run warning before Run completion, add a regression assertion, and append exactly one matching warning to the already accepted P38 promotion Run through the public Run History service. Do not recreate the definition or stream, alter mathematical snapshots, change direction, select a default stream, or invoke any downstream/trading capability.

### Resolution update

Status: Fixed during PROPOSAL-038 validation.

`MathematicalCycleStateService.promote` now records each accepted source warning through `AlgorithmRunService.record_message` with code `QT-MATHEMATICAL-CYCLE-SOURCE-WARNING` before completing the Run. The regression fixture supplies the local-only warning and proves operation warning, Run status, one stage-scoped message and deterministic retry agree. The already accepted P38 promotion Run `f1981c65-1fe7-45af-abab-9c1256e6cbec` received exactly one matching public Run message `79f7330b-ca55-54dd-88ef-419946dbd430`; exact database deltas then matched the approved P38 table and no mathematical-state row changed.

Focused P37/GUI/architecture verification passed 128 tests, and the complete repository passed 658 tests. Not added to `KNOWN_ISSUES.md` because the defect was fixed before handoff. Rollback is a normal code revert only if warning observability must be removed; preserve the accepted append-only Run message and all P38 state evidence.

## BUG-20260814-003

### Title
Canonical proposal index omitted existing PROPOSAL-006

### Status
Fixed during PROPOSAL-039 proposal-record audit

### Severity
Low

### Area
Governance documentation / proposal discoverability

### Reproduction and cause

Enumerate `docs/proposals/PROPOSAL-*.md` and compare the continuous proposal IDs with `docs/proposals/README.md`. All 38 pre-P39 proposal files `PROPOSAL-001` through `PROPOSAL-038` exist with no duplicate or missing file ID, but the canonical proposal index contains no `PROPOSAL-006` token or link. The historical-backtesting proposal itself is intact; only the index entry was omitted as later proposal summaries accumulated.

### Resolution and regression evidence

Added the existing `PROPOSAL-006-historical-backtesting.md` to the canonical proposal index without changing its content or status. The governance integrity test now enumerates proposal filenames, requires one unique file for every ID from 001 through the current maximum, and requires every discovered proposal ID to appear in the canonical index. The same audit confirmed 148 unique pre-edit Edit Log IDs and 122 unique pre-edit Bug Log IDs.

Not added to `KNOWN_ISSUES.md` because the omission was confirmed and repaired in the same task. Rollback is a documentation-only revert, although doing so would restore the discoverability defect.

## BUG-20260815-001

### Title
Target Position parent GUI imported Asset State directly for a P39 type annotation

### Status
Fixed during PROPOSAL-039 implementation

### Severity
Low

### Area
Algorithm Control GUI dependency boundary

### Reproduction and cause

Run the architecture suite after wiring the P39 sibling inspector. `test_target_position_gui_uses_typed_services_without_sql_or_financial_consumers` reported that `target_position_panel.py` imported `quant_trading.asset_state`. The import supplied only the `MathematicalCycleStateQueryService` annotation passed through to the dedicated P39 child panel; no Asset State calculation or mutation was present. Even so, it broadened the established parent Target Position GUI dependency and made the generic page appear to consume Asset State directly.

### Resolution and regression evidence

Removed the parent-panel Asset State import and kept its pass-through dependency opaque. The dedicated `mathematical_cycle_target_link_panel.py` continues to depend on the public read-only P37 query protocol, while composition supplies the implementation. All 126 architecture/governance tests and all 668 repository tests pass; no formula, source selection, GUI behavior, database row or trading meaning changed.

Not added to `KNOWN_ISSUES.md` because the boundary defect was confirmed and fixed in the same implementation. Rollback would reintroduce the architecture violation and is not recommended.
