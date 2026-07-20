# Known Issues

记录当前仍影响用户、需要持续关注的问题摘要。完整的发现、调查、修复与延期历史统一写入 `logs/BUG_LOG.md`；本文件不替代Bug Log。新增条目应包含影响、证据、临时措施、相关Bug ID和后续决策需求；不要把计划功能伪装成缺陷。

## Open

- **KI-0004 — Physical-display visual QA pending.** PySide6/QWebEngineView 已在 Qt offscreen 模式完成启动和动态重绘烟雾测试；无界面环境产生 GPU 上下文提示。仍需用户在实际桌面显示环境确认字体、缩放和窗口布局观感。
- **KI-0005 — Transitive WebSocket deprecation warning.** pytest 导入 `alpaca-py` 时，其传递依赖 `websockets` 报告 legacy 命名空间弃用警告。本模块没有实现或调用 WebSocket；等待上游依赖更新。
- **KI-0006 — Active synchronous request can delay window close.** alpaca-py 的同步历史请求没有当前模块可用的安全取消接口；窗口关闭会停止计时器并清除未开始任务，但会等待正在执行的请求安全结束。强杀线程可能破坏 SDK/SQLite 状态，因此本次未伪造取消。详见 `BUG-20260713-005`。
- **KI-0007 — Early-close sessions are not calendar-aware.** 分钟和小时数据按 `America/New_York` 的 09:30–16:00 固定窗口过滤，夏令时转换正确，但项目当前没有交易所日历依赖，无法识别感恩节后等提前收盘日。如果 Alpaca 在此类日期返回 13:00 后盘后 Bar，它们可能仍被显示。临时措施是查看此类日期时留意成交时段；若需精确处理，应由用户批准交易日历来源或依赖后再实施。详见`BUG-20260715-010`。
- **KI-0008 — IEX实际历史可能短于请求区间。** 2026-07-15批量请求110支热门股票近10年Raw/IEX日、周、月行情时，330个组合都成功返回并写入，但多数成熟股票的日线实际从2020-07-27左右开始，未覆盖完整10年。当前Coverage表示“该请求区间已成功向Provider查询”，不等于该区间每天都有实际Bar；这会让请求覆盖与真实Bar覆盖看起来不一致。临时措施是以数据库中实际最早/最晚Bar为准。若必须获得2020年前数据，应先单独验证SIP权限或批准其他数据源；不要静默混用Feed。详见 `BUG-20260715-005`。

## Resolved

- **KI-0013 — Canonical governance references were ambiguous.** Resolved 2026-07-16: Portfolio Accounting retains `INTENT-017`, Main Launcher is uniquely `INTENT-019`, Run History is `INTENT-020`, architecture invariants are monotonic through 34, and Compass verification metadata reflects the current Phase 1 worktree and 312-test evidence. Architecture regression tests enforce unique Intent IDs and invariant numbering. See `BUG-20260716-010`.

- **KI-0012 — 请求区间内的未来Market Bar可通过验证。** Resolved 2026-07-15：Market Data合同现在以验证时UTC为上界拒绝未来Bar，不改写或排序输入。详见`BUG-20260715-009`。
- **KI-0011 — Decision“添加条件”按钮可能把Qt checked状态当作业务对象。** Resolved 2026-07-15：新增显式无参signal adapter，防止bool进入DecisionCondition slot。详见`BUG-20260715-008`。

- **KI-0010 — 刷新后的状态内容把历史数据窗口向下撑出屏幕。** Resolved 2026-07-15：控制面板与状态区域改为在可见高度不足时自身纵向滚动，刷新产生的换行内容不再抬高主窗口最低高度。该问题不同于已修复的Plotly WebView内部溢出。详见 `BUG-20260715-007`。

- **KI-0009 — Factor版本视觉高亮与内部选择不同步。** Resolved 2026-07-15：清空表单时同步清除current row，并在真实选择变化时重新加载版本；回归测试确认归档版本可重新选择并恢复为可用。详见 `BUG-20260715-006`。

- **KI-0001 — Git repository not initialized.** Resolved 2026-07-13：已按用户授权初始化本地仓库，默认分支为 `main`，并配置项目级提交身份与 `origin`。首次提交在同一任务中创建。
- **KI-0002 — Technology stack undecided.** Resolved 2026-07-13：用户明确授权股票历史数据模块采用 Python、PySide6/QWebEngineView、Plotly、`alpaca-py`、pandas、SQLite 和 pytest。其他未来模块仍由实际需求决定。
- **KI-0003 — Alpaca Market Data path not credential-verified.** Resolved 2026-07-13：只读诊断使用现有环境变量成功请求最近一周 AAPL IEX 日线并返回 5 行；凭据值未输出，未访问账户或订单。常规自动测试仍只使用 Fake/Mock。
