# Runtime Artifacts

本目录用于程序运行产生的日志、缓存、临时状态和生成报告，不存放源代码。除本说明外，内容默认由 `.gitignore` 排除。

运行日志不得与版本化的 `logs/EDIT_LOG.md` 混淆，且不得包含密钥、真实账户信息或其他敏感数据。

股票历史数据模块使用：

- `runtime/data/market_history.sqlite3`：Bar、Coverage 和 Fetch History。
- `runtime/logs/app.log`：应用操作与状态的轮转日志。
- `runtime/logs/error.log`：包含 Error Code 和技术堆栈的警告/错误轮转日志。

两个日志文件均使用 UTF-8，单文件上限 5 MB，并保留 5 份历史文件。旧版 `runtime/logs/market_history.log` 如已存在仅作为历史文件保留，当前程序不再写入。

当前唯一运行日志属于 `market_data` 范畴，不包含账户或订单执行。未来若 execution 获批，必须使用可明确区分的 `paper_execution` 与 `live_execution` 日志类别，并在每条账户/订单记录中标注 `environment=paper` 或 `environment=live`。Paper 与 Live 日志不得混用；当前不得产生 `live_execution` 日志。

任何运行日志都不得记录 API Secret、完整授权头、完整账户敏感信息或不必要的个人信息。

删除数据库会清空本地缓存，必须先关闭程序并确认备份；不得把数据库或运行日志加入版本控制。
