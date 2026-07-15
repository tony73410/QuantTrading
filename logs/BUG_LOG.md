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
