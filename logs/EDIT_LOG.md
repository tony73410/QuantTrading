# Edit Log

本文件是只追加的开发事实记录。不得删除或改写旧条目；如需纠正，新增更正条目。

## EDIT-20260713-001

### Date

2026-07-13 11:05:19 -07:00

### Request

检查当前仓库，并在不选择技术栈、不实现交易业务的前提下建立长期可维护、可追踪、可测试、可回滚的项目治理与目录基础。

### Scope

包含仓库级规则、项目入口、状态/路线图/术语、架构与依赖规则、ADR 机制、模块文档规范、开发/测试/文档标准、目录职责、忽略规则和首条编辑记录。明确不包含 Git 初始化、依赖安装、技术选型、正式模块、交易逻辑、外部服务和实盘连接。

### Pre-change state

工作目录为空；没有文件、现有技术栈或未提交文件可合并。`git status --short --branch` 返回当前目录不是 Git 仓库。

### Files changed

- Added:
  - `.gitignore`
  - `AGENTS.md`
  - `README.md`
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `docs/INDEX.md`
  - `docs/project/PROJECT_STATE.md`
  - `docs/project/ROADMAP.md`
  - `docs/project/GLOSSARY.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/architecture/DEPENDENCY_RULES.md`
  - `docs/decisions/README.md`
  - `docs/decisions/ADR-0001-project-governance.md`
  - `docs/modules/README.md`
  - `docs/development/WORKFLOW.md`
  - `docs/development/CODING_STANDARDS.md`
  - `docs/development/TESTING_STANDARDS.md`
  - `docs/development/DOCUMENTATION_STANDARDS.md`
  - `logs/EDIT_LOG.md`
  - `config/README.md`
  - `src/README.md`
  - `tests/README.md`
  - `scripts/README.md`
  - `runtime/README.md`
  - `archive/README.md`
- Modified: None.
- Deleted: None.
- Renamed: None.

### Implementation

建立了用户授权的语言无关目录骨架，并在每个文件中写入实际用途、权限边界或维护方法。根规则将细节路由到 `docs/`；项目状态明确当前无模块、接口和交易能力；ADR-0001 记录为何不提前选择技术或业务架构；`.gitignore` 排除密钥、常见临时产物及 `runtime/` 内容但保留说明文件。

### Reason

在业务开发前固定最小治理边界，可以让后续需求以小步、可审查方式实现，同时保留用户对交易语义和技术选择的决定权。

### Behavior impact

无程序行为变化；仓库中没有交易业务代码。

### Interface impact

无公共接口，也没有接口变化。

### Dependency impact

未添加、移除或升级任何依赖。

### Configuration or data impact

未定义配置格式或持久化数据结构，未执行迁移，未添加敏感信息。只建立 `config/` 与 `runtime/` 的职责和忽略规则。

### Validation

- 检查根目录、隐藏项和递归文件清单。
- 执行 `git status --short --branch` 确认 Git 状态。
- 对照授权结构检查 26 个预期文件；写入本条记录前，25 个基础文件存在且只有本日志待创建。
- 检查零字节文件和 `src/` 内容。
- 写入日志后执行最终结构、内容边界、引用目标及敏感信息模式检查。

### Results

初步检查通过：25 个先行文件均非空，`src/` 仅含 `README.md`，未发现业务实现。Git 检查确认目录未初始化为仓库。最终检查结果记录于本条完成后的任务报告；若发现问题，将通过新日志条目更正，不回写本记录。

### Documentation

创建了本记录“Files changed”中列出的全部治理和目录说明文档。

### Rollback

当前没有 Git 历史可用于恢复。若确认这些文件之后未承载新工作，可删除本条列出的新增文件和由此形成的空目录；执行前应再次检查用户修改并获得适用批准。更安全的后续方式是在用户决定初始化 Git 后，通过提交建立可恢复基线。

### Open issues

- 当前目录未初始化 Git，无法检查提交历史、分支或 Git diff。
- 技术栈、测试工具和所有交易业务能力均待用户决定。

### Approval

本次创建的完整基础结构已由用户在当前请求中明确授权，无需重复审批。未执行任何超出授权范围的事项。

## EDIT-20260713-002

### Date

2026-07-13 11:11:45 -07:00

### Request

将“用户背景与需求解释协议”纳入长期项目治理：理解用户真正目标，纠正含混术语，补齐普通工程细节，按风险等级处理歧义，并使用通俗语言汇报。

### Scope

新增一份权威的需求解释规范，并更新仓库入口、标准工作流、项目状态和版本级治理记录。明确不包含业务代码、交易规则、技术栈、依赖、接口、配置、数据结构或实盘能力变更。

### Pre-change state

仓库已有范围控制、审批和交易安全规则，但没有集中定义如何区分用户目标与用户建议的方法，也没有 Level A–D 的需求歧义分级、概念纠错模板或通俗汇报要求。当前目录仍未初始化为有效 Git 仓库。

### Files changed

- Added:
  - `docs/development/REQUIREMENT_INTERPRETATION.md`
- Modified:
  - `AGENTS.md`
  - `CHANGELOG.md`
  - `docs/INDEX.md`
  - `docs/development/WORKFLOW.md`
  - `docs/project/PROJECT_STATE.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

建立需求解释权威文档，定义 User goal、User-proposed method、Technical interpretation、Trading interpretation 和 Recommended implementation；规定精确术语、工程自主判断、最小假设原则、Level A–D 处理方式、概念纠错模板、禁止隐藏金融建议、实施前重述、假设持久记录和通俗汇报。`AGENTS.md` 只保留强制摘要并指向细则，工作流和文档索引增加入口。

### Reason

采用的专业解释为 Level A：用户提供的是长期治理协议，而非某项交易功能需求。集中维护权威细则可避免规则散落或在 `AGENTS.md` 中无限重复，同时确保未来任务在实现前澄清真实目标和高风险语义。

### Behavior impact

没有程序或交易行为变化。开发协作行为发生变化：未来需求必须按风险解释、记录重要假设，并以用户可理解的语言报告。

### Interface impact

无公共程序接口变化。

### Dependency impact

未添加、移除或升级依赖。

### Configuration or data impact

无配置格式、持久化数据结构或迁移影响。

### Validation

- 读取现有 `AGENTS.md`、工作流、编码/文档标准、项目状态、文档索引和最近编辑日志。
- 执行 `git status --short --branch` 检查版本状态。
- 检查新协议的章节、五类解释字段、Level A–D、概念纠错字段和实施前重述字段。
- 检查 `AGENTS.md`、文档索引和工作流是否引用权威协议。
- 检查 Markdown 链接、空文件及 `src/` 中是否出现业务源码。

### Results

第一次内容验证脚本因 PowerShell 变量后紧跟冒号的插值语法错误而未执行；修正脚本后检查通过。20 个必需协议字段无缺失，三个要求的入口引用均存在，Markdown 断链为 0，空项目文件为 0，`src/` 仍只有说明文件。`git status` 仍报告当前目录不是有效 Git 仓库，因此无法执行 Git diff。

### Documentation

新增需求解释协议，并同步根规则、文档索引、开发工作流、项目状态和 CHANGELOG。

### Rollback

由于没有 Git 历史，回滚应手动移除新增协议，并撤销本条列出的其他文档增量；不得删除或重写本日志条目，应追加新的回滚记录。操作前必须确认没有后续内容依赖该协议。

### Open issues

- 当前目录未初始化为有效 Git 仓库，无法提供 Git diff 或提交级回滚。
- 本协议只建立解释规则，尚未产生可由程序测试的业务行为。

### Approval

用户在当前请求中明确提供整套长期协议。将其合并到既有治理文档属于小范围、非破坏性文档修改，不触发额外审批事项。

## EDIT-20260713-003

### Date

2026-07-13 11:42:34 -07:00

### Request

初始化 Git，使用 `main` 分支，创建首次提交；将作者配置为仅当前项目生效的 `Tony Wang <wangyoutian@berkeley.edu>`，并连接远程仓库 `tony73410/QuantTrading`。

### Scope

包含本地 Git 初始化、项目级提交身份、`origin` 配置、首次治理基线提交以及相关项目状态同步。明确不包含 fetch、pull、push、远程内容修改、分支合并或历史改写。

### Pre-change state

项目已有 27 个治理和说明文件，但 `.git` 只是空的环境占位目录，`git status` 返回不是有效 Git 仓库；所有项目文件均未被版本控制跟踪。

### Files changed

- Added:
  - `.git/` repository metadata（不作为项目内容提交）。
- Modified:
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `docs/project/PROJECT_STATE.md`
  - `docs/project/ROADMAP.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

初始化本地 Git 仓库并将默认分支设为 `main`；在 `.git/config` 中设置仅本项目生效的作者名称和邮箱；添加 HTTPS 远程 `origin`：`https://github.com/tony73410/QuantTrading.git`。同步当前项目状态，将 Git 未初始化问题标为已解决，并准备把全部治理文件创建为首次基线提交。

### Reason

用户需要可追踪和可回滚的本地版本基线，并明确提供了分支、提交身份、身份范围和远程仓库信息。项目级身份不会改变电脑上其他仓库的 Git 配置。

### Behavior impact

无程序或交易行为变化。开发过程现在可以记录提交、比较差异和回滚已提交内容。

### Interface impact

无公共程序接口变化。

### Dependency impact

未添加、移除或升级程序依赖。Git 是版本控制工具，不是运行依赖。

### Configuration or data impact

新增本地 `.git` 元数据和项目级 Git 配置；未修改应用配置、数据格式或持久化数据。

### Validation

- 初始化前读取治理规则、工作流、项目状态和最近编辑记录，并检查空 `.git` 占位目录。
- 检查当前分支、项目级 `user.name`、项目级 `user.email`、`origin` URL 和 Git 状态。
- 检查项目文件数量、空文件、`src/` 内容和常见凭据模式。
- 本条写入后创建首次提交，并在最终报告前检查提交作者、提交内容和工作区状态。

### Results

首次普通权限初始化因受保护的 `.git` 目录拒绝写入而失败，没有形成有效仓库或部分 Git 配置；获得写入授权后重新执行成功。验证得到分支 `main`、名称 `Tony Wang`、邮箱 `wangyoutian@berkeley.edu`、正确的 `origin`；27 个项目文件均非空，`src/` 无业务源码，常见凭据模式命中为 0。首次提交结果将在本条写入后验证并在最终报告中说明。

### Documentation

更新 CHANGELOG、已知问题、路线图、项目状态和本编辑日志，以反映 Git 已启用。

### Rollback

文档变化应通过后续提交回退，并追加新的编辑日志。可以单独移除 `origin` 或清除本项目身份配置；删除 `.git` 会永久移除所有本地提交历史，属于破坏性操作，未经明确批准不得执行。

### Open issues

- 尚未验证远程仓库内容，也未 fetch 或 push；远程是否为空不作假设。
- 技术栈和交易业务能力仍未决定。

### Approval

用户明确授权初始化 Git、创建首次提交、设置项目级身份并提供远程仓库地址。未执行未授权的 push、pull 或历史修改。

## EDIT-20260713-004

### Date

2026-07-13 11:48:05 -07:00

### Request

将内容上传到 GitHub 仓库 `tony73410/QuantTrading`。

### Scope

将已经验证的项目治理基线发布到远程 `origin`，而不是创建无用途的随机文件。包含只读远程检查、本条编辑记录提交、普通首次 push 和上游分支配置；不包含强制推送、远程历史覆盖、业务代码或交易功能。

### Pre-change state

本地 `main` 工作区干净，包含首次治理基线提交 `9831308`；`origin` 已配置，但 `main` 没有上游分支，且此前未执行 fetch、pull 或 push。

### Files changed

- Added: None.
- Modified:
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

执行只读 `git ls-remote --heads origin` 检查远程分支；远程没有返回任何 heads，因此无需合并，也不存在需要覆盖的已知远程分支。记录本次发布操作后，准备以非强制方式推送本地 `main` 并设置 `origin/main` 为上游。

### Reason

用户的目标是让远程仓库拥有项目内容。上传已有且有实际用途的治理基线，比创建随意占位文件更符合目标，并保持仓库整洁和可追踪。

### Behavior impact

无程序或交易行为变化。版本控制内容将从仅本地状态变为可在指定 GitHub 仓库访问。

### Interface impact

无公共程序接口变化。

### Dependency impact

无依赖变化。

### Configuration or data impact

无应用配置或数据格式变化。成功推送后，本地 `main` 将跟踪 `origin/main`。

### Validation

- 检查本地工作区、当前分支、提交历史、远程 URL 和上游状态。
- 运行 `git ls-remote --heads origin`，确认远程没有现有分支。
- 提交本记录后运行非强制首次 push。
- push 后检查本地工作区、上游关系、本地/远程提交一致性。

### Results

推送前检查通过：本地工作区干净，分支为 `main`，远程 heads 为空。最终 push 和远程一致性结果将在本条写入后的任务验证及最终报告中说明。

### Documentation

仅追加本编辑记录；项目功能和架构文档无需变化。

### Rollback

本记录不得删除或重写。若未来需要撤销已发布内容，应先确认远程使用情况，再通过新的提交或经明确批准的远程操作处理；不得擅自 force push 或删除远程分支。

### Open issues

- 推送前尚未验证 GitHub 的网页展示；以 push 后的远程引用检查为准。
- 技术栈和交易业务能力仍未决定。

### Approval

用户明确要求向该远程仓库上传内容，构成对本次普通非强制 push 的授权。未授权且不会执行远程历史覆盖。

## EDIT-20260713-005

### Date

2026-07-13 12:41:07 -07:00

### Request

实现独立的股票历史数据控制面板：从 Alpaca Market Data 获取历史 Bar，使用 SQLite 本地优先和增量缓存，通过 PySide6/QWebEngineView + Plotly 提供可交互桌面 GUI，并完整测试和更新文档。

### Scope

包含 Python 项目配置、明确领域模型、Provider/Store Protocol、SQLite schema/事务/upsert/Coverage/Fetch History、Alpaca Provider 分页与有限重试、Service 缺失区间和过期尾部刷新、Plotly 图表、PySide6 后台 Worker GUI、单元/集成测试、配置示例、ADR 和文档。明确不包含策略、指标策略、信号、回测、订单、券商交易、实盘、WebSocket、逐笔行情或投资建议。

### Pre-change state

Git 工作区干净并与 `origin/main` 同步。仓库只有治理文档，没有 Python 包、GUI、配置/数据库抽象或测试体系。机器可运行 Python 3.14.5；系统登记的 WindowsApps Python 3.11 无法启动。PySide6、Plotly、alpaca-py、pandas 和 pytest 均未安装，指定 Alpaca 环境变量均不存在。

### Files changed

- Added:
  - `.env.example`
  - `pyproject.toml`
  - `docs/decisions/ADR-0002-market-history-stack.md`
  - `docs/modules/market-history.md`
  - `src/quant_trading/__init__.py`
  - `src/quant_trading/market_history/__init__.py`
  - `src/quant_trading/market_history/__main__.py`
  - `src/quant_trading/market_history/app.py`
  - `src/quant_trading/market_history/config.py`
  - `src/quant_trading/market_history/controller.py`
  - `src/quant_trading/market_history/errors.py`
  - `src/quant_trading/market_history/interfaces.py`
  - `src/quant_trading/market_history/models.py`
  - `src/quant_trading/market_history/service.py`
  - `src/quant_trading/market_history/charts/__init__.py`
  - `src/quant_trading/market_history/charts/plotly_chart_builder.py`
  - `src/quant_trading/market_history/providers/__init__.py`
  - `src/quant_trading/market_history/providers/alpaca_provider.py`
  - `src/quant_trading/market_history/storage/__init__.py`
  - `src/quant_trading/market_history/storage/sqlite_store.py`
  - `src/quant_trading/market_history/ui/__init__.py`
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/conftest.py`
  - `tests/integration/market_history/test_local_first_flow.py`
  - `tests/unit/market_history/test_alpaca_provider.py`
  - `tests/unit/market_history/test_chart_builder.py`
  - `tests/unit/market_history/test_controller.py`
  - `tests/unit/market_history/test_models_and_config.py`
  - `tests/unit/market_history/test_service.py`
  - `tests/unit/market_history/test_sqlite_store.py`
- Modified:
  - `.gitignore`
  - `README.md`
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `config/README.md`
  - `docs/INDEX.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/decisions/README.md`
  - `docs/development/CODING_STANDARDS.md`
  - `docs/development/TESTING_STANDARDS.md`
  - `docs/modules/README.md`
  - `docs/project/GLOSSARY.md`
  - `docs/project/PROJECT_STATE.md`
  - `docs/project/ROADMAP.md`
  - `runtime/README.md`
  - `src/README.md`
  - `tests/README.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

建立 `quant_trading.market_history` 分层包。领域模型使用 UTC、Enum、dataclass、Protocol 和 Decimal；SQLite 用组合唯一键隔离 symbol/timeframe/adjustment/feed，Bar/Coverage/成功 Fetch 状态在同一事务提交。Service 计算多个 Coverage 间的真实缺口，普通 Load 本地优先，Refresh Latest/过期刷新只重取可配置尾部，Force Refresh 不先删除旧数据，失败时返回已有缓存。Alpaca Provider 只创建 Market Data Client，依赖官方 SDK `next_page_token` 分页，临时错误最多三次指数退避。GUI 使用单 Worker 线程池、Signal/Slot、debounce、自动更新计时器和 Plotly.react；缺少凭据时保持离线可启动。

### Reason

用户明确授权首个历史数据模块及 Python/PySide6/Plotly/alpaca-py/pandas/SQLite/pytest 技术组合。分层实现使 Provider、Store、缓存决策、图表和 GUI 可独立测试与替换，并防止行情浏览逻辑扩散成交易功能。

### Behavior impact

新增可启动的桌面股票历史数据浏览器。用户可选择股票、日期、日/周/月、复权、IEX/SIP、K线/折线/OHLC、折线字段、成交量和范围滑块；图表设置只重绘，数据设置在后台重新评估缓存。没有新增任何交易行为。

### Interface impact

新增首批公共 Python 接口：`HistoricalDataRequest`、`MarketBar`、`HistoricalMarketDataProvider`、`HistoricalDataStore`、`HistoricalDataService`、`HistoryController` 和桌面启动入口。此前没有公共程序接口，因此无兼容性破坏。

### Dependency impact

新增直接依赖：PySide6 6.x、Plotly 6.x、alpaca-py 0.x、pandas 2.2–3.x；开发依赖 pytest 8–9。实际安装验证版本为 PySide6 6.11.1、Plotly 6.9.0、alpaca-py 0.43.5、pandas 3.0.3、pytest 9.1.1。SQLite 为 Python 标准库。`.venv` 与 editable install 产物被 Git 忽略。

### Configuration or data impact

新增 `pyproject.toml` 和安全 `.env.example`。凭据变量为 `APCA_API_KEY_ID`/`APCA_API_SECRET_KEY`；可选缓存变量控制 24 小时时效、默认 5 根重叠和默认 5 分钟自动更新。新增本地数据库 `runtime/data/market_history.sqlite3`，含 `market_bars`、`data_coverage`、`fetch_history` 和查询索引；数据库及运行日志不提交 Git。未迁移或修改任何既有业务数据。

### Validation

- 阅读仓库规则、架构、模块标准、项目状态、最近编辑日志和 Git 状态；检查 Python、包、配置和凭据变量是否存在。
- 核对 Alpaca、Qt 和 Plotly 官方文档，并检查已安装 alpaca-py 源码的 `next_page_token` 循环。
- 创建 Python 3.14 `.venv` 并执行 editable dependency install。
- 运行 `compileall`、pytest、`pip check`、Git diff/ignore、文档章节/链接、凭据模式及禁止框架/交易 API 扫描。
- 使用 Qt offscreen 模式执行无凭据 GUI 启动、动态重绘、控件禁用和退出烟雾检查。
- 通过 pytest 检查三张表和三个查询索引；所有 Provider 测试无真实网络。

### Results

最终结果：56 tests passed；`compileall` 通过；`pip check` 报告无依赖冲突；GUI reactive smoke exit 0；数据库文件、运行日志路径、`.venv` 和 `*.egg-info` 均被 Git 忽略；模块必需章节、Markdown 链接、禁止依赖/交易 API、凭据值扫描和 `git diff --check` 均无问题。pytest 有 1 个上游弃用警告：alpaca-py 的传递依赖导入 `websockets.legacy`，本模块未使用 WebSocket。

中间检查如实记录：首次 40 项测试有 1 项因错误假设 Alpaca SDK 保留 tzinfo 而失败；修正后又因错误假设 UTC 字符串必须以 `Z` 而非 `+00:00` 结尾失败，按 SDK 实际 UTC 序列化修正后通过。第一次 GUI smoke 因 Windows cp1252 无法输出中文标题而失败，设置 UTF-8 后通过。两次内联 SQLite schema 命令因 PowerShell 引号转义失败，改为永久 schema pytest 后通过。Qt offscreen 环境产生 GPU 上下文回退提示，不影响退出码。

### Documentation

新增完整模块文档和 ADR-0002；更新 README、文档索引、架构概览、模块映射、项目状态、路线图、术语、编码/测试标准、CHANGELOG、KNOWN_ISSUES 和目录说明。未实现能力均明确标注为限制或 Not implemented。

### Rollback

当前改动尚未提交。回滚代码时应保留本日志历史，撤销本条列出的新增/修改项目文件；删除 `.venv` 只影响本地依赖。若需删除生成的 SQLite，必须先关闭应用并确认不需要缓存；数据库删除不可恢复。不得自动 reset、丢弃用户修改或改写 Git 历史。

### Open issues

- 没有 Alpaca 凭据，因此未真实验证认证、Feed 权限和服务端数据；见 KI-0003。
- 尚未在物理显示器进行人工视觉验收；offscreen GPU 回退提示见 KI-0004。
- 上游 WebSocket legacy 弃用警告见 KI-0005；本模块无 WebSocket 功能。
- 当前没有独立 formatter、linter 或静态类型检查器；使用 compileall、测试和运行时类型边界替代，不声称已执行类型检查。

### Approval

用户在当前请求中明确授权创建股票历史数据模块、相应测试和文档，并在不存在等效工具时添加 PySide6、Plotly、QWebEngineView、alpaca-py、pandas、SQLite 和 pytest。未执行 commit、push、merge 或历史修改。

## EDIT-20260713-006

### Date

2026-07-13 14:54:30 -07:00

### Request

将 Fidelity 明确设为用户主要券商并保持手动执行，同时保留 Alpaca 仅作为行情数据提供商；修正配置、GUI 文字、架构边界、测试和文档，禁止 Fidelity 自动连接及任何自动下单。

### Scope

包含应用级角色与安全默认值、Alpaca Market Data 凭据命名、GUI 状态显示、无 Fidelity 凭据要求和交易 API 导入保护测试，以及相关文档同步。明确不包含订单模型、Execution Provider、Fidelity 适配器、网页登录/自动化、账户同步、策略、真实网络请求或任何交易执行。

### Pre-change state

工作区包含尚未提交的股票历史数据浏览器实现。Alpaca Provider 实际只导入 `alpaca.data` 并负责历史行情，没有 Trading、Account 或 Order API；项目也没有订单或 execution 模块。缺口是应用未以正式配置表示 Fidelity、手动执行和自动交易关闭，GUI 未显示这些角色，部分凭据字段与提示使用了不够明确的通用名称。

### Files changed

- Added:
  - `src/quant_trading/application_settings.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
- Modified:
  - `.env.example`
  - `README.md`
  - `CHANGELOG.md`
  - `config/README.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `src/quant_trading/market_history/app.py`
  - `src/quant_trading/market_history/config.py`
  - `src/quant_trading/market_history/errors.py`
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_alpaca_provider.py`
  - `tests/unit/market_history/test_models_and_config.py`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

新增互不混用的 `MarketDataProviderType`、`BrokerageType` 与 `ExecutionMode` 枚举，以及只描述当前状态、不连接网络的 `ApplicationRoleSettings`。默认角色为 Alpaca 行情、Fidelity 主要券商、`MANUAL_FIDELITY`，自动下单和实盘均为关闭。历史数据配置字段改为明确的 Alpaca Market Data 名称；GUI 新增四项只读状态并将 API/错误文字明确为 Alpaca 行情。未创建 execution 接口或 Fidelity 实现，因为项目尚无订单需求。

### Reason

行情数据来源与实际券商是不同概念。明确边界可防止未来把 Alpaca 行情凭据误用为交易凭据，也不会让“用户使用 Fidelity”被错误理解为程序已经连接 Fidelity。

### Behavior impact

历史数据下载、SQLite 缓存、增量更新和图表行为保持不变。用户现在在 GUI 中看到 Alpaca 是行情来源、Fidelity 未连接且只允许手动操作、自动下单未启用。缺少 Alpaca Market Data 凭据时仍可离线启动并查看本地缓存。

### Interface impact

新增应用级角色设置类型。内部 `AppSettings` 字段改为 `alpaca_market_data_api_key` / `alpaca_market_data_secret_key`，GUI 构造参数改为 `market_data_credentials_available` 并接收角色设置；启动组合根已同步。历史数据领域模型、Provider/Store Protocol、Service 和 Controller 公共接口没有变化。

### Dependency impact

无新增、删除或升级依赖。行情模块仍只使用官方 `alpaca.data` Market Data 客户端；没有交易 SDK 客户端或 Fidelity 依赖。

### Configuration or data impact

环境变量名称保持 `APCA_API_KEY_ID` 和 `APCA_API_SECRET_KEY`，但其语义明确限定为 Alpaca Market Data。没有新增 Fidelity 环境变量、用户名、密码、双重认证或 API Key。SQLite schema、缓存文件及持久化数据均无变化。

### Validation

- 读取仓库规则、架构、模块文档、项目状态、最近编辑日志和 Git 状态，并搜索 Alpaca/broker/trading/execution/account/API key/Fidelity 相关内容。
- 先运行配置、GUI、Provider 与本地优先集成的针对性测试。
- 运行完整 pytest、`compileall`、`pip check`、`git diff --check`。
- 扫描生产代码中的 Alpaca Trading/订单调用和 Fidelity 凭据引用，并核对 Alpaca SDK 导入只来自 `alpaca.data`。

### Results

针对性测试 24 passed；最终完整测试 59 passed，均未访问真实网络。`compileall` 通过；`pip check` 报告无依赖冲突；`git diff --check` 通过，仅显示 Windows 后续可能将 LF 转为 CRLF 的提示。安全扫描未在生产代码发现 `alpaca.trading`、`TradingClient`、`submit_order` 或 Fidelity 凭据读取；匹配到的相关字符串仅用于否定性测试和安全说明。pytest 仍有 1 个已知上游 `websockets.legacy` 弃用警告，本模块未使用 WebSocket。

### Documentation

更新 README、配置说明、架构概览、模块映射、market-history 模块文档、项目状态和 CHANGELOG，明确 Alpaca=行情、Fidelity=主要券商、当前程序=查看/分析且手动执行。

### Rollback

删除本次新增的两个文件，并仅撤销本条列出的局部配置、GUI、测试和文档修改即可恢复修改前状态。SQLite 数据无需迁移或删除。工作区包含前一任务的未提交成果，回滚时不得使用 reset 或覆盖这些既有修改；本编辑记录应保留并用新记录说明回滚。

### Open issues

- 当前没有订单或 execution 模块，因此 `MANUAL_FIDELITY` 只表示角色和安全状态，不生成订单摘要或手动成交记录。
- Fidelity 账户、持仓、余额、交易历史和订单状态均不会同步。
- Alpaca 真实 Market Data 认证与 Feed 权限仍未使用真实凭据验证。

### Approval

用户明确授权本次角色、配置、GUI、测试和文档的非破坏性修改，并要求直接实施。未执行 Fidelity 或 Alpaca 真实连接、订单操作、commit、push、merge 或 Git 历史修改。

## EDIT-20260713-007

### Date

2026-07-13 15:03:13 -07:00

### Request

将 Alpaca 设为项目主要行情数据提供商和计划主要券商，默认目标执行环境改为 Alpaca Paper；保持 Alpaca Live、自动订单提交关闭并要求人工确认，Fidelity 不再作为默认券商。

### Scope

包含应用角色/环境枚举、安全默认值、GUI 状态、凭据说明、运行日志规划、测试及治理/架构/模块文档同步。保留 Fidelity 和 `MANUAL_FIDELITY` 为非默认兼容选项。明确不包含交易策略、信号、订单/账户模型、Alpaca Paper 或 Live Execution Provider、任何订单提交、真实账户连接、风险逻辑或 Fidelity 自动化。

### Pre-change state

工作区包含尚未提交的历史数据浏览器和上一轮角色修正。Alpaca 生产代码只使用 Market Data SDK；没有 brokerage、account、order 或 execution 模块。应用默认主要券商为 Fidelity，默认执行方式为 `MANUAL_FIDELITY`，GUI 和当前状态文档也据此显示。自动下单和 Live 已关闭，且不存在 Fidelity 凭据读取。

### Files changed

- Added: None.
- Modified:
  - `.env.example`
  - `AGENTS.md`
  - `README.md`
  - `CHANGELOG.md`
  - `config/README.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/development/WORKFLOW.md`
  - `docs/modules/market-history.md`
  - `docs/project/GLOSSARY.md`
  - `docs/project/PROJECT_STATE.md`
  - `runtime/README.md`
  - `src/quant_trading/application_settings.py`
  - `src/quant_trading/market_history/service.py`
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `tests/unit/market_history/test_models_and_config.py`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

`BrokerageType` 新增并默认使用 `ALPACA`；新增 `ExecutionEnvironment.ALPACA_PAPER` 与 `ALPACA_LIVE`，保留 `MANUAL_FIDELITY`，并保留旧 `ExecutionMode` 名称和只读 `execution_mode` 属性作为兼容入口。默认设置为 Alpaca Market Data、Alpaca Brokerage、Alpaca Paper、Paper 状态开启、Live 关闭、自动提交关闭、人工确认开启；配置对象拒绝 Paper/Live 状态混用。GUI 显示 Alpaca、Paper 模拟状态、无真实资金订单、Live/自动提交关闭及人工确认。没有添加执行客户端。

### Reason

用户明确将项目长期主要券商改为 Alpaca，并要求先以 Paper 为默认安全环境，为未来独立 execution 模块保留扩展能力。行情与执行即使由同一公司提供，也必须保持职责和授权边界。

### Behavior impact

用户可见的券商/环境状态从 Fidelity 手动执行改为 Alpaca Paper 默认目标。历史行情下载、本地 SQLite 缓存、增量更新和 Plotly 图表行为不变。Paper 只是配置状态，当前仍不能查询账户、持仓或提交模拟订单；任何 Alpaca Key 只会在现有代码中启用行情下载。

### Interface impact

新增 `ExecutionEnvironment`，保留 `ExecutionMode` 兼容别名；默认 `primary_brokerage` 从 `FIDELITY` 改为 `ALPACA`，默认执行值从 `MANUAL_FIDELITY` 改为 `ALPACA_PAPER`。新字段为 `execution_environment`，旧 `execution_mode` 仍可只读访问。历史数据模型、Provider/Store Protocol、Service/Controller 和数据库接口均无变化。

### Dependency impact

无新增、删除或升级依赖。生产代码继续只导入 `alpaca.data`；未添加 Alpaca Trading Client、Fidelity 客户端或其他外部服务。

### Configuration or data impact

环境变量名称保持 `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`。当前实现仍只将其用于 Market Data；Key 存在不会打开 Paper/Live 订单能力。无 Fidelity 凭据，无配置文件格式或 SQLite schema 变化，无数据迁移。未来 Paper/Live 凭据和 endpoint 必须明确隔离，但本次不提前创建重复变量。

### Validation

- 重新阅读仓库规则、架构、模块、工作流、项目状态、最近日志和 Git 状态，并搜索 Fidelity/Alpaca/brokerage/execution/Paper/Live/凭据/订单/账户相关内容。
- 运行配置、GUI、Provider 和本地优先集成的针对性测试。
- 运行完整 pytest、`compileall`、`pip check` 和 `git diff --check`。
- 扫描生产代码中的 Alpaca Trading/订单/账户调用及 Fidelity 凭据读取。

### Results

针对性测试 28 passed；最终完整测试 62 passed，均未访问真实网络或提交模拟/真实订单。`compileall` 通过；`pip check` 无依赖冲突；`git diff --check` 通过，仅有 Windows LF/CRLF 提示。生产代码对 `alpaca.trading`、`TradingClient`、订单/账户调用及 Fidelity 凭据读取的扫描为 0。pytest 仍有 1 个已知上游 `websockets.legacy` 弃用警告，本模块未使用 WebSocket。

### Documentation

更新仓库安全规则、普通用户 README、配置说明、架构数据流/模块边界、开发验证流程、market-history 模块文档、术语、项目当前状态、运行日志规则和 CHANGELOG。Paper/Live 执行均明确标记为 Planned/Not implemented，而非已连接能力。

### Rollback

仅撤销本条列出的局部默认值、GUI、测试和文档修改即可恢复上一轮 Fidelity 手动默认；保留历史编辑记录并新增更正/回滚记录。SQLite 无需迁移或删除。由于工作区还包含早先未提交成果，不得使用 reset、强制 checkout 或覆盖用户修改。

### Open issues

- Alpaca Paper Execution Provider、账户、持仓、订单、成交和取消功能均未实现。
- Alpaca Live 仅有未来枚举和保护规划，没有 endpoint、凭据加载、风险控制或启用路径。
- 当前运行日志只有 Market Data；`paper_execution` / `live_execution` 类别将在执行模块获批后实现。
- 真实 Alpaca Market Data 认证与 Feed 权限仍未使用真实凭据验证。

### Approval

用户明确授权本次非破坏性配置、命名、GUI、文档和测试修改，并要求默认 Alpaca Paper、Live 关闭。未访问任何真实账户、未提交任何订单，未执行 commit、push、merge、rebase 或 Git 历史修改。

## EDIT-20260713-008

### Date

2026-07-13 15:53:34 -07:00

### Request

修复用户在股票历史数据 GUI 点击“加载”后出现“发生未预期错误”的问题。

### Scope

包含诊断运行日志、修复 GUI/Controller 下拉值类型转换、增加正常/非法字符串和真实 Qt 控件回归测试、更新模块文档、项目状态和 CHANGELOG。明确不包含数据库迁移、缓存算法、Alpaca API、凭据、图表、交易配置或订单功能修改。

### Pre-change state

用户已启动 GUI 并加载 AAPL。运行日志多次显示 `AttributeError: 'str' object has no attribute 'value'`，发生在 API 访问前的 SQLite 查询。PySide6 将 `StrEnum` 下拉数据以普通字符串返回，但 Controller 直接将其放入 `HistoricalDataRequest`；数据库随后假设 timeframe/adjustment/feed 为枚举并访问 `.value`。现有测试绕过真实 Qt 下拉控件，未覆盖该转换。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/controller.py`
  - `tests/unit/market_history/test_controller.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

`HistoryController.build_request()` 现在接受领域枚举或 Qt 返回的字符串，并在创建领域请求前分别转换为 `Timeframe`、`Adjustment` 和 `DataFeed`。不支持的值转换为 `RequestValidationError`，不再延迟到 SQLite 层崩溃。新增字符串正常/非法测试及通过真实 `HistoryPanel` 下拉框构建请求的回归测试。

### Reason

Controller 的既定职责包含 GUI 参数转换；在该边界标准化可保持领域请求和 Store 的明确类型契约，并避免让 Qt 表示方式泄漏到数据库层。

### Behavior impact

点击“加载”时，日线/周线/月线、复权和 Feed 会以正确枚举进入本地缓存与 API 流程，不再出现 `.value` 异常。无效内部选项得到输入验证错误。股票历史下载、缓存和图表语义不变。

### Interface impact

`HistoryController.build_request()` 的三个参数由仅标注枚举放宽为枚举或字符串，并统一返回原有强类型 `HistoricalDataRequest`。其他公共接口无变化。

### Dependency impact

无依赖变化。

### Configuration or data impact

无环境变量、凭据、配置格式、SQLite schema 或数据变化。

### Validation

- 读取运行日志，确认错误发生在 API 调用前且与凭据无关。
- 运行 Controller、真实 Qt GUI、SQLite 和本地优先集成的针对性测试。
- 运行完整 pytest、`compileall`、`pip check` 和 `git diff --check`。

### Results

针对性测试 21 passed；最终完整测试 65 passed。`compileall` 通过；`pip check` 无依赖冲突；`git diff --check` 通过，仅有 Windows LF/CRLF 提示。测试未访问真实网络，也未提交任何订单。pytest 仍有 1 个上游 `websockets.legacy` 弃用警告，本模块未使用 WebSocket。

### Documentation

更新 market-history 模块职责/测试说明、PROJECT_STATE、CHANGELOG 和本编辑记录。

### Rollback

撤销 Controller 标准化、三项回归测试及对应文档修改即可恢复修改前状态；不需要处理数据库。回滚会重新暴露 GUI 加载崩溃，不建议执行。工作区包含其他未提交成果，不得使用 reset 或强制 checkout。

### Open issues

- 本次修复后仍需用户在实际 GUI 中重新点击“加载”，才能验证真实 Alpaca 凭据和网络响应；自动测试按规则不访问真实 API。
- 上游 WebSocket 弃用警告与本问题无关。

### Approval

用户明确要求修复。未访问或显示用户凭据，未访问交易 API，未执行 commit、push 或 Git 历史修改。

## EDIT-20260713-009

### Date

2026-07-13 16:02:00 -07:00

### Request

修复股票历史数据已成功加载但右侧交互图表保持白屏的问题。

### Scope

包含诊断运行日志和 Plotly HTML 大小、调整 QWebEngine 初始页面加载方式、增加实际 JavaScript 执行回归测试、更新模块文档、项目状态和 CHANGELOG。明确不包含行情请求、SQLite、缓存、凭据、图表数据语义或交易功能修改。

### Pre-change state

GUI 状态显示 AAPL、251 行、本地 Coverage 和数据加载完成；运行日志确认 Alpaca 成功返回 251 行，没有新的数据错误。Plotly 自包含 HTML 实测约 4.86 MB，代码通过 `QWebEngineView.setHtml()` 加载；该方法使用受大小限制的内存 data URL，导致完整离线 Plotly bundle 未显示，右侧为白色。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

初始 Plotly HTML 改为写入带 `.html` 后缀的 `QTemporaryFile`，关闭写句柄后通过本地文件 URL 交给 QWebEngine 加载；文件对象由 View 持有并在销毁时自动删除。后续图表更新仍使用原有 `Plotly.react`。新增 offscreen QWebEngine 回归测试，等待 `loadFinished` 并执行 JavaScript，验证 Plotly 全局对象和图表 DOM 均存在。仅测试进程关闭 Chromium sandbox，以允许无界面环境加载本地文件；生产代码没有降低沙箱设置。

### Reason

保持 Plotly 完全离线需要内嵌完整 JavaScript bundle，其大小超过 `setHtml()` 适合的内存 URL 范围。本地临时 HTML 保留离线和自动清理特性，同时避免页面大小限制。

### Behavior impact

已有或新下载的股票 Bar 现在可在右侧显示交互 Plotly 图表。悬停、缩放、拖动、动态 `Plotly.react` 和缓存逻辑保持不变。

### Interface impact

无公共接口变化。`_PlotlyView` 内部新增临时文件生命周期管理。

### Dependency impact

无依赖变化；使用 PySide6 已有 `QTemporaryFile` / `QDir`。

### Configuration or data impact

无环境变量、凭据、SQLite schema 或持久化数据变化。图表 HTML 只存在于操作系统临时目录并自动删除，不提交 Git。

### Validation

- 检查运行日志，确认 Alpaca 已成功返回 251 行且白屏发生在渲染层。
- 测量自包含 Plotly HTML 为约 4.86 MB。
- 运行真实 QWebEngine 本地文件加载与 JavaScript 执行测试。
- 运行完整 pytest、`compileall`、`pip check` 和 `git diff --check`。

### Results

最终完整测试 66 passed；Plotly/QWebEngine 测试确认 `loadFinished=True`、本地文件 URL、Plotly JavaScript 和图表 DOM 均可用。`compileall` 通过；`pip check` 无依赖冲突；`git diff --check` 通过，仅有 Windows LF/CRLF 提示。测试没有访问真实网络或订单接口。pytest 仍有 1 个上游 `websockets.legacy` 弃用警告。

首次新增回归测试在 offscreen Chromium sandbox 下连最小本地 HTML 也返回 `loadFinished=False`；确认这是测试环境限制后，仅为测试进程设置 `QTWEBENGINE_DISABLE_SANDBOX=1`，复测通过。生产桌面程序没有设置该变量。

### Documentation

更新 market-history 模块的图表加载职责/临时文件副作用、PROJECT_STATE、CHANGELOG 和本编辑记录。

### Rollback

恢复 `_PlotlyView` 的 `setHtml()` 调用、移除 QTemporaryFile 和对应测试/文档即可；但会恢复大页面白屏。无需处理数据库或已下载行情。不得使用 reset 覆盖工作区其他未提交修改。

### Open issues

- 需要用户关闭并重新启动实际桌面应用后确认物理显示器上的最终渲染；自动化已验证 QWebEngine JavaScript 路径。
- 上游 WebSocket 弃用警告与本问题无关。

### Approval

用户报告白屏并要求继续处理当前程序。未访问或显示凭据，未调用交易 API，未执行 commit、push 或 Git 历史修改。

## EDIT-20260713-010

### Date

2026-07-13 16:08:04 -07:00

### Request

继续修复右侧已显示 Plotly 初始提示，但加载 251 行 AAPL 数据后仍未切换为 K线图的问题。

### Scope

包含复现 `Plotly.react` 正常与初始加载竞态、核对真实缓存 Chart Builder 输出、修复 GUI 图表选项类型、增强 Qt 控件和动态刷新测试，并同步模块文档、项目状态、CHANGELOG 和编辑日志。明确不包含重新下载、缓存、数据库、凭据、行情语义或交易功能变化。

### Pre-change state

Plotly 本地 HTML 已可加载，初始页面显示“请输入股票代码”。GUI 状态显示 AAPL、251 行和数据完成，但页面不更新。动态 `Plotly.react` 独立测试成功，SQLite 中 251 行可构建 2 条 traces（Candlestick + Volume），启动期间排队更新也成功。最终定位到 `chart_type_combo` 与 `price_field_combo` 的 `StrEnum` 经 PySide6 后变成普通字符串；Chart Builder 在 `options.chart_type.value` 处于 Qt 主线程抛出异常，该路径未进入 Worker 运行日志，因此页面保留初始提示。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

`HistoryPanel._chart_options()` 现在将 Qt 下拉数据显式转换为 `ChartType` 和 `PriceField` 后再建立 `ChartOptions`。GUI 控件测试新增这两个强类型断言。Plotly 回归测试进一步验证正常 `Plotly.react` 会把 trace 数更新为 1，并新增“初始页面仍在加载时排队数据图”的竞态测试。

### Reason

行情请求选项和图表显示选项都必须在 GUI 边界标准化，避免 Qt 的字符串表示泄漏到领域/Chart Builder。直接覆盖动态 DOM trace 数量可防止只验证“页面打开”却遗漏“数据图没有替换初始图”。

### Behavior impact

数据加载完成后，初始提示会被实际 K线/折线/OHLC及可选成交量图替换；图表设置动态刷新恢复。行情数据和缓存行为不变。

### Interface impact

无公共接口变化；仅增强 `HistoryPanel` 内部图表选项转换。

### Dependency impact

无依赖变化。

### Configuration or data impact

无配置、凭据、SQLite schema 或数据变化；已有 251 行 AAPL 缓存可直接使用。

### Validation

- 检查最新日志和截图状态，确认数据已加载且无新 Worker 错误。
- 从 SQLite 读取相同范围，验证 251 bars 生成 Candlestick 与 Volume 两条 traces。
- 验证 Plotly 正常动态更新和初始加载期间的排队更新。
- 运行 GUI/Chart/Controller 针对性测试、完整 pytest、`compileall`、`pip check` 和 `git diff --check`。

### Results

针对性测试 18 passed；最终完整测试 67 passed。动态测试确认 Plotly trace 从初始状态更新，排队更新也成功。`compileall` 通过；`pip check` 无依赖冲突；`git diff --check` 通过，仅有 Windows LF/CRLF 提示。未访问真实网络或交易接口。pytest 保留 1 个无关的上游 `websockets.legacy` 弃用警告。

### Documentation

更新 market-history 的 GUI 边界说明、PROJECT_STATE、CHANGELOG 和本编辑记录。

### Rollback

撤销 `_chart_options()` 枚举转换和相关测试/文档即可，但会恢复数据加载后停留初始提示的问题。无需处理数据库或缓存，不得使用 reset 覆盖其他未提交修改。

### Open issues

- 需要用户重启实际桌面应用并点击“加载”进行最终物理显示确认。
- Qt 主线程图表异常当前不会进入 Worker 错误弹窗；本次通过强类型边界和回归测试消除已知路径，未来可单独考虑统一 UI 异常监控。

### Approval

用户通过连续截图要求继续修复当前显示问题。未访问或显示凭据，未调用交易 API，未执行 commit、push 或 Git 历史修改。

## EDIT-20260713-011

### Date

2026-07-13 16:16:02 -07:00

### Request

修复选择“过去 5 年”并成功加载 1255 行 AAPL 数据后，主图仍未显示五年数据的问题。

### Scope

包含诊断截图中的数据状态和 Plotly 视图保留逻辑、让请求日期范围变化时重置旧缩放坐标、增加回归测试并同步模块文档、项目状态和 CHANGELOG。明确不包含行情下载、SQLite、缓存数据、凭据、交易配置或交易功能修改。

### Pre-change state

GUI 状态确认 AAPL 的 2021-07-13 至 2026-07-13 范围已从本地缓存返回 1255 行，但图表主区域仍沿用此前数据范围的坐标。Plotly `uirevision` 只包含股票代码、时间粒度和图表类型，没有包含请求开始/结束时间，因此从一年切换到五年时不会自动重算横轴和纵轴；旧坐标之外的数据看起来像是没有显示。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/charts/plotly_chart_builder.py`
  - `tests/unit/market_history/test_chart_builder.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

Plotly `uirevision` 现在由 symbol、请求开始/结束时间、timeframe、adjustment 和 feed 共同组成。日期范围或数据维度发生变化时 revision 随之改变，Plotly 会重新计算视图；只切换 K线/折线等显示样式时 revision 保持不变，从而保留用户当前缩放。新增测试分别锁定“日期范围变化必须改变 revision”和“同一数据范围的样式变化不得改变 revision”。

### Reason

五年数据已经正确存在于本地并返回 GUI，问题属于图表交互状态而非数据缺失。让视图标识跟随实际数据范围是最小、局部且可回滚的修复，也符合“明确改变日期范围时可以重置、普通图表样式变化尽量保留视图”的既有要求。

### Behavior impact

用户从过去一年切换到过去五年、十年或自定义范围后，图表会自动显示新范围，不再被旧缩放坐标隐藏。对同一数据范围切换图表类型、成交量等显示选项时仍保留当前视图。

### Interface impact

无公共接口变化。`ChartOptions`、Controller 和 GUI 对外行为保持兼容。

### Dependency impact

无依赖变化。

### Configuration or data impact

无配置、凭据、SQLite schema 或本地缓存数据变化；已有 1255 行 AAPL 五年缓存无需重新下载。

### Validation

- 根据截图核对状态中的 AAPL、五年显示范围、本地 Coverage 和 1255 行数据。
- 运行 Chart Builder 与 GUI 针对性测试。
- 运行完整 pytest、`compileall`、`pip check` 和 `git diff --check`。

### Results

针对性测试 13 passed；完整测试 69 passed，保留 1 个与本次无关的上游 `websockets.legacy` 弃用警告。`compileall` 通过；`pip check` 报告无依赖冲突；`git diff --check` 通过。所有自动测试均未访问真实 Alpaca 网络或任何订单接口。

### Documentation

更新 market-history 模块的视图重置说明、PROJECT_STATE 当前验证状态、CHANGELOG 和本编辑记录。

### Rollback

将 `uirevision` 恢复为不含请求开始/结束时间的旧组成，并撤销两项回归测试及对应文档记录即可；回滚会恢复切换日期范围后数据可能被旧坐标隐藏的问题。工作区含其他未提交修改，不得使用 reset 或强制 checkout。

### Open issues

- 需要用户关闭并重新启动当前桌面程序后，在实际显示器上重新选择“过去 5 年”确认最终视觉效果。
- 上游 `websockets.legacy` 弃用警告与本次问题无关，项目没有使用 WebSocket 行情或交易。

### Approval

用户报告五年数据未显示并要求继续处理当前程序。修复为当前模块内的小范围非破坏性改动；未访问或显示凭据，未调用交易 API，未执行 commit、push 或 Git 历史修改。

## EDIT-20260713-012

### Date

2026-07-13 16:22:32 -07:00

### Request

在股票历史数据控制面板的股票代码输入框增加热门股票搜索建议，例如输入 `A` 时自动出现 `AAPL`。

### Scope

包含使用 PySide6 现有能力增加本地股票代码前缀自动补全、增加 GUI 回归测试并同步模块文档、项目状态和 CHANGELOG。明确不包含在线股票搜索、自动加载、股票推荐、投资建议、行情/API/缓存变化或任何交易功能。

### Pre-change state

股票代码使用普通 `QLineEdit`，只能由用户完整手动输入；项目没有代码搜索、自动补全或最近股票功能。输入变化本身不会访问 API，只有加载动作才会进入 Controller 和 Service。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

为股票代码输入框配置 PySide6 `QCompleter`，使用不区分大小写的前缀匹配和最多 8 条可见建议。本地初始列表包含 AAPL、AMD、AMZN、BAC、COST、DIS、GOOG、GOOGL、JPM、META、MSFT、NFLX、NVDA、TSLA 和 WMT。工具提示明确列表只用于输入帮助，用户仍可输入列表之外的代码。选择建议只填充输入框，仍需用户点击“加载”或按回车。

### Reason

本地固定列表能够满足输入 `A` 显示 `AAPL` 的目标，不新增依赖、不需要额外外部服务或账户权限，也不会把股票搜索和行情/交易职责混合。保留自由输入避免首版列表限制用户实际查询范围。

### Behavior impact

用户输入股票代码的前几个字母时会看到常见代码建议；匹配不区分大小写。建议列表不代表推荐股票，不自动请求数据，也不自动执行任何操作。

### Interface impact

无公共 Python 接口变化；仅为 `HistoryPanel` 内部输入控件增加补全器。

### Dependency impact

无依赖变化；使用已安装 PySide6 的 `QCompleter`。

### Configuration or data impact

无配置格式、环境变量、凭据、SQLite schema 或缓存数据变化。建议列表只存在于程序代码中，不访问网络。

### Validation

- 运行 GUI 针对性测试，验证小写 `a` 可匹配 AAPL、AMD 和 AMZN，补全不区分大小写，且列表外代码仍可输入。
- 运行完整 pytest、`compileall`、`pip check` 和 `git diff --check`。

### Results

针对性 GUI 测试 5 passed；完整测试 70 passed，保留 1 个无关的上游 `websockets.legacy` 弃用警告。`compileall` 通过；`pip check` 报告无依赖冲突；`git diff --check` 通过。测试未访问 Alpaca 网络、Fidelity 或任何订单接口。

### Documentation

更新 market-history 用户能力、PROJECT_STATE 当前能力/验证状态、CHANGELOG 和本编辑记录。

### Rollback

移除 `HistoryPanel` 中的 `_POPULAR_STOCK_SYMBOLS`、`QCompleter` 配置、对应 GUI 测试和文档更新即可恢复普通输入框；数据库和缓存无需处理。工作区包含其他未提交修改，不得使用 reset 或强制 checkout。

### Open issues

- 热门代码列表是首版本地小列表，不会自动跟随市场上市/退市或名称变化；列表之外的有效代码仍可直接输入。
- 当前不支持按公司名称搜索，例如输入 `Apple`；如未来需要在线完整证券目录，必须单独评估数据来源、更新机制和接口边界。

### Approval

用户明确请求在现有面板增加热门股票搜索结果。实现为当前 GUI 内小范围、非破坏性输入辅助；未新增依赖或外部服务，未访问凭据或交易接口，未执行 commit、push 或 Git 历史修改。

## EDIT-20260713-013

### Date

2026-07-13 16:26:14 -07:00

### Request

将股票代码自动补全纳入更多热门股票，并包含所有行业。

### Scope

将“所有行业”解释为覆盖当前 GICS 的 11 个大类行业，每类维护 10 个常见美股代码；扩展本地补全目录、增加行业覆盖回归测试并同步文档。明确不包含全部上市证券目录、在线股票搜索、公司名称搜索、股票推荐、投资建议、自动更新目录、行情缓存变化或交易功能。

### Pre-change state

自动补全只有 15 个常见代码，没有显式行业分组，主要集中在科技、通信、消费和金融，无法验证能源、材料、房地产、公用事业等大类是否得到覆盖。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

将本地代码目录改为按 11 个 GICS 大类行业分组：Communication Services、Consumer Discretionary、Consumer Staples、Energy、Financials、Health Care、Industrials、Information Technology、Materials、Real Estate 和 Utilities。每类收录 10 个常见代码，扁平化并排序后提供给原有 `QCompleter`，合计 110 个且无重复。测试验证 11 类名称完整、每类数量为 10、总数为 110 且代码唯一。

### Reason

GICS 11 个 sector 是“覆盖所有行业”的清晰、可验证且行业通用的最高层级解释；更细层级包含大量行业和子行业，直接声称覆盖所有上市公司或所有细分行业会不准确并造成高维护成本。本地分组保持实现简单、可撤销、不新增外部服务，同时明显改善代码发现范围。

### Behavior impact

输入框可对约 110 个分布于所有 11 个大类行业的常见美股代码进行不区分大小写的前缀提示。列表之外的代码仍可手动输入；出现建议不代表股票推荐，也不会自动加载数据。

### Interface impact

无公共接口变化。`HistoryPanel` 内部补全数据由单一元组调整为按行业分组后生成的元组。

### Dependency impact

无依赖变化；继续使用 PySide6 `QCompleter`。

### Configuration or data impact

无配置格式、环境变量、凭据、SQLite schema 或缓存数据变化。目录是程序内本地静态数据，不进行网络同步。

### Validation

- 核对 S&P Dow Jones Indices 的 GICS 官方说明，确认当前结构包含 11 个 sector。
- 运行 GUI 针对性测试，验证行业集合、每类数量、总数、唯一性和原有大小写不敏感前缀匹配。
- 运行完整 pytest、`compileall`、`pip check` 和 `git diff --check`。

### Results

针对性 GUI 测试 6 passed；完整测试 71 passed，保留 1 个无关的上游 `websockets.legacy` 弃用警告。`compileall` 通过；`pip check` 报告无依赖冲突；`git diff --check` 通过。测试未访问真实 Alpaca、Fidelity 或任何订单接口。

### Documentation

更新 market-history 用户能力和已知限制、PROJECT_STATE 当前能力/限制/验证状态、CHANGELOG 和本编辑记录。

### Rollback

将 `_POPULAR_STOCK_SYMBOLS_BY_SECTOR` 和生成逻辑恢复为上一版 15 个代码元组，撤销行业覆盖测试及对应文档更新即可；数据库和缓存无需处理。工作区包含其他未提交修改，不得使用 reset 或强制 checkout。

### Open issues

- “热门”不是客观、永久不变的属性；本目录是方便输入的人工维护集合，不是按成交量、市值或收益率计算的排名。
- GICS 分类及股票代码可能变化，本地目录不会自动同步上市、退市、改名或行业调整。
- 当前覆盖 11 个大类行业，不声称覆盖 GICS 的所有行业组、行业、子行业或全部上市证券。

### Approval

用户明确要求扩展热门股票并包含所有行业。实现仅扩展现有 GUI 本地输入辅助，无新增依赖或外部服务，未访问凭据或交易接口，未执行 commit、push 或 Git 历史修改。

## EDIT-20260713-014

### Date

2026-07-13 16:55:31 -07:00

### Request

实际运行和系统测试当前程序，定位并修复可确认的 Bug；建立长期统一的 Error Code、Session/Request ID、运行日志、异常捕获、诊断命令、BUG_LOG 和 Debug 流程。

### Scope

覆盖股票历史数据 GUI、Plotly 图表、本地 SQLite、Alpaca Market Data、缓存、后台 Worker、配置和 Paper/Live 安全边界。包含真实 GUI 启动/本地缓存烟雾检查，以及用户明确授权的只读 Alpaca Market Data 连通性诊断。明确不包含交易策略、账户操作、Paper/Live 订单、数据库迁移、大范围 GUI 重写或第三方依赖变更。

### Pre-change state

Windows 11、Python 3.14.5、PySide6 6.11.1、Plotly 6.9.0、pandas 3.0.3、alpaca-py 0.43.5、pytest 9.1.1。虚拟环境为 `.venv`；入口为 `python -m quant_trading.market_history`；数据库为 `runtime/data/market_history.sqlite3`。Alpaca 两个环境变量存在但值未读取到报告。工作区包含用户此前尚未提交的多项修改。修改前完整测试为 71 passed、1 个上游 `websockets.legacy` 弃用警告；GUI 实际启动并保持响应至少 6 秒，无启动异常。

### Files changed

- Added:
  - `src/quant_trading/error_codes.py`
  - `src/quant_trading/errors.py`
  - `src/quant_trading/observability.py`
  - `src/quant_trading/diagnostics.py`
  - `tests/unit/test_observability.py`
  - `tests/unit/test_diagnostics.py`
  - `docs/development/DEBUGGING.md`
  - `logs/BUG_LOG.md`
- Modified:
  - `.env.example`
  - `pyproject.toml`
  - `src/quant_trading/market_history/app.py`
  - `src/quant_trading/market_history/config.py`
  - `src/quant_trading/market_history/errors.py`
  - `src/quant_trading/market_history/controller.py`
  - `src/quant_trading/market_history/service.py`
  - `src/quant_trading/market_history/providers/alpaca_provider.py`
  - `src/quant_trading/market_history/storage/sqlite_store.py`
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_alpaca_provider.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `tests/unit/market_history/test_models_and_config.py`
  - `tests/unit/market_history/test_service.py`
  - `README.md`
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `docs/INDEX.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/development/TESTING_STANDARDS.md`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `runtime/README.md`
  - `logs/BUG_LOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

建立集中 `ErrorCode` 枚举和小型 `QuantTradeError` 异常层级；为配置、认证、API、数据、数据库、缓存、图表、GUI、线程和未知异常提供稳定编号。每次启动生成 Session ID，每次加载/刷新生成 Request ID，并显式传播到 Qt Worker。使用标准库 `logging` 写入 UTC 结构化、UTF-8、5 MB/5 份轮转的 `app.log` 与 `error.log`；日志过滤器统一遮挡环境中的 Key/Secret、授权头和常见敏感格式。安装主线程及 Python 后台线程未处理异常钩子，并让 Qt Worker 与图表构建失败保留堆栈、编号和上下文。

GUI 错误提示现在显示通俗原因、可采取操作、Error Code 和 Request ID；技术堆栈只进入日志。加载期间修改范围或数据选项会排队最新选择并在当前请求完成后自动重新加载，避免旧结果成为最终界面。Provider 将超时、HTTP 状态和畸形响应映射到稳定分类；Service 在 API 失败时保留本地数据并带编号警告。增加默认离线的只读诊断入口，检查环境、依赖、目录、SQLite schema/integrity、凭据存在性和交易安全；只有显式 `--network` 才执行只读行情请求。

### Reason

此前错误可能只显示通用对话框，后台链路缺少统一关联标识，且部分失败无法快速定位层级。集中编号、上下文和轮转日志让非专业用户只需提供 Error Code 与 Request ID；最小异常层级和模块内转换保留现有边界，不引入新依赖或交易能力。

### Behavior impact

正常历史行情、缓存和图表功能保持不变。用户会看到更可操作的错误提示和请求编号；运行时自动生成诊断日志。加载期间快速修改设置不再静默丢失。Debug 模式只改变日志详细程度，不改变 Paper/Live 或订单安全配置。

### Interface impact

新增内部公共诊断/错误基础类型和 `python -m quant_trading.diagnostics` 入口；现有 market-history 公共请求、Bar、Provider、Store、Service 与 Controller 接口未破坏。GUI Worker 内部信号增加诊断对象/Request ID 传递，不是对外稳定接口。

### Dependency impact

无第三方依赖新增、删除或升级。日志、轮转、上下文、诊断与脱敏使用 Python 标准库。

### Configuration or data impact

新增可选 `QUANT_TRADE_DEBUG=false` 和 `QUANT_TRADE_LOG_LEVEL=INFO`。运行日志改为 `runtime/logs/app.log` 与 `runtime/logs/error.log`；旧 `market_history.log` 不删除。SQLite schema、Bar/Coverage/Fetch History 格式无变化，无迁移。凭据值不会写入代码、文档或日志。

### Validation

- 修改前完整 pytest：71 passed、1 warning。
- 修改后完整 pytest：90 passed、1 warning，15.28 秒。
- 实际启动 GUI，多次确认进程持续响应；使用 GUI 加载 AAPL 本地缓存 251 行并成功构建图表。
- 修复 Worker 上下文后，以真实 GUI 请求 `REQ-B61A580A94F9` 验证 GUI/Controller/Service/Store/Chart 共用 `SES-5D86DC5EB9D9`。
- 默认诊断全部本地项目为 PASS，网络项 SKIPPED；显式只读网络诊断获取 AAPL IEX 5 行并 PASS。
- 运行 `compileall`、`pip check`、`git diff --check`。
- 扫描仓库文本与运行日志，确认当前凭据值没有泄漏；扫描正式源码，确认没有 `alpaca.trading`、`TradingClient`、`submit_order` 或 `cancel_order` 引用。

### Results

90 项测试全部通过；保留 1 个来自已安装 `websockets.legacy` 的上游弃用警告。`compileall` 通过，`pip check` 为 `No broken requirements found`，`git diff --check` 无错误，仅报告现有 Windows LF/CRLF 转换提示。SQLite 只读连接、schema `market_history_v1` 与 `quick_check=ok`。运行日志脱敏扫描通过，交易 API 引用为 0。

### Documentation

新增 DEBUGGING 与 BUG_LOG；更新 README 使用说明、文档索引、测试标准、架构概览/模块图、market-history 模块说明、项目状态、运行目录说明、CHANGELOG 与 KNOWN_ISSUES。

### Rollback

逐文件撤销本记录列出的 Debug/错误处理修改，移除新增四个源码文件、两个测试文件、DEBUGGING 和 BUG_LOG，并将日志路径恢复为旧路径。SQLite 无需回滚或迁移。由于工作区含用户其他未提交修改，不得使用 `git reset --hard` 或强制 checkout；应依据本记录做局部反向修改。

### Open issues

- `BUG-20260713-005` / `KI-0006`：同步 Alpaca SDK 请求没有安全取消接口，网络长时间挂起时关闭窗口可能等待请求返回；本次未用强制终止线程伪装修复。
- 未在真实物理显示器上逐项人工拖动、缩放和快速改变窗口尺寸；offscreen GUI、图表结构测试和用户此前的实际截图覆盖主要路径。
- 上游 `websockets.legacy` 弃用警告不影响当前功能；未获批升级依赖。

### Approval

用户明确授权完整运行检查、Bug 修复和 Debug 基础设施。本次未新增第三方依赖、未修改数据库 schema、未访问账户或订单接口、未提交任何订单、未启用 Live/自动执行，也未执行 commit、push、merge、rebase 或 Git 历史操作。

### Post-record verification update

2026-07-13 16:58:35 -07:00：通过实际 offscreen GUI 加载此前本地不存在的 MSFT 一年日线，成功从 Alpaca Market Data 只读获取并缓存 251 行，来源显示 `API update`，Request ID 为 `REQ-70820AF8A2B3`。随后在禁止网络权限的普通沙箱中重新加载相同请求，成功返回 251 行，来源显示 `Local cache`，Request ID 为 `REQ-40B439C155A2`，证明重启式重新组合后本地缓存命中且未依赖网络。两次均显示 Error Code 为“无”。QtWebEngine offscreen 环境输出 GLES3/GLES2 GPU Context 回退信息，图表流程仍成功；该提示已作为非物理显示环境限制报告。测试只读取行情并写入本地运行缓存，没有访问 Alpaca 账户或提交订单。

## EDIT-20260713-015

### Date

2026-07-13 17:12:05 -07:00

### Request

解释并修复每次加载图表后 GUI 看似放大、底部年份坐标不可见的问题。

### Scope

将问题专业解释为 Plotly 网页高度超过 QWebEngineView viewport 的响应式布局缺陷。只修改图表承载 WebView 的 HTML/CSS、resize 调用、回归测试和相关文档；不修改行情数据、复权语义、缓存、SQLite、窗口整体设计、依赖或交易功能。

### Pre-change state

用户截图显示相同 GOOGL 五年拆股复权数据在不同加载结果下具有不同纵向布局：异常状态中成交量和年份坐标延伸到窗口底部之外，正常状态中年份 2022–2026 可见。`_PlotlyView` 使用 `autosize=True` 和 responsive config，但 HTML/body 未定义 viewport 高度，首次加载、动态 `Plotly.react` 和 Qt resize 后没有统一显式同步 Plotly 尺寸。修改前完整测试为 90 passed。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/BUG_LOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

在自包含 Plotly HTML 的 head 中注入响应式 CSS，使 HTML、body 和 `market-history-chart` 具有当前 WebView 的 100% 宽高、零 margin/padding、`min-height: 0` 且不生成网页纵向滚动。页面首次完成加载后调用 `Plotly.Plots.resize()`；`Plotly.react` 完成后再次同步；QWebEngineView 收到 `resizeEvent` 时排队一次同步。所有动态 JavaScript 放入独立函数作用域，防止多次运行时全局 `const` 重复声明。

### Reason

Plotly 的 `responsive` 选项只能响应浏览器容器尺寸；如果上层 HTML/body 没有确定高度，百分比图表可能沿用初始像素高度。修复容器约束并在三个尺寸变化时点显式同步，能够直接修复根因，同时保持 Chart Builder 与 GUI 模块边界。

### Behavior impact

加载、换图或调整窗口后，图表页面不再向下溢出；底部年份坐标保持在当前窗口可见区域。鼠标悬停、缩放、拖动、成交量和范围滑块继续保留。

### Interface impact

无公共接口变化。仅增加 `_PlotlyView` 私有响应式 HTML 和 resize 实现。

### Dependency impact

无依赖变化。

### Configuration or data impact

无配置、凭据、SQLite schema、缓存或行情数据变化。

### Validation

- 针对性 Qt/WebEngine 测试：10 passed。
- 真实 offscreen QWebEngine 页面验证首次布局不溢出、`Plotly.react` 可继续更新数据。
- 将 WebView 从 900×600 缩小为 900×450，验证图表高度与 viewport 误差不超过 1 像素，body scroll height 和图表底边不超过 viewport。
- 完整 pytest、compileall、pip check、git diff --check。

### Results

完整测试 90 passed，保留 1 个上游 `websockets.legacy` 弃用警告；compileall 通过；pip check 报告 `No broken requirements found`；git diff 检查无错误，仅有既有 Windows LF/CRLF 提示。首次测试曾发现动态 JavaScript 的全局 `const chart` 冲突并失败，随后改为独立函数作用域并重新验证通过，没有隐藏该失败。

### Documentation

更新 market-history 用户能力和 WebView 尺寸职责、PROJECT_STATE 最后验证时间、CHANGELOG，并新增 `BUG-20260713-007`。

### Rollback

局部移除 `_RESPONSIVE_STYLE`、`_make_responsive_html()`、`_resize_plot()`、`resizeEvent()` 和 react 后 resize；撤销对应测试及文档即可。无需处理数据库或缓存。工作区包含其他未提交修改，不得使用 reset 或强制 checkout。

### Open issues

仍建议用户在真实显示器上重启程序并重复加载确认；自动测试使用真实 QWebEngine 但运行于 offscreen 环境，仍会输出已知 GPU context 回退提示。

### Approval

用户明确指出当前 GUI 加载后可见缺陷并要求解释。该修复属于当前 GUI 内部、小范围、非破坏性 Bug 修复，无新增依赖、公共接口或交易行为；未执行 commit、push 或 Git 历史操作。

## EDIT-20260713-016

### Date

2026-07-13 17:17:30 -07:00

### Request

从一年数据切换到五年数据时让图表自动刷新，不再要求用户再次点击“加载”。

### Scope

只调整已有结果之后的时间范围预设交互：1/5/10 年选择后立即启动后台自动加载，并增加完整 GUI 信号回归测试和文档。首次启动仍需输入股票并加载一次；自定义日期、时间粒度、复权和 Feed 保留 350ms debounce；不修改缓存算法、网络范围、数据库、行情含义或交易功能。

### Pre-change state

代码已有自动重载路径：时间范围下拉变化会更新日期，并在 `controller.current_result` 存在时启动 350ms timer。此前测试只直接调用 `_schedule_reload()`，没有从真实 `range_combo.currentIndexChanged` 信号覆盖完整用户操作。新增修改前行为测试证明该路径理论上可自动执行，但用户实际操作仍感知为需要手动加载，且界面没有明确显示正在等待自动刷新。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

`_on_range_changed()` 对离散的 1/5/10 年预设使用立即自动加载；`_schedule_reload()` 增加私有 `immediate` 选项，已有结果且当前空闲时停止旧 debounce 并直接从最新控件建立请求。状态区域显示“时间范围已改变，正在自动刷新图表…”。若当前请求仍在运行，继续使用 `_reload_after_busy`，完成后只加载最后一次选择。自定义日期、粒度、复权和 Feed 仍使用原有 debounce，避免连续操作产生重复请求。

### Reason

1/5/10 年下拉框是一次性的明确选择，不需要等待文本/日期连续编辑结束；立即启动后台任务更符合用户对“选择后自动刷新”的理解。实际数据仍通过 Service 本地优先算法获取，因此本地覆盖完整时不访问 API，扩大范围时只补充缺失区间。

### Behavior impact

首次打开后仍由用户选择股票并点击一次“加载”。已有图表后，从一年切到五年或十年会立即出现加载状态并自动更新图表，无需再次点击按钮。已有本地数据直接读取，缺少的前部区间才访问 Alpaca Market Data。

### Interface impact

无公共接口变化；只修改 `HistoryPanel` 私有调度方法。

### Dependency impact

无依赖变化。

### Configuration or data impact

无配置、凭据、SQLite schema 或缓存格式变化。

### Validation

- 新增完整 Qt 信号测试：建立已有结果，实际改变 `range_combo` 到 `5y`，验证自动调用一次最新控件加载、开始日期等于结束日期减五年，并显示自动刷新状态。
- GUI 针对性测试 11 passed。
- 完整 pytest、compileall、pip check、git diff --check。

### Results

完整测试 91 passed，保留 1 个上游 `websockets.legacy` 弃用警告；compileall 通过；pip check 为 `No broken requirements found`；git diff 检查无错误，仅有既有 Windows LF/CRLF 提示。自动测试未访问真实网络或任何交易接口。

### Documentation

更新 market-history 的首次加载/自动刷新说明、PROJECT_STATE 当前能力、CHANGELOG 和本编辑记录。

### Rollback

将 `_on_range_changed()` 恢复为普通 `_schedule_reload()`，移除 `immediate` 分支、状态文字和对应测试/文档，即恢复 350ms debounce 行为。无需修改数据库或缓存；不得使用 reset 覆盖工作区其他未提交修改。

### Open issues

如果用户仍在运行修改前已启动的 Python 进程，必须关闭并重新启动后新行为才会生效。

### Approval

用户明确要求时间范围选择后自动刷新。修改为现有 GUI 内部、小范围、非破坏性交互增强；无新增依赖、公共接口、外部服务或交易行为，未执行 commit、push 或 Git 历史操作。

## EDIT-20260713-017

### Date

2026-07-13 17:25:35 -07:00

### Request

继续修复加载后图表仍向下延伸超过显示屏、必须手动重新全屏才能恢复的问题。

### Scope

针对上一版响应式修复在真实显示器仍可复现的 Qt/Chromium 异步尺寸时序进行最小修复；增强真实 QWebEngine 回归测试，并同步 BUG_LOG 和文档。不修改窗口整体设计、行情、缓存、数据库、配置、依赖或交易功能。

### Pre-change state

`BUG-20260713-007` 已约束 HTML/body/图表为 100% WebView 高度，并在 Qt resizeEvent 后通过 `QTimer.singleShot(0)` 调用 Plotly resize。用户继续报告加载后仍可能向下延伸，但手动重新最大化窗口即可恢复，说明第二次窗口 resize 能纠正第一次错误。测量确认左侧状态内容更新前后窗口 `minimumSizeHint` 均为 500×829、默认窗口仍为 1380×860，因此不是状态文字扩大窗口最小高度。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/BUG_LOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

为 `_PlotlyView` 增加 150ms single-shot resize timer；窗口连续变化只重启该 timer，等待 Qt splitter、窗口最大化和 Chromium viewport 稳定后再执行最终 Plotly resize。页面加载完成后安装单例 `ResizeObserver` 监听 document root，浏览器确认 viewport 变化时通过 `requestAnimationFrame` 调用 Plotly。初始加载和 `Plotly.react` 后同样启动延迟校正。

### Reason

Qt 的下一轮 event loop 与 Chromium renderer 应用 viewport 不是同一个完成时点；零延迟回调可能仍读到旧浏览器高度。结合 Qt 延迟校正和浏览器自身 ResizeObserver，能够覆盖两个事件系统的真实完成顺序，而不要求用户通过重新最大化人为制造第二次 resize。

### Behavior impact

加载、动态换图、最大化、还原或拖动窗口尺寸后，图表会在布局稳定后自动适配，不再需要手动重新全屏。最多约 150ms 的重排延迟不会冻结 GUI、读取数据库或访问 API。

### Interface impact

无公共接口变化；仅增加 `_PlotlyView` 私有 timer 和浏览器 observer。

### Dependency impact

无依赖变化，使用现有 Qt、浏览器原生 ResizeObserver 和 Plotly API。

### Configuration or data impact

无配置、凭据、SQLite schema、缓存或数据变化。

### Validation

- 测量左侧状态文字更新前后的窗口 size/minimumSizeHint，排除左侧状态区扩大窗口。
- 使用真实 offscreen QWebEngine 验证浏览器 ResizeObserver 存在、Qt 延迟 timer 在 resize 后激活。
- 回归图使用 50 根 Candlestick、Volume 子图和 Range Slider，而非上一版的简单空 Figure。
- 执行 `Plotly.react` 后将 WebView 从 900×600 改为 900×450，确认最终图表高度与 viewport 误差不超过 1 像素且无纵向溢出。
- GUI 针对性测试、完整 pytest、compileall、pip check 和 git diff 检查。

### Results

GUI 针对性测试 11 passed；完整测试 91 passed，保留 1 个上游 `websockets.legacy` 弃用警告。compileall 通过，pip check 为 `No broken requirements found`，git diff 检查无错误，仅有既有 Windows LF/CRLF 提示。

### Documentation

更新 market-history 的双层尺寸同步说明、PROJECT_STATE、CHANGELOG，新增 `BUG-20260713-008`，并追加本编辑记录。

### Rollback

移除 `_plot_resize_timer`、`_install_resize_observer()` 及相关测试/文档，恢复零延迟 resize。无需修改数据库或缓存；工作区含其他未提交改动，不得使用 reset 或强制 checkout。

### Open issues

自动化测试使用真实 QWebEngine 但运行于 offscreen；仍需用户完全关闭旧进程、启动新进程后在实际显示器复验。若仍失败，应提供新的 Request ID 和整窗截图，下一步将记录实际 `window.innerHeight`、图表 bounds 和 Windows screen geometry 到 Debug 日志，而不是继续猜测。

### Approval

用户明确要求继续修复同一 GUI 可见缺陷。修改小范围、非破坏性，不涉及新依赖、公共接口、交易语义或外部服务；未执行 commit、push 或 Git 历史操作。

## EDIT-20260713-018

### Date

2026-07-13 17:52:18 -07:00

### Request

在现有股票历史数据浏览器中增加比日线更细的时间粒度，并按推荐方案支持 10 分钟、30 分钟和 1 小时历史 Bar。

### Scope

扩展现有 `market_history` 模块的粒度枚举、Alpaca 行情映射、常规交易时段处理、GUI 选项、请求范围保护、缓存隔离测试和文档。本次不实现实时 WebSocket、盘前/盘后专用模式、交易策略、信号、账户、Paper 订单、自动下单或 Live Trading。

### Pre-change state

程序只支持 Alpaca 原生 `1Day`、`1Week` 和 `1Month` 历史 Bar。SQLite 唯一键已经包含 timeframe，因此具备隔离新粒度的结构，但 GUI、领域枚举和 Provider 尚不接受分钟或小时请求。修改前完整测试基线为 91 passed、1 个上游弃用警告。

### Files changed

- Added: None.
- Modified:
  - `src/quant_trading/market_history/models.py`
  - `src/quant_trading/market_history/providers/alpaca_provider.py`
  - `src/quant_trading/market_history/ui/history_panel.py`
  - `tests/unit/market_history/test_models_and_config.py`
  - `tests/unit/market_history/test_alpaca_provider.py`
  - `tests/unit/market_history/test_history_panel_roles.py`
  - `tests/unit/market_history/test_sqlite_store.py`
  - `tests/unit/market_history/test_service.py`
  - `README.md`
  - `docs/modules/market-history.md`
  - `docs/project/PROJECT_STATE.md`
  - `docs/architecture/MODULE_MAP.md`
  - `KNOWN_ISSUES.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None. 一个临时的未跟踪 runtime 验收脚本在验证后已删除。
- Renamed: None.

### Implementation

新增 `10Min`、`30Min` 和内部 `1Hour` 枚举。10/30 分钟直接映射 Alpaca 官方粒度并按 `America/New_York` 过滤 09:30（含）至 16:00（不含）；1 小时为避免 Alpaca 原生整点 Bar 将 09:00 盘前数据混入，改为请求 30 分钟 Bar，再从 09:30 起按小时聚合，保留 15:30–16:00 的最后半小时尾 Bar。GUI 根据粒度动态提供范围：10 分钟最多 1 年，30 分钟和 1 小时最多 5 年，日/周/月保持 1/5/10 年；已有结果时切换粒度立即自动加载。领域请求同时执行相同上限验证，避免自定义日期绕过界面保护。

### Reason

用户需要在同一历史浏览器中观察日内变化。采用 Alpaca 已支持的分钟粒度可复用现有 Provider、缓存和图表边界；显式常规时段过滤及 09:30 对齐能让小时 Bar 更符合美股正常交易日的直观含义，同时避免新增依赖或创建新的顶层模块。

### Behavior impact

用户现在可以选择 10 分钟、30 分钟和 1 小时图。粒度变化会同步更新快捷范围并自动刷新；首次请求写入 SQLite，之后仍按 symbol/timeframe/adjustment/feed 独立本地复用和增量补齐。日/周/月行为保持不变。

### Interface impact

获用户明确批准后，公共 `Timeframe` 枚举增加 `TEN_MINUTES`、`THIRTY_MINUTES` 和 `HOUR`；现有枚举值和接口签名未改变。`1Hour` 是项目内部语义明确的 09:30 对齐 Bar，不等同于 Alpaca 原生整点 `1Hour`。

### Dependency impact

无新增或升级依赖。使用 Python 标准库 `zoneinfo` 和现有 `alpaca-py`；Provider 仍只访问 Market Data，不导入或调用 Trading API。

### Configuration or data impact

无配置格式、环境变量或 SQLite schema 迁移。现有唯一键和 Coverage 维度已包含 timeframe，新旧数据不会混合。分钟/小时数据会增加本地数据库体积；请求范围上限用于控制单次数据量。

### Validation

- 修改后相关单元测试：88 passed，1 个上游 `websockets.legacy` 弃用警告。
- 完整 `pytest -q`：109 passed，1 个相同上游警告。
- `compileall -q src tests`：通过。
- `pip check`：`No broken requirements found`。
- `git diff --check`：通过，仅输出既有 Windows LF/CRLF 转换提示。
- 只读真实 Alpaca Market Data 验收：AAPL 2026-07-10 IEX 返回 10 分钟 39 行（13:30–19:50 UTC）、30 分钟 13 行（13:30–19:30 UTC）、1 小时 7 行（13:30–19:30 UTC）。第一次在受限沙箱中因 socket 权限失败；获准在网络环境重试后成功。未访问账户、订单或交易接口，未输出 Key/Secret。
- 一次内联只读验收命令因 PowerShell 引号转义产生 `SyntaxError`，随后改用临时脚本并成功执行；没有将失败误报为通过。

### Results

新增粒度的模型、Provider、GUI、SQLite 隔离和刷新逻辑均通过自动测试及只读真实行情验证。自动测试不访问真实网络、不读取真实凭据、不提交 Paper 或 Live 订单。

### Documentation

更新 README、market-history 模块说明、模块地图、项目状态、CHANGELOG、KNOWN_ISSUES 和本编辑记录，明确范围上限、常规时段、小时聚合含义及提前收盘限制。

### Rollback

移除三个新增 `Timeframe` 值及 Provider/GUI 分支，删除对应测试和文档条目即可恢复仅日/周/月行为。SQLite 无 schema 变化；已缓存的新 timeframe 行不会影响旧查询，可保留，也可在应用关闭并备份后按现有数据库清理说明整体删除。工作区含其他用户未提交修改，不得使用 reset 或强制 checkout。

### Open issues

常规时段过滤使用纽约时间固定 09:30–16:00 窗口，能处理夏令时，但没有交易所日历依赖，无法识别提前收盘日；若供应商返回提前收盘后的盘后 Bar，可能仍被保留。已记录为 KI-0007，未擅自引入新依赖。

### Approval

用户明确同意按推荐方案增加 10 分钟、30 分钟、1 小时及常规时段/范围保护。未执行 commit、push、merge、rebase 或任何 Git 历史操作；未启用 Paper/Live 订单提交。

## EDIT-20260713-019

### Date

2026-07-13 18:00:42 -07:00

### Request

将当前完整版本上传到 GitHub 仓库 `tony73410/QuantTrading`。

### Scope

检查当前 `main` 分支、远程地址、工作区、忽略文件和敏感信息；将现有完整项目版本提交并推送到 `origin/main`；记录实际发布结果。不修改程序行为、配置格式、数据库、凭据或交易安全设置。

### Pre-change state

本地 `main` 与 `origin/main` 基于提交 `b2b21f3`，工作区包含此前已完成但尚未提交的行情浏览器、SQLite 缓存、GUI、Debug 基础设施、分钟/小时数据、测试和同步文档。`runtime/data/`、`runtime/logs/` 被 Git 忽略。

### Files changed

- Added: None.
- Modified: `logs/EDIT_LOG.md`（本发布记录）。
- Deleted: None.
- Renamed: None.

### Implementation

确认远程 `origin` 为 `https://github.com/tony73410/QuantTrading.git`，分支为 `main`。检查 `.env.example` 只有空凭据占位符；扫描仓库中的 Key、Secret、Authorization Header 和私钥模式；确认真实 `.env`、SQLite 文件及运行日志未进入暂存。随后创建主版本提交 `c9a0d8c`（`feat(market-history): publish local-first data browser`）并成功推送到 `origin/main`。

### Reason

用户明确要求把当前可运行版本保存到 GitHub；单一主版本提交便于追踪、回滚和在其他电脑恢复项目。本条后续日志提交只记录已经发生的发布事实。

### Behavior impact

无程序行为变化。GitHub `main` 现在包含当前股票历史数据浏览器版本。

### Interface impact

无额外公共接口变化；接口变化均已记录在此前对应编辑记录中。

### Dependency impact

无新增、移除或升级依赖。

### Configuration or data impact

无配置或数据库变化。真实 Alpaca 凭据、本地 SQLite 缓存和运行日志未上传。

### Validation

- 发布前完整测试基线：109 passed，1 个上游弃用警告。
- `git diff --cached --check`：通过；修正 4 个文件末尾多余空行后重新检查。
- 敏感信息检查：`.env.example` 的 Key/Secret 值为空；Authorization 命中仅为日志脱敏自动测试中的假数据。
- 忽略文件检查：`runtime/data/`、`runtime/logs/` 未进入提交。
- 主版本 push：`b2b21f3..c9a0d8c  main -> main`，成功。

### Results

主版本提交 `c9a0d8c` 已上传到 GitHub。未泄露凭据，未上传本地行情数据库或运行日志。

### Documentation

仅追加本条 `EDIT_LOG` 发布记录；未修改其他文档。

### Rollback

若需要撤销远程版本，应在用户明确批准后使用新的 `git revert c9a0d8c` 提交并推送；不得 reset、force push 或改写历史。本地运行数据库不受 Git 回滚影响。

### Open issues

无本次发布新增问题。既有 KI-0004 至 KI-0007 保持不变。

### Approval

用户明确要求上传当前版本，因此已授权本次 commit 和 push。未执行 pull、merge、rebase、reset、force push 或历史改写。

## EDIT-20260714-020

### Date

2026-07-14 10:38:37 -07:00

### Request

建立根目录 `PROJECT_COMPASS.md`，为未来 AI 和开发者提供项目中心思想、当前语义、用户意图追踪、歧义处理、架构防漂移及实施前后自我审查机制。

### Scope

基于实际代码、配置、Accepted ADR、测试、项目状态和已知问题建立唯一中心语义入口；将 Compass 阅读和前后审查接入仓库工作规则、开发流程和文档索引；记录该长期治理决策。本次不修改程序代码、依赖、配置、SQLite、行情、策略、回测、账户、订单或交易行为，也不实施尚待批准的本地数据清理规则。

### Pre-change state

仓库已有 `AGENTS.md`、PROJECT_STATE、架构/模块文档、ADR、Edit/Bug Log 和需求解释协议，但没有一个同时区分稳定用户意图与动态事实、维护 Active Intent/Assumption/Open Decision，并要求 AI 在重要任务前后审查的中心入口。开始时 `main` 与 `origin/main` 同步于 `4fe358e88e1843cffc4e477ca873c17c183c277b`，工作区干净。

### Files changed

- Added:
  - `PROJECT_COMPASS.md`
  - `docs/decisions/ADR-0003-project-compass.md`
- Modified:
  - `AGENTS.md`
  - `README.md`
  - `docs/INDEX.md`
  - `docs/decisions/README.md`
  - `docs/development/WORKFLOW.md`
  - `docs/development/DOCUMENTATION_STANDARDS.md`
  - `docs/project/PROJECT_STATE.md`
  - `CHANGELOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

创建 Compass version 1，分为仅经用户批准可改的 Stable Core 和基于证据演进的 Project State。Stable Core覆盖项目目的、用户/AI权责、可控性、模块化、安全、证据和用户理解原则。动态部分记录实际产品定义、模块、外部服务、代码默认值、已批准/明确不存在能力、Open Decisions、Assumption Register、需求解释/歧义等级、Active Intent Ledger、冲突优先级、前后审查、漂移检测、风险、下一方向和更新/Stable Core变更协议。新增Accepted ADR-0003记录采用这一长期治理机制；AGENTS和WORKFLOW强制重要任务读取Compass并在最终报告提供有依据的Compass audit。

### Reason

用户长期依赖AI开发，需要一个不依赖单次对话记忆、不会把AI建议冒充用户决定、也不会仅凭现有代码合理化项目漂移的持久语义来源。现有详细文档各有职责，Compass以摘要和链接连接它们，避免建立第二套完整历史。

### Behavior impact

无运行时或金融行为变化。未来AI工作流新增强制的Compass实施前/后审查和漂移标记；普通用户启动、行情查询、图表、缓存和日志行为不变。

### Interface impact

无程序公共接口变化。新增仓库级治理入口及报告要求；Stable Core未来修改必须走Compass Change Proposal和明确用户批准。

### Dependency impact

无依赖增删升级。

### Configuration or data impact

无环境变量、默认配置、SQLite schema、缓存数据或运行日志格式变化。自动数据清理仍为Compass DEC-001 / INTENT-005中的`Proposed, not approved`，没有删除任何本地数据。

### Validation

- 阅读 `AGENTS.md`、README、PROJECT_STATE、架构概览/模块图、ADR-0001/0002、KNOWN_ISSUES、最近EDIT_LOG、实际角色设置、Market History配置和项目依赖。
- 检查代码/文档中的 Alpaca、Fidelity、Paper、Live、自动提交、未实现能力和测试状态语义。
- 完整 `pytest -q`：109 passed，1个上游 `websockets.legacy` 弃用警告。
- `compileall -q src tests`：通过。
- `pip check`：`No broken requirements found`。
- Markdown相对链接检查：PASS。
- 必需章节/AGENTS集成关键词检查：PASS。
- `git diff --check`：通过，仅有既有Windows LF/CRLF提示。
- 首次将多项验证放在同一工具会话时只返回部分pytest进度且未返回退出码，因此未将其计为成功；随后分别重新执行并取得上述完整结果。

### Results

根目录Compass、Stable Core、动态事实、Active Intent、Assumption Register、Open Decisions、冲突优先级、前后审查、漂移检测和更新协议均已建立并链接到现有权威文档。109项现有程序测试继续通过，证明本次纯治理修改未破坏当前代码基线。

### Documentation

新增Compass和ADR-0003；更新AGENTS、README入口、文档索引、工作流、文档职责标准、PROJECT_STATE、CHANGELOG、ADR索引及本记录。

### Rollback

移除 `PROJECT_COMPASS.md` 与ADR-0003，并撤销上述文档中的Compass入口、审查和状态条目即可恢复此前治理结构。无代码、配置或数据迁移需要回滚。工作区修改不得通过reset或强制checkout丢弃。

### Open issues

- `paper_trading_enabled=true`仍可能被非专业读者误解；Compass已明确它只是计划环境标签，执行模块不存在。当前不改代码命名以避免未批准的公共语义变化。
- 本地存储增长控制仍需用户批准具体保留期限、不可逆删除和SQLite/Coverage方案；未静默实施。
- KI-0004至KI-0007保持不变。

### Approval

用户明确授权创建Compass、修改治理入口并建立审查机制。未执行commit、push、pull、merge、rebase、reset或Git历史修改；未启用Paper/Live订单能力。

## EDIT-20260714-021

### Date

2026-07-14 11:00:20 -07:00

### Request

检查 QuantTrade 的实际代码与现有架构文档，建立并长期维护一个唯一主要架构来源，明确模块职责、依赖、数据流、架构不变量、影响范围、扩展规则和漂移检查，并让未来 AI 在修改前执行架构审查。

### Scope

选择并扩充现有 `docs/architecture/OVERVIEW.md`，不创建重复的 `SYSTEM_ARCHITECTURE.md`；基于实际 Python 包、入口、import、配置、测试和外部集成状态记录当前架构；增加低风险、无新依赖的 import 边界回归测试；同步 Compass、AGENTS、索引、状态、ADR和 Changelog。本次不改变运行代码、公共接口、配置、SQLite、第三方依赖、行情行为或任何交易语义，也不实施大范围重构。

### Pre-change state

仓库已有 `OVERVIEW.md`、`MODULE_MAP.md` 和 `DEPENDENCY_RULES.md`，其中 Overview 最接近总体架构来源，但三者没有明确唯一主从关系；Overview 只有简要数据流和外部服务边界，缺少完整模块目录、依赖矩阵、变更影响范围、架构不变量、漂移风险和自动检查。开始本任务时，Compass治理改动仍未提交，已作为用户工作区内容保留。

### Files changed

- Added:
  - `docs/decisions/ADR-0004-canonical-system-architecture.md`
  - `tests/architecture/test_dependency_boundaries.py`
- Modified:
  - `PROJECT_COMPASS.md`
  - `AGENTS.md`
  - `README.md`
  - `CHANGELOG.md`
  - `docs/INDEX.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/architecture/DEPENDENCY_RULES.md`
  - `docs/decisions/README.md`
  - `docs/project/PROJECT_STATE.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

将现有 Overview 扩展为 version 1 的 canonical system architecture，按实际代码记录 composition root、UI、Controller、Service、领域契约、Alpaca Market Data Adapter、SQLite Store、Plotly Chart Adapter、配置、安全角色、可观测性与诊断的职责/非职责、接口、输入输出、依赖、副作用、配置和测试。补充依赖矩阵、启动/加载/错误数据流、外部服务边界、共享模型、配置/测试边界、12项架构不变量、新模块与公共接口规则、blast radius 模板、更新规则及当前漂移风险。增加4项标准库AST测试，检查循环import、非法跨层import、production导入tests/archive及唯一具体组装入口。ADR-0004记录沿用现有Overview而非创建重复文件的长期决定；AGENTS要求重要任务先读该文件并报告影响范围；Compass更新为version 2并增加INTENT-006。

### Reason

单一、基于实际代码且可部分自动验证的架构来源可以防止多个文档互相冲突，也能让局部改动在实施前识别职责归属和连锁影响。复用现有 Overview 比新增相近文件更符合最小变更和文档去重原则。

### Behavior impact

无程序运行行为或用户金融行为变化。未来开发流程新增架构所有权、依赖和 blast-radius 审查；架构测试会在违反当前依赖边界时失败。

### Interface impact

无 Python 公共接口变化。仓库治理接口明确 `docs/architecture/OVERVIEW.md` 为唯一主要架构来源。

### Dependency impact

无第三方依赖增删升级。架构测试只使用 Python 标准库 `ast` 和 `pathlib`。

### Configuration or data impact

无环境变量、默认值、凭据、SQLite schema、缓存数据或运行日志格式变化。Live、自动提交和所有订单能力保持关闭/未实现。

### Validation

- 实际检查 `src/quant_trading` 包、入口、GUI、Controller、Service、Provider、Store、Chart、配置、错误/日志、诊断及测试 import。
- `python -m pytest tests/architecture -q`：4 passed。
- 完整 `python -m pytest`：113 passed，1个上游 `websockets.legacy` 弃用警告。
- `python -m compileall -q src tests`：通过。
- `python -m pip check`：`No broken requirements found`。
- 新增文档/测试关键路径 `Test-Path`：全部存在。
- `git diff --check`：通过；仅显示 Windows 工作区 LF/CRLF 转换提示。

### Results

项目只有一个明确的主要架构文件。4项架构回归测试与109项既有测试全部通过；未发现循环import、GUI直接依赖Alpaca/SQLite、Provider依赖Store、production依赖tests/archive或多个具体组装入口。

### Documentation

更新主要架构、Compass version 2、AGENTS、README/文档索引、模块图/通用依赖说明、PROJECT_STATE、CHANGELOG、ADR索引，并新增Accepted ADR-0004及本记录。

### Rollback

撤销本条列出的文档修改并删除ADR-0004和架构测试即可恢复此前结构。无代码、依赖、配置或数据迁移需要回滚；不得使用reset或强制checkout丢弃其他未提交工作。

### Open issues

- `ui/history_panel.py` 当前文件较大，但仍遵守外部边界；只有后续职责继续增长时才建议提出局部拆分方案。
- `diagnostics.py` 直接了解SQLite预期表名并构造具体Market Data Provider进行可选只读检查；schema/Provider构造变化时必须同步诊断测试。
- Controller当前依赖具体Service/Chart Builder类型；在没有第二实现前不提前增加抽象。
- 既有KI-0004至KI-0007与Compass DEC-001保持不变。

### Approval

用户明确授权完善主要架构文件、更新AGENTS/状态/索引、增加低风险架构测试并记录漂移。未执行commit、push、pull、merge、rebase、reset或历史修改；未增加或启用交易功能。

## EDIT-20260714-022

### Date

2026-07-14 11:49:45 -07:00

### Request

创建并强制维护“已发现错误”文档：开发编辑过程中发现的任何可信错误或潜在缺陷都应记录，能够安全确认和修复时修复，暂时无法修复时透明保留记录。

### Scope

复用并升级已有 `logs/BUG_LOG.md`，避免创建第二个相同用途的文件；定义候选问题的记录门槛、状态、必填证据、修复/延期原则和任务结束审查；接入AGENTS、开发/Debug流程、文档索引、Compass和项目状态。本次不修改正式程序代码、公共接口、依赖、配置、SQLite或任何交易行为，也不把纯理论担忧和功能建议伪装成Bug。

### Pre-change state

仓库已有只追加的 `logs/BUG_LOG.md` 和8条历史Bug，但文件只声明记录“已确认缺陷”，没有要求尚未确认但具有具体失败机制的候选问题先记录，也没有强制未来每次任务报告Bug discovery audit。`KNOWN_ISSUES.md`、运行日志、Bug历史和Edit历史已有区分，但关系尚不完整。

### Files changed

- Added: None.
- Modified:
  - `PROJECT_COMPASS.md`
  - `AGENTS.md`
  - `CHANGELOG.md`
  - `KNOWN_ISSUES.md`
  - `docs/INDEX.md`
  - `docs/development/DEBUGGING.md`
  - `docs/development/DOCUMENTATION_STANDARDS.md`
  - `docs/development/WORKFLOW.md`
  - `docs/project/PROJECT_STATE.md`
  - `logs/BUG_LOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

将 `BUG_LOG.md` 明确为确认错误与可信潜在缺陷的唯一开发历史，保留全部既有条目并增加强制流程：Discover、Record first、honest classification、safe fix、transparent defer、verify、report。增加 `Suspected`、`Investigating`、`Open`、`Fixed`、`Cannot reproduce`、`Deferred`、`Rejected` 状态定义和统一必填字段。AGENTS与WORKFLOW要求重要任务读取Bug Log、发现后先分配ID、能安全局部修复则加回归测试、否则记录规避/验证/审批需求，并在最终报告提供Bug discovery audit。明确Bug Log、KNOWN_ISSUES、runtime logs和EDIT_LOG各自职责。Compass升级为version 3并增加INTENT-007。

### Reason

只记录已修复问题会让未复现、等待批准或暂时无法安全处理的风险丢失。统一记录和诚实状态能够保留调查上下文，同时避免为了“修复”而猜测性改代码或扩大任务范围。

### Behavior impact

无应用运行或金融行为变化。未来开发流程会强制记录可信候选缺陷，并要求每次任务说明发现、修复或延期情况。

### Interface impact

无程序公共接口变化。仓库治理约定新增Bug discovery audit和扩展后的Bug状态语义。

### Dependency impact

无依赖增删升级。

### Configuration or data impact

无配置、凭据、SQLite schema、缓存或运行数据变化；没有删除任何历史Bug、运行日志或调试证据。

### Validation

- 检查既有 `logs/BUG_LOG.md` 的8条历史、`KNOWN_ISSUES.md`、DEBUGGING、WORKFLOW、DOCUMENTATION_STANDARDS、Compass、Project State和Git状态。
- 完整 `python -m pytest`：113 passed，1个上游 `websockets.legacy` 弃用警告。
- `python -m compileall -q src tests`：通过。
- `python -m pip check`：`No broken requirements found`。
- 必需治理关键词和文档入口检查：通过。
- `git diff --check`：通过；仅有Windows工作区LF/CRLF转换提示。

### Results

没有创建重复文件；现有Bug Log已成为唯一发现错误文档，既能保存未确认候选，也能约束Fixed必须有证据。现有113项测试保持通过。本任务文档审查未发现新的可信程序缺陷，因此没有编造新的Bug ID。

### Documentation

更新Bug Log规则、AGENTS、开发/Debug流程、文档标准与索引、KNOWN_ISSUES关系、Compass version 3、PROJECT_STATE、CHANGELOG和本记录。

### Rollback

撤销本条列出的治理文字和Compass/状态条目即可恢复此前“仅确认Bug”的规则。既有8条Bug历史不应删除或改写；无代码、配置、依赖或数据迁移需要回滚。

### Open issues

既有BUG-20260713-005/KNOWN_ISSUES KI-0006仍为Deferred；KI-0004、KI-0005、KI-0007继续保留。本任务未发现新的可信缺陷。

### Approval

用户明确要求建立并维护已发现错误记录及修复/延期规则。未执行commit、push、pull、merge、rebase、reset或历史修改；未启用Paper/Live订单能力。

## EDIT-20260714-023

### Date

2026-07-14 13:07:19 -07:00

### Request

建立彼此解耦、可独立开发和测试的Single-Asset Factor Engine与Trading Decision Engine，以版本化FactorSnapshot单向通信；同时建立无算法的编排边界、测试和文档，不自行发明因子公式、买卖规则、仓位、风险或订单行为。

### Scope

新增`quant_trading.factors`、`quant_trading.decision`和最小`quant_trading.orchestration`正式模块，以及对应公开合同、注册器、无公式/无规则引擎、Fake测试、架构依赖检查、模块文档和ADR。Factor输入显式记录Bar完成/可用时间以阻止前视数据；Decision输出仅为TradeIntent。现有Market History GUI/Service不接入该流水线；不新增配置格式、持久化、外部依赖、账户、Risk、Execution或券商调用。

### Pre-change state

项目只有历史行情、SQLite缓存、GUI/图表、配置和Debug模块。源码/测试搜索未发现factor、indicator、signal、strategy、decision、portfolio、risk、execution或order业务实现；`ALPACA_PAPER`只是安全标签。主要架构明确策略、风险和执行均未实现。开始时Compass、主要架构和Bug治理改动仍未提交，均被保留。

### Files changed

- Added:
  - `src/quant_trading/factors/__init__.py`
  - `src/quant_trading/factors/errors.py`
  - `src/quant_trading/factors/models.py`
  - `src/quant_trading/factors/interfaces.py`
  - `src/quant_trading/factors/registry.py`
  - `src/quant_trading/factors/engine.py`
  - `src/quant_trading/decision/__init__.py`
  - `src/quant_trading/decision/errors.py`
  - `src/quant_trading/decision/models.py`
  - `src/quant_trading/decision/interfaces.py`
  - `src/quant_trading/decision/registry.py`
  - `src/quant_trading/decision/engine.py`
  - `src/quant_trading/orchestration/__init__.py`
  - `src/quant_trading/orchestration/analysis_decision_pipeline.py`
  - `tests/unit/factors/test_factor_engine.py`
  - `tests/unit/decision/test_decision_engine.py`
  - `tests/integration/test_analysis_decision_pipeline.py`
  - `docs/modules/factors.md`
  - `docs/modules/trading-decision.md`
  - `docs/modules/analysis-decision-pipeline.md`
  - `docs/decisions/ADR-0005-two-stage-algorithm-architecture.md`
- Modified:
  - `PROJECT_COMPASS.md`
  - `AGENTS.md`
  - `README.md`
  - `CHANGELOG.md`
  - `docs/INDEX.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/decisions/README.md`
  - `docs/modules/README.md`
  - `docs/project/GLOSSARY.md`
  - `docs/project/PROJECT_STATE.md`
  - `tests/architecture/test_dependency_boundaries.py`
  - `logs/BUG_LOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: None.
- Renamed: None.

### Implementation

Factor层定义`MarketDataObservation/Window`、`FactorContext/Parameter`、六种FactorStatus、FactorResult/Snapshot/Collection、FactorCalculator Protocol、显式Registry和SingleAssetFactorEngine。每个Calculator必须声明名称、版本、最小输入、单位和缺失处理；Window拒绝未完成、as-of后才可用、混合维度、乱序及非法数值的Bar。Decision层定义独立参数上下文、最小无持仓语义PortfolioSnapshot、DecisionInput/Result、TradeIntent、Policy Protocol/Registry和TradingDecisionEngine；显式STALE/非VALID Factor会阻止Policy，Intent不含订单/券商/执行字段。Orchestration只执行Factor→Snapshot→Decision并返回两侧结果。架构测试禁止反向依赖、具体Factor实现依赖、Market History/SQLite/Alpaca/Execution依赖和循环import。未创建production implementations目录、公式或Policy。

### Reason

将“描述资产特征”和“根据特征形成交易意图”分开，能够让用户逐步批准公式和规则，也能独立替换/测试每层而不让Market Data、策略、风险和券商耦合。显式availability时间和版本追踪为未来防前视、复现和审计提供合同基础。

### Behavior impact

新增可由Python调用的合同级Factor/Decision/Orchestration API，但现有GUI、行情下载、缓存和图表行为完全不变。没有正式算法注册，应用启动不会自动运行这些层，也不会产生任何交易意图或订单。

### Interface impact

新增公开接口；未修改任何既有接口。Factor与Decision只能通过`FactorSnapshotCollection`通信。未来修改字段、状态或含义属于公共接口变更，必须重新审批和迁移调用方。

### Dependency impact

无第三方依赖增删升级。Factors只依赖stdlib和公开MarketBar/dimension模型；Decision只依赖Factor公开models/interfaces；Orchestration依赖两侧公开engine/models。架构测试验证禁止方向。

### Configuration or data impact

无配置文件/环境变量、SQLite schema或运行数据变化。Factor/Decision参数使用两个独立的不可变typed context；FactorSnapshot和DecisionResult持久化未实现。Live和自动订单提交保持关闭。

### Validation

- 搜索实际源码、测试和文档中的factor/indicator/signal/strategy/decision/portfolio/risk/execution/order，确认无既有等效业务模块。
- 针对性Factor/Decision/Pipeline/Architecture测试：24 passed。
- 完整`python -m pytest`：133 passed，1个上游`websockets.legacy`弃用警告。
- `python -m compileall -q src tests`：通过。
- `python -m pip check`：`No broken requirements found`。
- 禁止依赖/敏感调用源码搜索：Factors无Decision/Alpaca/SQLite/订单依赖；Decision无Factor engine/Market History/Alpaca/SQLite依赖。
- `git diff --check`：通过；仅有Windows LF/CRLF提示。

### Results

两层可分别用Fake输入运行；替换Factor实现不修改Decision Policy，替换Decision Policy不修改Factor层。Factor结果具有版本、as-of、参数、状态、质量和来源范围；Decision结果引用Factor Snapshot与Policy版本，且不表示成交。没有Risk/Execution直连路径。

### Documentation

新增三份模块文档和Accepted ADR-0005；更新Compass version 4/INTENT-008/DEC-005/006、主要架构version 2、模块图、AGENTS不变量、README、索引、Glossary、PROJECT_STATE、CHANGELOG、ADR/模块索引、Bug Log和本记录。

### Rollback

删除三个新源码包、三组新测试、三份模块文档和ADR-0005，撤销本条列出的架构/Compass/索引/状态/日志文字，即可恢复历史浏览器状态。没有配置、数据库或运行数据迁移需要回滚；不得reset或强制checkout覆盖其他未提交工作。

### Open issues

- Market History Bar到`available_at_utc`的粒度/交易日历语义未批准，因此流水线未接入现有Service；见Compass DEC-005。
- 复权历史是否满足未来point-in-time Factor/回测语义未批准；见Compass DEC-006。
- Portfolio holdings/exposure、Factor/Decision持久化、正式公式/Policy、Risk和Execution均未实现。
- 既有KI-0004至KI-0007保持不变。

### Approval

用户明确批准建立两层算法架构、接口、模型、测试边界、文档和必要编排。未执行commit、push、pull、merge、rebase、reset或Git历史修改；未连接账户、访问交易API或启用Paper/Live订单。

## EDIT-20260714-024

### Date

2026-07-14 13:56:08 -07:00

### Request

在Single-Asset Factor和Trading Decision之后建立独立Risk Control层；Risk可批准、否决、缩减、延迟、人工审查或暂停，但不得增加风险、修改上游算法或直接下单。建立合同、保守优先级、三层编排、Execution类型门、测试、架构约束和文档，不选择具体风险数值。

### Scope

包含Risk公共模型/Protocol/Registry/Engine、Factor → Decision → Risk接口级Pipeline、结构化原因和审计日志、Fake独立/优先级/架构/集成测试及治理文档同步。明确不包含数值Risk Policy、账户/持仓连接、持久化、GUI、Order Construction、Paper/Live执行、自动平仓或任何策略。

### Pre-change state

项目已有独立Factor和Decision合同及两层Pipeline；Risk与Execution均为文档中的Not implemented边界。没有风险规则散落在GUI/Decision/Provider，也没有任何执行模块或绕过风险的下单路径。修改前完整测试133 passed，1个上游弃用警告。工作区包含用户此前尚未提交的Compass/架构/两层算法治理改动，本次保留且未覆盖。

### Files changed

- Added:
  - `src/quant_trading/risk/__init__.py`
  - `src/quant_trading/risk/errors.py`
  - `src/quant_trading/risk/interfaces.py`
  - `src/quant_trading/risk/models.py`
  - `src/quant_trading/risk/registry.py`
  - `src/quant_trading/risk/engine.py`
  - `src/quant_trading/orchestration/trading_evaluation_pipeline.py`
  - `tests/unit/risk/test_risk_engine.py`
  - `docs/modules/risk-control.md`
  - `docs/decisions/ADR-0006-independent-risk-control-gate.md`
- Modified:
  - `src/quant_trading/orchestration/__init__.py`
  - `tests/architecture/test_dependency_boundaries.py`
  - `tests/integration/test_analysis_decision_pipeline.py`
  - `AGENTS.md`
  - `PROJECT_COMPASS.md`
  - `README.md`
  - `CHANGELOG.md`
  - `docs/INDEX.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/architecture/DEPENDENCY_RULES.md`
  - `docs/decisions/README.md`
  - `docs/modules/README.md`
  - `docs/modules/factors.md`
  - `docs/modules/trading-decision.md`
  - `docs/modules/analysis-decision-pipeline.md`
  - `docs/project/GLOSSARY.md`
  - `docs/project/PROJECT_STATE.md`
  - `logs/BUG_LOG.md`
  - `logs/EDIT_LOG.md`
- Deleted: none.
- Renamed: none.

### Implementation

- 建立不可变Risk上下文、Account/OpenOrders中性快照、SystemRiskState、RiskRuleResult、RiskDecision和`RiskApprovedTradeIntent`类型门。
- 定义`RiskPolicy`及账户/组合/未完成订单的Planned Provider Protocol；没有具体外部连接。
- Risk Engine在Policy前拦截系统/股票暂停、Live、自动提交、Intent/Factor不一致及过期/不完整数据；没有规则时要求人工审查。
- 保守合并优先级；多个缩减取最严格值。任何扩大、反转、发明目标或无动作进入Order Construction的尝试失败关闭。
- 每次裁决记录Decision/Intent ID、原始/批准值、原因、Policy/配置版本和Paper环境；不记录Secret。
- 新增TradingEvaluationPipeline，输出Factor、Decision、Risk结果后停止；不存在OrderRequest或ExecutionResult。
- 添加AST依赖边界和未来Execution Gate测试；Factors/Decision不反向依赖Risk，Risk不依赖具体实现/Alpaca/SQLite/GUI/Execution。

### Reason

独立安全门可以否决或降低交易算法的建议而不污染Factor或Decision职责。将“通过风险审查”与普通TradeIntent分为不同类型，并把不增加风险写入公共合同和测试，可防止未来Execution误接原始建议。

### Behavior impact

新增可调用但未接入GUI的合同级Risk评估能力。现有历史数据浏览器、缓存、图表、Factor和Decision行为不变。没有账户、订单、Paper或Live运行行为。

### Interface impact

新增Risk公共接口和TradingEvaluationPipeline；现有Factor/Decision/AnalysisDecision接口未删除或改变。`orchestration.__init__`只增加兼容性导出。未来Execution的强制输入边界被定义为Risk-approved对象，不是普通TradeIntent。

### Dependency impact

新增单向依赖：Risk → public Factor/Decision models；Orchestration → Risk。Factors/Decision不依赖Risk；Risk不依赖Execution、Alpaca、Market History具体实现、SQLite或GUI。没有新增第三方依赖和循环依赖。

### Configuration or data impact

无配置格式、环境变量、SQLite schema、持久化或迁移变化。RiskContext只记录显式配置版本和安全环境状态；金额、比例、Loss/Drawdown、杠杆、保证金值均未选择。Live和自动提交保持关闭，人工确认默认开启。

### Validation

- 修改前完整`python -m pytest`：133 passed，1个上游`websockets.legacy`弃用警告。
- 目标Risk/Architecture/Pipeline测试：24 passed；增加审计测试后Risk单元15 passed。
- 修改后完整`python -m pytest`：151 passed，1个相同上游弃用警告。
- `python -m compileall -q src tests`：通过。
- `python -m pip check`：`No broken requirements found`。
- `git diff --check`：通过，仅Windows LF/CRLF提示。
- 禁止依赖搜索：Risk/Orchestration无Alpaca、SQLite、GUI或订单调用；Factor/Decision无Risk import。

### Results

Risk可使用Fake Intent/Factor/Portfolio/Account独立测试；支持Approve/Reject/Reduce/Defer/Manual/Symbol Pause/System Pause。Reject和System Pause按保守优先级生效，多个缩减取40而非60，100→150的错误Rule失败关闭。三层Pipeline不访问网络、不提交订单并在RiskDecision停止。

### Documentation

新增Risk模块文档和Accepted ADR-0006；Compass升级version 5并记录INTENT-009/ASM-008/DEC-007；主要架构升级version 3；同步AGENTS、模块图/边界、README、索引、Glossary、PROJECT_STATE、CHANGELOG、BUG_LOG和本记录。

### Rollback

删除新Risk包、TradingEvaluationPipeline、Risk测试/文档/ADR-0006，撤销本条列出的Risk相关导出、架构测试和文档段落即可恢复Factor → Decision停止状态。没有数据库、配置或运行数据迁移。不得使用reset或强制checkout覆盖其他未提交工作。

### Open issues

- 数值Risk Policy及最大仓位/订单、现金、Buying Power、Daily Loss、Drawdown、集中度、杠杆、保证金值均待用户批准，见Compass DEC-007。
- Account/Portfolio/OpenOrders Provider只有Protocol；没有账户数据连接或持久化。
- Risk结果尚未接入GUI或持久化；Order Construction和Execution未实现。
- Emergency de-risking当前只暂停新Intent；自动降仓/平仓Not implemented。
- 既有DEC-001/005/006及KI-0004至KI-0007不变。

### Approval

用户明确批准新Risk主要模块、三层依赖方向、权限边界、接口、测试和文档。本次未选择具体风险数值，未新增配置/数据库/依赖，未连接任何账户或交易API，未提交Paper/Live订单，未执行commit、push、pull、merge、rebase、reset或Git历史修改。

## EDIT-20260714-025

### Date

2026-07-14 14:35:14 -07:00

### Request

创建独立算法控制中心GUI，统一管理Factor、Trading Decision和Risk组件的注册元数据、参数、依赖、配置版本、安全预览、Pipeline Dry Run和审计，同时严格禁止GUI承载算法/风险/执行逻辑或提交订单。

### Scope

包含新的`quant_trading.algorithm_control`管理面、独立启动入口、通用ParameterSchema、Draft/Saved/Active生命周期、原子JSON控制状态、依赖/安全验证、后台NO EXECUTION预览、GUI六个页面、审计、错误代码、测试和架构/Compass/模块文档同步。明确不包含正式Factor公式、Decision Policy、数值Risk规则、行情下载、账户连接、订单构建、Paper/Live执行或任何自动交易。

### Pre-change state

项目已有独立Factor/Decision/Risk合同、Registry、Engine和接口级Pipeline，但无正式算法、无执行模块、无算法管理GUI、无通用参数架构或配置版本存储。历史数据浏览器是唯一桌面GUI。修改前完整测试为151 passed和1项上游弃用警告；工作区包含用户此前未提交的治理与三层算法改动，本次全部保留。

### Files changed

- Added:
  - `src/quant_trading/algorithm_control/__init__.py`
  - `src/quant_trading/algorithm_control/__main__.py`
  - `src/quant_trading/algorithm_control/app.py`
  - `src/quant_trading/algorithm_control/audit_service.py`
  - `src/quant_trading/algorithm_control/configuration_service.py`
  - `src/quant_trading/algorithm_control/controller.py`
  - `src/quant_trading/algorithm_control/errors.py`
  - `src/quant_trading/algorithm_control/interfaces.py`
  - `src/quant_trading/algorithm_control/models.py`
  - `src/quant_trading/algorithm_control/preview_service.py`
  - `src/quant_trading/algorithm_control/registry.py`
  - `src/quant_trading/algorithm_control/storage.py`
  - `src/quant_trading/algorithm_control/system_components.py`
  - `src/quant_trading/algorithm_control/ui/__init__.py`
  - `src/quant_trading/algorithm_control/ui/component_panel.py`
  - `src/quant_trading/algorithm_control/ui/main_panel.py`
  - `src/quant_trading/algorithm_control/ui/parameter_editor.py`
  - `src/quant_trading/algorithm_control/ui/workers.py`
  - `src/quant_trading/algorithm_control/validation_service.py`
  - `tests/unit/algorithm_control/test_configuration_service.py`
  - `tests/unit/algorithm_control/test_parameter_editor.py`
  - `tests/unit/algorithm_control/test_preview_and_controller.py`
  - `tests/unit/algorithm_control/test_registry_and_validation.py`
  - `tests/architecture/test_algorithm_control_boundaries.py`
  - `docs/modules/algorithm-control-gui.md`
  - `docs/decisions/ADR-0007-algorithm-control-plane.md`
- Modified:
  - `src/quant_trading/error_codes.py`
  - `pyproject.toml`
  - `AGENTS.md`
  - `PROJECT_COMPASS.md`
  - `README.md`
  - `CHANGELOG.md`
  - `docs/INDEX.md`
  - `docs/architecture/OVERVIEW.md`
  - `docs/architecture/MODULE_MAP.md`
  - `docs/architecture/DEPENDENCY_RULES.md`
  - `docs/decisions/README.md`
  - `docs/modules/README.md`
  - `docs/project/PROJECT_STATE.md`
  - `logs/EDIT_LOG.md`
- Deleted: none.
- Renamed: none.

### Implementation

- 建立Registry驱动的完整ComponentMetadata和ParameterSchema，通用编辑器支持integer/decimal/boolean/string/enum/date/percentage/money/duration/list；GUI没有按算法名称分支。
- Draft仅存在当前会话；Save创建SAVED版本但不激活；Apply创建新的ACTIVE版本；Restore从旧记录创建新的SAVED版本。所有持久记录和Audit只追加，不覆盖历史。
- 使用`runtime/algorithm_control/control_state.json`原子临时文件替换，和行情SQLite分开且被Git忽略；未读写Secret。
- 建立类型/范围/枚举/必填/依赖和Locked验证；四项真实项目安全不变量默认Active且GUI不可停用。
- 建立六页PySide6控制中心：Overview、Factor、Decision、Risk、Pipeline和Audit。Factor/Decision没有正式组件时如实显示为空；Risk只显示四个Locked系统安全项。
- Preview通过QThreadPool后台执行并强制`no_execution=True`；没有注册正式Preview时返回Not implemented。Pipeline缺Factor/Decision时验证失败并禁用Dry Run。
- 新增QT-ALG-COMPONENT/DEPENDENCY/CONFIG/PREVIEW/STORAGE错误代码，接入现有轮转日志和全局异常Hook；预览错误包含请求编号且不显示技术堆栈给普通用户。

### Reason

将“管理算法组件和配置”与“运行算法、处理行情、执行订单”分开，可以让未来组件通过稳定元数据出现而不污染GUI，也可以让用户明确区分编辑草稿、保存版本、应用版本和只读预览。空的生产Registry避免将示例公式或风险数值误当成用户批准的交易逻辑。

### Behavior impact

用户可单独启动算法控制中心，查看当前三层注册状态、四项安全不变量、版本历史、验证和审计。当前不会产生Factor值、TradeIntent、RiskDecision或订单；历史数据浏览器行为不变。所有预览均不可执行，Live和自动提交保持关闭。

### Interface impact

新增Algorithm Control公共模型、Protocol、Registry、Service、Controller、Panel和`quant-algorithm-control`入口；未删除或修改现有Market History、Factor、Decision、Risk或Orchestration公共接口。

### Dependency impact

复用现有PySide6和标准库，无第三方依赖增删升级。Algorithm Control只依赖公开Factor/Decision/Risk结果合同、应用安全设置和PySide6；架构测试禁止具体Alpaca、历史SQLite、Execution和tests依赖。

### Configuration or data impact

新增独立schema version 1的运行时JSON控制状态，不修改SQLite schema、环境变量或持久化行情。首次启动只写入四个Locked安全配置及对应Audit，不写凭据。Save/Apply/Restore均产生新版本；没有数据迁移。

### Validation

- 修改前完整`python -m pytest`：151 passed，1项上游`websockets.legacy`弃用警告。
- 目标Algorithm Control与架构测试：23 passed。
- 修改后完整`python -m pytest`：174 passed，1项相同上游弃用警告。
- `python -m compileall -q src tests`：通过。
- `python -m pip check`：`No broken requirements found`。
- `git diff --check`：通过；只有Windows LF/CRLF提示。
- 禁止依赖/敏感调用搜索：Algorithm Control源码无TradingClient、submit_order、具体Alpaca Provider、SQLite Store或Execution Provider引用。
- Offscreen PySide6烟雾测试实例化六页控制中心，验证Factor/Decision为空、Risk四项Locked、Live/自动提交关闭、Pipeline不可运行。

### Results

完整测试174项通过。通用配置生命周期、重启持久化、原子写入、依赖缺失、Locked安全、版本比较/恢复、Preview不可执行、审计、GUI和架构边界均有回归证据。没有访问真实网络、账户或任何订单接口。

### Documentation

新增Algorithm Control模块文档和Accepted ADR-0007；Compass升级version 6并增加INTENT-010/ASM-009；主要架构升级version 4；同步AGENTS、README、模块图、依赖规则、文档/ADR索引、PROJECT_STATE、CHANGELOG及本记录。

### Rollback

删除`src/quant_trading/algorithm_control`、对应测试、模块文档和ADR-0007；撤销`pyproject.toml`入口、错误代码及本条列出的文档增量；必要时手动删除被Git忽略的`runtime/algorithm_control/control_state.json`。历史行情SQLite、Factor/Decision/Risk合同均无需迁移。不得用reset或强制checkout覆盖其他未提交工作。

### Open issues

- 生产Factor、Decision和数值Risk算法均Not implemented，因此生产Preview和Pipeline Dry Run不可运行；这是安全边界，不是伪装成完成的功能。
- 实际物理显示器人工视觉验收未执行；offscreen GUI烟雾测试通过。
- 配置历史与Audit的长期保留/清理仍受Compass DEC-001约束，未擅自引入不可逆删除规则。
- 原有KI-0004至KI-0007保持不变。

### Approval

用户明确授权创建Algorithm Control主要模块、GUI、配置/审计持久化、测试和文档。本次未新增算法公式、决策规则、风险数值、账户或执行能力；未访问外部交易服务；未提交Paper/Live订单；未执行commit、push、pull、merge、rebase、reset或Git历史修改。

## EDIT-20260714-026

### Date
2026-07-14 15:11:01 -07:00。

### Request
建立统一的新思想准入、架构归属、能力权限、公共合同、冲突检测、默认关闭、Pipeline运行前验证、GUI Conflict Center、迁移/回滚/废弃和审计机制。

### Scope
本次扩展现有Algorithm Control和治理文档；不包含Factor公式、Decision规则、数值Risk规则、Order/Execution、账户连接、Paper订单或Live能力。

### Pre-change state
已有Compass、主要架构、ADR、模块边界、Risk Gate、组件Registry、Draft/Saved/Active配置和架构import测试；但没有Proposal准入模板、统一Owner/Capability/Contract声明、独立功能生命周期、注册冲突状态、Pipeline Admission或GUI Conflict Center。修改前完整测试为174 passed、1项上游弃用警告。

### Files changed
- Added: `src/quant_trading/algorithm_control/admission_models.py`, `admission_service.py`, `capabilities.py`, `contracts.py`, `proposal_registry.py`, `tests/unit/algorithm_control/test_change_admission.py`, `docs/proposals/README.md`, `docs/proposals/PROPOSAL_TEMPLATE.md`, `docs/decisions/ADR-0008-change-admission-and-conflict-prevention.md`.
- Modified: `AGENTS.md`, `PROJECT_COMPASS.md`, `README.md`, `CHANGELOG.md`, `docs/INDEX.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/MODULE_MAP.md`, `docs/architecture/DEPENDENCY_RULES.md`, `docs/decisions/README.md`, `docs/modules/algorithm-control-gui.md`, `docs/project/PROJECT_STATE.md`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`, `src/quant_trading/algorithm_control/__init__.py`, `configuration_service.py`, `controller.py`, `models.py`, `registry.py`, `storage.py`, `system_components.py`, `ui/component_panel.py`, `ui/main_panel.py`, `validation_service.py`, `tests/architecture/test_algorithm_control_boundaries.py`, `tests/unit/algorithm_control/test_configuration_service.py`, `test_parameter_editor.py`, `test_preview_and_controller.py`, `test_registry_and_validation.py`.
- Deleted: none.
- Renamed: none.

### Implementation
- 建立Proposal状态、OwnerLayer、Responsibility、Capability、FeatureState、Conflict Assessment、Blast Radius、ActivationEvidence和Change Impact类型；AI建议不能伪装为用户批准。
- 建立唯一职责Owner矩阵和每层Capability白名单；组件注册拒绝重复ID、错误Owner、越权能力、未知合同、非Execution执行权限和未授权Live能力，失败组件状态为INVALID且不可运行。
- 建立版本化公共合同声明和兼容性检查；主要合同登记为Implemented或Planned，major变化要求Migration、类型变化要求Adapter。
- 将实现/配置/激活分离：新组件默认REGISTERED/disabled，Preview、Dry Run、Paper、Live资格与Active需要逐级证据；Locked系统安全保持Active。
- Pipeline Admission在运行前检查Factor/Decision/Risk完整性、Locked安全、多个Decision/Execution Primary、未决Proposal和Live/自动提交；阻断冲突返回Conflict ID、严重度、影响组件、原因、建议和批准要求。
- GUI增加只读Conflict Center；Dry Run只在Admission允许时启用。多个Decision不会平均/投票/随机选择；多个Risk仍由现有Risk Engine采用最严格结果。
- Proposal文档规定Idea至Activation、迁移对比、回滚和废弃流程；Accepted ADR-0008记录长期架构决定。

### Reason
将“代码已经写好”与“用户已经批准运行或交易”严格分开，并在新思想进入运行路径前自动发现职责、权限、合同、配置、并行组件和安全冲突。

### Behavior impact
算法控制GUI新增Conflict Center。当前因没有生产Factor/Decision/数值Risk组件而明确显示Pipeline BLOCKED；没有既有可执行行为被移除，因为执行模块仍不存在。历史数据浏览器不变。

### Interface impact
扩展`ComponentMetadata`和配置记录，新增Admission/Capability/Contract/Proposal公共类型；未修改Market History、FactorSnapshot、TradeIntent或RiskDecision字段语义。旧控制JSON缺少新字段时通过兼容默认读取。

### Dependency impact
无第三方依赖增删升级。新代码只使用Python标准库、现有应用设置和Algorithm Control公共模型；未引入Alpaca Trading、SQLite或Execution依赖。

### Configuration or data impact
Algorithm Control JSON仍使用schema version 1并兼容旧字段；新保存记录包含FeatureState和ActivationEvidence。没有SQLite schema、环境变量、凭据、Market Bar或账户数据变化；没有数据迁移。

### Validation
- 修改前完整`python -m pytest -q`：174 passed，1项既有`websockets.legacy`弃用警告。
- 中间完整测试：179 passed、1 failed；失败为旧字符串扫描把Capability元数据`submit_orders`误判成执行调用，已改成AST import检查。
- 中间完整`python -m pytest -q`：180 passed，1项相同上游弃用警告；补充启用证据与Conflict Center断言后执行最终验证。
- `python -m compileall -q src tests`、`python -m pip check`、`git diff --check`在最终验证阶段执行，结果见Results。
- 所有自动测试使用Fake/临时目录；未访问真实网络、账户或订单接口。

### Results
最终完整`python -m pytest -q`：183 passed，1项既有`websockets.legacy`弃用警告；Admission/Architecture针对性测试39 passed；`python -m compileall -q src tests`通过；`python -m pip check`返回`No broken requirements found`；`git diff --check`通过并仅报告Windows LF/CRLF转换提示。没有访问网络、Alpaca/Fidelity账户或任何订单端点。

### Documentation
Compass升级version 7并增加INTENT-011/ASM-010；主要架构升级version 5并增加Admission、Ownership Matrix、Capability优先级和迁移规则；新增Proposal指南/模板及ADR-0008；同步AGENTS、README、索引、依赖、模块、项目状态和CHANGELOG。

### Rollback
撤销本记录Files changed中的Admission增量、Conflict Center、Proposal/ADR-0008和文档更新；恢复旧Algorithm Control模型/配置读取。保留其他未提交工作，不使用reset或强制checkout。现有Market SQLite无需迁移；控制JSON可恢复旧读取器，但将失去实现/激活分离保护。

### Open issues
- 当前没有生产Factor、Decision或数值Risk组件，因此Pipeline保持BLOCKED；这是真实安全状态。
- Proposal持久历史以Markdown为准；运行时ProposalRegistry是内存索引，GUI不编辑或批准Proposal。
- 物理显示器人工视觉验收尚未执行；offscreen GUI自动测试覆盖7个页签和Conflict ID。
- 既有KI-0004至KI-0007以及数据清理开放决定不变。

### Approval
用户明确授权本次Change Admission主要治理扩展、Proposal目录、Capability/Contract/Feature State、Conflict Center和测试。本次未添加交易语义或执行能力，Live与自动提交保持关闭；未commit、push、pull、merge、rebase、reset或修改Git历史。

## EDIT-20260714-027

### Date
2026-07-14 15:25:34 -07:00。

### Request
为所有未来任务增加FAST、STANDARD、DEEP执行模式，要求采用最低安全模式，并禁止局部任务自动扩展为全项目审计。

### Scope
仅修改仓库工作流程说明和Proposal准入说明；不修改代码、配置、公共合同、数据库、GUI、交易语义或安全默认值。

### Pre-change state
现有流程要求所有重要任务读取完整Compass/架构并进行较广审查，但没有根据任务规模区分检查、测试和文档更新强度。

### Files changed
- Added: none.
- Modified: `AGENTS.md`, `docs/development/WORKFLOW.md`, `docs/proposals/README.md`, `logs/EDIT_LOG.md`.
- Deleted: none.
- Renamed: none.

### Implementation
新增FAST、STANDARD、DEEP的适用范围、必读内容、测试强度和文档更新边界；要求实施前报告Task mode、Primary module、Expected files、Tests和Documents；要求FAST/STANDARD发现严重架构、权限、合同、迁移、金融语义或交易安全冲突时停止并建议升级DEEP，而不是静默扩大任务。

### Reason
让小型修改保持快速、局部和可预测，同时确保真正高影响变更仍接受完整架构与安全审查。

### Behavior impact
仅改变未来AI/开发者的任务执行流程；程序运行、行情、算法合同、风险和交易行为不变。

### Interface impact
无公共代码接口变化。

### Dependency impact
无依赖变化。

### Configuration or data impact
无配置、数据库或运行数据变化。

### Validation
检查三个文档均包含模式分类和升级规则；执行`git diff --check`。

### Results
文档一致性检查通过；`git diff --check`结果见本任务最终报告。未运行pytest，因为没有程序行为或代码变化。

### Documentation
更新仓库指令、开发流程和重要Proposal与任务模式的关系；按照本任务规则未更新Compass、主要架构、ADR、PROJECT_STATE或CHANGELOG。

### Rollback
撤销上述三个工作流程文档中的Task Mode段落和本条Edit记录对应增量；不要改写或删除旧日志。

### Open issues
无。未来任务仍需根据实际影响选择最低安全模式，不能只根据用户使用的标签机械分类。

### Approval
用户明确提供并要求采用本任务模式协议；未执行commit、push或Git历史修改。

## EDIT-20260714-028

### Date
2026-07-14 16:04:32 -07:00.

### Request
Use one central database to preserve each stock's Market Data, meaningful daily/historical Factor results, and all Factor calculation attempts without allowing meaningless duplicate data growth.

### Scope
Reuse the existing local SQLite file, add central schema management and independent Factor-history persistence, optionally connect it to the existing orchestration contract, and update tests/governance. No Factor formula, historical backfill, Decision/Risk rule, GUI change, account, order or execution capability is included.

### Pre-change state
`runtime/data/market_history.sqlite3` stored Market Bars, Coverage and Fetch History. Factor contracts/engine existed but explicitly had no persistence; ordinary Pipeline execution was inactive because no production Factor or Decision Policy exists. The previous complete suite contained 183 passing tests and one upstream deprecation warning.

### Files changed
- Added: `src/quant_trading/persistence/__init__.py`, `sqlite_database.py`, `factor_sqlite_store.py`; `src/quant_trading/factors/storage_models.py`; `tests/unit/factors/test_sqlite_factor_store.py`; `docs/modules/central-persistence.md`; `docs/proposals/PROPOSAL-001-central-sqlite-factor-history.md`; `docs/decisions/ADR-0009-central-sqlite-factor-history.md`.
- Modified: `src/quant_trading/market_history/storage/sqlite_store.py`, `src/quant_trading/factors/__init__.py`, `errors.py`, `interfaces.py`, `src/quant_trading/orchestration/analysis_decision_pipeline.py`, `src/quant_trading/diagnostics.py`, `src/quant_trading/error_codes.py`, `tests/unit/market_history/test_sqlite_store.py`, `tests/unit/test_diagnostics.py`, `tests/integration/test_analysis_decision_pipeline.py`, `tests/architecture/test_dependency_boundaries.py`, `PROJECT_COMPASS.md`, `README.md`, `CHANGELOG.md`, `docs/INDEX.md`, `docs/architecture/OVERVIEW.md`, `MODULE_MAP.md`, `DEPENDENCY_RULES.md`, `docs/decisions/README.md`, `docs/modules/README.md`, `factors.md`, `analysis-decision-pipeline.md`, `market-history.md`, `docs/project/PROJECT_STATE.md`, `docs/proposals/README.md`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`.
- Deleted: none.
- Renamed: none.

### Implementation
- Added central SQLite schema version 1, keeping the existing path and Market tables while adding `schema_migrations`, `factor_snapshots`, `factor_results`, and `factor_calculation_runs`.
- Added typed Factor Store Protocol, calculation-run records and a concrete infrastructure adapter outside the pure Factor layer.
- Preserved Decimal/int/bool/string values, Factor version/parameters/status/quality flags, UTC source bounds, adjustment/feed and configuration/source/content fingerprints.
- Exact semantic recalculations reuse a canonical snapshot/result; every run remains separately recorded with correlation/status/error fields.
- Added optional Orchestration Store injection so a calculated snapshot is persisted before Decision evaluation. No Store means prior behavior is unchanged.
- Market Store now delegates only connection and schema initialization to the central infrastructure boundary; its Bar/Coverage/Fetch query logic remains unchanged.

### Reason
The user needs durable, reproducible Factor history and Debug traceability without repeated clicks or identical reruns copying the same result payload indefinitely. One physical file is convenient, while independent Store contracts prevent a central database from becoming a coupled business-logic module.

### Behavior impact
On the next normal Store initialization, the existing SQLite file receives additive Factor-history tables without moving or deleting Market data. A future explicitly configured Factor Pipeline can persist results; current GUI usage creates no Factor rows because no production Factor exists. Trading behavior is unchanged.

### Interface impact
Added `FactorSnapshotStore`, `FactorCalculationRun`, `FactorCalculationStatus`, `CentralSQLiteDatabase`, and `SQLiteFactorSnapshotStore`. `AnalysisDecisionRequest` gains an optional correlation ID and `AnalysisDecisionPipeline` gains an optional Store constructor argument; existing callers remain compatible.

### Dependency impact
No third-party dependency was added. Concrete `sqlite3` remains in infrastructure; architecture tests prevent pure Factor, GUI, Decision, Risk and Execution layers from crossing the new boundary.

### Configuration or data impact
The default path remains `runtime/data/market_history.sqlite3`. Schema changes are additive and idempotent; existing Market rows are untouched. The real ignored runtime file is upgraded on its next application initialization, not modified by the automated temporary-database tests. No automatic deletion or historical Factor backfill is performed.

### Validation
- Target Store/Market/Pipeline tests: 26 passed.
- Initial architecture suite: 9 passed, 1 failed because the first concrete adapter location imported SQLite inside the Factor package.
- After the boundary correction, architecture plus target tests: 36 passed.
- Complete `python -m pytest -q`: 192 passed, one existing upstream `websockets.legacy` deprecation warning.
- `python -m compileall -q src tests`: passed.
- `python -m pip check`: `No broken requirements found`.
- `git diff --check`: passed; only expected Windows LF/CRLF conversion warnings.

### Results
Central schema initialization, legacy Market-row preservation, Factor typed round-trip, version/dimension isolation, exact-result deduplication, all-run audit, controlled failure audit, transaction rollback, optional Pipeline persistence and dependency boundaries are verified. No network, account or order endpoint was accessed.

### Documentation
Added approved PROPOSAL-001, Accepted ADR-0009 and central persistence module documentation; Compass advanced to version 8 with INTENT-012/ASM-011; canonical architecture advanced to version 6; synchronized README, indexes, module docs, Project State, Changelog, Bug Log and this Edit entry.

### Rollback
Stop injecting `FactorSnapshotStore` and restore the prior Market-only schema initializer. Do not automatically drop the additive Factor tables because they may contain user history. Existing Market tables remain readable; no destructive Git or database rollback is required.

### Open issues
- No production Factor formula exists, so ordinary use does not yet create Factor values or backfill past dates.
- Market Bar `available_at_utc` and point-in-time adjustment semantics remain open before a production Factor can safely consume stored history.
- Automatic retention/deletion thresholds remain open under Compass DEC-001; this task intentionally preserves Factor history and performs no deletion.

### Approval
The user explicitly approved Scheme A on 2026-07-14: reuse the existing SQLite database and preserve Factor history under the proposed deduplication/audit rules. No Live, automatic submission, Paper order, account or execution authority was requested or added. No commit, push, pull, merge, rebase or Git history operation was performed.

## EDIT-20260714-029

### Date
2026-07-14 16:13:51 -07:00.

### Request
When a new request resembles earlier work that the user may not remember, proactively remind the user and ask whether the existing idea should be extended or otherwise changed.

### Scope
Extend the existing requirement-interpretation and change-admission governance with an existing-work reminder protocol. This task does not change application code, configuration, database contents, algorithms, GUI behavior, trading semantics, or activation state.

### Pre-change state
The repository already required ownership and conflict checks and asked whether an existing component owned a responsibility, but it did not explicitly require a user-facing reminder that explains verified prior work and asks how materially overlapping work should relate to it.

### Files changed
- Added: none.
- Modified: `AGENTS.md`, `PROJECT_COMPASS.md`, `docs/development/REQUIREMENT_INTERPRETATION.md`, `docs/proposals/README.md`, `logs/EDIT_LOG.md`.
- Deleted: none.
- Renamed: none.

### Implementation
- Required repository evidence to be checked when a request appears materially similar to existing code, configuration, module ownership, Active Intent, Proposal, ADR, or approved behavior.
- Standardized the reminder content: existing work, verified status, overlap, difference, and the smallest recommended reuse path.
- Required the user's choice before material extension, replacement/supersession, or coordinated parallel implementation; leaving existing work unchanged remains an explicit option.
- Exempted trivial private implementation details and clarified that an earlier AI suggestion is not user approval.
- Added Compass assumption ASM-012 and active intent INTENT-013 without changing Stable Core.

### Reason
The protocol helps the user recover project context, avoids duplicate systems and accidental replacement, and keeps product authority with the user even when earlier work is not remembered.

### Behavior impact
Future AI development conversations must surface meaningful overlap before materially changing related existing work. Runtime application behavior is unchanged.

### Interface impact
No software public interface changed.

### Dependency impact
No dependency changed.

### Configuration or data impact
No configuration, schema, persistent data, or runtime data changed.

### Validation
Searched the governance documents for the new reminder requirements, reviewed the affected diff, and executed `git diff --check`. No pytest run was required because no executable code or runtime behavior changed.

### Results
The reminder, evidence/status explanation, user-choice requirement, trivial-detail exemption, and AI-suggestion safeguard are consistently recorded in the repository workflow, Compass, interpretation protocol, and Proposal admission rules.

### Documentation
Updated the repository instructions, Compass evolving state, detailed requirement-interpretation protocol, Proposal admission guidance, and this append-only Edit Log entry. No architecture, Project State, ADR, module document, or Changelog update was needed because application structure and behavior did not change.

### Rollback
Remove only the existing-work reminder additions, ASM-012, INTENT-013, and the corresponding version increment. Preserve this historical Edit Log entry; if correction is needed, append a new record instead of rewriting history.

### Open issues
None. Future agents must distinguish credible repository evidence from a merely similar phrase or an unapproved historical AI suggestion.

### Approval
The user explicitly requested this long-term reminder behavior. No commit, push, pull, merge, rebase, or Git-history operation was performed.

## EDIT-20260714-030

### Date
2026-07-14 16:27:10 -07:00.

### Request
Create two same-level layers for simulated trading and real-money trading. Future testing will occur primarily in the simulated layer, but no contents or trading behavior should be added yet.

### Scope
Create empty, disabled `quant_trading.execution.paper` and `quant_trading.execution.live` sibling package boundaries, protect them with architecture tests, and synchronize the approved architecture/governance state. No account, position, order, fill, Provider, broker client, credential, endpoint, GUI, configuration, Risk rule, execution behavior or activation is included.

### Pre-change state
`ALPACA_PAPER` existed as a tested safe target label, Live and automatic submission were disabled, and Risk exposed a type-distinct future gate. Execution was documented as Planned/Not implemented and no `quant_trading.execution` package existed.

### Files changed
- Added: `src/quant_trading/execution/__init__.py`, `src/quant_trading/execution/paper/__init__.py`, `src/quant_trading/execution/live/__init__.py`, `tests/architecture/test_execution_environment_boundaries.py`, `docs/modules/execution-environments.md`, `docs/proposals/PROPOSAL-002-paper-live-execution-boundaries.md`, `docs/decisions/ADR-0010-paper-live-execution-boundaries.md`.
- Modified: `AGENTS.md`, `PROJECT_COMPASS.md`, `README.md`, `CHANGELOG.md`, `docs/INDEX.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/MODULE_MAP.md`, `docs/architecture/DEPENDENCY_RULES.md`, `docs/decisions/README.md`, `docs/modules/README.md`, `docs/project/PROJECT_STATE.md`, `docs/proposals/README.md`, `logs/EDIT_LOG.md`.
- Deleted: none.
- Renamed: none.

### Implementation
- Established one Execution ownership parent containing two sibling namespaces: `paper` and `live`.
- Kept all three package initializers declaration-only: one safety docstring each, no imports, interfaces, registration or executable statements.
- Added architecture tests proving the two children are siblings, contain no runtime implementation and do not import one another.
- Recorded both boundaries as disabled with `execution_allowed=false` and `live_allowed=false`; future contents remain subject to separate Proposal and approval.
- Added accepted ADR-0010, implemented-disabled PROPOSAL-002, Compass INTENT-014/ASM-013 and updated canonical architecture version 7.

### Reason
Explicit Paper/Live separation gives future simulated testing a clear home without allowing experimental Paper work, credentials or state to drift into a real-money boundary. An empty structure preserves the user's requested sequencing without inventing execution semantics.

### Behavior impact
No application runtime behavior changes. Importable namespace identity now exists, but neither package can connect to an account, construct an order or submit anything.

### Interface impact
New package paths exist, but they intentionally export no public software interface. Existing contracts and callers are unchanged.

### Dependency impact
No third-party or runtime dependency was added. Both new sibling packages have zero imports and are forbidden from importing one another at this stage.

### Configuration or data impact
No configuration, credential name, endpoint, database schema, persistent data or runtime file changed. `ALPACA_PAPER` remains a target label; Live and automatic submission remain false.

### Validation
- Target execution/dependency architecture tests: 10 passed.
- Complete `python -m pytest -q`: 195 passed with one existing upstream `websockets.legacy` deprecation warning.
- `python -m compileall -q src tests`: passed.
- `python -m pip check`: `No broken requirements found`.
- `git diff --check`: passed; only expected Windows LF/CRLF conversion warnings.
- Reviewed the new source files to confirm they contain docstrings only.

### Results
The two same-level boundaries exist and are independently identifiable, empty, disabled and structurally tested. Prior Market Data, SQLite, Factor/Decision/Risk, GUI and safety behavior remains verified. No network, account or order endpoint was accessed.

### Documentation
Added the Execution environment module document, approved Proposal and Accepted ADR; updated Compass, canonical architecture, module/dependency indexes, Project State, README, Changelog, repository instructions and this Edit Log.

### Rollback
Remove the three declaration-only execution package files, the new architecture test and the new module/Proposal/ADR documents, then revert only the corresponding INTENT-014/ASM-013 and architecture/index references. No database, configuration or runtime rollback is needed. Preserve this Edit Log history or append a correction.

### Open issues
- Paper account/order contracts and behavior are still Not implemented and require a future approved Proposal.
- Live credentials, endpoint, protections and behavior are still Not implemented and require separate high-risk approval.
- No new credible defect was discovered during this task; `logs/BUG_LOG.md` was therefore not modified.

### Approval
The user explicitly approved creating only the two sibling layers and explicitly deferred all contents. No Paper or Live order authority was granted. No commit, push, pull, merge, rebase, reset or Git-history operation was performed.

## EDIT-20260714-031

### Date
2026-07-14 16:54:47 -07:00.

### Request
Implement approved Scheme A: let the user create, modify and save Factor calculation behavior in the GUI through a safe design, and let Decision configuration select which Factor versions are inputs.

### Scope
Add restricted expression Factor definitions/calculation, immutable local definition versions, disabled-by-default component registration, Factor authoring GUI, exact Decision Factor-version selection, validation, tests and documentation. This does not add an approved financial Factor, Decision rule, threshold, position rule, Risk value, Market History-to-Factor runtime adapter, Pipeline activation, account access, Paper/Live order or execution behavior.

### Pre-change state
Factor/Decision contracts and a generic Algorithm Control Center existed, but production component lists were empty. The GUI could edit metadata-driven parameters only; it intentionally had no Factor definition editor. Decision configuration had static dependency metadata but no saved user selection of exact Factor versions. Central SQLite Factor-result history existed but had no active production calculator.

### Files changed
- Added: `src/quant_trading/factors/definitions.py`, `src/quant_trading/factors/expression_language.py`, `src/quant_trading/factors/expression.py`, `src/quant_trading/algorithm_control/factor_definition_store.py`, `src/quant_trading/algorithm_control/factor_definition_service.py`, `src/quant_trading/algorithm_control/ui/factor_authoring_panel.py`, `tests/unit/factors/test_safe_expression_factor.py`, `tests/unit/algorithm_control/test_factor_definition_authoring.py`, `docs/modules/factor-authoring.md`, `docs/proposals/PROPOSAL-003-safe-factor-authoring-and-decision-selection.md`, `docs/decisions/ADR-0011-restricted-factor-authoring.md`.
- Modified: `AGENTS.md`, `PROJECT_COMPASS.md`, `README.md`, `CHANGELOG.md`, `docs/INDEX.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/MODULE_MAP.md`, `docs/architecture/DEPENDENCY_RULES.md`, `docs/decisions/README.md`, `docs/modules/README.md`, `docs/modules/factors.md`, `docs/modules/trading-decision.md`, `docs/modules/algorithm-control-gui.md`, `docs/project/PROJECT_STATE.md`, `docs/proposals/README.md`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`, `src/quant_trading/factors/__init__.py`, `src/quant_trading/factors/errors.py`, `src/quant_trading/factors/interfaces.py`, `src/quant_trading/algorithm_control/app.py`, `src/quant_trading/algorithm_control/configuration_service.py`, `src/quant_trading/algorithm_control/controller.py`, `src/quant_trading/algorithm_control/models.py`, `src/quant_trading/algorithm_control/storage.py`, `src/quant_trading/algorithm_control/validation_service.py`, `src/quant_trading/algorithm_control/ui/component_panel.py`, `src/quant_trading/algorithm_control/ui/main_panel.py`, `tests/architecture/test_dependency_boundaries.py`, `tests/unit/algorithm_control/test_configuration_service.py`, `tests/unit/algorithm_control/test_parameter_editor.py`.
- Deleted: none.
- Renamed: none.

### Implementation
- Added an immutable `FactorDefinition` contract with Factor identity, version, expression, minimum observations, units, missing-input policy, typed Decimal parameters, actor, time and change reason.
- Added a deliberately small expression language: approved OHLCV/VWAP/trade-count fields, arithmetic and `latest`/`lag`/aggregation/absolute functions. AST validation rejects imports, attributes, indexing, comprehensions, assignment, unknown fields/functions and malformed calls; no `eval`, `exec`, `compile` or `__import__` path exists.
- Added a Decimal-based Factor calculator that returns explicit `INSUFFICIENT_DATA`, `MISSING_INPUT` or `CALCULATION_ERROR` states without fabricating zero.
- Added atomic ignored JSON definition persistence and version-specific `ComponentMetadata`; each new version is `REGISTERED`, disabled, non-executing and not Live-eligible.
- Added an Algorithm Control Factor authoring tab with definition history and validation/save controls. Loading an older version and saving creates a new version rather than overwriting history.
- Added versioned `selected_factor_ids` to Decision configuration, GUI checkboxes, persistence, validation and comparison. Unknown/non-Factor selections are rejected, and enabled Decisions require selected Factors to be active.
- Kept syntax validation as a public Factor contract and calculation inside the Factor layer; Algorithm Control never evaluates market values.
- Recorded and fixed BUG-20260714-009, a temporary GUI wrapper compatibility regression found by the existing smoke test.

### Reason
Scheme A preserves the user's direct control over calculation behavior while avoiding arbitrary Python execution and preserving Factor/GUI/Decision/Risk/Execution boundaries. Immutable exact-version references keep later results reproducible and rollback-friendly.

### Behavior impact
The Algorithm Control Center now has a Factor create/modify tab. Saved definitions appear as disabled Factor versions. A registered Decision component can display and save exact Factor-version selections. Saving or selecting does not calculate cached Market Data, create a decision, or submit an order.

### Interface impact
Added public Factor definition/language/calculator contracts and a `FactorDefinitionStore` Protocol. Added backward-compatible defaulted `selected_factor_ids` fields to Draft/Saved configuration and corresponding optional controller/service update input. Existing JSON loads without the new field as an empty selection.

### Dependency impact
No third-party dependency changed. Algorithm Control depends only on public Factor definition/expression-language contracts, not concrete Factor calculation internals. Architecture tests enforce this boundary and prohibit dynamic Python execution calls.

### Configuration or data impact
Authored definitions are stored atomically at ignored `runtime/algorithm_control/factor_definitions.json`. Algorithm control-state JSON gains an optional `selected_factor_ids` field and remains backward-compatible. No SQLite schema, Market data, credential, endpoint, account or order data changed.

### Validation
- Target safe-expression, authoring, configuration, GUI and architecture tests: 32 passed, then 47 passed after adding the compatibility fix and expanded checks.
- Complete `.\.venv\Scripts\python.exe -m pytest -q`: 216 passed with one existing upstream `websockets.legacy` deprecation warning.
- `.\.venv\Scripts\python.exe -m compileall -q src tests`: passed.
- `.\.venv\Scripts\python.exe -m pip check`: `No broken requirements found`.
- `git diff --check`: passed; only expected Windows LF/CRLF conversion warnings.

### Results
Scheme A is implemented and verified at authoring/configuration/calculator-contract level. Arbitrary Python is rejected, definitions and selections survive versioned persistence, GUI catalog/selection behavior is covered offscreen, and all prior tests continue to pass. No network or order endpoint was accessed.

### Documentation
Added approved PROPOSAL-003, Accepted ADR-0011 and Factor-authoring module documentation; Compass advanced to version 11 with ASM-014/INTENT-015; canonical architecture advanced to version 8; synchronized repository instructions, README, indexes, module docs, Project State, Changelog, Bug Log and this Edit entry.

### Rollback
Hide/remove the authoring tab and Decision selector, stop registering stored definitions, and revert the optional selection field while retaining backward-compatible reads. Preserve ignored `factor_definitions.json` for recovery and do not delete central SQLite Factor history. No destructive Git or database rollback is required.

### Open issues
- The GUI validates syntax but does not yet run a real Market Data calculation preview.
- Market History-to-Factor availability and point-in-time adjustment semantics remain open, so authored Factors are not automatically run against cached Bars.
- No production Decision Policy exists; selecting Factors cannot produce a TradeIntent.
- Only `return_missing_status` is supported for missing inputs.

### Approval
The user explicitly approved recommended Scheme A. This approval covers restricted Factor authoring and Decision Factor selection only; it does not approve arbitrary Python, a financial formula, a Decision rule, Factor activation, Paper/Live execution, account access or order submission. No commit, push, pull, merge, rebase, reset or Git-history operation was performed.
## EDIT-20260714-032

### Date
2026-07-15T00:34:05Z

### Request
将之前说明的六个阶段整理成一份完整修改计划书并保存，供用户稍后决定是否实施。

### Scope
本次仅创建规划提案，覆盖 Factor 版本生命周期、Factor 验证工作台、Decision Policy 编辑、冲突与 Risk Gate、独立 Execution 控制界面以及完整测试验收。明确记录当前已有能力、未实现能力、审批关口和回滚方式。不修改程序代码、配置、数据库、交易语义或运行状态。

### Pre-change state
`PROPOSAL-003` 已记录并实现为 disabled 状态的受限 Factor 编辑和 Decision 精确 Factor 版本选择，但尚无统一后续计划覆盖归档、真实数据预览证据、Decision 规则编辑和独立 Execution GUI。

### Files changed
- Added: `docs/proposals/PROPOSAL-004-factor-lifecycle-decision-authoring-and-execution-control.md`
- Modified: `docs/proposals/README.md`, `logs/EDIT_LOG.md`
- Deleted: None
- Renamed: None

### Implementation
创建 `PROPOSAL-004`，把六阶段目标、当前基线、职责边界、每阶段范围/验收/回滚、公共合同、权限矩阵、冲突评估、影响范围和审批记录写入可持续维护的提案；在提案索引中登记为 Draft。

### Reason
保存用户意图并防止未来将 Factor 管理、Decision 逻辑与 Execution 权限混在一起，同时避免重复实现已经存在的 Scheme A 能力。

### Behavior impact
None. 计划书不会启用 Factor、Decision、Risk、Paper 或 Live 行为。

### Interface impact
None.

### Dependency impact
None.

### Configuration or data impact
None. 未修改运行配置、Factor 定义、SQLite Schema 或已保存数据。

### Validation
检查提案模板、现有 `PROPOSAL-003`、提案索引和 Git 状态；检查新增文档的必需章节、状态、链接、六阶段范围和安全边界；检查 Git diff。

### Results
计划已保存为 `DRAFT`，明确区分已实现与 Planned，并明确“保存计划”不构成实施或交易授权。

### Documentation
新增完整计划书并更新提案索引；未更新 Compass、架构、Project State 或 CHANGELOG，因为项目实际行为没有变化。

### Rollback
删除尚未被实施或引用的 `PROPOSAL-004` 并撤销提案索引条目；若保留历史，则将其标记为 `REJECTED` 或 `ROLLED_BACK` 并追加更正日志。不得改写本条历史记录。

### Open issues
Factor 永久删除条件、Bar 可用时间/复权语义、Decision action/条件/缺失数据/多策略语义，以及任何 Paper/Live 执行能力仍需用户逐项决定。

### Approval
用户明确授权创建并保存计划书；没有授权实施六个阶段、删除 Factor、制定交易规则或启用任何订单能力。

## EDIT-20260714-033

### Date
2026-07-15T00:43:27Z

### Request
将当前项目提交并推送到 GitHub，同时保存当前版本行为、编辑目的和当前关注目标作为版本记录。

### Scope
为当前累积且已分别记录的实现创建发布检查点，补充一份只追加式版本历史，更新 Compass 的已验证工作树状态和 Project State 的当前关注方向；随后完整验证、检查密钥和忽略文件、提交当前仓库改动并推送 `main`。不启用任何 Factor、Decision、Risk、Paper/Live 或订单行为。

### Pre-change state
`main` 位于 `7b5bd7f`，当前中央 SQLite Factor 历史、空 Paper/Live 边界、Scheme A Factor 编辑、六阶段 Draft 提案及相关治理/测试尚未提交。远程 `origin` 指向 `https://github.com/tony73410/QuantTrading.git`。

### Files changed
- Added: `docs/project/VERSION_HISTORY.md`
- Modified: `docs/INDEX.md`, `PROJECT_COMPASS.md`, `docs/project/PROJECT_STATE.md`, `logs/EDIT_LOG.md`
- Deleted: None
- Renamed: None

### Implementation
新增 `CHECKPOINT-20260714-001`，记录当前用户可见行为、算法/执行状态、架构路径、编辑目的、六阶段 Draft 关注目标、验证证据、限制、安全状态和回滚方式；更新文档索引、Compass 版本/验证状态和 Project State 链接。

### Reason
让用户和未来 AI 不依赖聊天记忆即可理解该 Git 版本实际能做什么、为何存在、尚未实现什么以及下一步关注什么。

### Behavior impact
None. 版本记录和 Git 发布不改变程序运行行为。

### Interface impact
None.

### Dependency impact
None.

### Configuration or data impact
None. `runtime/algorithm_control/`、`runtime/data/`、`runtime/logs/` 和真实环境凭据继续被 Git 忽略。

### Validation
- `\.venv\Scripts\python.exe -m pytest -q`
- `\.venv\Scripts\python.exe -m compileall -q src tests`
- `\.venv\Scripts\python.exe -m pip check`
- `git diff --check`
- 检查 `.env.example`、凭据变量命中、可疑长凭据字面量、Git ignored runtime 路径、分支和远程。

### Results
216 tests passed；1条上游 `websockets.legacy` deprecation warning。Compileall通过；pip check报告无损坏依赖；diff check通过并仅显示Windows换行转换提示；`.env.example`凭据为空，未发现可疑长凭据字面量，运行数据库、日志和算法控制本地状态未进入提交范围。

### Documentation
新增版本检查点并同步文档索引、Compass和Project State。本条记录还将由Git commit正文补充提交级摘要。

### Rollback
使用普通 `git revert <checkpoint-commit>` 创建反向提交；不得reset或改写历史。源码回滚不会删除被忽略的本地运行数据。

### Open issues
Factor真实数据预览、Factor归档/删除、Decision Policy语义、Paper执行和Live保护仍未实现或未批准；详见`PROPOSAL-004`和版本检查点。

### Approval
用户明确授权本次commit和push到GitHub。没有授权Paper/Live订单、真实账户访问、自动提交、交易策略或风险数值。

## EDIT-20260715-001

### Date
2026-07-15T17:44:33Z

### Request
按照已保存的 `PROPOSAL-004` 直接实施全部六个Phase：Factor生命周期、本地证据预览、受限Decision编辑、Factor→Decision→Risk Dry Run、独立Execution状态界面，以及完整测试/文档收尾。

### Scope
实现禁用优先、仅本地、NO EXECUTION的算法工作台。包含不可变Factor/Decision版本、非破坏性Factor归档/弃用/恢复、本地缓存Factor预览和可选中央SQLite结果保存、受限Decision数值规则、Risk门控Dry Run及只读Paper/Live状态。明确不包含Factor永久删除、任意Python、数量/仓位算法、数值Risk限制、账户连接、订单构造、Paper/Live下单或生产激活。

### Pre-change state
项目已有受限Factor定义编辑、精确Factor版本选择、中央SQLite Factor历史合同、Factor/Decision/Risk公共合同和空Paper/Live边界；没有本地Factor运行入口、Decision规则编辑器、可运行Dry Run或Execution状态页。完整基线为216 tests passed及1条上游warning。

### Files changed
- Added: `src/quant_trading/algorithm_control/decision_definition_service.py`, `decision_definition_store.py`, `factor_lifecycle.py`, `ui/decision_authoring_panel.py`, `ui/execution_control_panel.py`, `ui/factor_workbench_panel.py`, `src/quant_trading/decision/definitions.py`, `rule_policy.py`, `src/quant_trading/market_history/local_store_factory.py`, `src/quant_trading/orchestration/algorithm_dry_run.py`, `algorithm_preview_composition.py`, `factor_preview.py`, `tests/unit/algorithm_control/test_decision_authoring.py`, `test_execution_control_metadata.py`, `test_factor_preview_workbench.py`.
- Modified: `src/quant_trading/algorithm_control/app.py`, `controller.py`, `factor_definition_service.py`, `models.py`, `registry.py`, `system_components.py`, `ui/factor_authoring_panel.py`, `ui/main_panel.py`, `validation_service.py`, `src/quant_trading/decision/__init__.py`, `tests/unit/algorithm_control/test_configuration_service.py`, `test_factor_definition_authoring.py`, `test_parameter_editor.py`, `README.md`, `CHANGELOG.md`, `PROJECT_COMPASS.md`, `docs/architecture/OVERVIEW.md`, `MODULE_MAP.md`, `DEPENDENCY_RULES.md`, `docs/modules/algorithm-control-gui.md`, `execution-environments.md`, `factor-authoring.md`, `risk-control.md`, `trading-decision.md`, `docs/project/PROJECT_STATE.md`, `docs/proposals/PROPOSAL-004-factor-lifecycle-decision-authoring-and-execution-control.md`, `docs/proposals/README.md`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`.
- Deleted: None. Two uncommitted, architecture-invalid execution runtime draft files were removed before completion and never became repository changes.
- Renamed: None.

### Implementation
Phase 1增加append-preserving Factor生命周期与Registry同步。Phase 2只加载匹配的本地SQLite Bars，使用保守completed-Bar过滤，后台计算精确Factor版本并可选保存快照。Phase 3增加不可变受限Decision定义和确定性比较Policy，引用精确Factor版本且不包含数量。Phase 4组合本地Factor、Decision与Risk；没有批准Risk规则时停在人工审查。Phase 5只增加Paper/Live声明元数据和只读状态页，Execution包保持空白。Phase 6补齐测试、修复实施中发现的回归/架构漂移，并同步文档。

### Reason
让用户能够保存、管理、预览和组合自己的算法定义，同时维持Factor→Decision→Risk单向边界和“实现不等于激活”的安全原则；任何可能影响资金的执行能力继续缺席。

### Behavior impact
Algorithm Control新增Factor生命周期和本地预览、受限Decision版本编辑、Pipeline Dry Run及Execution状态页。用户组件仍默认禁用；Dry Run只返回分析/Risk结果，不构造或提交订单。

### Interface impact
Additive only: new Factor lifecycle, Decision definition/policy, local preview/dry-run services and optional `PreviewRequest` fields. Existing GUI inspection aliases were preserved. No existing public field meaning changed.

### Dependency impact
No third-party dependency added. GUI remains isolated from concrete Alpaca/SQLite/execution implementations; orchestration uses a narrow local Market Store factory and public contracts. Execution packages remain declaration-only.

### Configuration or data impact
Adds ignored local JSON files `runtime/algorithm_control/factor_lifecycle.json` and `decision_definitions.json`. Optional Factor preview persistence reuses the existing central SQLite schema/path without migration. No existing data is deleted or rewritten.

### Validation
- Baseline: `.venv\Scripts\python.exe -m pytest -q` → 216 passed, 1 upstream warning.
- Final: `.venv\Scripts\python.exe -m pytest -q` → 223 passed, 1 upstream `websockets.legacy` warning.
- `.venv\Scripts\python.exe -m compileall -q src tests`.
- `.venv\Scripts\python.exe -m pip check`.
- `git diff --check`.
- Offscreen PySide6 smoke: 8 tabs, saved local Factor visible, 0 saved Decision definitions in the inspected runtime, 2 execution-status rows.

### Results
All 223 automated tests passed; compileall and dependency integrity passed; diff check found no whitespace errors and only Windows line-ending notices. No test accessed real Alpaca/Fidelity, submitted Paper/Live orders, or enabled Live/automatic submission.

### Documentation
Updated Proposal-004 to `IMPLEMENTED_DISABLED`, Compass v13, canonical architecture v9, Project State, README, CHANGELOG, proposal index, dependency/module documents, Bug Log and this append-only Edit Log.

### Rollback
Revert this logical change as one future Git revert after it is committed. Runtime definitions/lifecycle JSON and optional Factor history are ignored local user data and should be retained; disabling/removing the new GUI composition restores previous authoring-only behavior without deleting that data. Do not reset or rewrite history.

### Open issues
Exact exchange-calendar Bar availability and point-in-time adjusted-data semantics remain unresolved for historical simulation/backtesting. Position sizing, portfolio context, numerical Risk limits, Decision/Risk persistence, Paper execution and Live execution remain Not implemented. Physical multi-monitor GUI QA remains a known manual limitation.

### Approval
User explicitly instructed implementation of all six saved phases. This did not authorize permanent Factor deletion, arbitrary Python, financial parameter selection, Paper/Live order submission, account access, or activation of any component.

## EDIT-20260715-002

### Date
2026-07-15T18:01:02Z

### Request
创建一个简单的主要GUI，作为其他所有GUI功能的统一入口；以后新增独立功能时也应在该Main GUI中添加入口。

### Scope
新增一个无业务逻辑的桌面主控制台，目前登记“股票历史数据浏览器”和“算法控制中心”两个按钮，并以独立进程启动。增加直观的根包/console启动入口、可信目标验证、架构保护和测试。未合并现有窗口，未添加行情、Factor、Decision、Risk、账户或交易行为。

### Pre-change state
用户必须记住并分别运行`quant_trading.market_history`和`quant_trading.algorithm_control`命令；没有统一GUI入口或未来GUI登记规则。工作区包含上一项已完成但尚未提交的六阶段修改，本次在其上局部追加且未覆盖。

### Files changed
- Added: `src/quant_trading/__main__.py`, `src/quant_trading/launcher/__init__.py`, `launcher/__main__.py`, `launcher/app.py`, `tests/unit/launcher/test_main_launcher.py`, `docs/modules/main-launcher.md`.
- Modified: `pyproject.toml`, `README.md`, `AGENTS.md`, `PROJECT_COMPASS.md`, `docs/architecture/OVERVIEW.md`, `MODULE_MAP.md`, `DEPENDENCY_RULES.md`, `docs/modules/README.md`, `docs/project/PROJECT_STATE.md`, `CHANGELOG.md`, `tests/architecture/test_dependency_boundaries.py`, `logs/EDIT_LOG.md`.
- Deleted: None.
- Renamed: None.

### Implementation
建立不可变`LaunchTarget`可信目录和`MainLauncherWindow`，根据目录生成按钮；使用`QProcess.startDetached`和当前Python解释器直接启动已登记模块，不使用shell，不接受用户输入的可执行路径。`python -m quant_trading`和`quant-trade`成为主要入口；两个原始直接启动命令继续兼容。未来独立GUI必须登记目录、测试和模块文档，业务逻辑不得进入主菜单。

### Reason
让不熟悉命令行的用户从一个稳定窗口进入所有当前和未来功能，同时保持各功能进程、状态和模块职责独立。

### Behavior impact
用户现在可以启动主控制台并点击两个按钮打开现有GUI。每次点击启动一个独立窗口；关闭某一功能不关闭主控制台或另一功能。重复点击目前可打开多个实例。

### Interface impact
Additive：新增`python -m quant_trading`、`python -m quant_trading.launcher`、`quant-trade`、`LaunchTarget`和`MainLauncherWindow`。现有入口未改变。

### Dependency impact
无新增第三方依赖；复用PySide6。架构测试禁止Launcher导入功能GUI、数据、算法、Risk或Execution实现。

### Configuration or data impact
无配置格式、数据库或持久化数据变化。Launcher只写普通运行日志。

### Validation
- Targeted launcher/GUI tests: 20 passed.
- Launcher plus architecture boundary tests: 14 passed.
- Full suite: 228 passed, 1 upstream `websockets.legacy` warning.
- `.venv\Scripts\python.exe -m compileall -q src tests`.
- `.venv\Scripts\python.exe -m pip check`.
- Offscreen smoke: `buttons=2 safety=True`.
- `git diff --check`.

### Results
主窗口成功构建两个可信入口，安全状态可见；所有测试、编译和依赖完整性检查通过。第一次离屏烟雾命令尝试将中文标题输出到CP1252控制台时发生仅限命令输出的`UnicodeEncodeError`，改用ASCII检查值后通过；GUI字符串和程序行为未受影响。

### Documentation
新增Launcher模块文档；同步README、模块索引、Compass v14、主架构v10、Project State、Changelog、依赖规则和未来AI工作规则。

### Rollback
删除Launcher包和根`__main__`，移除`quant-trade`脚本及对应测试/文档条目即可恢复原来的两个直接命令。无需修改或删除任何运行数据。

### Open issues
Launcher目前不监控子窗口启动后的健康状态，重复点击会打开多个同类窗口，诊断工具仍需终端运行。这些均已在模块文档中说明。

### Approval
用户明确授权创建主要GUI并要求未来新功能在其中增加入口；没有授权改变任何金融语义、账户访问、Paper/Live订单或自动提交状态。

## EDIT-20260715-003

### Date
2026-07-15T18:23:00Z

### Request
按照推荐方案，将100支或更多热门股票的历史行情全部下载到本地。

### Scope
使用现有热门股票目录中的110支跨行业美股，通过现有Alpaca Market Data与本地优先服务，请求近10年的Raw/IEX日线、周线和月线，共330个数据组合。只补充本地缺失或需要更新的部分，并写入现有中央SQLite。明确不下载10分钟/小时等高容量盘中数据，不访问账户，不提交Paper或Live订单，不改变任何交易、Factor、Decision或Risk行为。

### Pre-change state
中央数据库`runtime/data/market_history.sqlite3`约3,977,216 bytes，包含13,833条Market Bar和5个股票代码。Alpaca Market Data凭据在当前环境中可用；只检查了是否存在，没有输出或记录其值。

### Files changed
- Added: None.
- Modified: `runtime/data/market_history.sqlite3`（Git忽略的本地运行数据）、`KNOWN_ISSUES.md`、`logs/BUG_LOG.md`、`logs/EDIT_LOG.md`.
- Deleted: None.
- Renamed: None.

### Implementation
对110支内置热门股票逐一执行Daily、Weekly、Monthly请求，统一使用Raw adjustment和IEX Feed。所有请求通过`HistoricalDataService`执行，使已有Coverage优先命中、本地缺口按区间补充、返回数据upsert并最终从SQLite统一读取。批次之间保留短间隔以降低请求频率压力；任一单项失败时原计划继续其他股票并记录，但本批没有失败。

### Reason
以可控数据量建立覆盖全部主要行业的长期本地研究数据基础，同时避免批量保存高容量盘中数据。复用现有Store和增量缓存可防止重复Bar及后续无意义的完整重下载。

### Behavior impact
程序代码行为没有改变。本机离线可用行情显著增加：110支股票均具有Raw/IEX的日、周、月数据。请求区间约为2016-07-15至2026-07-15，但IEX实际返回的历史多数约从2020-07-27开始；因此不得把“成功请求10年”表述为“实际获得完整10年”。

### Interface impact
无公共接口变化。

### Dependency impact
无依赖变化；只使用现有`alpaca-py`、SQLite和Market History服务。

### Configuration or data impact
中央SQLite从约3.98 MB增长到59,215,872 bytes（约59.2 MB/56.5 MiB）。本批110支股票的Raw/IEX日、周、月组合共有206,009条Bar；数据库全部Market Bar为215,340条，包含本批之前已存在的其他粒度/数据。没有保存Secret，没有更改配置格式或Schema。

### Validation
- 批量结果：330/330成功，0失败，0警告。
- 选定组合：110支股票，330个symbol/timeframe组合，206,009条Bar。
- 分粒度：Daily 163,852；Weekly 34,160；Monthly 7,997。
- SQLite `PRAGMA integrity_check`。
- 检查Market Bar唯一键重复数量。
- 检查数据库路径仍由`.gitignore`排除。

### Results
SQLite完整性为`ok`，重复唯一键为0。所有110支股票都存在Daily数据。实际总时间边界：Daily最早2018-01-02、Weekly最早2018-01-01、Monthly最早2018-01-01；多数成熟股票的Daily最早日期为2020-07-27。最晚日期分别为2026-07-15、2026-07-13和2026-07-01。未执行pytest，因为本次没有修改源代码或测试行为；改用数据库完整性、组合数量、时间边界和重复键检查验证运行数据。

### Documentation
新增`BUG-20260715-005`并在`KNOWN_ISSUES.md`记录IEX实际历史短于请求区间以及Coverage语义限制；本条记录保存批次范围、数据量、验证和安全边界。未更新CHANGELOG或PROJECT_COMPASS，因为程序能力、默认值、架构和交易语义没有变化。

### Rollback
本地数据属于Git忽略的运行数据，不能通过Git revert恢复。若要撤销本批数据，应先备份数据库，再使用受控SQLite事务按本次110支symbol、Raw、IEX及三个timeframe删除对应Bars/Coverage/Fetch History；当前未执行删除。文档记录可通过未来普通反向提交撤销，但历史Edit Log不得删除，只能追加更正记录。

### Open issues
`BUG-20260715-005`：IEX可返回短于请求区间的实际历史，而Coverage记录成功查询区间。若用户确实需要2020年前的完整数据，应另行验证Alpaca SIP权限或批准其他Provider；不得静默混合不同Feed。

### Approval
用户明确授权下载100支或更多股票并采用推荐方案。该授权仅限Market Data本地持久化，不包含账户访问、Paper订单、Live订单、自动提交或其他交易行为。

## EDIT-20260715-004

### Date
2026-07-15

### Request
诊断Factor版本归档后点击“恢复为可用”却提示未选择版本的问题。

### Scope
只读检查Factor authoring GUI的选择和生命周期事件连接；记录确认的用户可见缺陷。不修改源代码、测试、配置、数据或交易行为。

### Files changed
- Modified: `KNOWN_ISSUES.md`、`logs/BUG_LOG.md`、`logs/EDIT_LOG.md`。
- Added/Deleted/Renamed: None.

### Result
确认视觉高亮与内部`_selected_id`可能不同步，登记`BUG-20260715-006`和`KI-0009`。本次未实施修复，也未运行测试；后续修复需覆盖归档后重载、同一行重选和恢复路径。

### Safety and rollback
无金融含义、交易权限、订单、Paper或Live影响。文档为追加式记录；若结论变化，应追加更正记录。
## EDIT-20260715-005

### Date
2026-07-15T19:30:00Z

### Request
在股票历史数据浏览器左侧增加可滚动的全部已下载股票列表，点击股票后自动显示图表数据。

### Scope
仅扩展现有 `quant_trading.market_history` 模块：从既有 SQLite `market_bars` 只读发现股票代码，在 GUI 中增加独立列表栏，并复用现有 Controller/Service 后台加载和图表流程。没有新增下载规则、数据库 Schema、Provider、Factor、Decision、Risk、账户、订单或 Execution 行为。

### Files changed
- Modified: `src/quant_trading/market_history/interfaces.py`, `src/quant_trading/market_history/storage/sqlite_store.py`, `src/quant_trading/market_history/service.py`, `src/quant_trading/market_history/controller.py`, `src/quant_trading/market_history/ui/history_panel.py`, `tests/unit/market_history/test_sqlite_store.py`, `tests/unit/market_history/test_history_panel_roles.py`, `docs/modules/market-history.md`, `logs/EDIT_LOG.md`.
- Added/Deleted/Renamed: None.

### Implementation
`HistoricalDataStore.list_symbols()` 对现有 Bar 表按规范化股票代码去重、排序；Service 与 Controller 逐层暴露只读列表，不让 GUI 访问 Store。主窗口改为“已下载股票 / 控制与状态 / 图表”三栏；单击列表项会更新输入框并调用既有加载入口。成功加载后刷新列表，使新缓存股票立即可选；加载期间的新选择继续使用既有最后选择排队机制。

### Impact
Blast radius 为 `LIMITED`。新增的是模块内可加性的只读 Store/Service/Controller 方法和 GUI 行为；无配置、迁移、第三方依赖、跨模块依赖、金融语义或安全权限变化。列表中的“已下载”表示本地至少存在一条 Bar，不声称所选范围或所有维度完整覆盖。

### Validation
- `.venv\\Scripts\\python.exe -m pytest tests/unit/market_history/test_sqlite_store.py tests/unit/market_history/test_controller.py tests/unit/market_history/test_service.py tests/unit/market_history/test_history_panel_roles.py -q` — 49 passed.
- `.venv\\Scripts\\python.exe -m pytest tests/unit/market_history tests/integration/market_history tests/architecture/test_dependency_boundaries.py -q` — 116 passed，1 项上游 `websockets.legacy` 弃用警告。
- `git diff --check` — 无空白错误；仅报告工作区既有 Windows LF/CRLF 提示。

### Documentation
同步 `docs/modules/market-history.md` 的用户能力与 Store 接口说明。未更新 Compass、主架构、Project State 或 Changelog，因为模块职责、主要架构、默认值与安全边界未改变。

### Rollback
移除三栏中的股票列表、点击连接及逐层 `list_symbols` 方法与对应测试/文档即可；不需要删除、回滚或迁移任何 SQLite 数据。

### Bugs
本次未发现、修复或延期新的 Bug；没有新增 Bug ID。既有 `BUG-20260715-005` 的 IEX 历史深度/Coverage 语义限制仍不变。

## EDIT-20260715-006

### Date
2026-07-15

### Request
修复Factor版本归档后点击“恢复为可用”却提示未选择版本的问题。

### Scope
FAST局部修复，仅调整算法控制中心Factor authoring列表选择同步，增加GUI回归测试并关闭已登记问题。未改变公共合同、配置、数据库、Factor计算、Decision、Risk、Execution、Paper或Live行为。Blast radius：LOCAL。

### Files changed
- Modified: `src/quant_trading/algorithm_control/ui/factor_authoring_panel.py`、`tests/unit/algorithm_control/test_parameter_editor.py`、`KNOWN_ISSUES.md`、`logs/BUG_LOG.md`、`logs/EDIT_LOG.md`。
- Added/Deleted/Renamed: None.

### Implementation
`clear_form()`将`QListWidget`的current row显式重置为`-1`；增加`itemSelectionChanged`处理，使再次选择同一行时重新装载版本并同步`_selected_id`。没有改变生命周期服务或持久化逻辑。

### Validation
- `.venv\Scripts\python.exe -m pytest -q tests\unit\algorithm_control\test_parameter_editor.py tests\unit\algorithm_control\test_factor_definition_authoring.py tests\architecture\test_dependency_boundaries.py` — 19 passed。
- `git diff --check` — 无空白错误；仅有工作区既有LF/CRLF转换提示。
- 首次直接调用`pytest`以及工作区通用Python分别因命令未安装和缺少pytest而未启动测试，随后使用项目`.venv`成功完成验证。

### Bugs and safety
修复`BUG-20260715-006`并将`KI-0009`移入Resolved。未发现新的Bug；无金融含义、交易权限、自动提交、账户或订单影响。

### Rollback
撤销本次两处GUI选择同步改动和对应测试即可；不需要数据库或配置迁移。

## EDIT-20260715-007

### Date
2026-07-15

### Request
修复股票历史数据浏览器点击刷新后窗口向下延伸并超出屏幕的问题，并核对以前是否修过。

### Scope
FAST局部布局修复。只调整Market History GUI控制/状态栏的高度约束、增加回归测试并同步模块与缺陷文档；不修改行情请求、Provider、缓存、SQLite、图表数据、公共合同、配置、依赖或交易行为。Blast radius：LOCAL。

### Existing overlap
`BUG-20260713-007`曾修复Plotly HTML高于WebView viewport；`BUG-20260713-008`曾修复Qt与Chromium resize时序。两者保持Fixed且其实现保留。本次截图证明新问题发生在Qt外层：刷新后的状态文字提高控制栏minimum size hint，从而撑高整个窗口；不是原Plotly页面再次溢出。

### Files changed
- Modified: `src/quant_trading/market_history/ui/history_panel.py`、`tests/unit/market_history/test_history_panel_roles.py`、`docs/modules/market-history.md`、`KNOWN_ISSUES.md`、`logs/BUG_LOG.md`、`logs/EDIT_LOG.md`。
- Added/Deleted/Renamed: None.

### Implementation
将控制面板、状态、进度和消息放入`QScrollArea`；该区域可调整内部widget，禁用横向滚动，纵向size policy使用`Ignored`且最低高度为0。刷新后内容超高时在控制栏自身滚动，不再要求主窗口扩大；图表WebView和已下载股票列表仍是同一Splitter中的独立栏。

### Validation
- `.venv\Scripts\python.exe -m pytest -q tests\unit\market_history\test_history_panel_roles.py -k "status_refresh_cannot_expand or downloaded_symbol_list"` — 2 passed，12 deselected。
- `.venv\Scripts\python.exe -m pytest -q tests\unit\market_history tests\integration\market_history tests\architecture\test_dependency_boundaries.py` — 117 passed，1个既有上游`websockets.legacy`弃用警告。
- `git diff --check` — 最终审查执行；LF/CRLF提示不属于空白错误。

### Documentation and bugs
登记并修复`BUG-20260715-007`，将`KI-0010`记入Resolved；模块文档补充小高度下控制/状态栏自身滚动的行为。未更新Compass、主架构、Project State或CHANGELOG，因为模块职责、默认值、公共能力和安全边界未变化。

### Safety and rollback
无金融含义、凭据、账户、Paper/Live、订单或自动提交影响。回滚仅需撤销scroll-area包装及对应测试/文档，不需要数据库或配置迁移。

## EDIT-20260715-008

### Date
2026-07-15

### Request and scope
DEEP / Architecture scaffold only：建立统一Portfolio Accounting Layer，并在其中分离append-only Trading Ledger、派生Accounting、report-only Reconciliation和read-only Queries；增加核心合同、内存实现、架构/单元测试、现有Algorithm Control只读页签及治理文档。明确不包含Broker同步、持久化迁移、OrderRequest/Execution Provider、完整成本/P&L、税务、保证金、公司行为、Paper订单、Live或自动提交。Blast radius：MULTI_MODULE。

### Existing overlap and compatibility
实施前确认`decision.PortfolioSnapshot`与`risk.AccountSnapshot`只是无余额/持仓语义的trace envelope，Execution Paper/Live仍为空，且无Order/Fill模型。新财务快照放入`quant_trading.portfolio_accounting`，不替换旧类；Risk仅新增`AccountingAccountSnapshotProvider`/`AccountingPortfolioSnapshotProvider`只读别名合同，现有Provider签名保持不变。

### Implementation
- 新增typed `OrderLifecycleEvent`、`TradeFill`、`CashMovement`及`InMemoryLedgerRepository`；使用UTC、唯一ID、Decimal、稳定幂等键和不可变metadata。重复外部事件/entry ID失败；修正/反转必须作为带目标与原因的新记录。
- 新增`AccountSnapshot`、`PositionSnapshot`、`PortfolioSnapshot`、`DailyPnLSnapshot`及内存replay。订单生命周期事件不改变状态；确认买卖成交和有效signed cash movement参与现金/净多头数量重放。成本、估值及P&L保持空值/partial；超卖做空与多币种失败关闭并保留为Open Decision。
- 新增Reconciliation比较与结构化差异；只报告差异，不修改local/external输入。新增Query Service与现有Algorithm Control中的只读`Portfolio & Ledger`页签；无余额编辑、SQL、Broker或订单入口。Launcher无需新增独立入口，因为功能作为现有Algorithm Control页签提供。
- 建立PROPOSAL-005、ADR-0012、两份模块文档，并同步Compass v15、canonical architecture v11、模块图、依赖规则、项目状态、AGENTS、Changelog和相关模块文档。

### Files changed
- Added: `src/quant_trading/portfolio_accounting/**`, `src/quant_trading/algorithm_control/ui/portfolio_ledger_panel.py`, `tests/unit/portfolio_accounting/**`, `docs/modules/portfolio-accounting.md`, `docs/modules/trading-ledger.md`, `docs/proposals/PROPOSAL-005-portfolio-accounting-layer.md`, `docs/decisions/ADR-0012-portfolio-accounting-ledger.md`.
- Modified: `src/quant_trading/risk/__init__.py`, `src/quant_trading/risk/interfaces.py`, `src/quant_trading/algorithm_control/app.py`, `src/quant_trading/algorithm_control/ui/main_panel.py`, `tests/unit/algorithm_control/test_parameter_editor.py`, `tests/architecture/test_dependency_boundaries.py`, `AGENTS.md`, `PROJECT_COMPASS.md`, `CHANGELOG.md`, `docs/INDEX.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/MODULE_MAP.md`, `docs/architecture/DEPENDENCY_RULES.md`, `docs/project/PROJECT_STATE.md`, `docs/modules/algorithm-control-gui.md`, `docs/modules/risk-control.md`, `docs/modules/execution-environments.md`, `docs/proposals/README.md`, `docs/decisions/README.md`, `logs/EDIT_LOG.md`.
- Deleted/Renamed: none.

### Validation
- `.venv\Scripts\python.exe -m pytest tests/unit/portfolio_accounting tests/unit/algorithm_control tests/unit/risk tests/architecture -q` — 92 passed（中途兼容测试发现GUI构造参数与tab计数需同步，均在最终实现中修正）。
- `.venv\Scripts\python.exe -m pytest -q` — 251 passed，1个既有上游`websockets.legacy`弃用警告。
- `git diff --check` — 无空白错误；仅工作区既有LF/CRLF转换提示。
- 未访问网络、账户、Broker Order API或真实凭据；未commit/push。

### Compass, safety, bugs, and rollback
Intent/architecture/safety与用户批准方向一致：Ledger记录事实，Accounting派生状态，Broker只核对，Risk/GUI只读。未加入未批准的会计口径、交易权限或运行激活；Live/自动提交仍关闭。Open Decisions记录为DEC-008。Bug discovery audit：未发现需登记的新仓库Bug；实现过程中暴露的测试兼容回归在同一变更中修正，未形成已交付缺陷。

回滚时删除新增Portfolio Accounting包、测试、Proposal/ADR/模块文档和GUI页签，并撤销Risk/架构/治理文档的纯追加引用即可。无数据库、配置、外部账户或运行数据迁移；不得使用破坏性Git历史操作。

## EDIT-20260715-009

### Date
2026-07-15

### Request and scope
DEEP但严格限定的现有系统稳定性检查：建立修改前运行/测试基线，修复可证实Bug，盘点模块成熟度，并在已有Error Code/observability/diagnostics体系上增加统一ValidationResult与fail-closed健康汇总。未新增Factor、策略、Risk数值、订单、完整Ledger/Accounting、Paper/Live或自动交易。Blast radius：MULTI_MODULE，但业务规则仍由原模块拥有。

### Baseline before changes
- Windows 10.0.26200（Python platform显示Windows-11标识）、Python 3.14.5、项目`.venv`、`pip check`无破损依赖。
- 修改前全套：251 passed、0 failed、0 skipped、1个既有`websockets.legacy`弃用警告，28.75秒。
- 本地diagnostics退出0；依赖、运行目录、SQLite schema/quick check、凭据完整性和安全默认值通过，网络检查SKIPPED。
- 当前SQLite `integrity_check=ok`；临时空root的日志/数据目录自动创建、首次数据库初始化`ok`；无凭据配置仍成功加载且Live/automatic均false。
- `quant_trading.launcher.app`、`market_history.app`、`algorithm_control.app`均以Qt offscreen真实构造/显示/事件循环/关闭并退出0。Market History产生无界面GPU fallback提示；物理显示QA仍未验证。

### Confirmed bugs and fixes
- `BUG-20260715-008` Fixed：实际error.log保存Decision“添加条件”将Qt bool当作DecisionCondition的`AttributeError`堆栈。按钮改经显式无参adapter连接；新增offscreen bool-overload回归测试。不改变Decision规则或合同。
- `BUG-20260715-009` Fixed：失败测试证明请求区间内的未来Market Bar旧实现未阻止。模块自有`validate_market_bars`现在以一次验证时UTC为上界拒绝未来Bar，不排序/修正/写入数据。

### Validation and health
- 新增根级`quant_trading.validation`共享合同：`ValidationSeverity/Status/Issue/Result`、`InvariantViolation`、`HealthStatus/HealthCheckResult`和小型`ValidationRegistry`。
- 复用集中`ErrorCode`，新增`QT-CONTRACT-001`和`QT-INTEGRITY-001`；issue文本使用既有redaction。Validator异常写技术堆栈并转成CRITICAL，不能默认PASS。
- diagnostics保留逐项结果并新增`SYSTEM_HEALTH`。默认网络检查未运行时为UNKNOWN且`automatic_execution_allowed=false`。BLOCKED/CRITICAL/UNKNOWN均不允许自动执行；当前Execution仍不存在。
- 架构测试禁止validation基础依赖任何业务模块、GUI、Alpaca、SQLite或Execution。

### Module status inventory
Market Data、Local Storage、GUI、Charting、Configuration、Logging、Diagnostics和Algorithm Control GUI为`IMPLEMENTED_VERIFIED`；Factor/Decision/Risk为`PARTIALLY_IMPLEMENTED`；Execution/Trading Ledger/Portfolio Accounting/Reconciliation为`SCAFFOLD_ONLY`；Paper/Live Trading为`NOT_IMPLEMENTED`；Order Construction/Execution Provider为`PLANNED`。没有模块标记`IN_DEVELOPMENT`。状态基于当前代码、测试、入口/diagnostics运行和安全配置，不基于旧Prompt。

### Files changed
- Added: `src/quant_trading/validation.py`, `tests/unit/test_validation.py`, `docs/development/VALIDATION.md`.
- Modified: `src/quant_trading/error_codes.py`, `src/quant_trading/diagnostics.py`, `src/quant_trading/market_history/models.py`, `src/quant_trading/algorithm_control/ui/decision_authoring_panel.py`, `tests/unit/test_diagnostics.py`, `tests/unit/market_history/test_models_and_config.py`, `tests/unit/algorithm_control/test_decision_authoring.py`, `tests/architecture/test_dependency_boundaries.py`, `docs/project/PROJECT_STATE.md`, `docs/architecture/MODULE_MAP.md`, `docs/architecture/OVERVIEW.md`, `docs/development/DEBUGGING.md`, `docs/INDEX.md`, `docs/modules/market-history.md`, `docs/modules/algorithm-control-gui.md`, `PROJECT_COMPASS.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`.
- Deleted/Renamed: none. No database/schema/config migration.

### Final validation
- 定向模块/集成/架构：247 passed、1 warning，31.73秒。
- 修改后最终全套：259 passed、0 failed、0 skipped、1个既有warning，25.76秒（公共模型类型检查完成后的最终工作树）。
- 离线手动路径：`" aapl "`规范为AAPL并从Local cache读取4行；非法symbol和反向日期均以`QT-UI-001`阻止；未来Bar以`QT-DATA-002`阻止。
- 受控validator异常：健康`critical`、automatic allowed=false、`QT-INTEGRITY-001`及完整技术堆栈写入error.log。
- 修改后三个GUI入口offscreen再次退出0；diagnostics输出`SYSTEM_HEALTH UNKNOWN automatic_execution_allowed=false`并退出0。
- `git diff --check`无空白错误，只有工作区既有LF/CRLF提示。未访问账户/Order API，未提交Paper/Live订单，未commit/push。

### Security, open issues, and rollback
Secret只检查存在性且日志/ValidationIssue继续脱敏；未输出Key值。网络Market Data检查本次主动不运行，标为SKIPPED/UNKNOWN。既有KI-0004/0005/0006/0007/0008仍open；将KI-0007补登记为`BUG-20260715-010` Deferred，因为精确修复需要用户批准交易日历语义/依赖，本次未扩展。未发现新架构漂移或其他可复现Bug。回滚只需撤销两个局部修复、validation/diagnostics增量、对应测试和文档；无数据/配置迁移。回滚未来Bar检查会恢复前视数据风险，回滚Qt adapter会恢复GUI异常风险。
## EDIT-20260715-025 — Isolated historical backtesting baseline

### Scope
Implemented the user-approved historical Backtesting & Simulation layer without adding broker Paper/Live execution or production trading authority.

### Architecture and behavior
- Added `quant_trading.backtesting` as a domain distinct from `execution.paper`.
- Added immutable request/result/trade/equity contracts, runner/repository ports, isolated JSON repository, approved SMA20/50 long-only next-bar-open runner, GUI and reproducible CLI.
- Simulation uses Decimal, whole shares, sells before buys, same-day equal cash allocation, zero costs and final mark-to-market. Results are explicitly `historical_simulation` / `RESEARCH_ONLY`.
- Added a trusted **Backtesting & Simulation** entry to the existing main launcher. No Alpaca Trading client, account API, Paper order or Live order path was introduced.

### Actual offline evidence
- Command: `.venv\Scripts\python.exe -m quant_trading.backtesting.cli --start 2025-07-15 --end 2026-07-14 --cash 1000000`
- Run ID: `395c9f70-c3bd-4513-831f-5fb8ac3b90d5`; 110/110 symbols; 0 skipped; 43 simulated trades.
- Ending cash `102.745`; market value `1726651.230`; equity `1726753.975`; research-only return `0.726753975`.
- This is not production performance evidence because Raw/IEX corporate actions, fees, slippage, partial fills and other advanced semantics are not modeled.

### Tests and bug audit
- Before change: 259 passed, 1 upstream warning in 36.53s.
- Targeted: 9 passed in 0.42s; Backtesting GUI constructed offscreen successfully.
- Final complete suite: 263 passed, 0 failed, 0 skipped, 1 upstream warning in 36.18s.
- Fixed `BUG-20260715-011`, a new test-package collection collision; no existing business bug was found or changed.

### Files
- Added: `src/quant_trading/backtesting/`, `tests/unit/backtesting/`, `tests/architecture/test_backtesting_boundaries.py`, `docs/modules/backtesting.md`, `docs/proposals/PROPOSAL-006-historical-backtesting.md`, `docs/decisions/ADR-0013-isolated-historical-backtesting.md`.
- Modified: `src/quant_trading/launcher/app.py`, `tests/unit/launcher/test_main_launcher.py`, `pyproject.toml`, `PROJECT_COMPASS.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/MODULE_MAP.md`, `docs/project/PROJECT_STATE.md`, `docs/modules/main-launcher.md`, `docs/INDEX.md`, `CHANGELOG.md`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`.

### Safety and rollback
Live Trading and automatic order submission remain disabled. Simulation results live only below `runtime/simulations/backtests/`; operational accounting and execution do not read them. Roll back by removing the Backtesting package/tests/docs/launcher target/script entry and the isolated runtime simulation directory. No market-data or production database migration occurred. No commit or push was performed.
### Verification update — 2026-07-15

After extracting the approved SMA fixture behind the replaceable `HistoricalSignalProvider` boundary, targeted tests again passed 9/9 and the latest complete suite passed 263/263 with one upstream warning in 36.44s. This preserves the future Factor → Decision → Risk adapter seam without claiming that the currently incomplete production Pipeline was exercised.
## EDIT-20260715-026 — User-named Simulation Strategy phase one

### Approval and scope
User explicitly approved Simulation Strategy phase one. Added immutable, locally saved research strategy versions and strategy selection to Backtesting. No new sizing, fill, cost, universe, Risk, Paper/Live or operational execution semantics were introduced.

### Behavior
- Algorithm Control now exposes a `Simulation Strategies` page. Users select one exact INCREASE Decision for buys and one exact DECREASE/EXIT Decision for sells, enter their own strategy ID/name/description/reason, and save an immutable version.
- Each Decision continues to lock exact Factor versions. Editing an existing strategy creates the next version; existing records are not overwritten.
- Strategies persist atomically at `runtime/algorithm_control/simulation_strategies.json` with `research_only=true`, `execution_allowed=false`, and `live_allowed=false`.
- Backtesting now exposes a strategy dropdown. The built-in SMA20/50 fixture remains available; saved versions replay the public safe Factor calculator and Decision policy through `DefinitionSignalProvider`.
- Phase-one execution semantics remain all eligible local symbols, long-only, next-bar-open whole shares, sells before equal-cash buys, zero commission/slippage. Conflicting buy/sell Decisions fail closed.

### Files
- Added: `src/quant_trading/backtesting/strategy_definitions.py`, `strategy_store.py`, `strategy_service.py`, `src/quant_trading/algorithm_control/ui/simulation_strategy_panel.py`, `tests/unit/backtesting/test_strategy_definitions.py`.
- Modified: Backtesting `__init__.py`, `app.py`, `service.py`, `strategies.py`; Algorithm Control `app.py`, `controller.py`, `ui/main_panel.py`; Algorithm Control GUI test; Compass, canonical architecture, Module Map, Project State, Backtesting/Algorithm Control module docs, Proposal 006, ADR-0013, Changelog, Bug Log and Edit Log.

### Validation
- Targeted Backtesting/Algorithm Control/architecture tests: 74 passed in 11.17s.
- Complete suite: 267 passed, 0 failed, 0 skipped, one existing upstream warning in 34.31s.
- Offscreen GUI smoke: Algorithm Control built 10 tabs and exposed `Simulation Strategies`; Backtesting built its strategy selector. Current user runtime contains no saved custom strategy yet, so the selector correctly contains only the built-in baseline until the user saves one.
- Security search found no order-submission or Paper/Live imports in the new strategy path. `git diff --check` found no whitespace errors, only existing line-ending notices.

### Bug, safety, and rollback
Fixed `BUG-20260715-012`, the new GUI tab-count regression; no other confirmed bug was discovered. Live Trading and automatic order submission remain disabled; no network, broker account, order API, real credentials, commit or push was used. Roll back by removing the strategy files/page/tests, reverting controller/composition/backtest-selector changes, and deleting only `runtime/algorithm_control/simulation_strategies.json` if created. No SQLite migration occurred.

### Compass audit
Intent and architecture align with the approved reuse of exact Factor/Decision versions; the GUI contains composition metadata only and Backtesting owns replay. No unapproved financial semantics or authority were added. Remaining drift risk: production Risk policies remain incomplete, so saved strategies are simulation-only and must not be presented as Paper/Live-ready.
## EDIT-20260715-027 — Asset/Market Factor and Decision Sizing phase one

### Approval and scope
User explicitly approved Asset/Market Factor separation and Decision Sizing phase one. Existing Factors are now explicitly single-stock Asset Factors; a sibling Market Factor responsibility and traceable suggested USD notional were added. No concrete production formula, Risk value, order submission, Paper/Live access or automatic trading authority was introduced.

### Architecture and behavior
- Added immutable `MarketFactorDefinition/Result`, explicit symbol universes and deterministic mean/sum/minimum/maximum/count aggregation over one exact Asset Factor version. Missing/invalid required inputs return explicit non-valid status and are not silently omitted.
- Added atomic local Market Factor definition storage and an Algorithm Control `市场/宏观因子` page; renamed the existing visible Factor entry to `单只股票因子` without migrating or rewriting existing definitions.
- Added `SizingDefinition/Mode`, immutable `SizingContext/Reference`, restricted Decimal expression evaluation and traceable TradeIntent `requested_notional`. Approved namespaces are `asset`, `market`, `account` and `position`; account/position values remain read-only context rather than Factors.
- Added Decision GUI modes, fixed input, synchronized 1–100% slider/spin control, restricted expression and exact Market Factor selection. Action/mode incompatibilities fail validation.
- Extended Risk contracts with original/approved notional. Approval preserves, reduction must remain positive and no larger, blocked decisions approve none. No numerical Risk policy was added.
- Simulation rebuilds exact referenced Market Factors and evaluates sizing against point-in-time simulated cash/equity/position. Requests exceeding simulated cash or holding value block instead of silently truncating.

### Files
- Added: `src/quant_trading/factors/market.py`, Algorithm Control Market Factor store/service/UI, `src/quant_trading/decision/sizing.py`, Market Factor/Sizing tests, `docs/modules/market-factors.md`, Proposal 007 and ADR-0014.
- Modified: Factor/Decision/Risk public contracts and exports; Algorithm Control admission/contracts/capabilities/composition/controller/main/Decision GUI; Backtesting provider/service/app tests; architecture tests; Compass, architecture/module/dependency/project docs, module docs, indexes, Changelog, Bug Log and Edit Log.
- Persistence: one new isolated JSON definition file `runtime/algorithm_control/market_factor_definitions.json`; no SQLite or operational-account migration.

### Validation
- Before change: 267 passed, 1 existing upstream warning in 26.02s.
- Intermediate Decision/Risk regression: 26 passed; architecture/Market Factor admission: 34 passed; broad targeted set: 95 passed.
- Final complete suite: 277 passed, 0 failed, 0 skipped, 1 existing upstream warning in 45.87s.
- End-to-end Fake test saved Asset/Market/Decision/Strategy exact versions and used `account.cash` plus `market.market.one` to size an isolated simulated trade.
- Offscreen GUI smoke: 11 tabs, distinct Asset/Market entries, sizing slider range 1–100, Backtesting selector built. Safety defaults remained Live=false, automatic=false, manual confirmation=true.
- Actual one-year baseline rerun: run `e2ef62e2-3546-44d5-989f-6d602ec4c009`, 110/110 symbols, 43 trades, ending equity `1726753.975`, research-only return `0.726753975`; no behavior regression.
- Security search found no TradingClient/order submission in the new paths. `git diff --check` found no whitespace errors, only existing line-ending notices.

### Bugs, safety and rollback
Fixed `BUG-20260715-013` and `BUG-20260715-014`, both test-contract compatibility issues caused by the approved new GUI/public contract. No other confirmed bug was discovered. Live and automatic submission remain disabled; no broker/account/network/order API, real credentials, commit or push was used.

Rollback removes new Market Factor/Sizing files/tests/docs, reverts the public-contract/GUI/Simulation/Risk increments, and deletes only `runtime/algorithm_control/market_factor_definitions.json` if created. Existing Asset Factor/Decision/market data/backtest results require no migration rollback.

### Compass audit
Intent alignment: the approved single-stock versus market-wide distinction and amount-selection workflow are implemented. Architecture alignment: accounts stay Portfolio context, Market Factor stays inside Factor ownership, Decision proposes and Risk controls. Safety alignment: research-only, fail-closed and no execution authority. Unapproved behavior/assumptions: none beyond internal reversible representation. Remaining drift risk: no production Market Factor formulas or numerical Risk policies exist, so these definitions remain disabled/research-only.

## EDIT-20260715-028 — Complete daily Simulation Decision Journal

### Approval, interpretation and impact
The user approved the recommended interpretation that every valid trading day evaluates every symbol without forcing a fill. Primary owner is `quant_trading.backtesting`; secondary impacts are its read-only GUI, result JSON, architecture contracts and documentation. Public result contracts were additively extended; old JSON remains readable. No configuration, SQLite, operational ledger/account, broker or execution migration. Blast radius: MULTI_MODULE but research-isolated.

### Behavior and files
- Added immutable `DecisionJournalEntry`, `FactorTrace`, `ConditionTrace`, `JournalAction` and `JournalOutcome` contracts and a complete first-party evaluation port.
- Built-in and saved strategies retain one entry per valid Daily bar/symbol, including OHLCV, exact Asset/Market Factor identity/value/status/lookback, per-condition values, Decision result, sizing references, requested/approved simulated amount, quantity/fill and cash/position before/after.
- Separated GUI **Simulated Trades** and **Daily Decision Journal** tabs; added symbol/action filters and read-only detail inspection.
- Result JSON atomically persists the journal under the existing isolated run path and decodes old results without the new field.
- Added Proposal 008, ADR-0015 and updates to Backtesting, Compass, canonical architecture, Module Map, Project State, Changelog, proposal/ADR indexes and tests.

### Bugs and regression evidence
Fixed `BUG-20260715-015` (legacy signal-provider compatibility), `BUG-20260715-016` (condition trace type scope) and `BUG-20260715-017` (completed non-fills incorrectly left pending). Targeted Backtesting/architecture tests passed 12/12 after final architecture addition; complete suite passed 278/278 with one existing upstream warning before that test-only addition, and the final architecture addition was rerun targeted.

### Actual one-year run and GUI evidence
Run `2daae9c4-829c-4a2d-9874-7b8869a4fb21` completed on 110/110 symbols with 43 simulated fills, ending equity `1726753.975` and research-only return `0.726753975`. It persisted 27,610 daily symbol evaluations: 26,976 NO_DECISION, 307 BUY and 327 SELL; outcomes were 26,976 NO_TRADE, 43 FILLED and 591 BLOCKED, with zero pending outcomes. All entries contained Factor evidence. The isolated JSON was about 52.3 MB. Offscreen GUI constructed the journal page and filters.

### Safety, limitations and rollback
No Trading client, order submission, account API, network call, credential, commit or push was used. Live=false and automatic submission=false. The journal is not the operational Trading Ledger; Portfolio Accounting and Execution cannot import it. Natural days without a valid bar are not fabricated. Existing zero-cost/next-bar-open/long-only research semantics remain unchanged. Roll back the additive journal/evaluation/result/UI contracts, tests and docs; existing old result JSON needs no migration, and generated research result files may be removed manually if desired.

### Compass audit
Intent alignment: detailed daily per-symbol explainability is implemented without forcing trades. Architecture alignment: Backtesting owns research evidence; GUI is read-only; operational Ledger/Accounting remain separate. Safety alignment: simulation-only, no broker or execution authority. Unapproved behavior added: none. Assumption introduced: “daily” means a valid Daily bar for that symbol. Compass updated: B5 approved capability and version metadata. Remaining drift risk: result size grows linearly with days × symbols × traces, and the baseline remains a simplified research model rather than production performance evidence.

### Final verification update — 2026-07-15
After adding the explicit Portfolio Accounting isolation test, targeted Backtesting/architecture validation passed 12/12 and the final complete suite passed 279/279 with one existing upstream deprecation warning in 29.33 seconds.

## EDIT-20260715-029 — Whole-project stabilization and boundary audit

### Scope and baseline
DEEP existing-system stabilization only: no new strategy, Factor formula, Risk value, order, Paper/Live behavior or account connection. The uncommitted working tree was preserved. Baseline: Python 3.14.5 on Windows, `pip check` clean, compile/diagnostics/SQLite integrity passed, complete suite 279/279 with one upstream warning, and all four GUI entries constructed offscreen. Network diagnostics were intentionally skipped and system health therefore remained UNKNOWN/fail-closed.

### Confirmed fixes
- `BUG-20260715-018`: partial simulated sells no longer clear the whole holding.
- `BUG-20260715-019`: requested notional is distinct from rounded executed gross.
- `BUG-20260715-020`: Market Factor Journal traces retain real version/universe metadata.
- `BUG-20260715-021`: saved-strategy preparation clears run-scoped Market Factor caches.
- `BUG-20260715-022`: Backtesting domain service now consumes the narrow read-only `HistoricalBarSource` Protocol; SQLite remains a composition-root detail.
- `BUG-20260715-023`: Market Factor aggregation rejects duplicate symbols and mixed as-of input.
- `BUG-20260715-024`: unexpected validation exceptions are no longer mislabeled/skipped.
- `BUG-20260715-025`: canonical documents no longer claim research Backtesting/sizing are absent.

### Structure and security audit
Architecture tests and source searches found no production import cycle, GUI-to-Alpaca Trading/SQL path, Decision-to-Execution bypass, Execution account mutation, test/archive runtime dependency or operational import of Backtesting. All 129 production modules imported successfully. Launcher exposes three trusted child applications; Algorithm Control has 11 pages; Backtesting retains separate fill/journal views. The 939-line Market History GUI remains a documented internal-complexity risk, but it currently respects module boundaries; no unapproved file split was performed.

### Files changed for this audit
Code: `backtesting/interfaces.py`, `service.py`, `strategies.py`, `__init__.py`, and `factors/market.py`. Tests: Backtesting service/strategy, Market Factor and Backtesting architecture suites. Documentation: Compass, canonical Overview, Module Map, Project State, Backtesting/Decision/Algorithm Control module docs and Changelog. Records: Bug Log and Edit Log. No configuration, dependency, SQLite schema, account data or migration changed.

### Final evidence
- Targeted Factor/Backtesting/architecture: 40 passed.
- Complete suite: 283 passed, 0 failed, 0 skipped, one existing `websockets.legacy` warning, 29.06 seconds.
- Diagnostics: local configuration/dependencies/directories/SQLite schema/integrity/safety passed; optional network check SKIPPED; UNKNOWN health kept automatic execution false.
- Actual isolated run `5b27a755-d3e5-456c-b9a4-1cf3c8133006`: 110/110 symbols, 43 fills, 27,610 journal entries, zero pending, ending equity `1726753.975`, research-only return `0.726753975`.
- Final offscreen/import smoke: Launcher 3 targets, Algorithm Control 11 tabs, Backtesting 6 journal filters, 129/129 modules imported.
- Security scan found only declaration/forbidden-capability strings for order submission; no Trading client or submission method. Live=false, automatic submission=false. `git diff --check` had no whitespace errors, only existing LF/CRLF notices.

### Rollback and Compass audit
Rollback the five localized code files, four regression/architecture test files and factual documentation updates; no data migration reversal exists. Reverting 018/019/023 would knowingly restore research-state or Factor-integrity defects. Intent alignment: the project was stabilized without expanding trading behavior. Architecture alignment: a concrete storage dependency was removed and all established directions held. Safety alignment: diagnostics remain fail-closed and no account/order authority was introduced. Unapproved behavior added: none. Assumptions introduced: none affecting financial semantics; partial sell follows the already-approved requested-notional/whole-share meaning. Compass sections updated: current evidence/status only, not Stable Core. Remaining drift risk: large GUI files and transitional duplicate trace-only snapshot contracts warrant future separately approved refactors, while production execution/accounting remain incomplete by design.

## EDIT-20260716-001 — Backtesting contract and research-record stabilization

### Scope and baseline
DEEP stabilization within the existing Backtesting boundary. The user explicitly excluded algorithm/Decision development, so no Factor formula, strategy semantics, Risk value, order path, Paper/Live behavior or account connection was changed. The existing uncommitted worktree was preserved. Before changes, the complete suite passed 283/283 on Python 3.14.5 with one upstream `websockets.legacy` warning.

### Confirmed fixes
- `BUG-20260716-001`: result/request run identity, chronology, symbol counts, Decimal terminal totals/return, equity curve and journal ownership now fail fast when inconsistent.
- `BUG-20260716-002`: simulated trades and equity points validate UTC, normalized identities, finite Decimal values and exact gross/cash/equity arithmetic.
- `BUG-20260716-003`: JSON result saves are create-only by run ID, and reads verify decoded identity against the requested ID or filename.
- `BUG-20260716-004`: Factor/condition traces and daily journal entries validate identity, UTC, finite values, OHLCV and complete `FILLED` evidence.
- `BUG-20260716-005`: launcher documentation now names all three registered child GUI targets.

### Files and compatibility
Code modified: `src/quant_trading/backtesting/models.py`, `src/quant_trading/backtesting/repository.py`. Test added: `tests/unit/backtesting/test_contracts.py`. Documentation modified: `docs/modules/backtesting.md`, `docs/modules/main-launcher.md`, `docs/project/PROJECT_STATE.md`. Records appended: `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`. The JSON schema, CLI/GUI inputs, strategy semantics, configuration, dependencies and SQLite schema did not change. All seven pre-existing result files, including three 27,610-entry files, decoded successfully after the stricter validation.

### Validation evidence
- New contract regressions: 11 passed after reproducing 11 pre-fix failures.
- Targeted Backtesting and architecture: 26 passed.
- Complete suite: 294 passed, 0 failed, 0 skipped, one upstream warning, 42.44 seconds.
- `pip check`: no broken requirements. `compileall`: passed. Local diagnostics: dependencies/directories/SQLite schema/integrity/safety passed; optional network check skipped, therefore health remained `UNKNOWN` and automatic execution remained false.
- Offscreen entry smokes: Launcher, Market History, Algorithm Control and Backtesting all constructed and exited 0. An initial Market History harness attempt created a second `QApplication` and exited 1; a corrected entry-compatible smoke passed, so this was not recorded as a product bug.
- Actual isolated one-year run `1b7651ca-52bc-486a-89e5-5cdb851992e5`: 110/110 symbols, 43 fills, ending cash `102.745`, ending market value `1665324.480`, ending equity `1665427.225`, research-only return `0.665427225`; 27,720 journal entries, 43 linked fills and zero pending outcomes.
- Security search found no `TradingClient`, submit/close order, account or position API in Backtesting/Execution. Live=false and automatic submission=false. Scoped `git diff --check` found no whitespace error, only existing line-ending notices.

### Safety, rollback and Compass audit
No network request, real/Paper order, broker account, credential value, commit or push was used. The new run exists only in the ignored research result path. Rollback the two Backtesting code files, remove the new contract test, and revert the three factual document updates plus appended log records; no database or JSON migration is required. Removing the repository guard would knowingly restore silent overwrite behavior. Intent alignment: engineering quality improved without algorithm work. Architecture alignment: validation remains inside immutable Backtesting contracts and its repository; Service and GUI responsibilities did not grow. Safety alignment: all research/account/execution isolation remains unchanged. Unapproved behavior added: none. Assumptions introduced: saved run identity is immutable, consistent with unique run IDs and audit evidence. Compass sections updated: none, because project direction and financial semantics did not change. Remaining drift risk: large GUI files and transitional snapshot contracts remain documented and require separate approval before refactoring.

## EDIT-20260716-002 — Passive Algorithm Idea Notebook

### Approval, scope and impact
The user explicitly requested a place inside the program to record all algorithm ideas without affecting any module. This STANDARD change adds one passive Algorithm Control submodule and page only. Primary owner: `quant_trading.algorithm_control`; secondary impacts: its composition root, main panel, architecture/status documentation and tests. Public trading contracts, configuration, SQLite schema, dependencies, financial semantics and launcher targets are unchanged. Blast radius: LIMITED.

### Architecture and behavior
- Added immutable `IdeaNote`/`IdeaNoteStatus`, an `IdeaNoteStore` Protocol, in-memory and atomic JSON adapters, and `IdeaNotebookService` create/update/list/archive/restore operations.
- Added the `算法 Idea 笔记` page to the existing Algorithm Control window with title, plain-text body, tags, archive/restore and archived-note visibility.
- Production composition uses the dedicated ignored file `runtime/algorithm_control/idea_notes.json`. It is separate from component state, Factor/Decision definitions, Backtesting results, market SQLite, Portfolio Accounting and execution state.
- No component registration, proposal conversion, Factor/Decision/Risk/strategy input, Pipeline/Backtest invocation, account mutation, broker call or execution output exists. The notebook model/service has no import from any other QuantTrade business module; the panel imports only PySide6 and its notebook contract.

### Files
- Added: `src/quant_trading/algorithm_control/idea_notebook.py`, `src/quant_trading/algorithm_control/ui/idea_notebook_panel.py`, `tests/unit/algorithm_control/test_idea_notebook.py`, `docs/modules/idea-notebook.md`.
- Modified: Algorithm Control `app.py`, `ui/main_panel.py` and GUI/architecture tests; Compass, canonical Overview, Module Map, Project State, module/doc indexes, Algorithm Control module doc, Changelog, Bug Log and Edit Log.
- No dependency, database, account, order, credential or migration file changed for this capability.

### Bug and validation evidence
- Reproduced and fixed `BUG-20260716-006`: save confirmation was overwritten by the table selection callback. Moving the operation result after reload preserved the intended status; the regression changed from `1 failed, 15 passed` to `16 passed`.
- Final complete suite: 298 passed, 0 failed, 0 skipped, one existing `websockets.legacy` deprecation warning in 44.72 seconds.
- Offscreen Algorithm Control smoke: 12 tabs, one temporary note saved/reloaded, `execution_invocations=0`.
- Architecture regression prohibits Idea Notebook and its panel from importing Factor, Decision, Risk, Backtesting, Portfolio Accounting, Execution, Market History or the Algorithm Control controller.
- No network, real/Paper account, order endpoint, credential, commit or push was used.

### Safety, limitations and rollback
Live Trading and automatic submission remain disabled. The GUI explicitly warns that notes do not trigger algorithms or trading and must not contain secrets. Phase one is plain text/tags/archive only: no search, attachment, cloud sync, encryption, delete, proposal conversion or activation. Rollback by removing the two notebook source files, its test/doc, the one main-panel tab and composition injection, then reverting factual documentation entries. If the user has created notes, preserve or separately back up `runtime/algorithm_control/idea_notes.json`; no database migration reversal is required.

### Compass audit
Intent alignment: the requested idea-recording space is implemented and deliberately passive. Architecture alignment: it is an isolated Algorithm Control presentation/local-storage branch and does not enter the algorithm or execution data path. Safety alignment: no financial meaning, account state, Risk authority, order path, Live or automatic-submission setting changed. Unapproved behavior added: none. Assumptions introduced: local plain text with non-destructive archive is the smallest reversible first phase; no deletion was inferred. Compass sections updated: evolving product definition, capability evidence, approved capability and verification metadata; Stable Core is unchanged. Remaining drift risk: users could manually copy note text into future authoring tools, but there is no automatic code path or authority transfer.

## EDIT-20260716-003 — Complete Main GUI core-page discoverability

### Scope and impact
The user requested verification that every core function/module is reachable from the Main GUI and asked that missing entries be added. The audit confirmed all three standalone GUIs were already registered, while eleven existing Algorithm Control pages were only discoverable after opening that child application. Backend-only Configuration, Storage, Logging and Validation have no independent page; Diagnostics remains an explicit terminal tool and was not represented by a fake GUI. Primary owner: `quant_trading.launcher`; secondary owner: Algorithm Control presentation navigation. Blast radius: LIMITED.

### Architecture and behavior
- Kept the three primary application buttons: Market History, Algorithm Control, and Backtesting & Simulation.
- Added a compact `核心功能直达` selector for Idea Notebook, Asset Factor, Market Factor, Decision, Risk, Execution status, Portfolio & Ledger, Simulation Strategies, Pipeline, Conflict Center and Audit.
- Extended immutable `LaunchTarget` with optional static arguments and retained shell-free `QProcess.startDetached`. Users cannot enter modules, commands or arguments.
- Added stable Algorithm Control page IDs plus `select_page()`. The `--page` option changes only the selected existing tab and invokes no action on that page.
- The launcher still imports no feature module. Feature ownership, persistence, validation, simulation, accounting and execution behavior remain unchanged.

### Files and contracts
- Modified code: `src/quant_trading/launcher/app.py`, launcher `__init__.py`, Algorithm Control `app.py` and `ui/main_panel.py`.
- Modified tests: Launcher GUI/command regressions and Algorithm Control page-map regression.
- Modified docs: Main Launcher and Algorithm Control module docs, Compass, canonical Overview, Module Map, Project State and Changelog; appended Bug/Edit records.
- Additive interfaces: `LaunchTarget.arguments`, `DEFAULT_CORE_SHORTCUTS`, `ALGORITHM_CONTROL_PAGE_IDS`, `AlgorithmControlPanel.select_page()`, and optional CLI `--page`. No dependency, configuration format, database, strategy, financial or execution contract changed.

### Bugs and validation evidence
- Fixed `BUG-20260716-007`, the confirmed core-page discoverability gap.
- Fixed `BUG-20260716-008`, an implementation-time obsolete-colon syntax defect found by immediate source inspection before runtime tests.
- Targeted Launcher/Algorithm Control/architecture tests: 30 passed.
- Complete suite: 301 passed, 0 failed, 0 skipped, one existing `websockets.legacy` warning in 24.70 seconds.
- Compile check passed. Offscreen smoke: three applications, eleven shortcuts, exact `portfolio_ledger` detached arguments, real Algorithm Control `--page` parse, exit 0 and zero execution invocation.

### Safety, rollback and Compass audit
No network, broker, account, order, real/Paper submission, credential, dependency, commit or push was used. Live Trading and automatic submission remain disabled. Rollback by removing `DEFAULT_CORE_SHORTCUTS` and its combo UI, removing `LaunchTarget.arguments`, restoring the module-only start command, and removing Algorithm Control `--page`/`select_page`; the original three application buttons remain. No data migration or cleanup is required.

Intent alignment: all existing user-facing core functions are now easy to find from the Main GUI without fabricating pages for infrastructure. Architecture alignment: navigation metadata stays in Launcher and actual pages remain in Algorithm Control; no reverse import or duplicated logic. Safety alignment: page selection grants no runtime, trading or financial authority. Unapproved behavior added: none. Assumption introduced: “all core functions/modules” means all existing user-facing GUI capabilities; backend infrastructure remains internal or terminal-only. Compass sections updated: verified Launcher capability, Active Intent status and evidence metadata; Stable Core unchanged. Remaining drift risk: Diagnostics still requires the documented terminal command, and repeated clicks may open multiple child processes.

## EDIT-20260716-004 — Algorithm observability stage-zero inventory record

### Scope and impact
Performed a read-only DEEP inventory for the user-provided development-roadmap and algorithm-observability framework. Inspected the Compass, canonical architecture, project state/index/roadmap, relevant module and proposal documents, current Git state, central SQLite schema/data, Factor/Decision/Risk/orchestration/control/backtesting/accounting contracts, recent Edit/Bug history, and launcher requirements. No runtime code, public contract, configuration, database schema, financial semantics, algorithm, Risk value, Paper/Live boundary or execution authority changed.

### Findings and records
Confirmed that central Factor history, Factor/Decision/Risk public contracts, local dry-run orchestration, versioned Algorithm Control definitions, research Backtesting evidence and the in-memory Portfolio Accounting scaffold already exist. Confirmed that a top-level `AlgorithmRun`, durable Decision/Risk result stores and a unified Run History Explorer do not exist. The 59.2 MB central SQLite database is schema version 1 with 215,340 Market Bars and zero Factor history rows; integrity and foreign-key checks passed. Eight isolated Backtesting result files total about 200 MB. Recorded deferred `BUG-20260716-010` / `KI-0013` for duplicate canonical identifiers, duplicate invariant numbering and stale Git-state verification metadata discovered during the audit.

### Files changed
- Appended: `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`.
- Modified current-issue summary: `KNOWN_ISSUES.md`.
- No source, test, schema, runtime-data, proposal, Compass or architecture file was changed.

### Validation
`python -m pytest tests/unit/factors/test_sqlite_factor_store.py tests/integration/test_analysis_decision_pipeline.py tests/unit/algorithm_control/test_preview_and_controller.py tests/unit/backtesting/test_contracts.py tests/architecture -q` passed 54/54. SQLite read-only `PRAGMA integrity_check` returned `ok`; `PRAGMA foreign_key_check` returned no rows. Git evidence before the record change was clean at `5a32cf6`, matching `origin/main`.

### Safety, rollback and Compass audit
No network, broker, account, credential, order, Paper/Live submission, automatic activation or data mutation was used. Roll back only the three appended issue/audit records if their evidence is disproved; do not rewrite earlier log history. Intent alignment: the inventory preserves the user's observability goal and existing implementation. Architecture alignment: it recommends extending the existing central persistence and owner modules rather than creating parallel authorities. Safety alignment: Live and automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: none affecting financial meaning. Compass sections updated: none; the detected canonical-document defect is logged for a separately reviewed correction. Remaining drift risk: the proposed unified run contract and schema migration still require a formal approved proposal before implementation.

## EDIT-20260716-005 — Unified Algorithm Run History phase one

### Approval, task mode and scope
The user explicitly approved fixing `BUG-20260716-010`, creating `PROPOSAL-009`, and implementing observability phase one: a new neutral `run_history` module, central SQLite schema v1→v2 migration, durable Factor/Decision/Risk preview evidence, and the minimum Run History Explorer. Task mode: **DEEP**. Primary modules: `run_history` and central persistence. Secondary modules: Factor, Decision, Risk, local preview orchestration, Algorithm Control GUI and Main Launcher. Explicit exclusions were preserved: no new trading formula, numerical Risk limit, Portfolio Accounting persistence, Paper capability, Live capability, broker access or order submission. Expected blast radius: **SYSTEM_WIDE** because this adds a schema migration and a cross-module correlation contract, while runtime trading authority remains unchanged.

### Implemented behavior and contracts
- Added immutable, typed `AlgorithmRun`, stage, version binding, message, query and detail contracts. The service supports validated start/terminal lifecycle transitions, child/parent correlation, exact definition/configuration bindings, warning/error preservation and software/worktree identity. The only phase-one execution mode is `NO_EXECUTION`.
- Added append-oriented SQLite repositories for run history and Decision/Risk evidence. Existing Factor snapshots gained optional top-level Run/stage correlation. Pipeline preview now records Market Data → Factor → Decision → Risk under one `FULL_PIPELINE_PREVIEW` Run ID; individual Factor and Decision previews use their corresponding run types. Failures and invalid evidence remain reloadable after restart.
- Added schema v2 migration with mandatory pre-migration backup, transactional DDL/data validation, row-count preservation checks, foreign-key validation and integrity validation. Historical result rows are not overwritten. Added the Run History Explorer as an Algorithm Control presentation page using only the typed query contract; added a trusted Main Launcher shortcut and automatic opening of the completed preview Run.
- Created approved `PROPOSAL-009` and `ADR-0016`. Fixed `BUG-20260716-010` by assigning distinct canonical intent IDs to Main Launcher (`INTENT-019`) and Run History (`INTENT-020`), restoring monotonic architecture-invariant numbering and correcting current verification metadata. Added governance regression tests to prevent recurrence.

### Central database migration evidence
The authorized central database `runtime/data/market_history.sqlite3` was migrated from schema v1 to v2. The required backup is `runtime/data/backups/market_history.schema-v1-to-v2.20260716T221625973960Z.sqlite3`. Before/after preserved 215,340 Market Bars and 365 fetch audit rows. The migrated database reports schema version 2, zero foreign-key violations and `PRAGMA integrity_check = ok`; the backup remains schema version 1 with the same counts and integrity result. Runtime database files remain Git-ignored.

### Files changed
- Governance and project records: `PROJECT_COMPASS.md`, `CHANGELOG.md`, `KNOWN_ISSUES.md`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`, `docs/INDEX.md`, `docs/project/PROJECT_STATE.md`, `docs/project/ROADMAP.md`, `docs/proposals/README.md`, `docs/proposals/PROPOSAL-009-unified-algorithm-run-history.md`, `docs/decisions/README.md`, `docs/decisions/ADR-0016-unified-algorithm-run-history.md`.
- Architecture and module documents: `docs/architecture/OVERVIEW.md`, `docs/architecture/DEPENDENCY_RULES.md`, `docs/architecture/MODULE_MAP.md`, `docs/modules/README.md`, `docs/modules/run-history.md`, `docs/modules/central-persistence.md`, `docs/modules/algorithm-control-gui.md`, `docs/modules/analysis-decision-pipeline.md`, `docs/modules/factor-authoring.md`, `docs/modules/factors.md`, `docs/modules/trading-decision.md`, `docs/modules/risk-control.md`, `docs/modules/main-launcher.md`, `docs/modules/market-history.md`.
- Run History and persistence source: `src/quant_trading/run_history/__init__.py`, `src/quant_trading/run_history/models.py`, `src/quant_trading/run_history/interfaces.py`, `src/quant_trading/run_history/service.py`, `src/quant_trading/run_history/identity.py`, `src/quant_trading/persistence/__init__.py`, `src/quant_trading/persistence/sqlite_database.py`, `src/quant_trading/persistence/factor_sqlite_store.py`, `src/quant_trading/persistence/run_sqlite_store.py`, `src/quant_trading/persistence/algorithm_result_sqlite_store.py`.
- Domain/orchestration source: `src/quant_trading/factors/interfaces.py`, `src/quant_trading/factors/storage_models.py`, `src/quant_trading/decision/__init__.py`, `src/quant_trading/decision/interfaces.py`, `src/quant_trading/risk/__init__.py`, `src/quant_trading/risk/interfaces.py`, `src/quant_trading/orchestration/factor_preview.py`, `src/quant_trading/orchestration/algorithm_dry_run.py`, `src/quant_trading/orchestration/algorithm_preview_composition.py`.
- GUI/launcher source: `src/quant_trading/algorithm_control/app.py`, `src/quant_trading/algorithm_control/models.py`, `src/quant_trading/algorithm_control/ui/main_panel.py`, `src/quant_trading/algorithm_control/ui/run_history_panel.py`, `src/quant_trading/launcher/app.py`.
- Tests: `tests/unit/run_history/test_sqlite_run_history.py`, `tests/unit/algorithm_control/test_run_history_panel.py`, `tests/unit/algorithm_control/test_factor_preview_workbench.py`, `tests/unit/algorithm_control/test_parameter_editor.py`, `tests/architecture/test_run_history_boundaries.py`, `tests/architecture/test_governance_document_integrity.py`, `tests/architecture/test_dependency_boundaries.py`.

### Change Impact Report
- Public contracts: additive Run History domain/query/repository contracts plus additive Decision/Risk result-store protocols and optional Factor run correlation; no existing trading contract was removed or reinterpreted.
- Configuration: no user configuration format or default changed. Database: central schema v2 and its tested v1→v2 migration. GUI: one Algorithm Control page and one trusted Launcher shortcut. Permissions: no new credential, account, network or execution authority. Trading semantics and safety: existing Factor/Decision/Risk calculations are preserved; Risk still cannot enlarge or reverse an intent; all new tracked runs are `NO_EXECUTION`; `execution.paper` and `execution.live` remain empty and disabled.
- Migration rollback: stop writers, preserve a copy of the v2 database, restore the named schema-v1 backup, and revert the phase-one source/document changes. A code-only downgrade against the v2 file is not supported. No automated destructive downgrade was added.

### Validation and bug discovery audit
- Complete test suite: **312 passed, 0 failed, 0 skipped**, with one existing upstream `websockets.legacy` deprecation warning, in 35.04 seconds.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only Git's existing LF→CRLF working-copy notices.
- Fixed bug: `BUG-20260716-010`; `KI-0013` is resolved and the append-only Bug Log has a dated resolution update. No new confirmed or deferred bug was discovered in the final implementation audit. Existing unrelated known issues remain unchanged.

### Compass audit
Intent alignment: phase one implements the approved observability foundation and exact persistence/restart acceptance path without entering later financial phases. Architecture alignment: `run_history` owns neutral lifecycle/correlation contracts, persistence owns SQLite, Factor/Decision/Risk retain their result semantics, orchestration composes the pipeline, and GUI reads a typed query service without SQL or algorithm logic. Safety alignment: only `NO_EXECUTION` records are accepted, existing Risk authority is preserved, and no Paper/Live/order path was added. Unapproved behavior added: none. Assumptions introduced: `ASM-016` records append-oriented phase-one history, keeps Backtesting's existing JSON store independent, and makes tracked preview Factor evidence durable so Decision/Risk references remain reproducible. Compass sections updated: version/evidence metadata, current phase, verified capabilities, approved behavior, assumptions, Active Intents and implementation direction; Stable Core is unchanged. Remaining drift risk: recomputation replay, retention/archival automation, export, full historical time-series analysis, Portfolio Accounting persistence and later strategy phases remain explicitly unimplemented; physical display QA beyond automated offscreen/controller coverage remains a manual follow-up. Suggested commit message: `feat: add unified algorithm run history phase one`.

## EDIT-20260716-006 — Phase 2A admission proposal

### Scope and finding
In response to the user's request to continue development, performed the required DEEP admission review for the next roadmap step. Existing PROPOSAL-009/Schema v2 already provide per-Run Factor/Decision/Risk evidence and a read-only Run History Explorer. Basic Factor snapshot queries exist but do not expose one searchable successful/invalid/failed history view or exact-version comparison GUI. Current restricted Decision policies evaluate condition booleans at runtime, but neither `DecisionResult` nor Schema v2 preserves condition input/operator/threshold/outcome or exact sizing input values. Therefore a truthful Decision Inspector cannot be completed as a GUI-only change.

### Proposed resolution and approval boundary
Created `PROPOSAL-010` as a compatible Phase 2A extension of existing owners, not a replacement or parallel history system. It proposes typed Factor-history queries, exact-version tabular comparison, durable Decision condition/sizing traces, two read-only Algorithm Control history subpanels with Open Run, and additive central SQLite v2→v3 migration. It explicitly preserves isolated Backtesting JSON journals and defers chart overlay/export, Target Position, formulas, numerical Risk, accounting persistence, Paper and Live. Conflict result: `REQUIRES_MIGRATION`; blast radius: `SYSTEM_WIDE`. Explicit user approval is required before implementation.

### Files and validation
- Added: `docs/proposals/PROPOSAL-010-factor-history-and-decision-trace.md`.
- Modified: `docs/proposals/README.md`, `logs/EDIT_LOG.md`.
- No source, test, configuration, database, GUI, runtime data, financial meaning or execution authority changed. No bug was found or fixed.
- Rollback: remove the proposed document/index entry and this appended record only if the proposal is rejected; do not alter Phase 1 implementation or history.

### Compass audit
Intent alignment: converts “continue development” into the smallest auditable next-phase proposal while preserving the user's observability roadmap. Architecture alignment: extends Factor/Decision/Run History/persistence owners and rejects GUI reconstruction or a second store. Safety alignment: no implementation, migration, algorithm activation, Risk value, account/order path, Paper or Live behavior occurred. Unapproved behavior added: none. Assumptions introduced: the recommended next step is Phase 2A, with Target Position deferred until its financial semantics are explicitly approved. Compass sections updated: none because the proposal remains pending. Remaining drift risk: implementation must not start until the user approves the recorded schema/public-contract scope and deferrals.

## EDIT-20260716-007 — Factor history and Decision trace Phase 2A

### Approval, task mode and scope
The user explicitly approved `PROPOSAL-010`. This **DEEP** implementation extends the approved Phase 1 Run History instead of creating a parallel evidence system. Primary modules: Factor, Decision and central persistence. Secondary modules: Run History correlation, local preview orchestration and Algorithm Control presentation. Blast radius: **SYSTEM_WIDE** because the central schema and public immutable result contracts changed additively. Explicit exclusions were preserved: no Target Position, Factor/price chart/export, new formula/action/threshold, numerical Risk, Portfolio Accounting persistence, Backtesting JSON migration, account/order behavior, Paper or Live.

### Implemented contracts and behavior
- Added typed immutable Factor research contracts for bounded history filters and exact-version comparison. Successful, invalid and failed calculation attempts remain distinguishable; failed attempts do not fabricate snapshots or values, and comparison reports missing evidence without ranking versions.
- Added immutable Decision condition traces and exact sizing-input traces. The restricted policy captures input value/status/unit, operator, threshold, result and evaluation order at calculation time. Engine-blocked inputs are `NOT_EVALUATED`; legacy rows remain `TRACE_NOT_CAPTURED`. Existing sizing formulas and the public `evaluate_sizing()` behavior are unchanged.
- Added public Factor/Decision query-service ports and one SQLite infrastructure adapter. Persistence owns SQL; Factor/Decision own semantic records; Run History owns cross-run navigation; GUI consumes only injected typed read services and never reconstructs missing evidence.
- Added read-only `历史与比较` and `历史与计算明细` subtabs to the existing Factor and Decision pages. They support documented filters, detail display, exact-version comparison and `Open Run`. No new standalone GUI or Launcher shortcut was needed because the existing trusted Factor/Decision entries open these owner pages.

### Schema migration and runtime evidence
Central SQLite advanced additively from v2 to v3. Schema v3 adds `decision_results.trace_status`, normalized `decision_condition_results` and `trade_intent_sizing_inputs` tables, and bounded research-query indexes. The authorized migration created `runtime/data/backups/market_history.schema-v2-to-v3.20260716T231050870979Z.sqlite3`. The active database is Schema 3; the backup remains Schema 2. Both preserve 215,340 Market Bars and 365 Fetch History rows and return `integrity_check=ok`; the active database has zero foreign-key violations. Existing Factor/Run/Decision tables were preserved; the active database currently has no historical algorithm rows requiring trace backfill.

Rollback requires stopping writers, preserving the v3 database, restoring the named v2 backup and reverting Phase 2A code/contracts. A code-only downgrade against Schema v3 is unsupported. Never drop or overwrite v3-only trace evidence.

### Files changed
- Domain/source: `src/quant_trading/factors/history.py`, Factor exports/interfaces; `src/quant_trading/decision/history.py`, Decision exports/interfaces/models/engine/rule policy/sizing; persistence exports/database/result store/research query/Run detail adapter; Algorithm Control app, Factor/Decision authoring panels and the new history panels.
- Tests: new research-history repository/migration/reload tests and Factor/Decision history-panel tests; updated Decision sizing/engine, dry-run, architecture and governance regressions.
- Governance/design: `PROPOSAL-010`, ADR-0017, Compass, canonical architecture/dependency/module map, Project State/Roadmap/Changelog/indexes, affected Factor/Decision/Run History/persistence/orchestration/GUI/Launcher/Market/Risk module docs, Bug Log and Edit Log.
- Configuration, dependencies, Algorithm Control JSON formats, Backtesting JSON results, Portfolio Accounting, Execution packages and launcher catalog were not changed by Phase 2A.

### Validation and bug discovery audit
- Complete suite: **320 passed, 0 failed, 0 skipped**, with one existing upstream `websockets.legacy` deprecation warning, in 31.39 seconds.
- Final targeted governance/research-history/GUI suite: 10 passed. Broader governance/Run History/dependency suite: 22 passed.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing LF→CRLF working-copy notices.
- Confirmed and fixed `BUG-20260716-011`: Compass B6 denied the verified isolated research Backtesting capability. The correction distinguishes research simulation from absent production strategy/execution and has a governance regression test. It was resolved in the same task and was not added to `KNOWN_ISSUES.md`.
- No other confirmed, deferred or cannot-reproduce bug was discovered. No network, account, credential, broker, order, Paper or Live path was used.

### Change Impact Report
- Public contracts: additive Factor/Decision history/query records and backward-compatible Decision/TradeIntent trace fields. Configuration: unchanged. Database: additive central v2→v3 migration. GUI: two owner-page read-only subtabs. Tests/docs: expanded as listed. Permissions/trading semantics/safety defaults: unchanged; every recorded preview remains `NO_EXECUTION`, Risk cannot enlarge/reverse an intent, automatic submission remains disabled and Live remains disabled.
- Backtesting remains an isolated JSON research owner. Portfolio Accounting remains in memory. No Target Position or account/position financial meaning was introduced.

### Compass audit
Intent alignment: implements the approved Phase 2A research-inspection slice and its restart/audit goals while preserving every deferral. Architecture alignment: Factor/Decision own semantic contracts, persistence owns Schema v3/SQL, Run History owns navigation, orchestration forwards immutable results, and GUI uses typed query ports without calculation. Safety alignment: no trading authority, numerical Risk value, account mutation or Execution path was added; Paper/Live remain empty and disabled. Unapproved behavior added: none. Assumptions introduced: `ASM-017` records that historical Decision causality is truthful only when captured at evaluation time; legacy absence stays explicit. Compass sections updated: evolving phase/evidence, capabilities, architecture summary, approved boundary, assumption, `INTENT-021`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: charts/export, Target Position, recomputation replay, retention, full Backtesting integration and accounting persistence still require separate approval, and physical GUI display QA remains partly manual. Suggested commit message: `feat: add factor history and decision trace phase 2a`.

## EDIT-20260716-008 — Phase 2B visualization/export admission proposal

### Scope and existing-work reminder
In response to the user's request to continue development, performed a **DEEP proposal-only** admission review. Phase 2A already owns typed Factor history/version comparison and Schema v3; Market History already has a verified Plotly/QWebEngine renderer, but that renderer is private to its page. The recommended reuse path is therefore to extend the existing Factor research query, join only the exact persisted source Bar, and extract a neutral shared renderer rather than create another history database, import a private UI class or duplicate browser lifecycle code.

### Proposed resolution and approval boundary
Created `PROPOSAL-011` for Phase 2B exact-version Factor/source-price visualization and bounded CSV/JSON export. The proposed chart requires exact symbol/Factor/version/timeframe/adjustment/feed, joins only `MarketBar.timestamp_utc == FactorHistoryRecord.source_data_end_utc`, uses a separately labeled selected price field, converts Decimal to browser Number only for display, never interpolates/resamples/normalizes/ranks, and keeps invalid/failed/missing evidence visible. Export operates only on the current typed bounded result set, writes atomically to an explicitly selected path and requires confirmation before overwrite.

The proposal also requests approval for a new presentation-only `quant_trading.visualization` module containing public `PlotlyFigureView`. Market History would reuse it without changing its chart builder; Algorithm Control would provide its own Factor figure builder. Conflict result: `REQUIRES_ADAPTER`; blast radius: `MULTI_MODULE`. No Schema v4, data migration, Market Data download, recomputation, Target Position, Decision timeline, numerical Risk, accounting, Backtesting integration, Paper or Live is proposed.

### Bug discovery and files
- Confirmed and fixed `BUG-20260716-012`: the Proposal index still described central Factor-history implementation as wholly inactive, contradicting verified local `NO_EXECUTION` persistence from PROPOSAL-009/010. The corrected summary separates active local evidence from unapproved production activation and has a governance regression test.
- Added: `docs/proposals/PROPOSAL-011-factor-research-visualization-and-export.md`.
- Modified: `docs/proposals/README.md`, `tests/architecture/test_governance_document_integrity.py`, `logs/BUG_LOG.md`, `logs/EDIT_LOG.md`.
- No runtime source, public contract, dependency, configuration, SQLite schema/data, GUI behavior, Factor/Decision/Risk calculation, account, order or execution capability changed.

### Validation and rollback
Focused governance tests passed 5/5. `git diff --check` passed with only existing LF→CRLF working-copy notices. The last complete implementation suite remains the truthful Phase 2A result of 320 passed with one upstream warning; no new runtime implementation required rerunning it in this proposal-only step. Roll back this admission by removing PROPOSAL-011 and its index entry plus this Edit Log record if rejected; retain the factual BUG-20260716-012 correction and append-only Bug history.

### Compass audit
Intent alignment: converts a generic continuation request into the smallest coherent next visualization proposal while preserving the user's observability direction. Architecture alignment: reuses Phase 2A/Schema v3, keeps SQL in persistence, Factor semantics in Factor, GUI presentation in Algorithm Control, and proposes a neutral renderer instead of a private cross-module import. Safety alignment: no implementation or runtime/data mutation occurred; proposed behavior is local read-only evidence plus explicit export files and remains `NO_EXECUTION`. Unapproved behavior added: none. Assumptions introduced: the recommended price overlay is the exact final source Bar and selected stored field, never nearest/filled/resampled data; this remains a proposal pending user approval. Compass sections updated: none because project behavior has not changed. Remaining drift risk: implementation must not begin until approval of the new module/public contract/file-write behavior; Target Position and all financial/execution phases remain separately unapproved.

## EDIT-20260716-009 — Exact Factor research visualization and export Phase 2B

### Approval, task mode and scope
The user explicitly approved `PROPOSAL-011`. This **DEEP** implementation adds the approved Phase 2B read-only research surface over existing Phase 2A/Schema v3 evidence. Primary modules: Factor public research contracts and Algorithm Control presentation/export. Secondary modules: central Persistence exact read adapter, Market History presentation and the new business-neutral `quant_trading.visualization` renderer. Blast radius: **MULTI_MODULE**. Explicit exclusions were preserved: no Schema migration/backfill, new Factor/Decision formula, Target Position, Decision export/timeline, numerical Risk, Backtesting integration, Portfolio Accounting persistence, account/order behavior, Paper or Live.

### Implemented contracts and behavior
- Added immutable `FactorVisualizationQuery`/Point/Series contracts and `FactorVisualizationQueryService`. One query requires exact symbol, Factor name/version, UTC range, timeframe, adjustment, feed and stored `PriceField`. Source evidence distinguishes `AVAILABLE`, `NO_SOURCE_WINDOW`, `MISSING_SOURCE_BAR` and `MISSING_PRICE_FIELD`.
- `SQLiteResearchHistoryQueryService` reuses bounded Factor history and performs one parameterized Market Bar lookup. A price is attached only when `timestamp_utc == source_data_end_utc` and symbol/timeframe/adjustment/feed all match. Nearby/wrong-dimension Bars are ignored; no fill, interpolation, resampling, normalization, ranking or recomputation exists. Central SQLite remains Schema v3 and Phase 2B performed no runtime database write.
- Added a Factor-owned presentation adapter with separately labeled Factor/price axes and a status track. Only successful `VALID` numeric Factor values become line points; invalid/failed/missing or valid non-numeric evidence stays a gap with typed value, Factor/calculation/source status plus Run/Calculation IDs in hover details. Boolean/string values are not coerced.
- Added deterministic `FactorHistoryExportService`: JSON/CSV preserve typed values, Decimal strings, UTC times, IDs, dimensions, parameters, quality/error/status and optional exact source-price evidence. It exports only already queried records, uses same-directory atomic create/replace, refuses mismatched records, requires explicit overwrite, and does not query or mutate SQLite.
- Added exact dimension/price controls, chart and export actions to the existing Factor History subpanel. GUI combo values are normalized back to exact enum contracts. `Open Run` and tabular comparison remain unchanged; no new Launcher application or shortcut was needed.
- Extracted Market History's private offline Plotly/WebEngine lifecycle into public presentation-only `PlotlyFigureView`. Market History retains its Bar chart builder and behavior; Algorithm Control supplies its separate Factor chart builder.

### Files changed
- New source: `src/quant_trading/visualization/`, `src/quant_trading/algorithm_control/factor_history_chart.py`, `src/quant_trading/algorithm_control/factor_history_export.py`.
- Updated source: Factor history/interfaces/exports; Persistence research query; Algorithm Control app/main/Factor management/history panels; Market History history panel.
- Tests: new Factor visualization contracts, Factor chart/export tests and exact persistence join coverage; updated research GUI, Market History renderer and architecture/governance boundaries.
- Governance/design: implemented PROPOSAL-011, ADR-0018, new visualization module document, Compass v23, canonical architecture v19, dependency/module maps, Project State/Roadmap/Changelog/indexes, affected Factor/Persistence/Algorithm Control/Market History/Launcher docs, Bug Log and this Edit Log entry.
- Unchanged: dependency versions, configuration formats/defaults, central Schema/data, Decision/Risk calculations, Backtesting JSON, Portfolio Accounting, launcher catalog and all Execution packages.

### Validation and bug discovery audit
- Complete suite: **332 passed, 0 failed, 0 skipped**, with one existing upstream `websockets.legacy` deprecation warning.
- Focused architecture/research/GUI suite passed 64 tests; export regression suite passed 4 tests.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing Windows LF→CRLF working-copy notices.
- Confirmed and fixed `BUG-20260716-013`: PySide6 may return `StrEnum` combo data as plain strings; the GUI now reconstructs exact enum types before every history/comparison/visualization query.
- Confirmed and fixed `BUG-20260716-014`: create-only export no longer has a replace race; final hard-link creation fails atomically if another writer occupies the target. Confirmed and fixed `BUG-20260716-015`: valid non-numeric Factor results now remain uncoerced gaps with typed hover evidence and a distinct status color. All fixes have regression tests. No deferred or cannot-reproduce bug was introduced, and no new current Known Issue was created.

### Change Impact Report
- Public contracts: additive Factor visualization query/series/status Protocol; no existing contract removed. Configuration: unchanged. Database: read-only exact join over existing Schema v3; no migration/backfill/table/index. GUI: existing Factor owner subpanel only, plus source-compatible renderer extraction. Permissions: explicit local export-file write only; no credential/network/account/order access. Trading semantics/safety: no calculation or recommendation changed; every source gap remains explicit; Risk authority, `NO_EXECUTION`, automatic-submission disabled and Live disabled remain unchanged.
- Rollback: remove Factor chart/export controls/adapters and visualization query contracts, restore the previous private Market History renderer if the shared view regresses, and retain Schema v3/history unchanged. User-created export copies are not automatically deleted. No database downgrade is required.

### Compass audit
Intent alignment: implements the explicitly approved smallest Phase 2B observability slice—understand one exact Factor version relative to its actual persisted source price and export bounded evidence—while preserving every deferral. Architecture alignment: Factor owns evidence meaning, Persistence owns parameterized SQL, Algorithm Control owns Factor-specific presentation/export, and `visualization` owns rendering mechanics only; Market History reuses the public renderer without surrendering chart meaning. Safety alignment: exact identity and explicit gaps prevent invented market evidence; no Factor/Decision/Risk formula, account, order, Paper/Live path or trading authority was added. Unapproved behavior added: none. Assumptions introduced: `ASM-018` records the user-approved exact final source-Bar rule. Compass sections updated: evolving phase/evidence, capability/architecture summary, approved boundary, assumption, `INTENT-022`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: physical-display QA remains partly manual, and cross-version charts/ranking, Decision export, Target Position, recomputation replay, retention, numerical Risk, full Backtesting integration and accounting persistence still require separate approval. Suggested commit message: `feat: add exact factor visualization and export phase 2b`.

## EDIT-20260716-010 — End-of-session development checkpoint

### Recorded state
At the user's request, recorded a documentation-only checkpoint after the Phase 1–2B consistency audit. PROPOSAL-009/010/011 remain the complete approved observability scope: unified durable Run History, Factor/Decision research traces, exact Factor/source-price visualization and bounded Factor export. Central SQLite remains Schema v3, all tracked runs remain `NO_EXECUTION`, and Paper/Live remain empty and disabled.

The checkpoint explicitly separates completed work from later roadmap stages. Recalculation replay, capital buckets/conservation, asset state machines, Target Position, numerical Risk, full Backtesting integration and Portfolio Accounting persistence remain unimplemented and require separate proposals and approval. The current combined Phase 1–2B changes remain in the uncommitted worktree; no Git stage, commit or branch operation was performed.

### Validation and audit
- Re-ran 31 governance, dependency, Run History, Algorithm Control and Execution-boundary tests: all passed.
- Re-ran 21 Run persistence, research query, Factor visualization/export and GUI tests: all passed.
- No source, configuration, database, financial semantics or runtime behavior changed. No new Bug was found; existing KI-0005/KI-0006 are unrelated.
- Files changed: `docs/project/PROJECT_STATE.md`, `logs/EDIT_LOG.md`.

### Compass audit
Intent alignment: records the truthful current state and preserves the approved staged-development sequence. Architecture alignment: documentation only; no module boundary or public contract changed. Safety alignment: no account, order, Paper/Live or execution authority was added. Unapproved behavior added: none. Assumptions introduced: none. Compass sections updated: none; Stable Core and Evolving Project State already describe the implemented scope. Remaining drift risk: the uncommitted multi-phase worktree should receive a reviewed checkpoint before a separately approved next phase; physical GUI QA and DEC-005/DEC-006 remain open.

## EDIT-20260720-001 — Phase 3A capital-allocation admission proposal

### Scope and existing-work reminder
In response to the user's request to continue development, performed a **DEEP proposal-only** admission review from the Phase 1–2B checkpoint. Existing `portfolio_accounting` already owns factual Ledger-derived cash and positions but remains an in-memory scaffold; Run History and central Schema v3 already own durable local research evidence. A new capital feature must therefore model internal planning earmarks without becoming a second factual cash authority, and it must reuse the central Run/persistence/query boundaries.

### Proposed resolution and approval boundary
Created `PROPOSAL-012` for the smallest Phase 3A foundation: a disabled research-only `quant_trading.capital_allocation` domain, explicit user-entered USD research cash basis, exact locked/tactical/asset-cash leaf buckets, zero-tolerance Decimal conservation, append-only asset-to-asset transfers, immutable snapshots, `NO_EXECUTION` allocation Runs, central SQLite v3→v4 migration and one Algorithm Control owner page with a trusted Launcher shortcut.

The proposal explicitly distinguishes allocation transfers from Ledger `CashMovement` and forbids Accounting mutation, Decision/Risk/Backtesting consumption, reserve lending, sector cash ownership, dynamic weights, holdings/Target Position, numerical Risk, broker/order access, Paper and Live. The recommended split defers sector hierarchy because counting both parent sector pools and child asset cash can duplicate money, and defers tactical transfers because loan/repayment semantics belong to the later tactical-reserve phase.

### Change Impact Report and approval status
- Conflict result: `REQUIRES_MIGRATION`; blast radius: `MULTI_MODULE`.
- Proposed primary module: new `capital_allocation`; secondary modules: Run History, Persistence, Algorithm Control and Launcher.
- Proposed public/data changes: additive capital contracts, `ALLOCATION_REBALANCE`/`ALLOCATION` Run enum values and central Schema v4 tables with verified v3 backup/rollback.
- No source, public contract, configuration, database, GUI runtime, financial state, account, order or Execution behavior changed in this proposal-only task.
- Explicit user approval is required before implementation because this introduces a new module, financial interpretation, public contracts, migration and GUI page.

### Validation, bug audit and rollback
The proposal and index will be checked by the governance suite and `git diff --check`. No new Bug was discovered; the existing uncommitted Phase 1–2B worktree was preserved. Roll back this admission by removing PROPOSAL-012 and its index entry plus this append-only record if the proposal is rejected; no database or runtime rollback is needed because implementation has not started.

### Compass audit
Intent alignment: advances the user's staged observability-first roadmap with the smallest conserved capital foundation instead of inventing dynamic allocation. Architecture alignment: factual cash remains in Portfolio Accounting, planning semantics receive one proposed owner, Run History remains neutral, Persistence owns SQL and GUI remains a client of typed services. Safety alignment: proposed plans are explicit research inputs, protected reserves cannot be transferred, all Runs are `NO_EXECUTION`, and no Decision/Risk/order authority is added. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the proposed interpretation remains pending user approval. Compass sections updated: none because project behavior has not changed. Remaining drift risk: implementing before approval would create a second cash meaning and an unauthorized Schema/public-contract change; sector, tactical-loan, target-position and accounting semantics remain separately unresolved.

## EDIT-20260720-002 — Research Capital Allocation and conservation Phase 3A

### Approval, task mode and scope
The user explicitly approved `PROPOSAL-012`. This **DEEP** implementation adds a new public research-planning domain, two neutral Run enum values, central SQLite v3→v4 migration, one Algorithm Control owner page and one trusted Launcher shortcut. Primary module: `quant_trading.capital_allocation`. Secondary modules: Run History, Persistence, Algorithm Control and Launcher. Blast radius: **MULTI_MODULE** with a database migration. Explicit exclusions were preserved: no new trading formula, sector pool, dynamic weight, reserve borrowing/repayment, holdings/Target Position, state machine, numerical Risk, Backtesting consumer, Portfolio Accounting persistence/mutation, broker/account/order access, Paper or Live.

### Implemented contracts and behavior
- Added immutable schema-v1 `CapitalPlan`, bucket, transfer, snapshot, conservation, operation-attempt and typed list/detail/transfer-history contracts. A plan accepts only an explicit user-entered USD `RESEARCH_INPUT`, exactly one `LOCKED_RESERVE`, exactly one `TACTICAL_RESERVE` and zero or more symbol-unique `ASSET_CASH` buckets. All amounts are finite exact `Decimal`; no float, tolerance, inferred cash, ratio, symbol universe or Active plan exists.
- Added `CapitalAllocationService` and public Store/query Protocols. Initial totals must match exactly. Both reserve buckets are protected in Phase 3A; the only accepted movement is a positive, non-overdrawing, different-source/destination `ASSET_CASH → ASSET_CASH` transfer. Accepted events and snapshots are immutable; duplicate transfer identity has no second effect; invalid/failed attempts remain durable without creating capital facts.
- Added `ALLOCATION_REBALANCE` and `ALLOCATION` to neutral Run History. Every plan/transfer attempt produces one terminal `NO_EXECUTION` Run with Session/Request/software identity, plan/version binding, structured error evidence and capital snapshot artifacts. Run History remains a neutral read/navigation owner and never replays a transfer.
- Added central SQLite Schema v4 and `SQLiteCapitalAllocationStore`. Normalized plans/buckets/transfers/snapshots/balances/operations/raw-input rows use Decimal text, UTC and foreign keys. Plan creation/transfer append are transactional with predecessor concurrency, complete bucket-set, protected metadata, cash-basis and exact source/destination delta validation. No existing table or record is overwritten or backfilled.
- Added the Algorithm Control `Capital Allocation` page and the thirteenth trusted Launcher shortcut. The page creates explicit plans, filters/reloads history, shows exact conservation/current buckets, submits only asset-to-asset transfers, displays exact source/destination before/after balances and operation errors, and opens the related Run. GUI code contains no Decimal calculation, SQL, Accounting mutation or downstream consumer.

### Central database migration evidence
The authorized central database `runtime/data/market_history.sqlite3` was migrated from Schema v3 to v4. The verified backup is `runtime/data/backups/market_history.schema-v3-to-v4.20260720T184502106636Z.sqlite3`. Before and after counts are 215,340 `market_bars`, 365 `fetch_history`, and zero pre-existing Algorithm/Factor/Decision/Risk records. Both backup and migrated database return `PRAGMA integrity_check = ok` and zero foreign-key violations. The active database reports Schema 4; every new capital table contains zero rows, proving the migration did not fabricate a default plan or amount. Runtime database/backup files remain Git-ignored.

Rollback requires stopping writers, preserving the v4 file, restoring the named verified v3 backup and reverting the Phase 3A code together. A code-only downgrade against Schema v4 is unsupported, and v4 evidence must never be silently deleted or reinterpreted.

### Files changed
- New domain/source: `src/quant_trading/capital_allocation/__init__.py`, `errors.py`, `interfaces.py`, `models.py`, `service.py`.
- Persistence/Run source: `src/quant_trading/persistence/capital_allocation_sqlite_store.py`, persistence exports/schema/Run detail adapter, Run History enum models, centralized error codes.
- GUI/Launcher source: new `src/quant_trading/algorithm_control/ui/capital_allocation_panel.py`; Algorithm Control composition/main panel/Run History notice; Launcher catalog.
- Tests: new Capital domain/SQLite/migration/GUI/architecture suites; updated Run migration expectations, Algorithm Control page catalog, Launcher catalog and governance verification metadata.
- Governance/design: implemented PROPOSAL-012, ADR-0019, new Capital Allocation module document, Compass v24, canonical architecture v20, dependency/module maps, Project State/Roadmap/Changelog/indexes, affected Persistence/Run/Algorithm Control/Launcher/Portfolio/Decision/Risk docs, Bug Log and this Edit Log record.
- Unchanged by Phase 3A: configuration files/defaults, dependencies, Market/Factor/Decision/Risk calculation semantics, Backtesting JSON and services, Portfolio Accounting source/persistence, and all Execution package contents.

### Validation and bug discovery audit
- Complete suite: **349 passed, 0 failed**, with one existing upstream `websockets.legacy` deprecation warning, in 50.60 seconds.
- Architecture/governance suite: **39 passed**. Focused Capital domain/SQLite/GUI tests passed; temporary v3→v4 backup, migration-failure rollback, restart reload, durable invalid evidence and Open Run were exercised.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing Windows LF→CRLF notices.
- Confirmed and fixed `BUG-20260720-001`: the public SQLite Store now rejects a total-conserved snapshot that omits/mismatches plan buckets and rechecks every transfer delta inside its transaction. Regression coverage proves no partial plan/snapshot is committed. No deferred or cannot-reproduce bug was introduced and no current Known Issue was added.

### Change Impact Report
- Public contracts: additive Capital Allocation commands/models/views/Store/query interfaces and additive Run enum values; no existing trading contract removed or reinterpreted. Configuration/dependencies: unchanged. Database: additive central v3→v4 migration with verified backup/rollback. GUI: one owner page and one static shortcut. Permissions: local research SQLite writes only; no network, credential, account, broker or order authority. Trading semantics: none; plans are manual planning evidence and have no consumer. Safety: exact conservation, protected reserves, complete immutable snapshots, fail-closed attempts and `NO_EXECUTION`; Paper/Live remain empty and automatic submission/Live remain disabled.

### Compass audit
Intent alignment: implements the approved smallest Phase 3A foundation so stock-specific research cash can be observed, conserved, reloaded and audited before any target-position or allocation algorithm exists. Architecture alignment: Capital Allocation owns planning meaning, Portfolio Accounting remains the sole factual Ledger-derived owner, Run History owns lifecycle, Persistence owns SQL and Algorithm Control delegates through typed services; dependency tests prove there is no downstream consumer or cycle. Safety alignment: explicit research input cannot claim broker/account cash, reserves cannot move, accepted transfers are exact zero-sum, and every Run is `NO_EXECUTION`; no account/order/Paper/Live behavior was added. Unapproved behavior added: none. Assumptions introduced: `ASM-019` records the user-approved planning-versus-factual cash distinction. Compass sections updated: version/current phase/evidence, product capability, architecture, approval, non-capabilities, assumption, `INTENT-023`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: multiple plans are inactive comparison records only; sector/dynamic allocation, reserve borrowing, Accounting adapter, holdings/state/Target Position, numerical Risk and Backtesting integration still require separate approval. Suggested commit message: `feat: add conserved research capital allocation phase 3a`.

## EDIT-20260720-003 — Phase 4A asset-state/cycle admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after Phase 3A, performed a **DEEP proposal-only** admission review. The repository's existing `FeatureState` is Algorithm Control component lifecycle, Risk's `MarketState` is market-open context, Capital Allocation owns research cash earmarks, Portfolio Accounting owns factual Ledger-derived state, and Backtesting journals remain isolated simulation evidence. None can safely become the per-symbol strategy-state owner without changing its established meaning.

### Proposed resolution and approval boundary

Created `PROPOSAL-013` for the smallest Phase 4A foundation: a disabled research-only `quant_trading.asset_state` domain, immutable user-defined symbolic state graphs, one open cycle per symbol, explicit manual research transitions, append-only attempts/events/snapshots, deterministic replay, `NO_EXECUTION` state Runs, central SQLite v4→v5 migration and one Algorithm Control Asset State page with a trusted Launcher shortcut.

The proposal deliberately ships no default definition or state catalogue. Symbolic labels have no built-in financial meaning. Automatic Factor/Market-Factor evaluation, thresholds, hysteresis, saturation/reset logic, risk scale, standardized deviation, Target Position, Capital/Accounting consumption, Decision/Risk/Backtesting integration, Paper, Live and orders are all deferred. Exact Factor/Run IDs may be attached only as explanatory references; state history cannot reconstruct or recalculate their values.

### Change Impact Report and approval status

- Conflict result: `REQUIRES_MIGRATION`; blast radius: `MULTI_MODULE`.
- Proposed primary module: new `asset_state`; secondary modules: Run History, Persistence, Algorithm Control and Launcher.
- Proposed public/data changes: state definition/cycle/event/snapshot/attempt/replay/query contracts, additive `ASSET_STATE_RESEARCH`/`STATE` Run enum values and central Schema v5 tables with verified v4 backup/rollback.
- No source, public contract, configuration, database, GUI runtime, state record, financial meaning, account, order or Execution behavior changed in this proposal-only task.
- Explicit user approval is required before implementation because this adds a top-level module, public contracts, migration and GUI page and establishes the one-open-cycle/manual-transition semantics.

### Validation, bug audit and rollback

The full architecture/governance suite passed **39 tests** using the repository `.venv` (including 5 governance-document tests); `git diff --check` passed with only existing Windows LF→CRLF working-copy notices. An initial system-Python invocation could not import pytest, so it was replaced by the documented repository interpreter and is not a product/test failure. No new Bug was discovered; the existing uncommitted Phase 1–3A worktree remains preserved. Roll back this admission by removing PROPOSAL-013 and its index entry plus this append-only proposal record if rejected; no database/runtime rollback is needed because implementation has not started.

### Compass audit

Intent alignment: advances the user's stateful-strategy roadmap while separating durable state evidence from the still-unapproved trading mathematics. Architecture alignment: the proposed state owner does not reuse or mutate control lifecycle, Risk context, Capital Allocation, Accounting or Backtesting; Run History remains neutral, Persistence owns SQL and GUI delegates through typed services. Safety alignment: definitions and manual transitions are local `NO_EXECUTION` research evidence with no cash, holding, exposure, Risk or order effect. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the generic graph, one-open-cycle and manual-only semantics remain pending approval. Compass sections updated: none because project behavior has not changed. Remaining drift risk: treating user-defined labels as financial instructions or adding automatic transitions before formulas/thresholds are separately approved would be project drift.

## EDIT-20260720-004 — Manual Asset State and trading-cycle history Phase 4A

### Approval, task mode and scope

The user explicitly approved `PROPOSAL-013`. This **DEEP** implementation adds a new public manual research-state domain, two neutral Run enum values, central SQLite v4→v5 migration, one Algorithm Control owner page and one trusted Launcher shortcut. Primary module: `quant_trading.asset_state`. Secondary modules: Run History, Persistence, Algorithm Control and Launcher. Blast radius: **MULTI_MODULE** with a database migration. Explicit exclusions were preserved: no default or financial state catalogue, automatic Factor/Market-Factor transition evaluation, thresholds/hysteresis/saturation/reset formulas, mathematical reference/risk scale/standardized deviation, Target Position, Capital Allocation or Portfolio Accounting mutation, Decision/Risk/Backtesting consumer, broker/account/order access, Paper or Live.

### Implemented contracts and behavior

- Added immutable schema-v1 state declarations, allowed directed edges, exact-version definitions, one-open-cycle-per-normalized-symbol `TradingCycle`, start/close events, manual transition events, evidence bindings, snapshots, operation attempts/results, bounded queries and deterministic replay results. State keys are opaque user-defined symbols and carry no built-in buy/sell/exposure meaning.
- Added `AssetStateService` and public Store/query Protocols. Every definition save, cycle start, manual transition and close requires explicit typed input and creates one terminal `NO_EXECUTION` Run. A transition must use the current predecessor, change state and follow an allowed edge. Close preserves the final state and blocks later transitions. Invalid/storage-failed attempts remain searchable but create no accepted definition, event, transition or snapshot.
- Added separate attempt and operation identities. Same operation ID plus the same canonical payload returns the original completed result without a second effect; changed content is rejected and recorded. Exact transition note and unresolved requested cycle identity remain durable evidence. Optional Run/Factor references are explanatory local identities only and cannot calculate or infer state.
- Added deterministic replay from the immutable start event through accepted transitions. Replay verifies definition/version, symbol/cycle, strict sequence, predecessor, allowed edge, snapshot chain and close boundary, reports structured integrity issues and never repairs/recomputes history.
- Added `ASSET_STATE_RESEARCH` and `STATE` to neutral Run History plus typed Asset State operation/snapshot artifacts. Run History remains lifecycle/navigation only and assigns no state meaning.
- Added `SQLiteAssetStateStore` and central Schema v5 normalized definition/graph/cycle/event/transition/evidence/snapshot/operation/input tables. The Store independently revalidates completed definitions, exact Run/stage identity, operation input, current predecessor, graph edge, event/transition and resulting snapshot in one transaction.
- Added the Algorithm Control `Asset State` owner page and fourteenth trusted Launcher shortcut. The page creates explicit graphs, starts/closes cycles, submits only explicit allowed manual transitions, filters/reloads definitions/cycles/attempts, shows timeline/replay integrity and opens the related Run. GUI code contains no graph/transition calculation, SQL, financial logic or downstream invocation.

### Central database migration evidence

The authorized central database `runtime/data/market_history.sqlite3` was migrated transactionally from Schema v4 to v5. The verified backup is `runtime/data/backups/market_history.schema-v4-to-v5.20260720T205120471224Z.sqlite3`. Before and after counts preserve 215,340 `market_bars`, 365 `fetch_history` and zero pre-existing Algorithm/Factor/Decision/Risk/Capital research records. Both backup and active database return `PRAGMA integrity_check = ok` and zero foreign-key violations; the backup remains Schema 4 and the active database reports Schema 5. All twelve new state tables were initially empty, proving the migration created no definition, state, edge, symbol, cycle, event, transition, snapshot or operation. A final read-only check reconfirmed Schema 5/4, integrity, counts and zero accepted state definitions/cycles/transitions/operations. Runtime database and backup remain Git-ignored.

Rollback requires stopping writers, preserving the v5 database, restoring the named verified v4 backup and reverting Phase 4A code together. A code-only downgrade against Schema v5 is unsupported, and v5 evidence must never be silently deleted or reinterpreted.

### Files changed

- New domain/source: `src/quant_trading/asset_state/__init__.py`, `errors.py`, `interfaces.py`, `models.py`, `replay.py`, `service.py`.
- Persistence/Run source: new `src/quant_trading/persistence/asset_state_sqlite_store.py`; persistence exports/schema/Run artifact adapter; Run History enum models; centralized error codes.
- GUI/Launcher source: new `src/quant_trading/algorithm_control/ui/asset_state_panel.py`; Algorithm Control composition/main panel; Launcher catalog.
- Tests: new `tests/unit/asset_state/test_asset_state.py`, `test_sqlite_asset_state.py`, `tests/unit/algorithm_control/test_asset_state_panel.py`, `tests/architecture/test_asset_state_boundaries.py`; updated Run/capital migration expectations, Algorithm Control page catalog, Launcher catalog and governance verification metadata.
- Governance/design: implemented PROPOSAL-013, ADR-0020, new Asset State module document, Compass v25, canonical architecture v21 with invariants 43–46, dependency/module maps, Project State/Roadmap/Changelog/indexes, affected Persistence/Run/Algorithm Control/Launcher docs, Bug Log and this Edit Log record.
- Unchanged by Phase 4A: environment/config formats/defaults, dependencies, Market/Factor/Decision/Risk/Capital calculation semantics, Backtesting JSON/services, Portfolio Accounting source/persistence and all Execution package contents.

### Validation and bug discovery audit

- Complete suite: **362 passed, 0 failed**, with one existing upstream `websockets.legacy` deprecation warning, in 58.16 seconds.
- Final architecture/governance suite: **42 passed**. Focused Asset State domain/SQLite/GUI tests passed 8 after the Store/idempotency fixes; temporary v4→v5 backup, migration-failure rollback, restart reload, durable invalid/failed evidence, deterministic replay/corruption detection, Run artifacts and Open Run were exercised.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing Windows LF→CRLF notices.
- Confirmed and fixed `BUG-20260720-002`: original completed idempotent results now outrank later conflict attempts, and exact notes/requested cycle IDs persist. Confirmed and fixed `BUG-20260720-003`: the public Store now rejects inconsistent completed cross-object evidence transactionally. Both have deterministic regression coverage. No deferred/cannot-reproduce bug was introduced and no current Known Issue was added.
- No network, credential, account, broker, order, Paper or Live path was used. Live and automatic submission remain disabled.

### Change Impact Report

- Public contracts: additive Asset State commands/models/views/Store/query/replay interfaces and additive Run enum values; no existing financial/trading contract removed or reinterpreted. Configuration/dependencies: unchanged. Database: additive central v4→v5 migration with verified backup/rollback. GUI: one owner page and one static shortcut. Permissions: local research SQLite writes only. Trading semantics: none; labels and manual history have no consumer. Safety: one-open-cycle uniqueness, exact immutable definitions, allowed-edge/predecessor validation, idempotent operations, durable failures, transactional Store revalidation, deterministic replay and `NO_EXECUTION`; Paper/Live remain empty.

### Compass audit

Intent alignment: implements the approved smallest Phase 4A foundation so per-stock symbolic state/cycle history can be defined, observed, reloaded and audited before any trading mathematics is chosen. Architecture alignment: Asset State owns graph/cycle/transition/replay meaning; Run History owns neutral lifecycle, Persistence owns SQL, Algorithm Control delegates typed commands/queries, and dependency tests prove no Capital/Accounting/Decision/Risk/Backtesting/Execution consumer or import cycle. Safety alignment: every write is explicit and `NO_EXECUTION`; labels cannot change cash, holding, target exposure, risk or orders; automatic submission and Live remain disabled. Unapproved behavior added: none. Assumptions introduced: `ASM-020` records the user-approved manual-research-evidence interpretation. Compass sections updated: version/current phase/evidence, product capability, architecture, approval, non-capabilities, assumption, `INTENT-024`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: a future caller must not treat symbolic labels as financial instructions; automatic evaluation, state formula/thresholds, Target Position, downstream consumers, state correction/archive, numerical Risk, accounting persistence and execution still require separate approval. Suggested commit message: `feat: add manual asset state history phase 4a`.

## EDIT-20260720-005 — Phase 5A bounded Target Position admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after verified Phase 4A, performed a **DEEP proposal-only** admission review. Current Decision sizing owns a proposed action amount, not a desired portfolio level. Capital Allocation owns inactive research earmarks; Portfolio Accounting owns in-memory facts; Asset State owns symbolic manual history; Factor owns typed observations but no approved standardized-price formula. Automatically connecting them would silently choose data authority, units, financial direction and trading semantics.

### Proposed resolution and exact approval boundary

Created `PROPOSAL-014` for the smallest Phase 5A Target Position foundation: a disabled/unconsumed `quant_trading.target_position` research owner, immutable user-defined finite-knot curves, explicit manual scalar/USD capital/current-position inputs, exact bounded interpolation/clamping, structured target/difference trace, durable successful/invalid/failed attempts, `NO_EXECUTION` Target Position Runs, proposed central SQLite v5→v6 migration, and a Target Position Laboratory with one trusted Launcher shortcut.

The proposed mathematics is explicit and contains no default value: USD-only manual research basis/current value; long-only unlevered target fraction in `[0,1]`; user-selected non-increasing or non-decreasing finite knots; exact zero/neutral knot; endpoint clamping; exact Decimal linear interpolation inside each bracket; target notional equals basis times fraction; adjustment equals target minus current; exact zero yields `NONE`. This proposal does not approve any actual curve, direction, fraction, knot, amount or standardized-state formula.

Standardized reference/risk-scale calculation, automatic Factor/Asset State input, hysteresis/stateful levels, Capital/Accounting adapters, TradeIntent conversion, numerical Risk, Backtesting, accounting persistence, Paper, Live and orders remain explicitly deferred.

### Change Impact Report and approval status

- Conflict result: `REQUIRES_MIGRATION`; blast radius: `MULTI_MODULE`.
- Proposed primary module: new `target_position`; secondary modules: Run History, Persistence, Algorithm Control, Launcher and presentation-only visualization.
- Proposed public/data changes: additive curve/knot/request/result/trace/attempt/query/Store contracts, `TARGET_POSITION_PREVIEW`/`TARGET_POSITION` Run enum values and central Schema v6 tables with verified v5 backup/rollback.
- Proposed financial interpretation requires the user's explicit choice: manual research-only, USD, long-only, unlevered, monotone finite-knot interpolation. Approval would not create a runtime consumer or authorize any parameter values.
- No source, public runtime contract, configuration, database, GUI runtime, Target Position record, account, state, capital, Decision, Risk, order or Execution behavior changed in this proposal-only task.

### Validation, bug audit and rollback

The architecture/governance suite passed **42 tests** and `git diff --check` passed with only existing Windows LF→CRLF notices. No new confirmed, deferred or cannot-reproduce Bug was found; `KNOWN_ISSUES.md` is unchanged by this admission. Roll back this proposal by removing PROPOSAL-014 and its proposal-index entry while preserving the append-only record; no source/database/runtime rollback is needed because implementation has not started.

### Compass audit

Intent alignment: advances the user's mathematical Target Position roadmap while exposing the exact proposed formula and keeping every unresolved input authority outside the implementation. Architecture alignment: the proposal creates one narrow target-level owner instead of expanding Decision, Capital, State or Accounting; Run History remains neutral, Persistence owns proposed SQL and GUI remains presentation/input only. Safety alignment: proposed fractions are bounded long-only research evidence, every future Run is `NO_EXECUTION`, and no account/order/Paper/Live authority is requested. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the exact USD/long-only/monotone finite-knot interpretation is pending approval. Compass sections updated: none because current project behavior and phase are unchanged. Remaining drift risk: implementation before approval, or later treating manual inputs/results as factual account state or a TradeIntent, would be project drift.

## EDIT-20260720-006 — Implement approved PROPOSAL-014 Phase 5A bounded Target Position research

### Scope and approval

Implemented the user's explicit approval of PROPOSAL-014 as a **DEEP / MULTI_MODULE** disabled research slice. Added one separate `quant_trading.target_position` owner for immutable finite-knot target-level definitions and explicit manual previews. This implementation does not include a standardized reference/risk state, automatic Factor or Asset State input, Capital Allocation or Portfolio Accounting adapter, hysteresis/stateful level behavior, TradeIntent conversion, numerical Risk, Backtesting consumption, accounting persistence, Paper, Live or orders.

The exact approved financial interpretation is unchanged: USD-only explicit research basis/current value; long-only unlevered target fraction within `[0,1]`; user-selected non-increasing or non-decreasing finite knots; strictly increasing scalar values straddling exactly one zero/neutral knot; endpoint coverage/clamping; exact Decimal adjacent linear interpolation; target USD equals explicit basis times fraction; difference equals target minus explicit current value; exact zero yields `NONE`. No direction, fraction, knot, amount, symbol, state meaning or formula was defaulted.

### Implementation

- Added immutable schema-v1 curve/knot/command/result/trace/attempt/query contracts, public Store/query Protocols, pure `TargetPositionEngine` and `TargetPositionService`. Every definition save and preview creates one terminal `TARGET_POSITION_PREVIEW` / `TARGET_POSITION` `NO_EXECUTION` Run with exact configuration binding. Success, invalid input and storage failure remain searchable; accepted results are immutable and exact repeated inputs produce equal numeric outputs under distinct Run/attempt identities.
- Added central SQLite Schema v6 normalized definition/knot/operation/evidence/result/structured-trace tables and `SQLiteTargetPositionStore`. The Store revalidates exact Run/stage identity plus raw definition/preview inputs against accepted objects in one transaction. Run History renders Target Position operation/result artifacts without owning or recalculating their meaning.
- Added Target Position Laboratory in Algorithm Control and the fifteenth trusted Launcher shortcut. The GUI saves explicit definitions, collects only manual scalar/USD inputs, displays definitions/results/failed attempts, exact selected bracket/clamp trace, target/current value and direction, current-position fraction when the explicit basis is non-zero, distinct current/target markers through the shared Plotly renderer and `Open Run`. GUI code contains no SQL or target/money calculation.
- The new component remains unregistered as an Active trading component and has no consumer. `execution.paper` and `.live` were not changed; Live and automatic submission remain disabled.

### Central database migration evidence

The authorized ignored database `runtime/data/market_history.sqlite3` was migrated transactionally from Schema v5 to v6. The verified backup is `runtime/data/backups/market_history.schema-v5-to-v6.20260720T221057524713Z.sqlite3`. Migration preserved 215,340 `market_bars`, 365 `fetch_history` and zero pre-existing Algorithm/Factor/Decision/Risk/Capital/Asset State research records. Both backup and active database return `PRAGMA integrity_check = ok` and zero foreign-key violations; the backup remains Schema 5 and the active database reports Schema 6. All new Target Position definition/result/operation tables contain zero rows, proving no default curve, knot, amount or preview was created.

Rollback requires stopping writers, preserving the v6 database, restoring the named verified v5 backup and reverting Phase 5A code together. A code-only downgrade against Schema v6 is unsupported, and any future v6 evidence must never be silently deleted or reinterpreted.

### Files changed

- New domain/source: `src/quant_trading/target_position/__init__.py`, `engine.py`, `errors.py`, `interfaces.py`, `models.py`, `service.py`.
- Persistence/Run source: new `src/quant_trading/persistence/target_position_sqlite_store.py`; updated persistence exports/schema/Run artifact adapter, neutral Run enum models and centralized error codes.
- GUI/Launcher source: new `src/quant_trading/algorithm_control/target_position_chart.py` and `ui/target_position_panel.py`; updated Algorithm Control composition/main panel and Launcher catalog.
- Tests: new `tests/unit/target_position/test_target_position.py`, `test_sqlite_target_position.py`, Target Position panel/chart tests and architecture boundary tests; updated current-schema migration expectations, Algorithm Control page-count governance and Launcher catalog assertions.
- Governance/design: implemented PROPOSAL-014, ADR-0021, new Target Position module document, Compass/architecture/module map/dependency rules, Project State/Roadmap/Changelog/indexes, affected Persistence/Run/Algorithm Control/Launcher/Factor docs, Bug Log and this Edit Log record.
- Unchanged by Phase 5A: configuration/environment formats/defaults, third-party dependencies, Market/Factor/Decision/Risk/Capital/Asset State/Portfolio Accounting/Backtesting calculation semantics and all Execution package contents.

### Validation and bug discovery audit

- Complete suite: **375 passed, 0 failed**, with one existing upstream `websockets.legacy` deprecation warning, in 75.65 seconds.
- Final architecture/governance suite: **45 passed**. Focused Target Position domain/SQLite/GUI/chart/Launcher/current-page suite passed 25 tests. Temporary v5→v6 backup, migration-failure rollback, restart reload, exact endpoint/knot/interpolation behavior, deterministic repeated numeric values, durable invalid/failed evidence, Run artifacts, current/target markers and Open Run were exercised.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing Windows LF→CRLF notices.
- Confirmed and fixed `BUG-20260720-004`, `BUG-20260720-005` and `BUG-20260720-006`: Qt enum conversion, SQLite Store cross-object provenance and current-position fraction/marker completeness now have deterministic regression coverage. No deferred/cannot-reproduce Bug or new current Known Issue remains.
- No network, credential, account, broker, order, Paper or Live path was used. Live and automatic submission remain disabled.

### Change Impact Report

Primary module: new `target_position`. Secondary modules: Run History, Persistence, Algorithm Control, Launcher and presentation-only visualization adapter. Public contracts and neutral Run enum values are additive. Configuration and dependencies are unchanged. Database impact is additive central v5→v6 with verified backup/rollback. GUI impact is one owner page and one static shortcut. Permission impact is local research SQLite writes only. Trading semantics add one hypothetical desired-level calculation but no authoritative input adapter, action, risk approval or order. Safety behavior is bounded `[0,1]`, exact/versioned/manual-only, durable/fail-closed and `NO_EXECUTION`. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: implements the approved smallest mathematical Target Position foundation and makes every input, knot, intermediate and current/target difference inspectable without choosing unresolved data authorities. Architecture alignment: Target Position owns desired-level math; Run History owns lifecycle, Persistence owns SQL and cross-object validation, Algorithm Control delegates typed service/query calls, and boundary tests prove no existing business/execution module consumes the output. Safety alignment: the contract cannot represent a short, leverage or over-basis target; every action is explicit local `NO_EXECUTION`, and no result is a TradeIntent/Risk approval/order. Unapproved behavior added: none. Assumptions introduced: `ASM-021` records the user-approved manual research-only interpretation. Compass sections updated: current phase/evidence, capability/module inventory, approval, assumption, `INTENT-025`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future code must not treat manual scalar/capital/current values as Factor/State/Accounting facts or automatically convert a target result into Decision/Risk/Execution without a separately approved adapter and contract. Suggested commit message: `feat: add bounded target position research phase 5a`.

## EDIT-20260720-007 — Phase 1–5A verified Git release checkpoint

### Scope and version record

Recorded the user-authorized Git/GitHub handoff for the accumulated approved PROPOSAL-009 through PROPOSAL-014 implementation. The checkpoint is the Git commit containing this record; Git supplies its exact immutable revision ID. It is released from `main` to the configured GitHub `origin`, while the Python package version remains `0.1.0` and the governed implementation state is Phase 5A over central SQLite Schema v6.

The checkpoint includes unified Run History and durable Factor/Decision/Risk evidence, Factor/Decision research history and visualization, conserved manual Research Capital Allocation, manual Asset State/cycle history, and bounded manual Target Position research. Capital Allocation, Asset State and Target Position remain disabled/unconsumed research capabilities. Portfolio Accounting remains in-memory. Paper/Live Execution remain declaration-only; account access, order submission, automatic submission and Live trading remain disabled.

### Evidence and repository hygiene

- Pre-release evidence remains: complete suite **375 passed, 0 failed** with one existing upstream warning; architecture/governance suite **45 passed**; compileall and dependency-integrity checks passed.
- Central SQLite v5→v6 migration evidence remains external to Git: the ignored active database and verified backup preserve 215,340 Market Bars and 365 Fetch History rows, pass integrity/foreign-key checks, and contain zero default Target Position rows.
- Runtime databases, migration backups, local environment files and credentials are not release artifacts and must remain ignored. No package dependency, configuration default, financial formula, runtime consumer or execution authority is changed by this release record.
- Rollback is Git-level: revert the checkpoint commit for source/documentation rollback. Database downgrade still requires the separately documented stop-writers/preserve-v6/restore-verified-v5-backup procedure; a code-only downgrade against Schema v6 remains unsupported.

### Compass audit

Intent alignment: records and publishes the exact currently verified Phase 1–5A research state requested by the user. Architecture alignment: no module ownership, public dependency direction or persistence contract is changed. Safety alignment: release publication does not activate any registered component or execution path; Live and automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: none. Compass sections updated: only release-checkpoint metadata was advanced to version 26; Stable Core and project semantics are unchanged. Remaining drift risk: the package version is intentionally unchanged at `0.1.0`; future capability activation, financial integration, Paper or Live work still requires separate approval.

## EDIT-20260720-008 — Phase 5B manual standardized-price-state admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after the verified Phase 1–5A Git checkpoint, performed a **DEEP proposal-only** admission review. The existing Factor owner already governs one-stock quantitative observations, while Target Position accepts only an untyped manual scalar and explicitly has no upstream adapter. Asset State owns symbolic manual history, and the independent Risk layer owns downstream constraint authority. Placing reference-relative price mathematics in Target Position, Asset State or Risk would duplicate or blur those responsibilities.

Created `PROPOSAL-015` for the smallest Phase 5B foundation: an additive Factor-owned, disabled/unconsumed manual standardized-price-state research preview. The exact proposed interpretation is three explicit finite positive Decimal USD inputs—manual price `P`, manual reference `R` and manual normalization/risk scale `K`—with `deviation = P - R` and dimensionless `state = (P - R) / K`. No rounding, clamping, annualization, source lookup or hidden fallback is proposed. Negative/zero/positive states describe below/equal/above the manual reference only; they do not imply a target, action or Risk outcome.

Reference-price estimation, risk-scale/volatility estimation, price field/window/adjustment/calendar semantics, generic FactorSnapshot publication, Target Position/Asset State/Capital/Accounting adapters, hysteresis, Decision/TradeIntent, numerical Risk, Backtesting, Paper, Live and orders remain explicitly deferred. No source code, public runtime contract, central SQLite schema/data, GUI runtime, component activation or execution permission changed in this proposal-only task.

### Change Impact Report and approval status

- Proposal status: `PROPOSED`; user approval is pending. Conflict result: `REQUIRES_MIGRATION`; expected implementation blast radius: `MULTI_MODULE`.
- Proposed primary module: compatible extension of `quant_trading.factors`; proposed secondary modules: Run History, Persistence, Algorithm Control and Launcher. No new top-level business owner is proposed.
- Proposed additive contracts: immutable standardized-state definition, manual command, structured result/trace, durable attempt/query/Store contracts plus neutral Run type/stage values.
- Proposed database/GUI: central SQLite v6→v7 with verified backup/rollback and zero default records; one typed owner page and reviewed Launcher shortcut. These are not implemented or authorized yet.
- Approval would authorize only the exact manual USD formula/sign convention, structured history, Schema v7 and GUI scope. It would not authorize any actual price/reference/scale, estimator, automated input, downstream consumer or trading behavior.

### Validation, bug audit and rollback

The complete architecture/governance suite passed **45 tests**, and `git diff --check` passed with only existing Windows LF→CRLF notices. No new confirmed, suspected, deferred or cannot-reproduce Bug was found; `BUG_LOG` and `KNOWN_ISSUES` are unchanged. Roll back the proposal record by removing PROPOSAL-015 and its index/Roadmap pending-decision entries while preserving this append-only historical record; no source/database/runtime rollback is needed because implementation has not started.

### Compass audit

Intent alignment: advances the user's stated per-stock mathematical-state roadmap by exposing the smallest exact formula and every unresolved source decision before automation. Architecture alignment: the proposal reuses Factor ownership, keeps Run History neutral and reserves SQL/GUI work for their existing layers; it adds no parallel calculation authority. Safety alignment: all proposed records are manual, disabled, unconsumed and `NO_EXECUTION`; normalization scale is explicitly not numerical Risk authority, and Live/automatic submission remain disabled. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the USD inputs, positivity constraints and sign convention are pending user approval. Compass sections updated: none because current behavior, architecture and approved direction are unchanged. Remaining drift risk: implementing before approval, silently choosing a rolling reference/scale formula, or treating a standardized state as a Target Position/TradeIntent would be project drift.

## EDIT-20260720-009 — Phase 5B manual standardized price state research

### Scope and approved interpretation

Implemented the user's explicit approval `批准 PROPOSAL-015` as a **DEEP, MULTI_MODULE, disabled/unconsumed research change**. The Factor owner now provides immutable fixed-formula definitions and explicit manual previews for finite positive Decimal USD price `P`, reference `R` and normalization scale `K`: exact USD deviation `D=P-R` and dimensionless state `S=D/K`. No rounding, clamping, annualization, estimator, source lookup or hidden fallback exists. Negative/zero/positive describes only below/equal/above the manual reference and cannot imply a target, action, Risk result or order.

Automated reference/risk-scale formulas, Market Data adapters, generic FactorSnapshot publication, Target Position/Asset State/Capital Allocation/Portfolio Accounting consumers, Decision/TradeIntent, numerical Risk, Backtesting, Paper, Live and orders remain excluded. No component is Active and `execution.paper` / `.live` remain unchanged declaration-only boundaries.

### Implementation

- Added Factor-owned schema-v1 definition/command/result/trace/evidence/operation/query models, public Store/query Protocols, pure Decimal engine and service. Every explicit definition save and preview receives one terminal `STANDARDIZED_STATE_PREVIEW` / `STANDARDIZED_STATE` `NO_EXECUTION` Run. Accepted evidence is immutable; invalid and storage-failed attempts remain durable without an accepted result.
- Added central SQLite Schema v7 with five normalized standardized-state definition/operation/evidence/result tables and `SQLiteStandardizedPriceStateStore`. The adapter revalidates exact raw command, definition/result arithmetic, evidence and Run/stage identity transactionally. Run History renders persisted operation/result artifacts without recalculating Factor meaning.
- Added the service-backed `Standardized State` page to Algorithm Control and the sixteenth trusted Launcher shortcut. The GUI collects explicit inputs, displays definitions/results/attempts and the structured trace, filters history and opens the exact Run; it contains no Decimal formula, SQL, Market Data or trading consumer call.
- Added targeted unit/repository/migration/GUI/Run/Launcher and architecture regression coverage. Updated current-schema expectations from v6 to v7 while retaining explicit failure rollback tests for every historical migration boundary.

### Central database migration evidence

The authorized ignored database `runtime/data/market_history.sqlite3` migrated transactionally from Schema v6 to v7. Verified backup: `runtime/data/backups/market_history.schema-v6-to-v7.20260720T230549460397Z.sqlite3`. Backup remains Schema 6; active reports Schema 7. Both return `PRAGMA integrity_check=ok` and zero foreign-key violations. All 44 shared pre-existing business-table counts are identical, including 215,340 `market_bars` and 365 `fetch_history`; every new standardized-state table contains zero rows, proving no definition, value, operation or evidence was defaulted/backfilled.

Rollback requires stopping writers, preserving the v7 database, restoring the named v6 backup and reverting Phase 5B code together. A code-only downgrade against Schema v7 is unsupported; future v7 history must never be silently deleted or reinterpreted.

### Files changed

- Factor/source: new `standardized_state_models.py`, `standardized_state_interfaces.py`, `standardized_state_engine.py`, `standardized_state_service.py`; updated Factor exports/errors and centralized error codes.
- Persistence/Run: new `standardized_state_sqlite_store.py`; updated central schema/migrations, persistence exports, Run enum models and Run artifact adapter.
- GUI/Launcher: new `standardized_state_panel.py`; updated Algorithm Control composition/page catalog and trusted Launcher shortcut.
- Tests: new standardized-state domain/migration/GUI/architecture suites; updated Run/Factor/Launcher/current-schema/governance boundary expectations.
- Governance/design: implemented PROPOSAL-015, ADR-0022, new standardized-state module document, Compass/architecture/module/dependency maps, Project State/Roadmap/Changelog/indexes and affected Factor/Persistence/Run/Algorithm Control/Launcher docs; appended BUG-20260720-007 and this record.

### Validation and bug discovery audit

- Complete suite: **389 passed, 0 failed**, with one existing upstream `websockets.legacy` deprecation warning, in 62.67 seconds.
- Final architecture/governance suite: **49 passed**. Targeted migration/domain/Run/GUI/Launcher/current-boundary suite: **111 passed**.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing Windows LF→CRLF notices. Ruff was unavailable in the environment (`No module named ruff`) and was not claimed as passed.
- Confirmed and fixed `BUG-20260720-007`: the first Store provenance query used non-existent `algorithm_run_stages.name` rather than canonical `stage_name`; focused regression tests now prove completed, invalid and failed evidence persists correctly. No deferred/cannot-reproduce Bug or new current Known Issue remains.
- No network, credential, Market Data request, account, broker, order, Paper or Live path was used. Live and automatic submission remain disabled.

### Change Impact Report

Primary module: compatible `factors` extension. Secondary modules: Run History, Persistence, Algorithm Control and Launcher. Public contracts and neutral Run enum values are additive. Configuration and third-party dependencies are unchanged. Database impact is additive central v6→v7 with verified backup/rollback. GUI impact is one owner page and one static shortcut. Permission impact is local research SQLite writes only. Trading semantics add one hypothetical quantitative observation but no active FactorSnapshot, target, action, risk decision or order. Safety behavior is explicit positive manual inputs, immutable/fail-closed evidence and `NO_EXECUTION`. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: implements the approved smallest per-stock mathematical-state foundation and exposes every input/intermediate/version without choosing unresolved data estimators. Architecture alignment: Factor owns formula/units/result meaning, Persistence owns SQL, Run History owns lifecycle/navigation, Algorithm Control delegates typed services and architecture tests prove no consumer imports the specialized result. Safety alignment: no result can mutate a target, position, cash, Risk decision or order; every operation is explicit local `NO_EXECUTION`. Unapproved behavior added: none. Assumptions introduced: `ASM-022` records the user-approved manual USD normalization interpretation. Compass sections updated: Phase/evidence, capability/module inventory, approval, assumption, `INTENT-026`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future code must not treat manual values as Market Data, equate normalization scale with numerical Risk, publish a generic FactorSnapshot or connect Target/Decision/Execution without a separately approved adapter. Suggested commit message: `feat: add manual standardized price state research phase 5b`.

## EDIT-20260720-010 — Phase 5C linked standardized-state to Target Position admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after verified Phase 5B, performed a **DEEP proposal-only** admission review. Phase 5B already persists an exact dimensionless Standardized Price State with source definition/version, symbol, `as_of`, Run and structured manual formula inputs. Phase 5A already maps a manually entered scalar through an explicitly selected bounded Target Position curve using manual USD research capital/current-position values. Both capabilities are disabled/unconsumed and remain available independently.

The existing generic Target Position evidence binding is explanatory and does not transactionally prove that a referenced standardized-state result exists or that its scalar, symbol, time, definition and Run agree with the Target Position output. Directly connecting the two without a typed contract would therefore conflict with the project's reproducibility and audit requirements.

### Proposed resolution and exact approval boundary

Created `PROPOSAL-016` for the smallest Phase 5C bridge. A user would explicitly select one accepted persisted standardized-state `calculation_id` and one exact Target Position `definition_id`. Linked mode would copy the stored dimensionless scalar, symbol and `as_of` without editing or recalculation; retain explicit non-negative Decimal USD research capital/current-position inputs; delegate to the unchanged Target Position curve engine; and persist parent/child `NO_EXECUTION` Runs plus an immutable typed source/result link.

The proposal recommends a narrow application coordinator, additive Target Position input/link contracts and central SQLite v7→v8 operation/link tables with transactional cross-object validation. Existing manual source and Target Position previews remain unchanged. Reference/scale estimation, Market Data lookup, automatic latest/default selection, Capital Allocation or Portfolio Accounting adapters, Asset State, Decision/TradeIntent, numerical Risk, Backtesting, Paper, Live and orders remain explicitly deferred.

No source code, public runtime contract, database schema/data, GUI runtime, component activation or execution permission changed in this proposal-only task.

### Change Impact Report and approval status

- Proposal status: `PROPOSED`; user approval is pending. Conflict result: `REQUIRES_MIGRATION`; expected implementation blast radius: `MULTI_MODULE`.
- Proposed primary module: existing `quant_trading.orchestration`; secondary owners: Target Position accepted-input provenance, Factor standardized-state public query, Run History, Persistence and Algorithm Control.
- Proposed public contracts: exact linked command/source/result/attempt/link/query/Store contracts, optional Target Position parent/symbol context and one neutral Run type.
- Proposed database/GUI: additive central SQLite v7→v8 typed link/attempt tables, a separate linked mode inside the existing Target Position owner page and Run History source/parent/child navigation. These are not implemented or authorized yet.
- Trading/safety meaning: only an exact persisted observation-to-hypothetical-target handoff; no cash, holding, state, action, Risk approval, account, order or Live effect.
- Rollback at this proposal stage: remove the PROPOSAL-016 file and its proposal-index/Roadmap pending-decision entries while preserving this append-only historical record; no runtime or database rollback is required.

### Validation and bug discovery audit

The focused governance/dependency/Run/standardized-state boundary set passed **28 tests**, and the complete architecture/governance suite passed **49 tests**. `git diff --check` passed with only existing Windows LF→CRLF notices. The first test invocation selected the system Python, where pytest is not installed; the repository `.venv` was then used for both successful recorded runs. No confirmed, suspected, deferred or cannot-reproduce Bug was found during admission analysis; `BUG_LOG` and `KNOWN_ISSUES` are unchanged.

### Compass audit

Intent alignment: advances the stated mathematical chain by defining one observable source-to-target arrow without inventing reference/scale, capital/account or action semantics. Architecture alignment: Factor and Target Position retain their existing calculation ownership; application orchestration owns call order, Persistence would own SQL/cross-object checks and Run History remains neutral. Safety alignment: the proposed feature is explicit, local, disabled/unconsumed and `NO_EXECUTION`; manual modes and all execution boundaries remain unchanged. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the exact bridge and Schema v8 design await user approval. Compass sections updated: none because current capability and approved direction did not change. Remaining drift risk: implementing before approval, treating generic evidence as sufficient provenance, selecting latest results automatically, or presenting a linked target as a Decision/Risk/order would be project drift.

## EDIT-20260720-011 — Phase 5C exact standardized-state to Target Position linkage

### Scope and approved interpretation

Implemented the user's explicit approval `批准 PROPOSAL-016` as a **DEEP, MULTI_MODULE, disabled/unconsumed research change**. The new path requires one exact accepted persisted standardized-state calculation ID and one exact existing Target Position definition ID. It copies the source schema-v1 dimensionless scalar, normalized symbol and UTC `as_of` without editing, rounding, recalculation or fallback, then delegates to the unchanged bounded Target Position curve engine. Research capital basis and current-position value remain explicit non-negative Decimal USD hypothetical inputs.

Reference/risk-scale estimators, Market Data lookup, automatic latest/default/best source or curve selection, generic FactorSnapshot publication, Asset State, factual Capital Allocation/Portfolio Accounting adapters, Decision/TradeIntent, numerical Risk, Backtesting, fills, Paper, Live and orders remain excluded. Existing fully manual Standardized State and Target Position modes remain available and behaviorally unchanged. No component was activated and `execution.paper` / `.live` remain empty declaration-only boundaries.

### Implementation

- Added Target Position schema-v1 source-neutral linked command/input/result/operation/link/query contracts and `LinkedTargetPositionService`. The service delegates only to the existing `TargetPositionEngine`; the target package imports no Factor implementation.
- Added `StandardizedStateTargetPositionPreviewCoordinator` in application orchestration. It resolves the exact public standardized-state query result, creates one top-level `STANDARDIZED_TARGET_POSITION_PREVIEW` `NO_EXECUTION` Run, delegates a valid request to one child `TARGET_POSITION_PREVIEW` Run, preserves the historical source Run, and durably handles missing, invalid, conflicting and storage-failed requests. Exact operation retries return the original terminal outcome.
- Extended neutral Run History with typed parent/child/source/linked-preview relationships. The SQLite read adapter exposes linked operation/result artifacts and relationships without calculating domain meaning; Run History Explorer can open a selected related Run.
- Added central SQLite Schema v8 tables `target_position_linked_preview_operations` and `target_position_standardized_state_links`. `SQLiteTargetPositionStore` saves accepted target result/operation/link evidence transactionally and independently revalidates source existence/schema/unit/value/symbol/time/definition/Run/stage, target definition/result and parent-child identity. Migration creates no default/backfilled row.
- Extended the existing Target Position page with a visually separate linked mode. Source result and curve both require explicit selection; source inputs/formula/version are read-only; only manual USD basis/current value/reason are editable; completed/invalid/failed history and source/parent/child Open Run navigation are visible. GUI code contains no formula or SQL.

### Central database migration evidence

The authorized ignored database `runtime/data/market_history.sqlite3` migrated transactionally from Schema v7 to v8. Verified backup: `runtime/data/backups/market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3`. Backup remains Schema 7; active reports Schema 8. Both return `PRAGMA integrity_check=ok` and zero foreign-key violations. All 49 pre-existing business-table counts are identical, including 215,340 `market_bars` and 365 `fetch_history`; both new Phase 5C tables contain zero rows, proving no source selection, operation, link, result or definition was defaulted/backfilled.

Rollback requires stopping writers, preserving the v8 database, restoring the named v7 backup and reverting Phase 5C code together. A code-only downgrade against Schema v8 is unsupported. Feature-level rollback may disable linked composition while retaining readable v8 history; both manual workflows continue independently.

### Files changed

- Target Position/orchestration: new `target_position/linked_models.py`, `target_position/linked_service.py` and `orchestration/standardized_target_position_preview.py`; updated target Store/query exports/contracts and orchestration exports.
- Persistence/Run: updated central schema/migrations, Target Position SQLite Store, Run SQLite read adapter, Run enums/detail relationships and centralized error codes.
- GUI/composition: updated Algorithm Control composition/main panel, Target Position panel and Run History Explorer. No Launcher catalog item or new top-level GUI was added because Phase 5C extends the existing Target Position owner page.
- Tests: new linked target domain/repository/migration/Run and architecture suites; updated GUI/Run relationship/current-schema migration tests. No real network, account or order fixture was introduced.
- Governance/design: implemented PROPOSAL-016, added ADR-0023, updated Compass/architecture/dependency/module maps, affected module docs, Project State/Roadmap/Changelog/indexes and this append-only record; finalized `BUG-20260721-008` evidence.

### Validation and bug discovery audit

- Complete suite: **401 passed, 0 failed**, with one existing upstream `websockets.legacy` deprecation warning, in the final 104.10-second rerun.
- Final architecture/governance suite: **54 passed**. Linked target focused domain/repository/migration/Run suite: **6 passed**; the broader affected domain/Run/GUI set passed **113 tests**, and the final linked GUI/Run subset passed **10 tests** during implementation.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing Windows LF→CRLF notices.
- Confirmed and fixed `BUG-20260721-008`: standardized-state Run History optional values now use the canonical em dash instead of mojibake; linked integration reload provides regression coverage. Confirmed and fixed `BUG-20260721-009`: the Compass governance checkpoint assertion now follows the truthful Phase 5C/Schema v8 metadata. No deferred/cannot-reproduce Bug or new current Known Issue remains.
- Real central Schema v8 was rechecked after the full suite: `integrity_check=ok`, zero foreign-key violations and zero linked operation/link rows. No Market Data, credential, account, broker, order, Paper or Live path was used.

### Change Impact Report

Primary module: existing application `orchestration`. Secondary modules: Target Position accepted-input/provenance, public Factor standardized-state query, Run History, Persistence and Algorithm Control. Public contracts and neutral Run type/relationships are additive. Configuration, third-party dependencies and Launcher catalog are unchanged. Database impact is additive central v7→v8 with verified backup/rollback. GUI impact is a separate linked mode in the existing owner page plus related-Run navigation. Permission impact is local research SQLite reads/writes only. Trading semantics automate only the exact observation-to-hypothetical-target handoff; no action, Risk approval, account fact or order meaning is added. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: closes the first requested observable mathematical arrow while preserving exact inputs, versions, failures and Run relationships. Architecture alignment: Factor retains formula/result ownership, Target Position retains curve/result ownership, orchestration owns call order, Persistence owns SQL/cross-object validation, Run History remains neutral and GUI delegates typed services; 54 architecture/governance tests verify these boundaries. Safety alignment: every path is explicit `NO_EXECUTION`; USD context remains hypothetical, no downstream trading consumer exists, and Paper/Live/automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: `ASM-023` records the approved exact-result/manual-USD interpretation. Compass sections updated: phase/evidence, capabilities, architecture, approval, assumption, `INTENT-027`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future code must not choose latest sources, reinterpret manual USD as account truth, recalculate copied evidence or convert a target directly into an action/Risk/order without a separately approved adapter. Suggested commit message: `feat: link standardized state to target position preview`.

## EDIT-20260721-012 — Phase 5B/5C publication checkpoint preparation

At the user's explicit request to `commit + push 到 github一下，记得做记录`, added `CHECKPOINT-20260721-002` to the append-oriented Version History before Git delivery. The checkpoint binds the current `main` branch to previous commit `7ebe14b`, package version `0.1.0`, central Schema v8, the verified v7 backup, Phase 5B/5C user-visible behavior, complete validation evidence, safety state, deferred work and rollback procedure. The checkpoint commit is the Git commit containing that record; the exact immutable hash and remote push result are provided by Git and the delivery report.

No source behavior, financial meaning, public contract, configuration, dependency, database content or runtime permission changed in this record-only step. The prior final evidence remains 401 complete tests, 54 architecture/governance tests, compileall, dependency integrity and diff checks; no new Bug or Known Issue was discovered. Runtime databases, backups, credentials, logs and local control state remain ignored and are not included in the publication.

## EDIT-20260721-013 — Phase 5D target-adjustment Decision admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after the verified and published Phase 5B/5C checkpoint, performed a **DEEP proposal-only** admission review. Phase 5C already persists one exact linked Target Position result with trustworthy symbol, UTC time, current USD exposure, target USD exposure and signed adjustment. The existing Factor-policy `DecisionResult` and `TradeIntent` instead require generic `FactorSnapshot` identities, while Phase 5B was deliberately not published as a generic FactorSnapshot. Reusing those contracts unchanged would therefore fabricate provenance; loosening them would migrate the already verified Factor → Decision → Risk path.

Created `PROPOSAL-017` for the smallest Phase 5D Decision-owned bridge. It accepts only one explicitly selected completed Phase 5C link; application orchestration copies its exact source-neutral target evidence; and a specialized Decision mapper interprets a positive difference as `INCREASE`, a negative difference as `DECREASE`, and exact zero as `HOLD` with no intent. A non-zero result creates exactly one type-distinct research intent whose positive requested USD notional is the absolute difference while retaining the original signed desired change.

The proposal deliberately adds no `EXIT`, minimum threshold, tolerance, rounding, quantity, price, fee, confidence, cash check, account truth, Risk admission or execution consumer. Existing Factor-policy Decision/TradeIntent and Risk contracts remain unchanged. No source code, runtime public contract, central SQLite schema/data, GUI behavior, component activation or trading permission changed in this proposal-only task.

### Change Impact Report and approval status

- Proposal status: `PROPOSED`; user approval is pending. Conflict result: `REQUIRES_MIGRATION`; expected implementation blast radius: `MULTI_MODULE`.
- Proposed primary module: compatible specialized extension of `quant_trading.decision`; proposed secondary modules: application orchestration, Target Position public query, Run History, central Persistence and Algorithm Control.
- Proposed additive contracts: explicit command, source-neutral linked-target input, specialized result/intent/attempt/source-link/query/Store contracts and one neutral Run type. Existing Factor-policy contracts are not changed.
- Proposed database/GUI: central SQLite v8→v9 with four specialized evidence tables and zero backfill/default rows; a separate mode in the existing Decision Inspector plus exact source/parent/child Run navigation. No new Launcher shortcut is proposed.
- Approval would authorize only the exact Phase 5C-source sign mapping, positive absolute requested notional, specialized non-Risk intent, durable Schema v9 history and read-only research GUI scope. It would not authorize generic Decision migration, Risk admission or numerical Risk, Portfolio Accounting/Capital facts, Backtesting, Paper, Live, orders or fills.

### Validation, bug audit and rollback

The complete architecture/governance suite passed **54 tests**. `git diff --check` passed with only existing Windows LF→CRLF notices. No confirmed, suspected, deferred or cannot-reproduce Bug was found during this admission analysis; `BUG_LOG` and `KNOWN_ISSUES` are unchanged. Roll back the proposal record by removing PROPOSAL-017 and its proposal-index/Roadmap pending-decision entries while preserving this append-only historical record; no source/database/runtime rollback is needed because implementation has not started.

### Compass audit

Intent alignment: advances the approved observable chain from exact desired position toward Decision while exposing the necessary financial interpretation before implementation. Architecture alignment: Target Position retains desired-level mathematics, Decision owns action/notional meaning, orchestration would own source resolution/call order, Persistence would own SQL validation and Run History remains neutral. Safety alignment: the proposed result is explicit local `NO_EXECUTION` evidence, type-distinct from current Risk inputs, disabled/unconsumed and unable to construct or submit an order. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the exact sign/notional mapping and Schema v9 await user approval. Compass sections updated: none because current behavior, architecture and approved state remain Phase 5C/Schema v8. Remaining drift risk: implementing before approval, fabricating generic Factor evidence, silently adding an EXIT/threshold/rounding rule, or admitting the specialized intent to Risk/Execution would be project drift.

## EDIT-20260721-014 — Phase 5D exact Target Adjustment Decision preview

### Scope and approved interpretation

Implemented the user's explicit approval `批准 PROPOSAL-017` as a **DEEP, MULTI_MODULE, disabled/unconsumed research change**. The user must explicitly select one accepted Phase 5C `target_position_link_id`. Application orchestration resolves its exact immutable linked Target result and source evidence, then copies the persisted signed `target_position_difference_usd` into a source-neutral Decision input. The Decision owner maps positive to `INCREASE`, negative to `DECREASE`, and exact zero to `HOLD`; a nonzero specialized intent has requested USD equal to the exact absolute difference, while `HOLD` creates no intent.

The existing generic Factor-policy `DecisionResult`/`TradeIntent` and current Risk contracts remain unchanged. No tolerance, minimum size, rounding, `EXIT`, quantity, price, fee, cash/account fact, Risk admission or numerical Risk rule was added. Backtesting, Portfolio Accounting persistence, Paper, Live, orders and fills remain excluded. No component was activated, and every new Run is `NO_EXECUTION`.

### Implementation

- Added Decision-owned schema-v1 source-neutral command/input/result/specialized-intent/operation/source-link/query contracts, Store/query Protocols, an exact pure mapper and service. Exact operation retries return their original terminal result; conflicting reuse and missing/inconsistent source evidence fail closed and remain durable.
- Added `TargetAdjustmentDecisionPreviewCoordinator`. It requires an explicit Phase 5C link, resolves the exact link/Target/Standardized State evidence through public queries, creates a `TARGET_ADJUSTMENT_DECISION_PREVIEW` Run whose accepted parent is the Phase 5C Run, binds exact definitions/versions, delegates mapping to Decision and records Target/source relationships without performing sign or absolute-value arithmetic.
- Added central SQLite Schema v9 with `target_adjustment_decision_operations`, `target_adjustment_decision_results`, `target_adjustment_trade_intents` and `target_adjustment_decision_source_links`. `SQLiteTargetAdjustmentDecisionStore` transactionally revalidates Run/stage identity, Phase 5C link/source/Target evidence, versions, exact arithmetic and zero-or-one intent cardinality. Migration creates no default or backfilled row.
- Extended Run History with the specialized Run type, Decision/Phase5C/Target/source relationships and typed artifacts. Added a separate Target Adjustment Decision subtab inside the existing Decision owner page with explicit placeholder selection, bounded history, exact persisted inputs/outputs and related-Run navigation. GUI code contains no Decimal/sign/absolute-value calculation, SQL, Risk or execution logic; no Launcher shortcut was added.

### Central database migration evidence

The authorized ignored database `runtime/data/market_history.sqlite3` migrated transactionally from Schema v8 to v9. Verified backup: `runtime/data/backups/market_history.schema-v8-to-v9.20260721T190602679599Z.sqlite3`. Backup remains Schema 8; active reports Schema 9. Both return `PRAGMA integrity_check=ok` and zero foreign-key violations. All 51 pre-existing business-table counts are identical, including 215,340 `market_bars` and 365 `fetch_history`; all four new Phase 5D tables contain zero rows, proving no link selection, Decision, intent or source relationship was defaulted/backfilled.

Rollback requires stopping writers, preserving the v9 database, restoring the named v8 backup and reverting Phase 5D code together. A code-only downgrade against Schema v9 is unsupported. Feature-level rollback may disable new preview commands while retaining readable v9 history; Phase 5A/5B/5C and generic Factor-policy Decision paths remain independently available.

### Files changed

- Source contracts/services: `src/quant_trading/decision/__init__.py`, `errors.py`, `target_adjustment_models.py`, `target_adjustment_interfaces.py`, `target_adjustment_engine.py`, `target_adjustment_service.py`; `src/quant_trading/error_codes.py`; `src/quant_trading/target_position/interfaces.py`.
- Orchestration/Run/Persistence: `src/quant_trading/orchestration/__init__.py`, `target_adjustment_decision_preview.py`; `src/quant_trading/run_history/models.py`; `src/quant_trading/persistence/__init__.py`, `sqlite_database.py`, `run_sqlite_store.py`, `target_position_sqlite_store.py`, `target_adjustment_decision_sqlite_store.py`.
- GUI/composition: `src/quant_trading/algorithm_control/app.py`, `ui/main_panel.py`, `ui/decision_authoring_panel.py`, `ui/target_adjustment_decision_panel.py`.
- Tests: `tests/unit/decision/test_target_adjustment_decision.py`, `test_sqlite_target_adjustment_decision.py`; `tests/unit/algorithm_control/test_target_adjustment_decision_panel.py`; `tests/architecture/test_target_adjustment_decision_boundaries.py`, `test_run_history_boundaries.py`, `test_governance_document_integrity.py`; current-schema/relationship expectations in `tests/unit/asset_state/test_sqlite_asset_state.py`, `tests/unit/capital_allocation/test_sqlite_capital_allocation.py`, `tests/unit/factors/test_sqlite_standardized_state.py`, `tests/unit/run_history/test_research_history.py`, `tests/unit/run_history/test_sqlite_run_history.py`, `tests/unit/target_position/test_linked_target_position.py`, `tests/unit/target_position/test_sqlite_target_position.py`.
- Governance/design/user docs: `PROJECT_COMPASS.md`, `README.md`, `CHANGELOG.md`, `docs/INDEX.md`, `docs/architecture/OVERVIEW.md`, `MODULE_MAP.md`, `DEPENDENCY_RULES.md`, `docs/decisions/README.md`, `ADR-0024-target-adjustment-decision-preview.md`, `docs/proposals/README.md`, `PROPOSAL-017-target-adjustment-decision-preview.md`, `docs/modules/README.md`, `algorithm-control-gui.md`, `analysis-decision-pipeline.md`, `central-persistence.md`, `main-launcher.md`, `run-history.md`, `target-position.md`, `trading-decision.md`, `docs/project/GLOSSARY.md`, `PROJECT_STATE.md`, `ROADMAP.md`, and `logs/EDIT_LOG.md`.

### Validation and bug discovery audit

- Complete suite: **418 passed, 0 failed**, with one existing upstream `websockets.legacy` deprecation warning, in 98.74 seconds.
- Final architecture/governance suite: **59 passed**. Phase 5D focused Decision/repository/GUI suite: **12 passed**; earlier targeted affected suite passed **37 tests**.
- `python -m compileall -q src tests`: passed. `pip check`: no broken requirements. `git diff --check`: passed with only existing Windows LF→CRLF notices.
- Real central Schema v9 and named v8 backup were rechecked after the full suite: both `integrity_check=ok`, both have zero foreign-key violations, active retains 215,340 Market Bars/365 Fetch History rows and all four Phase 5D tables remain empty.
- No confirmed, suspected, deferred or cannot-reproduce Bug was discovered in this implementation; `BUG_LOG` and `KNOWN_ISSUES` are unchanged. No network, credential, Market Data request, account, broker, order, Paper or Live path was used.

### Change Impact Report

Primary module: compatible specialized extension of existing `quant_trading.decision`. Secondary modules: orchestration, public Target Position query, neutral Run History, central Persistence and Algorithm Control. Public contracts, Run type and query relationships are additive; existing generic Decision/Risk contracts are unchanged. Configuration, third-party dependencies and Launcher catalog are unchanged. Database impact is additive central v8→v9 with verified backup/rollback and no backfill. GUI impact is one separate subtab inside the existing Decision owner page. Permission impact is local research SQLite reads/writes only. Trading semantics add only the user-approved exact sign/notional interpretation and specialized non-Risk intent; no account, Risk-approved or order meaning is added. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: closes the approved Target Position → Decision observability arrow using one exact accepted Phase 5C source and persists inputs, intermediate identity, action, intent cardinality, versions and failures. Architecture alignment: Target Position retains desired-level math, Decision owns action/notional meaning, orchestration owns resolution/call order, Persistence owns SQL/cross-object validation, Run History remains neutral and GUI delegates typed services; 59 architecture/governance tests verify the boundaries. Safety alignment: specialized types cannot enter current Risk/Backtesting/Accounting/Execution, all operations are explicit `NO_EXECUTION`, and Paper/Live/automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: `ASM-024` records the approved exact mapping and type isolation. Compass sections updated: evolving phase/evidence, capability/module inventory, approval, non-capabilities, assumption, `INTENT-028`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future code must not select a latest link, add tolerance/rounding/EXIT, reinterpret manual USD as account truth, cast the specialized intent to generic `TradeIntent`, or admit it to Risk/trading without a separately approved contract and migration. Suggested commit message: `feat: add target adjustment decision preview phase 5d`.

## EDIT-20260721-015 — Phase 6A specialized Risk manual-review gate admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after verified Phase 5D, performed a **DEEP proposal-only** admission review. The existing generic `RiskEngine` already owns conservative Risk composition, but it accepts only generic Factor-policy `TradeIntent` with exact FactorSnapshot and neutral account/portfolio/market/system context. Phase 5D deliberately emits a different `TargetAdjustmentTradeIntent`; architecture tests currently ensure it cannot enter Risk. Casting it, fabricating Factor evidence or making generic Risk fields optional would weaken already verified provenance and approval gates.

Created `PROPOSAL-018` for the smallest next observable arrow: a Risk-owned, type-distinct Target-Adjustment Manual-Review Gate. It would accept only one explicitly selected completed Phase 5D specialized intent, copy/revalidate the complete Decision/Phase5C/Target/standardized-state chain, capture the existing locked non-execution safety state and persist three ordered structural gate results: source-chain integrity, non-execution safety state and absence of an approved numerical Risk policy. A valid request would always stop at `MANUAL_REVIEW_REQUIRED`; unsafe state would block; invalid sources and failures would remain durable. HOLD results have no intent and would remain ineligible.

The proposal recommends additive central SQLite v9→v10 evidence and a separate subtab inside the existing Risk page. It explicitly forbids an approved notional, `RiskApprovedTradeIntent`, numerical limit/reduction, account/portfolio/capital/reconciliation facts, pause mutation, Backtesting, Paper, Live, orders or fills. No source code, runtime public contract, database schema/data, GUI behavior, Compass truth, component activation or trading permission changed in this proposal-only task.

### Change Impact Report and approval status

- Proposal status: `PROPOSED`; user approval is pending. Conflict result: `REQUIRES_MIGRATION` with a type adapter; expected implementation blast radius: `MULTI_MODULE`.
- Proposed primary module: compatible specialized extension of `quant_trading.risk`. Secondary modules: application orchestration, public Decision/Target queries, Run History, Persistence and Algorithm Control.
- Proposed public contracts: explicit command, source-neutral Risk input, immutable safety snapshot, specialized final review/rule/attempt/source/query/Store contracts and one neutral Run type. Existing generic Decision/Risk/Risk-approved contracts remain unchanged.
- Proposed database/GUI: four additive central Schema v10 evidence tables and a separate mode in the existing Risk owner page; no backfill/default rows and no new Launcher shortcut.
- Trading/safety meaning: records only that a hypothetical request reached a structural Risk boundary and lacks numerical approval. It cannot approve, reduce, execute or alter exposure.
- Rollback at this proposal stage: remove PROPOSAL-018 and its proposal-index/Roadmap entry while preserving this append-only record; no runtime/database rollback is required.

### Validation and bug discovery audit

The complete architecture/governance suite passed **59 tests**. `git diff --check` passed with only existing Windows LF→CRLF notices. No runtime, database migration, network, account, broker or order path was invoked. No confirmed, suspected, deferred or cannot-reproduce Bug was identified during the admission analysis; `BUG_LOG` and `KNOWN_ISSUES` remain unchanged.

### Compass audit

Intent alignment: proposes the next Risk observability arrow while refusing to invent financial limits or approval authority. Architecture alignment: Decision retains source/action meaning, Risk would own structural gate/rule/disposition meaning, orchestration would resolve exact sources, Persistence would own SQL validation and Run History would remain neutral. Safety alignment: the proposed gate is manual-review/block-only, produces no approved object and retains `NO_EXECUTION`, Live-disabled and automatic-submission-disabled boundaries. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the specialized eligibility, locked rule order, manual-review-only outcome and Schema v10 await explicit approval. Compass sections updated: none because current capability and approved direction remain Phase 5D/Schema v9. Remaining drift risk: implementing before approval, weakening generic Risk provenance, treating structural checks as numerical approval, emitting a Risk-approved type or connecting Backtesting/Execution would be project drift.

## EDIT-20260721-016 — Phase 6A Target Adjustment Risk manual-review gate

### Summary

Implemented the user's explicit approval `批准 PROPOSAL-018` as a **DEEP, MULTI_MODULE, disabled/unconsumed research change**. One explicit completed nonzero Phase 5D `TargetAdjustmentTradeIntent` may now reach a type-distinct Risk-owned structural gate. The gate revalidates exact Phase 5D/Phase5C/Target/standardized-state identities, versions, times and copied Decimal arithmetic, captures immutable application non-execution safety/software identity, and records three locked rules in this order: `SOURCE_CHAIN_INTEGRITY@1`, `NON_EXECUTION_SAFETY_STATE@1`, `NUMERICAL_RISK_POLICY_AVAILABILITY@1`.

A valid source under safe local settings always returns `MANUAL_REVIEW_REQUIRED`; unsafe Live/automatic/execution-capability/manual-confirmation metadata returns `BLOCKED`. Missing/corrupt/conflicting source is durable invalid/failed evidence. HOLD remains ineligible because Phase 5D creates no intent. `TargetAdjustmentRiskReviewResult` is type-distinct from generic Risk and permanently enforces `approved_notional_usd=None` and `risk_approved_intent_id=None`.

### Implementation and contracts

- Added Risk-owned source/safety/command/rule/result/operation/source-link/query/Store contracts, the pure locked structural engine and `TargetAdjustmentRiskService`. Existing generic `RiskEngine`, `RiskDecision`, `RiskRuleResult` and `RiskApprovedTradeIntent` were not changed.
- Added the additive public Decision query `get_target_adjustment_intent(intent_id)` so orchestration resolves exactly one requested durable intent rather than selecting latest/default evidence.
- Added `TargetAdjustmentRiskReviewCoordinator`, `TARGET_ADJUSTMENT_RISK_REVIEW`, ordered Decision/Risk stages, exact Decision/Risk/configuration bindings, idempotent retry, durable query/storage failures and Decision/Phase5C/Target/standardized-state Run relationships. Orchestration contains no rule outcome or amount arithmetic.
- Added central SQLite Schema v10 tables `target_adjustment_risk_operations`, `target_adjustment_risk_review_results`, `target_adjustment_risk_rule_results` and `target_adjustment_risk_source_links`; `SQLiteTargetAdjustmentRiskStore` validates Run/stage/source/version/time/arithmetic/safety/rule/no-approval evidence transactionally and exposes bounded typed reload queries.
- Extended Run History artifacts/relationships with the specialized operation, accepted review, ordered rule pipeline, absent approval fields and upstream Run navigation.
- Added a separate SQL-free `Target Adjustment Manual Review` subtab inside the existing Risk page. It requires explicit intent selection/reason, displays immutable unapproved source/safety/rule/history evidence and has no approval or settings-override control. The existing Launcher Risk shortcut remains the correct entry; no shortcut was added.

### Database migration and rollback

The authorized ignored database `runtime/data/market_history.sqlite3` migrated transactionally from Schema v9 to v10. Verified backup: `runtime/data/backups/market_history.schema-v9-to-v10.20260721T211811897487Z.sqlite3`. The backup remains Schema 9; active reports Schema 10. Both return `PRAGMA integrity_check=ok` and zero foreign-key violations. All 55 pre-existing business-table counts were preserved; the four new Phase 6A tables contain zero rows, proving that no review, rule or approval evidence was defaulted/backfilled.

Feature rollback may disable the specialized review command/GUI while retaining readable v10 history. Physical downgrade requires stopping writers, preserving v10, restoring the named v9 backup and reverting to matching v9 code. Code-only downgrade against Schema v10 is unsupported.

### Files changed

- Risk/domain: `src/quant_trading/risk/target_adjustment_models.py`, `target_adjustment_interfaces.py`, `target_adjustment_engine.py`, `target_adjustment_service.py`, `risk/__init__.py`, and `src/quant_trading/error_codes.py`.
- Orchestration/query/composition: `src/quant_trading/orchestration/target_adjustment_risk_review.py`, `orchestration/__init__.py`, `src/quant_trading/decision/target_adjustment_interfaces.py`, `src/quant_trading/persistence/target_adjustment_decision_sqlite_store.py`, and `src/quant_trading/algorithm_control/app.py`.
- Persistence/Run: `src/quant_trading/persistence/sqlite_database.py`, `target_adjustment_risk_sqlite_store.py`, `run_sqlite_store.py`, `persistence/__init__.py`, and `src/quant_trading/run_history/models.py`.
- GUI: `src/quant_trading/algorithm_control/ui/target_adjustment_risk_panel.py` and `main_panel.py`.
- Tests: new Risk domain/repository/migration/GUI/architecture suites plus current-schema and governance expectation updates under `tests/`.
- Governance/design/user docs: `PROJECT_COMPASS.md` v30, canonical architecture v26/invariants 64–68, ADR-0025, PROPOSAL-018 status, README/CHANGELOG/indexes, affected Risk/Decision/Orchestration/Persistence/Run/Algorithm Control/Launcher/Target module docs, Project State/Roadmap/Glossary and this append-only Edit Log.

### Validation and bug discovery audit

- Full suite: **434 passed**, one existing third-party `websockets.legacy` deprecation warning.
- Architecture/governance suite: **63 passed**.
- Final affected Risk/domain/repository/GUI/architecture suite passed, including source-query failure persistence and transaction-time Phase 5D tamper rejection.
- `python -m compileall -q src tests`: passed.
- `python -m pip check`: passed (`No broken requirements found`).
- `git diff --check`: passed; output contains only repository line-ending conversion notices.
- Final active/backup database integrity and foreign-key checks: clean; all four Phase 6A tables remain empty.

No confirmed, suspected, deferred or cannot-reproduce product Bug was discovered during this task; `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` are unchanged. The initial shell quoting/time-limit diagnostics were tooling-command issues, not repository defects.

### Change Impact Report

Primary module: compatible specialized extension of `quant_trading.risk`. Secondary modules: orchestration, additive Decision query, neutral Run History, central Persistence and Algorithm Control. Public contracts and Run type are additive; generic Risk contracts and Phase 5D financial mapping are unchanged. Configuration is read-only capture of existing safety settings; no financial setting/default was added. Database impact is additive v9→v10 with verified backup/rollback and zero backfill. GUI impact is one subtab inside the existing Risk owner page; Launcher catalog is unchanged. Permissions are local SQLite research reads/writes only. Trading semantics record only that an unapproved hypothetical adjustment reached structural review and still lacks numerical approval. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: closes the approved Decision → Risk observability arrow for one exact specialized intent while preserving all inputs, rules, versions, failures and relationships. Architecture alignment: Decision retains action/source meaning, Risk owns structural disposition/rule meaning, orchestration owns exact resolution/call order, Persistence owns SQL/cross-object validation, Run History remains neutral and GUI delegates typed services; architecture invariants 64–68 and 63 tests verify this. Safety alignment: valid results always require manual review, unsafe execution metadata blocks, approval fields are structurally absent, every Run is `NO_EXECUTION`, and Live/automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: `ASM-025` records the approved specialized eligibility, locked rule order and no-approval invariant. Compass sections updated: evolving phase/evidence, capability/module inventory, approval, assumption, `INTENT-029`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future work must not treat structural checks as numerical approval, weaken source/safety provenance, add values or account facts, cast to generic Risk-approved types, or connect Backtesting/Accounting/Execution without a separately approved contract and migration. Suggested commit message: `feat: add target adjustment risk manual review phase 6a`.

## EDIT-20260721-017 — Phase 6B single-asset exposure-cap admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after verified Phase 6A, performed a **DEEP proposal-only** admission review. Phase 6A already provides a type-distinct structural Risk gate that accepts one explicit nonzero Phase 5D specialized intent, preserves the exact Phase5C/Target/standardized-state chain and always stops a safe valid request at `MANUAL_REVIEW_REQUIRED`. Its three locked rules contain no values and must not be edited or reinterpreted as numerical approval. The generic Factor-policy Risk path remains a different provenance and approval contract.

Created `PROPOSAL-019` for the smallest recommended next numerical slice: one immutable, symbol-specific, user-entered positive Decimal USD `max_target_exposure_usd` version evaluated against one explicitly selected completed Phase 6A manual-review result. The proposed locked `MAX_TARGET_EXPOSURE_USD@1` rule preserves an INCREASE within the cap, reduces an INCREASE crossing the cap to exact remaining headroom, blocks an INCREASE when current exposure is already at/above the cap, and preserves a DECREASE under the existing long-only research-source invariant. Exact equality, Decimal, no-tolerance/no-rounding and non-expansion/non-reversal semantics are stated explicitly.

A positive output is named only `cap_constrained_candidate_notional_usd` and still ends at `MANUAL_REVIEW_REQUIRED`; it is never approved notional and cannot create a generic or specialized Risk-approved object. The proposal includes no cap value/default/active selection, account or broker facts, multi-rule/comprehensive Risk approval, Backtesting, Accounting persistence, Paper, Live, orders or fills. It recommends additive central SQLite v10→v11 definition/operation/result/rule/source-link evidence and an `Exposure Cap Laboratory` subtab inside the existing Risk page, both pending approval. No source code, public contract, runtime behavior, database schema/data, component activation, Compass truth or trading permission changed in this proposal-only task.

### Change Impact Report and approval status

- Proposal status: `PROPOSED`; explicit user approval is pending because the exact cap formula and DECREASE treatment change financial meaning. Conflict result: `REQUIRES_MIGRATION`; expected implementation blast radius: `MULTI_MODULE`.
- Proposed primary module: compatible specialized extension of `quant_trading.risk`. Secondary modules: orchestration, Phase 6A public query, neutral Run History, central Persistence and Algorithm Control.
- Proposed public contracts: immutable cap-definition versions, explicit preview command, source-neutral linked input, one numerical rule result, final manual-review/block result, operation/source/query/Store contracts and one neutral Run type. Existing Phase 6A and generic Risk contracts remain unchanged.
- Proposed database/GUI: five additive central Schema v11 tables with zero backfill, plus one subtab under the existing Risk page; no new Launcher shortcut.
- Trading/safety meaning: this would be the first explicit numerical Risk constraint, but it uses hypothetical research exposure and can only preserve/reduce/block the original direction. One positive candidate still requires manual review and proves no other Risk rule.
- Rollback at this proposal stage: remove PROPOSAL-019 and its proposal-index/Roadmap entry while preserving this append-only record; no runtime/database rollback is required.

### Validation and bug discovery audit

Proposal wording and governance references were reviewed against the verified Phase 6A contracts before editing. The complete architecture/governance suite passed **63 tests**. `git diff --check` passed with only repository line-ending conversion notices. The first test command selected system Python without pytest; rerunning with the project's `.venv` succeeded, so this was a tooling-environment invocation issue rather than a repository defect. No runtime, database migration, network, account, broker or order path was invoked. No confirmed, suspected, deferred or cannot-reproduce Bug was identified during this admission analysis; `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` remain unchanged.

### Compass audit

Intent alignment: proposes the next observable numerical Risk step while requiring the user to decide the actual financial semantics and supplying no value/default. Architecture alignment: Decision and Phase 6A history stay immutable; Risk would own the cap definition/formula/result, orchestration exact resolution, Persistence SQL validation, Run History neutral relationships and GUI presentation only. Safety alignment: the proposed result is manual-review/block-only, non-expanding/non-reversing, type-distinct, `NO_EXECUTION` and unable to reach Backtesting/Accounting/Execution. Unapproved behavior added: none; proposal only. Assumptions introduced: none as current truth—the symbol scope, exact branches/equality behavior, DECREASE preservation, Schema v11 and GUI await explicit approval. Compass sections updated: none because the current implemented capability remains Phase 6A/Schema v10. Remaining drift risk: implementing before approval, inventing a cap/default, calling a candidate approved, mutating Phase 6A rules or adding account/downstream consumers would be project drift.

## EDIT-20260721-018 — Phase 6B single-asset exposure-cap preview

### Summary

Implemented the user's explicit approval `批准 PROPOSAL-019` as a **DEEP, MULTI_MODULE, disabled/unconsumed research change**. The Risk owner now supports immutable symbol-specific positive exact Decimal USD exposure-cap definition versions and one locked `MAX_TARGET_EXPOSURE_USD@1` preview over one explicitly selected exact Phase 6A `MANUAL_REVIEW_REQUIRED` result for the same symbol.

For `INCREASE`, an exact target at/below the cap preserves the original request, a target crossing the cap reduces the candidate to exact `cap - current`, and current exposure at/above the cap produces exact zero and `BLOCKED_BY_EXPOSURE_CAP`. A `DECREASE` preserves the existing long-only risk-reducing request. Exact equality applies; no tolerance, rounding, price/quantity/lot conversion or account-derived input exists. The candidate is structurally constrained to `[0, original]` and cannot reverse direction. Every positive candidate remains `MANUAL_REVIEW_REQUIRED`; no approved notional, Risk-approved intent or downstream executable object exists.

### Implementation and contracts

- Added Risk-owned definition/command/input/rule/result/operation/source-link/query/Store contracts, pure exact-Decimal `SingleAssetExposureCapEngine` and `SingleAssetExposureCapService`. Saving a new/edit definition appends an immutable version; archive appends an immutable `ARCHIVED` successor and prevents future use. There is no default value, `ACTIVE` state or automatic version selection.
- Added `TargetAdjustmentExposureCapPreviewCoordinator`: it resolves one exact Phase 6A result/source link and exact current cap version through public ports, captures current non-execution safety, parents a new `TARGET_ADJUSTMENT_EXPOSURE_CAP_PREVIEW` Run to Phase 6A, delegates all formula work to Risk and records exact upstream Run bindings/relationships. It contains no cap arithmetic.
- Added central SQLite Schema v11 tables `single_asset_exposure_cap_definitions`, `target_adjustment_exposure_cap_operations`, `target_adjustment_exposure_cap_results`, `target_adjustment_exposure_cap_rule_results` and `target_adjustment_exposure_cap_source_links`. `SQLiteExposureCapStore` transactionally revalidates immutable current definition, Phase 6A result/rules/source chain, Run/stage parentage, exact formula, non-expansion and disposition. Accepted, invalid, blocked and failed attempts are durable; no old result is backfilled or reinterpreted.
- Extended Run History with the neutral Run type, exact parent/source relationships and nested definition/operation/result/rule artifacts. Existing Phase 6A and generic Risk contracts remain unchanged.
- Added the SQL/arithmetic-free `Single-Asset Exposure Cap` subtab inside the existing Risk owner page. It requires placeholder-first exact definition/Phase 6A selection and reasons, delegates definition save/archive/preview commands, shows structured source/formula/result/history evidence and opens the Phase 6B/6A/Decision/Phase5C/Target/standardized-state Runs. The existing Risk Launcher shortcut remains sufficient; the application and sixteen-shortcut catalogs are unchanged.

### Database migration and rollback

The authorized ignored database `runtime/data/market_history.sqlite3` migrated transactionally from Schema v10 to v11. Verified backup: `runtime/data/backups/market_history.schema-v10-to-v11.20260721T232152196311Z.sqlite3`. The backup remains Schema 10; active reports Schema 11. Both return `PRAGMA integrity_check=ok` and zero foreign-key violations. An independent table-by-table comparison confirmed all 59 pre-existing business-table counts unchanged; all five new Phase 6B tables contain zero rows.

Feature rollback may disable/hide definition and preview commands while retaining readable v11 history. Physical downgrade requires stopping writers, preserving v11, restoring the named v10 backup and using matching v10 code. Code-only downgrade against Schema v11 is unsupported.

### Files changed

- Risk/domain: `src/quant_trading/risk/exposure_cap_models.py`, `exposure_cap_interfaces.py`, `exposure_cap_engine.py`, `exposure_cap_service.py`, `risk/__init__.py`, and `src/quant_trading/error_codes.py`.
- Orchestration/Run/Persistence: `src/quant_trading/orchestration/target_adjustment_exposure_cap_preview.py`, `orchestration/__init__.py`, `src/quant_trading/run_history/models.py`, `src/quant_trading/persistence/exposure_cap_sqlite_store.py`, `sqlite_database.py`, `run_sqlite_store.py`, and `persistence/__init__.py`.
- GUI/composition: `src/quant_trading/algorithm_control/ui/exposure_cap_panel.py`, `target_adjustment_risk_panel.py`, `main_panel.py`, and `src/quant_trading/algorithm_control/app.py`.
- Tests: `tests/unit/risk/test_exposure_cap.py`, `test_sqlite_exposure_cap.py`; `tests/unit/algorithm_control/test_exposure_cap_panel.py`; `tests/architecture/test_exposure_cap_boundaries.py`, `test_run_history_boundaries.py`, `test_governance_document_integrity.py`; current-Schema migration expectations in Capital Allocation, Asset State, standardized state, Target Position, linked Target Position, specialized Decision/Risk and Run History suites.
- Governance/design/user docs: `PROJECT_COMPASS.md` v31, canonical architecture v27/invariants 69–73, ADR-0026, PROPOSAL-019 status/approval, README/CHANGELOG/indexes, affected Risk/Decision/Orchestration/Persistence/Run/Algorithm Control/Launcher module docs, Project State/Roadmap/Glossary and this append-only Edit Log.

### Validation and bug discovery audit

- Full suite: **455 passed**, one existing third-party `websockets.legacy` deprecation warning, in 102.89 seconds.
- Architecture/governance suite: **68 passed**. Schema migration/legacy-domain regression subset: **52 passed**. Phase 6B domain/repository/GUI/architecture suites include exact branches/equalities, DECREASE, archive, idempotency, unsafe fail-closed, definition tamper, source-query failure, Run artifacts/relationships and v10→v11 rollback.
- `python -m compileall -q src`: passed. `python -m pip check`: `No broken requirements found`. `git diff --check`: passed with only normal Windows LF→CRLF notices.
- Final active/backup checks: versions 11/10, integrity `ok`, zero foreign-key violations and active v11 cap-table counts `0|0|0|0|0`.
- No network, credential, Market Data request, account, broker, order, Paper or Live path was used.

No confirmed, suspected, deferred or cannot-reproduce product Bug was discovered. The initial full-suite 120-second timeout and PowerShell verification quoting errors were tooling-command issues; the complete rerun and independent SQLite comparison passed. `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` are unchanged.

### Change Impact Report

Primary module: compatible specialized extension of existing `quant_trading.risk`. Secondary modules: exact-source orchestration, neutral Run History, central Persistence and Algorithm Control. Public contracts and Run type are additive; generic Risk and locked Phase 6A contracts are unchanged. Configuration has no financial default or new file. Database impact is additive v10→v11 with verified backup/rollback and zero backfill. GUI impact is one subtab inside the existing Risk page; Launcher catalog is unchanged. Permissions are local SQLite research reads/writes only. Trading semantics add exactly the user-approved one-symbol hypothetical USD cap rule, but one rule remains incomplete/unapproved for execution. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: implements the first explicit numerical Risk constraint while preserving every input, version, intermediate rule, failure and upstream Run relationship. Architecture alignment: Decision/Phase 6A retain immutable source meaning, Risk owns definition/formula/disposition, orchestration owns exact resolution/call order, Persistence owns SQL/cross-object validation, Run History remains neutral and GUI delegates typed services; architecture invariants 69–73 and 68 tests verify the boundaries. Safety alignment: the candidate can only preserve/reduce/block, positive candidates still require manual review, approval fields/types and downstream consumers are absent, every Run is `NO_EXECUTION`, and Live/automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: `ASM-026` records the approved exact source/version/formula/no-approval interpretation; no cap amount was assumed. Compass sections updated: evolving phase/evidence, capability/module inventory, approval, DEC-007 clarification, assumption, `INTENT-030`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future work must not invent/select a cap value, treat Phase 5D USD as account truth, call a one-rule candidate approved, add a latest/default selector, mutate Phase 6A, compose extra rules or connect Backtesting/Accounting/Execution without separate approval. Suggested commit message: `feat: add single-asset exposure cap preview phase 6b`.

## EDIT-20260721-019 — End-of-day handoff checkpoint

### Recorded state

- Recorded at `2026-07-21T17:29:04-07:00`. Current governed capability is Phase 6B from approved `PROPOSAL-019`: the single-asset exposure-cap preview is implemented and verified, but remains disabled/unconsumed and `NO_EXECUTION`. `docs/project/PROJECT_STATE.md` already carries the current product state, limitations and evidence; this checkpoint does not change behavior.
- Central SQLite is Schema v11. The most recent migration row is v11 (`single-asset exposure-cap definitions and numerical Risk preview evidence`). `PRAGMA integrity_check` returns `ok`, `PRAGMA foreign_key_check` returns no rows, and all five Phase 6B tables currently contain zero rows. The verified rollback backup remains `runtime/data/backups/market_history.schema-v10-to-v11.20260721T232152196311Z.sqlite3` at Schema v10.
- Latest completed verification remains: full suite **455 passed** with one existing third-party warning; architecture/governance suite **68 passed**; migration/legacy-domain subset **52 passed**; compileall, dependency check and diff check passed. Tests were not rerun for this record-only checkpoint because no code, schema, configuration or financial semantics changed.
- Git branch is `main`; latest committed revision is `34e4f69 feat: add standardized state and linked target preview`. The working tree is intentionally **uncommitted** with 84 entries (45 modified, 39 untracked), including the cumulative approved Phase 5D/6A/6B work for `PROPOSAL-017`, `PROPOSAL-018` and `PROPOSAL-019`. No commit or push was authorized or performed in this checkpoint.
- No cap definition/value/default exists, no approved Risk object or complete multi-rule Risk approval exists, and no Portfolio Accounting persistence, Backtesting consumer, broker/account access, order, Paper or Live behavior was added. Automatic submission and Live remain disabled.
- No confirmed, suspected, deferred or cannot-reproduce product Bug was discovered during this checkpoint. `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` remain unchanged.

### Resume instructions

1. Read `AGENTS.md`, `PROJECT_COMPASS.md` v31, `docs/architecture/OVERVIEW.md` v27, `docs/project/PROJECT_STATE.md`, and the latest `EDIT-20260721-018` / `EDIT-20260721-019` entries.
2. Inspect `git status` before editing and preserve all existing modified/untracked files; they are the current cumulative approved implementation, not disposable scratch changes.
3. Do not infer Phase 6C, invent a cap value/default, reinterpret one-rule preview output as approval, or connect Accounting/Backtesting/Execution. No further development slice is currently approved.
4. If the user asks for a repository checkpoint, review the full diff and secret safety, then commit/push only under that explicit authorization. If the user asks to continue product development, begin with the proposal/admission process for the exact user-selected next slice.

### Compass audit

Intent alignment: preserves a precise daily continuation point and distinguishes completed implementation from committed repository state. Architecture and safety alignment: no source, contract, database, GUI, configuration, financial meaning or execution authority changed. Unapproved behavior added: none. Assumptions introduced: none. Compass sections updated: none; the current truth is already recorded in Compass v31 and Project State. Remaining drift risk: the uncommitted cumulative work must be preserved, and future work must not proceed beyond Phase 6B without explicit scope and approval.

## EDIT-20260722-001 — Phase 6C research asset cash-floor admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after the verified Phase 6B checkpoint, performed a **DEEP proposal-only** admission review. Phase 6B already owns one exact symbol-specific maximum-target-exposure rule over a Phase 6A manual-review result; it preserves/reduces/blocks a specialized candidate but cannot approve it. Phase 5C already persists an explicit hypothetical `research_capital_basis_usd`, while Research Capital Allocation separately owns inactive planning buckets and Portfolio Accounting remains in-memory. Neither existing cash domain was treated as factual input or modified.

Created `PROPOSAL-020` for the smallest recommended compatible extension: a disabled/unconsumed Phase 6C second numerical Risk preview that consumes one explicit **positive** Phase 6B manual-review candidate and one explicit current same-symbol immutable minimum research-cash definition. The new locked `MIN_RESEARCH_ASSET_CASH_USD@1` rule is order 2 after the immutable Phase 6B `MAX_TARGET_EXPOSURE_USD@1` source evidence. It uses the exact persisted manual Phase 5C research basis, not Capital Allocation, Portfolio Accounting, Buying Power or broker cash.

For an `INCREASE`, the proposed exact capacity is `max(research basis - current exposure - floor, 0)` and the new candidate is the minimum of that capacity and the Phase 6B candidate. Exact equality at the floor passes; positive smaller capacity reduces; zero capacity blocks. For a verified long-only `DECREASE`, the Phase 6B candidate is preserved because it increases the hypothetical remainder. The proposed definition accepts a finite non-negative Decimal USD value; explicit zero is a versioned rule value meaning a zero residual floor, not an absent/default value. No amount is supplied.

Every positive candidate would still be `MANUAL_REVIEW_REQUIRED`; zero increase would be `BLOCKED_BY_RESEARCH_CASH_FLOOR`. The proposal permanently excludes approved-notional/approved-intent output, factual cash, complete Risk approval, Backtesting, Accounting persistence, Paper, Live, orders and fills. It proposes additive central SQLite v11→v12 definition/operation/result/rule/source-link evidence and one subtab inside the existing Risk page, both pending approval. No code, public contract, runtime behavior, database schema/data, Compass truth, component activation or trading permission changed.

### Change Impact Report and approval status

- Proposal status: `PROPOSED`; explicit user approval is pending because the cash-source meaning, non-negative/explicit-zero definition, exact formula/equality behavior, cap-first rule order and DECREASE treatment change financial semantics.
- Conflict result: `REQUIRES_MIGRATION` plus `NEEDS_USER_DECISION`; expected implementation blast radius: `MULTI_MODULE`.
- Proposed primary module: compatible specialized extension of `quant_trading.risk`. Secondary modules: orchestration, public Phase 6B/Target queries, neutral Run History, central Persistence and Algorithm Control.
- Proposed database/GUI: five additive central Schema v12 tables with zero backfill/default rows, plus one subtab under the existing Risk page; no Launcher shortcut.
- Trading/safety meaning: the rule may only preserve/reduce/block the inherited same-direction candidate. Passing two rules remains incomplete and cannot create generic Risk approval, an order or execution authority.
- Rollback at this proposal stage: remove PROPOSAL-020 and its proposal-index/Roadmap entry while preserving this append-only record; no runtime/database rollback is required.

### Files changed

- `docs/proposals/PROPOSAL-020-target-adjustment-research-asset-cash-floor.md`
- `docs/proposals/README.md`
- `docs/project/ROADMAP.md`
- `logs/EDIT_LOG.md`

### Validation and bug discovery audit

- Complete architecture/governance suite: **68 passed**.
- `git diff --check` for the proposal, proposal index and Roadmap: passed; output contains only normal Windows LF→CRLF notices.
- No runtime, schema migration, database mutation, network, account, broker, order, Paper or Live path was invoked.
- No confirmed, suspected, deferred or cannot-reproduce product Bug was identified. `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` remain unchanged.

### Compass audit

Intent alignment: proposes the next observable Risk constraint while preserving the user's staged, transparent and versioned research direction. Architecture alignment: Risk would own the formula/result, orchestration exact public-source resolution, Persistence SQL validation, Run History neutral relationships and GUI typed presentation; existing Phase 6B, Capital Allocation and Portfolio Accounting owners remain unchanged. Safety alignment: the proposed result is non-expanding/non-reversing, manual-review/block-only, `NO_EXECUTION`, disabled and unable to reach Backtesting/Accounting/Execution. Unapproved behavior added: none; proposal only. Assumptions introduced: none as implemented truth—the hypothetical-basis interpretation, explicit-zero meaning, formula, order, Schema v12 and GUI await approval. Compass sections updated: none because Phase 6B/Schema v11 remains the latest implemented state. Remaining drift risk: implementing before approval, calling the hypothetical remainder actual Asset Cash, composing two rules into approval, changing Phase 6B, choosing a value/default or adding a downstream consumer would be project drift.

## EDIT-20260722-002 — Implement approved Phase 6C research asset cash-floor preview

### Approval, scope and result

- The user explicitly approved `PROPOSAL-020` on 2026-07-22. Implemented the approved **DEEP**, `MULTI_MODULE` Phase 6C slice as a compatible extension of the existing Risk owner, exact-source orchestration, neutral Run History, central Persistence and existing Algorithm Control Risk page.
- Added immutable symbol-specific finite non-negative Decimal USD research-cash-floor definition versions. Explicit zero is valid and stored; no value, Active selection or default is supplied. Definition update/archive creates immutable successors and historical results continue to reference their exact versions.
- Added locked order-2 `MIN_RESEARCH_ASSET_CASH_USD@1` after immutable Phase 6B `MAX_TARGET_EXPOSURE_USD@1` evidence. The source is exactly one positive Phase 6B `MANUAL_REVIEW_REQUIRED` result and the exact persisted Phase 5C hypothetical `research_capital_basis_usd`; no Capital Allocation, Portfolio Accounting, account, broker, settled cash or Buying Power is read.
- For `INCREASE`, exact Decimal capacity is `max(B-C-F, 0)` and candidate is `min(N, capacity)`. Equality passes; positive lower capacity reduces; zero capacity yields `BLOCKED_BY_RESEARCH_CASH_FLOOR`. Long-only `DECREASE` preserves `N` and records exact pre/post residual and shortfall. No tolerance, rounding, quantity, price, fee or currency conversion was introduced.
- Every positive result remains `MANUAL_REVIEW_REQUIRED`. The Phase 6C result is type-distinct, has no approved-notional/approved-intent field and has no downstream Backtesting, Accounting or Execution consumer. All Runs remain `NO_EXECUTION`; Live and automatic submission remain disabled.
- Added durable definition/operation/result/order-2-rule/source-link evidence and exact Run relationships. Exact retries are idempotent; conflicting operation reuse, missing/unsafe/archived sources, definition/source tamper and storage failures fail closed while attempts remain searchable.
- Added one presentation-only subtab inside the existing Risk page for definition lifecycle, explicit eligible-source selection, persisted two-rule chain, hypothetical residual/shortfall, history/filtering and `Open Run`. No Launcher application or shortcut was added.

### Central SQLite v11→v12 migration

- Migrated the ignored real central database `runtime/data/market_history.sqlite3` transactionally from Schema v11 to v12 after creating `runtime/data/backups/market_history.schema-v11-to-v12.20260722T182459956607Z.sqlite3`.
- Schema v12 adds exactly five additive tables: `research_asset_cash_floor_definitions`, `target_adjustment_cash_floor_operations`, `target_adjustment_cash_floor_results`, `target_adjustment_cash_floor_rule_results` and `target_adjustment_cash_floor_source_links` plus their indexes/constraints. No historical row was backfilled or reinterpreted.
- Final verification: active database version 12 and backup version 11; both `integrity_check=ok`, both have zero foreign-key violations, all 64 pre-existing business-table row counts match exactly, and every new Phase 6C table contains zero rows.
- Rollback requires stopping writers, retaining the v12 file and restoring the verified v11 backup with matching v11 code. Code rollback alone is not a database downgrade.

### Files changed for Phase 6C

- Risk/domain: `src/quant_trading/risk/research_cash_floor_models.py`, `research_cash_floor_engine.py`, `research_cash_floor_interfaces.py`, `research_cash_floor_service.py`, `risk/__init__.py`, and `src/quant_trading/error_codes.py`.
- Orchestration/query contracts: `src/quant_trading/orchestration/target_adjustment_research_cash_floor_preview.py`, `orchestration/__init__.py`, and `src/quant_trading/target_position/interfaces.py`.
- Persistence/Run History: `src/quant_trading/persistence/research_cash_floor_sqlite_store.py`, `sqlite_database.py`, `run_sqlite_store.py`, `persistence/__init__.py`, and `src/quant_trading/run_history/models.py`.
- GUI/composition: `src/quant_trading/algorithm_control/ui/research_cash_floor_panel.py`, `target_adjustment_risk_panel.py`, `main_panel.py`, and `src/quant_trading/algorithm_control/app.py`.
- Tests: `tests/unit/risk/test_research_cash_floor.py`, `test_sqlite_research_cash_floor.py`, `tests/unit/algorithm_control/test_research_cash_floor_panel.py`, `tests/architecture/test_research_cash_floor_boundaries.py`, plus governed Run-history/current-schema/migration regression updates under `tests/architecture/` and the affected legacy-domain SQLite test files.
- Governance/design/user docs: `PROJECT_COMPASS.md` v32, canonical architecture v28/invariants 74–78, ADR-0027, approved/implemented PROPOSAL-020, README/CHANGELOG/indexes, affected Risk/Target/Decision/Orchestration/Persistence/Run/Algorithm Control/Launcher module docs, Project State/Roadmap/Glossary and this append-only Edit Log.

### Validation and bug discovery audit

- Complete suite: **475 passed**, with one existing third-party `websockets.legacy` deprecation warning, in 161.67 seconds.
- Architecture/governance suite: **73 passed**. Focused Phase 6C domain/repository/GUI/architecture/governance suite: **25 passed**. Coverage includes exact increase/equality/reduce/block and DECREASE behavior, explicit zero and invalid/non-finite values, restart reload, idempotency/conflict, definition version/archive, durable missing/unsafe/failed attempts, tamper rejection, ordered Run artifacts/relationships and v11→v12 backup/rollback.
- `python -m compileall -q src`: passed. `python -m pip check`: `No broken requirements found`. `git diff --check`: passed with only normal Windows LF→CRLF notices.
- No network, credential, Market Data request, account, broker, order, Paper or Live path was used.
- No confirmed, suspected, deferred or cannot-reproduce product Bug was discovered. The initial system-Python `pytest` invocation and two PowerShell verification quoting attempts were tooling-command errors; reruns with the project virtual environment and safer read-only query passed. `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` are unchanged.

### Change Impact Report

Primary module: compatible specialized extension of `quant_trading.risk`. Secondary modules: exact-source orchestration, neutral Run History, central Persistence and Algorithm Control. Public contracts and Run type are additive; Phase 5C/6A/6B historical meaning and generic Risk contracts are unchanged. Configuration adds no financial default or credential. Database impact is additive v11→v12 with verified backup/rollback and zero backfill. GUI impact is one subtab inside the existing Risk page; Launcher catalog remains three applications/sixteen shortcuts. Permissions are local SQLite research reads/writes only. Trading semantics add exactly the user-approved hypothetical research-cash-floor formula as a second non-expanding rule, but do not compose complete approval. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: advances the observable Risk chain from one to two exact ordered numerical research constraints while persisting inputs, versions, intermediate rules, failures and complete provenance. Architecture alignment: Risk owns definition/formula/disposition, orchestration owns exact public-source resolution and call order, Persistence owns SQL/cross-object validation, Run History remains neutral and GUI delegates typed services; canonical invariants 74–78 and 73 architecture/governance tests protect these boundaries. Safety alignment: the result can only preserve/reduce/block and cannot reverse direction; positive candidates remain manual-review-only, approval fields/types/consumers are absent, every Run is `NO_EXECUTION`, and Live/automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: only `ASM-027`, recording the explicitly approved hypothetical-basis, explicit-zero, formula/order and no-approval semantics; no amount was assumed. Compass sections updated: metadata/current phase, capability/module inventory, user approval, DEC-007 clarification, `ASM-027`, `INTENT-031`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future work must not invent/select a floor value, call the hypothetical residual actual cash, treat two rules as complete approval, add factual Capital/Accounting/broker adapters, alter Phase 6B, or connect Backtesting/Accounting/Execution without a separately approved proposal. Suggested commit message: `feat: add research cash floor preview phase 6c`.

## EDIT-20260722-003 — Phase 6D research asset-cash availability admission proposal

### Scope and existing-work reminder

In response to the user's request to continue development after the verified Phase 6C checkpoint, performed a **DEEP proposal-only** admission review. Phase 6C already owns a second ordered numerical Risk preview over a manual Phase 5C hypothetical per-asset basis. Phase 3A separately owns conserved `RESEARCH_INPUT` Capital Plans containing one protected locked reserve, one protected tactical reserve and symbol-specific `ASSET_CASH` buckets; these plans are inactive planning evidence and are not Portfolio Accounting or broker facts. Portfolio Accounting remains an in-memory factual-domain scaffold.

Created `PROPOSAL-021` for the smallest recommended compatible bridge: a disabled/unconsumed Phase 6D third numerical Risk preview that explicitly pairs one positive Phase 6C manual-review candidate with one user-selected Phase 3A plan and its exact latest conserved snapshot. `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1` would limit `INCREASE` to the same-symbol research `ASSET_CASH` balance, preserve long-only `DECREASE`, keep all arithmetic exact Decimal and retain the complete Phase 6C/upstream plus Capital Snapshot Run provenance.

The proposal makes the critical limitation explicit: a preview does **not** reserve or move cash. It records `research_cash_reserved=false`, warns that multiple previews can reuse the same balance, never appends a Capital transfer/snapshot, and cannot become complete Risk approval or execution. This avoids creating a second cash authority or making Phase 3A look factual.

### Change Impact Report and approval status

- Proposal status: `PROPOSED`; explicit user approval is pending because the Capital snapshot meaning, formula/equality, latest-snapshot condition, DECREASE treatment and non-reservation behavior change financial semantics.
- Conflict result: `COMPATIBLE_EXTENSION` + `REQUIRES_ADAPTER` + `REQUIRES_MIGRATION` + `NEEDS_USER_DECISION`; expected implementation blast radius: `MULTI_MODULE`.
- Proposed primary module: compatible specialized extension of `quant_trading.risk`. Secondary modules: exact-source orchestration, public read-only Capital Allocation query use, neutral Run History, central Persistence and Algorithm Control.
- Proposed database/GUI: four additive central Schema v13 operation/result/rule/source-link tables with zero backfill/default rows, plus one subtab under the existing Risk page; no Launcher shortcut.
- Trading/safety meaning: the third rule may only preserve/reduce/block and cannot reserve funds, mutate Capital Allocation, create an approved object or reach Backtesting/Accounting/Execution.
- Alternatives rejected for this slice: reusing the already-constrained Phase 5C basis again, reading non-persistent Accounting/broker cash, letting Risk mutate/reserve Phase 3A cash, or presenting the protected research reserve as factual insurance cash.
- Rollback at this proposal stage: remove PROPOSAL-021 and its proposal-index/Roadmap entries while preserving this append-only record; no runtime/database rollback is required.

### Files changed

- `docs/proposals/PROPOSAL-021-target-adjustment-research-asset-cash-availability.md`
- `docs/proposals/README.md`
- `docs/project/ROADMAP.md`
- `logs/EDIT_LOG.md`

### Validation and bug discovery audit

- No runtime code, public contract, schema, database data, GUI behavior, Compass truth, component activation or trading permission changed.
- Architecture/governance and diff checks are recorded after this proposal edit.
- No network, account, broker, order, Paper or Live path was invoked.
- No confirmed, suspected, deferred or cannot-reproduce product Bug was identified. `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` remain unchanged.

### Compass audit

Intent alignment: proposes a transparent bridge from existing stock-specific research funding evidence into the ordered Risk preview without claiming factual cash. Architecture alignment: Capital Allocation retains plan/bucket/conservation/mutation ownership; Risk would own candidate limitation; orchestration would resolve the public evidence; Persistence would validate exact source links; GUI would only delegate and display. Safety alignment: the proposed candidate is non-expanding/non-reversing, non-reserving, manual-review/block-only, `NO_EXECUTION`, disabled and unable to reach Backtesting/Accounting/Execution. Unapproved behavior added: none; proposal only. Assumptions introduced: none as implemented truth—the selected latest snapshot, exact formula and non-reservation semantics await approval. Compass sections updated: none because Phase 6C/Schema v12 remains current implemented truth. Remaining drift risk: implementing before approval, auto-selecting a plan, calling research cash factual, mutating/reserving a bucket, composing three rules into approval or adding a downstream consumer would be project drift.

## EDIT-20260722-004 — Implement approved Phase 6D research asset-cash availability preview

### Approval, scope and result

- The user explicitly approved `PROPOSAL-021` on 2026-07-22. Implemented the approved **DEEP**, `MULTI_MODULE` Phase 6D slice as a compatible extension of the existing Risk owner, exact-source orchestration, public read-only Capital Allocation queries, neutral Run History, central Persistence and the existing Algorithm Control Risk page.
- Added locked order-3 `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1` after immutable Phase 6B order-1 and Phase 6C order-2 evidence. The source is exactly one positive Phase 6C `MANUAL_REVIEW_REQUIRED` result, one explicitly selected Phase 3A `RESEARCH_INPUT` USD plan, and that plan's exact latest conserved snapshot with a same-symbol `ASSET_CASH` balance.
- For `INCREASE`, exact Decimal candidate is `min(N, A)`, where `N` is the Phase 6C candidate and `A` is the selected asset-cash balance. Equality passes; a lower positive balance reduces; zero balance yields `BLOCKED_BY_RESEARCH_ASSET_CASH`. Long-only `DECREASE` preserves `N` and records hypothetical post cash `A + N`. No rounding, tolerance, quantity, price, fee or currency conversion was introduced.
- Every positive result remains `MANUAL_REVIEW_REQUIRED`. Every result records `research_cash_reserved=false` and a repeated-preview warning: this read-only preview does not reserve, transfer or otherwise mutate Capital Allocation cash, so independent previews may reuse the same balance.
- Added durable operation/result/order-3-rule/source-link evidence, including the inherited order-1/order-2 chain and exact Run relationships. Exact retries are idempotent; conflicting operation reuse, missing/unsafe/non-latest/non-conserved/mismatched sources, incomplete snapshot bucket coverage, source tamper and storage failures fail closed while attempts remain searchable.
- Added one presentation-only subtab inside the existing Risk page for explicit Phase 6C/plan/latest-snapshot selection, stored inputs/results, ordered rule evidence, non-reservation warning, history/filtering and `Open Run`. The GUI performs no formula, SQL, Capital mutation or implicit plan selection. No Launcher application or shortcut was added.
- No complete Risk approval, Risk-approved intent, Capital reservation, factual cash claim, transfer, new trading formula, Backtesting integration, Portfolio Accounting persistence, Paper, Live, order or fill behavior was added.

### Central SQLite v12→v13 migration

- Migrated the ignored real central database `runtime/data/market_history.sqlite3` transactionally from Schema v12 to v13 after creating `runtime/data/backups/market_history.schema-v12-to-v13.20260722T195926466864Z.sqlite3` (60,342,272 bytes).
- Schema v13 adds exactly four additive tables: `target_adjustment_research_asset_cash_operations`, `target_adjustment_research_asset_cash_results`, `target_adjustment_research_asset_cash_rule_results` and `target_adjustment_research_asset_cash_source_links`, with their constraints/indexes. No historical row was backfilled or reinterpreted.
- Pre-migration verification: Schema v12, 70 non-internal tables, 216,055 rows, `integrity_check=ok`, zero foreign-key violations. Final verification: Schema v13, 74 non-internal tables, 216,056 rows including the schema-version row, `integrity_check=ok`, zero foreign-key violations, and all four new Phase 6D tables contain zero rows.
- Rollback requires stopping writers, retaining the v13 file and restoring the verified v12 backup with matching v12 code. Disabling/hiding the Phase 6D subtab and command is the non-destructive application rollback; code rollback alone is not a database downgrade.

### Files changed for Phase 6D

- Risk/domain: `src/quant_trading/risk/research_asset_cash_models.py`, `research_asset_cash_engine.py`, `research_asset_cash_interfaces.py`, `research_asset_cash_service.py`, `risk/__init__.py`, and `src/quant_trading/error_codes.py`.
- Orchestration/query contracts: `src/quant_trading/orchestration/target_adjustment_research_asset_cash_preview.py` and `orchestration/__init__.py`, using existing public Capital Allocation queries without introducing a Risk→Capital dependency.
- Persistence/Run History: `src/quant_trading/persistence/research_asset_cash_sqlite_store.py`, `sqlite_database.py`, `run_sqlite_store.py`, `persistence/__init__.py`, and `src/quant_trading/run_history/models.py`.
- GUI/composition: `src/quant_trading/algorithm_control/ui/research_asset_cash_panel.py`, `target_adjustment_risk_panel.py`, `main_panel.py`, and `src/quant_trading/algorithm_control/app.py`.
- Tests: `tests/unit/risk/test_research_asset_cash.py`, `test_sqlite_research_asset_cash.py`, `tests/unit/algorithm_control/test_research_asset_cash_panel.py`, `tests/architecture/test_research_asset_cash_boundaries.py`, plus affected current-schema, migration, Run-history, architecture and legacy persistence regression tests.
- Governance/design/user docs: `PROJECT_COMPASS.md` v33, canonical architecture v29/invariants 79–83, ADR-0028, approved/implemented PROPOSAL-021, README/CHANGELOG/indexes, affected Risk/Capital/Decision/Orchestration/Persistence/Run/Algorithm Control/Launcher module docs, Project State/Roadmap/Glossary, Bug Log and this append-only Edit Log.

### Validation and bug discovery audit

- Complete suite: **495 passed**, with one existing third-party `websockets.legacy` deprecation warning (`KI-0005`), in 208.75 seconds.
- Architecture/governance suite: **79 passed** in 14.35 seconds. Focused Phase 6D domain/repository/GUI/architecture tests passed; coverage includes exact increase/equality/reduce/block and DECREASE behavior, zero/invalid values, restart reload, idempotency/conflict, durable invalid/failed attempts, source/latest/conservation/coverage/tamper rejection, ordered Run artifacts/relationships and v12→v13 backup/rollback.
- `python -m compileall -q src tests`: passed. `python -m pip check`: `No broken requirements found`. `git diff --check`: passed with only normal Windows LF→CRLF notices.
- The real central database, verified backup and all runtime data remain ignored and untracked. No network, credential, Market Data request, account, broker, order, Paper or Live path was used.
- Discovered and fixed `BUG-20260722-001`: stale Run History documentation incorrectly said Phase 5D had no Risk consumer; it now truthfully documents the disabled 6A→6B→6C→6D research chain and absence of complete approval/execution.
- Discovered and fixed `BUG-20260722-002`: initial source validation allowed a conserved snapshot to omit a plan bucket while shifting its balance to another existing bucket. Orchestration and transactional persistence now require exact plan-bucket/snapshot-balance identity, with a regression test proving durable `INVALID_INPUT` and no result for tampered coverage.
- No new Bug remains deferred or cannot-reproduce; `KNOWN_ISSUES.md` needs no new current issue entry.

### Change Impact Report

Primary module: compatible specialized extension of `quant_trading.risk`. Secondary modules: exact-source orchestration, public read-only Capital Allocation queries, neutral Run History, central Persistence and Algorithm Control. Public contracts and Run type are additive; Phase 3A/5C/6A/6B/6C historical meaning and generic Risk contracts remain unchanged. Configuration adds no financial default, amount, credential or activation. Database impact is additive v12→v13 with verified backup/rollback and zero backfill. GUI impact is one subtab inside the existing Risk page; Launcher catalog remains unchanged. Permissions are local SQLite research reads/writes only. Trading semantics add exactly the approved third non-expanding read-only constraint while retaining manual review and non-reservation; no downstream execution authority is created. Blast radius: `MULTI_MODULE` as approved.

### Compass audit

Intent alignment: completes the approved observable third-stage Risk preview by tying a positive Phase 6C candidate to exact stock-specific research cash evidence and persisting all inputs, versions, intermediate rules, failures and provenance. Architecture alignment: Risk owns formula/disposition, orchestration resolves exact public sources, Capital Allocation retains plan/bucket/conservation/mutation authority, Persistence enforces cross-object truth, Run History remains neutral and GUI only delegates/displays; architecture/governance tests protect these boundaries. Safety alignment: order 3 can only preserve/reduce/block an existing candidate, cannot reverse direction, never reserves or moves cash, keeps positive results manual-review-only, exposes no approval field/type/consumer, and every Run remains `NO_EXECUTION`; Live and automatic submission remain disabled. Unapproved behavior added: none. Assumptions introduced: only approved `ASM-028`, recording explicit-source/latest/conserved/same-symbol/exact-Decimal/non-reservation semantics; no plan, balance or amount is auto-selected or invented. Compass sections updated: metadata/current phase, capability and module inventory, user approval/evidence, DEC-007 three-rule clarification, `ASM-028`, `INTENT-032`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future work must not call research cash factual or reserved, auto-select a plan, treat three previews as complete approval, mutate Capital Allocation from Risk, add factual Accounting/broker adapters, or connect Backtesting/Accounting/Execution without a separately approved proposal. Suggested commit message: `feat: add research asset cash preview phase 6d`. No commit or push was performed.

## EDIT-20260722-005 — Harden Phase 6D Capital evidence and propose a consolidated Risk explorer

### Request interpretation and admission result

- The user asked to continue development after the verified PROPOSAL-021 checkpoint. The task was classified `STANDARD`: first identify the smallest safe next slice, preserve the uncommitted Phase 5D–6D worktree and stop before any unapproved financial/authority change.
- Repository evidence confirmed that Phase 6A–6D already persist one structural gate and three ordered numerical research previews, but no later slice was approved. Creating another Risk formula, selecting real/default values, composing complete approval, reserving cash or adding a Backtesting/Execution consumer would exceed current authority.
- Created `PROPOSAL-022`, status `PROPOSED`, for the smallest compatible observability extension: a read-only consolidated Risk Chain Explorer in the existing Risk page. It would reuse exact Phase 6A–6D query/results, add optional inclusive UTC bounds to the Phase 6D read query, display stored structural/numerical chains, compare two exact results side by side and preserve all Open Run links. It explicitly excludes recalculation, new persistence, approval, acknowledgement, reservation, export, Backtesting, Accounting, Paper, Live, orders and execution.
- Proposal impact is `LIMITED`, has no Schema migration and requires explicit user approval before implementation. Roadmap and Proposal index now record it as pending, not approved.

### Phase 6D integrity hardening

- Discovered and fixed `BUG-20260722-003`: exact bucket-ID coverage plus total conservation did not detect a manually tampered snapshot that moved money out of a protected reserve into asset cash while preserving every ID and the total.
- Phase 6D orchestration now validates every snapshot balance's bucket type, currency and symbol against its immutable plan definition and requires locked/tactical reserve balances to equal their protected initial values.
- `SQLiteResearchAssetCashStore` independently repeats the same full metadata and protected-reserve validation inside the completed-result transaction. Existing asset-to-asset transfers remain valid; no candidate formula, Capital row, public result contract or database schema changed.
- Added two regressions: one requires durable `INVALID_INPUT` and no accepted result for a conserved protected-reserve tamper; the other directly proves the transaction-time revalidation rejects a source captured before the tamper.
- Discovered and fixed `BUG-20260722-004`: Compass B17 still named PROPOSAL-020 instead of latest completed PROPOSAL-021. Added a governance regression for the exact Phase 6D checkpoint.
- Discovered and fixed `BUG-20260722-005`: the queued Plotly load test did not show its QWebEngine view and deterministically missed `loadFinished` in the current offscreen environment. The test now uses the same resize/show lifecycle as the adjacent production-like test while preserving the original timeout and assertions; no production visualization code changed.

### Files changed

- Runtime validation: `src/quant_trading/orchestration/target_adjustment_research_asset_cash_preview.py`, `src/quant_trading/persistence/research_asset_cash_sqlite_store.py`.
- Regression tests: `tests/unit/risk/test_sqlite_research_asset_cash.py`, `tests/architecture/test_governance_document_integrity.py`, `tests/unit/market_history/test_history_panel_roles.py`.
- Proposal/governance: new `docs/proposals/PROPOSAL-022-consolidated-risk-chain-explorer.md`, `docs/proposals/README.md`, `docs/project/ROADMAP.md`, `PROJECT_COMPASS.md` v34, canonical architecture v30, `docs/project/PROJECT_STATE.md`, Risk/Capital/Persistence module docs, `logs/BUG_LOG.md` and this append-only record.

### Validation and bug discovery audit

- Focused Phase 6D SQLite suite: **7 passed**, including coordinator and transaction-level protected-reserve tamper regressions.
- First complete-suite run: **497 passed, 1 failed**, plus the existing `KI-0005` warning. The only failure was the unrelated QWebEngine lifecycle test recorded as `BUG-20260722-005`; the exact neighboring Plotly test passed and isolated reproduction confirmed the missing-show cause.
- After the test-lifecycle correction, the formerly failing test passed in isolation and the second complete suite passed **498 tests** with one existing upstream warning in 157.49 seconds.
- Final architecture/governance suite: **80 passed**. `python -m compileall -q src tests` passed. `git diff --check` passed with only expected Windows LF→CRLF notices.
- No real central database migration or row mutation occurred. Schema remains v13. No network, Market Data request, credential, account, broker, order, fill, Paper or Live path was used.
- Bugs discovered/fixed: `BUG-20260722-003`, `BUG-20260722-004`, `BUG-20260722-005`. No new Bug remains deferred or cannot-reproduce; no new Known Issue was added.

### Change Impact Report

Primary implemented impact: exact-source orchestration and central Persistence validation for the existing Phase 6D Risk preview. Secondary impact: tests and truthful governance/module documentation. Implemented public contracts, configuration, Schema v13, GUI behavior, candidate formulas, Risk dispositions, Capital transfer semantics and trading permissions are unchanged. The proposed-only impact would be Algorithm Control presentation plus a backward-compatible read-query extension; it remains unimplemented. Database migration: none. Permissions: local read-only/write-existing-research-evidence behavior only. Trading semantics: unchanged. Safety behavior is stricter against tampered planning evidence. Implemented blast radius: `LIMITED`; proposed blast radius: `LIMITED`. Rollback of the bug fix is not recommended because it would knowingly restore protected-reserve acceptance; PROPOSAL-022 can be removed from pending indexes without runtime rollback because no implementation exists.

### Compass audit

Intent alignment: preserves the user's observable connected-research goal while selecting a presentation-only next proposal instead of inventing another financial rule. Architecture alignment: Capital Allocation remains the plan/reserve owner; orchestration and Persistence only validate copied public evidence; the proposed Explorer remains in Algorithm Control and Run History stays neutral. Safety alignment: the implemented fix only fails closed on tampered protected reserves; Phase 6D remains manual-review/block-only, non-reserving and `NO_EXECUTION`. Unapproved behavior added: none—PROPOSAL-022 is explicitly proposed/pending and has no runtime code. Assumptions introduced: none; the fix enforces already approved protected-reserve semantics and the proposal awaits the user's choice. Compass sections updated: metadata/version, Phase 6D verification detail, B17 latest completed proposal and verification evidence; Stable Core is unchanged. Remaining drift risk: a future Explorer must not recompute rules, infer missing evidence, create approval/acknowledgement semantics or become a trading consumer. Suggested commit message: `fix: harden phase 6d capital evidence validation`. No commit or push was performed.

## EDIT-20260722-006 — Implement approved Phase 6E consolidated Risk chain explorer

### Approval, scope and result

- The user explicitly approved `PROPOSAL-022` on 2026-07-22. Implemented the approved **STANDARD**, `LIMITED` presentation/read-query slice inside the existing Algorithm Control and Risk boundaries.
- Added `RiskChainInspectionService` and presentation-only `TargetAdjustmentRiskChainView@1`. Resolution starts from persisted Phase 6D results and retrieves exact Phase 6C, Phase 6B and Phase 6A results/source links through their public query ports. Embedded and linked identities are cross-checked; missing or inconsistent evidence raises a visible inspection error and no completed chain view.
- Extended `ResearchAssetCashResultQuery@1` with optional inclusive timezone-aware `as_of_from_utc` / `as_of_to_utc` bounds. The SQLite read adapter applies them to stored `as_of_utc`; central Schema remains v13 and no table, migration, backfill, result or write path was added.
- Added the `Consolidated Risk Chain Explorer` as a subtab of the existing Risk page. It provides symbol/action/plan/snapshot/disposition/rule-outcome/warning/date filters, exact persisted source/capital/version details, Phase 6A structural gates separated from numerical rules 1–3, and all nine related Open Run paths.
- Added explicit side-by-side selection for two persisted Phase 6D chains. It displays exact A/B values and equality/difference markers only; it calculates no financial delta, ranking, score or preferred result.
- The explorer exposes no edit, acknowledgement, approval, reservation, rerun, export, Backtesting, Accounting, Paper, Live, order or execution control. It creates no algorithm Run/result and adds no Launcher entry.

### Files changed

- Presentation adapter/GUI: `src/quant_trading/algorithm_control/risk_chain_inspection.py`, `algorithm_control/__init__.py`, `algorithm_control/ui/risk_chain_panel.py`, `ui/target_adjustment_risk_panel.py`, `ui/main_panel.py`.
- Public query/read adapter: `src/quant_trading/risk/research_asset_cash_models.py`, `src/quant_trading/persistence/research_asset_cash_sqlite_store.py`.
- Tests: `tests/unit/algorithm_control/test_risk_chain_inspection.py`, `test_risk_chain_panel.py`, `tests/unit/risk/test_sqlite_research_asset_cash.py`, `tests/architecture/test_risk_chain_explorer_boundaries.py`, `test_governance_document_integrity.py`.
- Governance/user docs: `PROJECT_COMPASS.md` v35, canonical architecture v31/invariants 84–87, approved/implemented `PROPOSAL-022`, Proposal index, README, CHANGELOG, Module Map, Algorithm Control/Risk/Persistence/Launcher docs, Project State/Roadmap, Bug Log and this append-only Edit Log.

### Validation and bug discovery audit

- Complete suite after all corrections: **508 passed**, with one existing third-party `websockets.legacy` deprecation warning (`KI-0005`), in 268.65 seconds.
- One preceding complete-suite run passed 507 tests and failed only the queued Plotly callback with Qt's explicit missing-slot error; this produced and was corrected as `BUG-20260722-008` before the final clean run.
- Architecture/governance suite: **83 passed**. Focused Phase 6E/query suite: **17 passed**. Coverage includes inclusive/exclusive date edges, aware-UTC/range validation, prior positional-limit and GUI-parent compatibility, exact Phase 6D→6A reload, missing and tampered source rejection, real differing-chain equality markers, GUI structural/numerical separation, filters/comparison and nine Open Run signals.
- `python -m compileall -q src tests`, `python -m pip check`, and `git diff --check` are recorded after final documentation synchronization.
- No real central database, runtime row, network, Market Data request, credential, account, broker, order, fill, Paper or Live path was used. Live and automatic submission remain disabled.
- Discovered and fixed `BUG-20260722-006`: the initial additive query-field order could reinterpret an existing eighth positional `limit` argument as a date. The final contract keeps `limit` in its prior position and appends the optional dates, with a compatibility regression.
- Discovered and fixed `BUG-20260722-007`: the initial explorer parameter placement could reinterpret the existing sixth positional `RiskManagementPanel` parent argument. The final explorer argument is keyword-only and composition passes it explicitly. No current Known Issue was added; no Bug remains deferred or cannot-reproduce.
- Discovered and fixed `BUG-20260722-008`: a long full-suite QWebEngine lifecycle showed that `_on_load_finished(bool)` was not registered in the Qt meta-object, so queued Plotly data was not applied. The callback is now an explicit `@Slot(bool)` and its registration plus both production-like Plotly paths are tested. No current Known Issue was added; no Bug remains deferred or cannot-reproduce.

### Change Impact Report

Primary module: `quant_trading.algorithm_control` presentation adapter and existing Risk page. Secondary modules: additive public Phase 6D query DTO and SQLite read adapter. Public contract impact is backward-compatible optional UTC bounds plus a presentation-only view; configuration is unchanged. Database impact: none—Schema v13, tables, rows and write paths are unchanged. GUI impact: one existing-page subtab; Launcher remains three applications/sixteen shortcuts. Permissions remain local read-only research history. Trading and safety semantics are unchanged. Migration: none. Rollback: remove the explorer from `RiskManagementPanel` composition and stop constructing its presenter; the optional query fields can remain inert and compatible. Blast radius: `LIMITED` as approved.

### Compass audit

Intent alignment: turns the persisted Phase 6A–6D process into one searchable, explainable and comparable view while retaining exact historical evidence. Architecture alignment: Algorithm Control owns presentation aggregation, every Risk stage keeps its result meaning, public query ports mediate reads, Persistence alone owns SQL and Run History remains neutral; architecture invariants 84–87 and 83 tests protect those boundaries. Safety alignment: inspection is read-only, missing evidence fails closed, comparison has no derived financial delta and the GUI cannot approve/reserve/recalculate/execute; Phase 6D candidates remain manual-review/block-only and non-reserved. Unapproved behavior added: none. Assumptions introduced: only `ASM-029`, directly recording the approved exact-source/read-only/equality-only boundary; no financial amount or rule was inferred. Compass sections updated: metadata/current phase, approved capability, `ASM-029`, `INTENT-033`, limitations and next direction; Stable Core is unchanged. Remaining drift risk: future UI work must not reconstruct missing history, move rule meaning into presentation, treat comparison as ranking, or add acknowledgement/approval/reservation/downstream execution without a separately approved proposal. Suggested commit message: `feat: add consolidated risk chain explorer`. No commit or push was performed.

## EDIT-20260722-007 — Whole-program diagnostic sweep and central-schema fail-closed repair

### Task mode, scope and result

- Classified the user's whole-program debugging request as **DEEP** because it crosses application entries, diagnostics, central persistence, GUI composition and the existing v1→v13 migration boundary. Primary repair modules are `quant_trading.persistence` and `quant_trading.diagnostics`; secondary scope is regression tests and current-state/governance documentation. Blast radius is `MULTI_MODULE` for inspection evidence but `LIMITED` for runtime behavior.
- Preserved the existing Phase 1–6E working tree and all user/uncommitted changes. No new financial formula, Risk amount/rule, Portfolio Accounting persistence, Paper/Live content, account/order behavior, dependency version or Schema migration was added.
- Confirmed and fixed `BUG-20260722-009`: read-only diagnostics had a stale `central_sqlite_v1` literal and inspected only the seven Phase-1 tables. It now reports the exact supported/applied version, verifies every required logical table and reports foreign-key status.
- Confirmed and fixed `BUG-20260722-010`: a current-version database missing a later table could pass `CentralSQLiteDatabase.initialize()`. Persistence now derives the exact expected table set from its own migrations, rejects migration-history gaps/missing current-version tables, performs the same check before upgrading an existing older database, and revalidates the full current contract afterward. It never auto-repairs or deletes a damaged database.
- Refreshed the local editable installation so all five declared commands exist: `quant-trade`, `quant-history`, `quant-diagnostics`, `quant-algorithm-control`, and `quant-backtest`. The isolated build downloaded only its declared setuptools build backend; `pip check` remains clean and project dependency versions were not changed.

### Files changed in this debugging slice

- Runtime: `src/quant_trading/persistence/sqlite_database.py`, `persistence/__init__.py`, `src/quant_trading/diagnostics.py`.
- Regression tests: `tests/unit/test_diagnostics.py`, `tests/unit/run_history/test_sqlite_run_history.py`.
- Documentation/governance: `PROJECT_COMPASS.md` v36, `docs/architecture/OVERVIEW.md` v32, `docs/modules/central-persistence.md`, `docs/development/DEBUGGING.md`, `docs/project/PROJECT_STATE.md`, `CHANGELOG.md`, `logs/BUG_LOG.md`, and this append-only Edit Log.

### Validation and debugging evidence

- Final complete suite: **512 passed**, with only the existing transitive `websockets.legacy` deprecation warning (`KI-0005`), in 177.31 seconds.
- Architecture/governance suite: **83 passed**. Final combined architecture plus exact diagnostics/persistence suite: **93 passed**. Exact diagnostics/persistence suite: **10 passed**.
- One pre-final combined run exposed and immediately fixed `BUG-20260722-011`: the broader Compass verification summary had dropped the still-true Phase 6E `no persistent write path changed` phrase protected by the governance test. The final 93-test run passed after restoring that evidence; runtime behavior was never affected.
- `python -m compileall -q src tests`, `python -m pip check` and `git diff --check` passed; diff check emitted only expected Windows LF→CRLF notices.
- Four formal GUI compositions—Launcher, Market History, Backtesting and Algorithm Control opened directly on Risk—constructed, entered an offscreen Qt event loop and closed normally in separate temporary roots with exit code 0. The first common failure was proven to be the external smoke driver's incorrect binding of static Qt `exec`, not product behavior, and was not recorded as a Bug.
- Real central SQLite inspection used URI `mode=ro`: applied migrations are exactly 1–13, all 74 required tables exist, `integrity_check=ok`, foreign-key violations are zero, Market Bars remain 215,340 and Fetch History remains 365. Existing algorithm/risk research result tables checked in this database remain empty. No database migration, repair or business-row mutation occurred.
- Default diagnostics performed no network check and ended `SYSTEM_HEALTH UNKNOWN automatic_execution_allowed=false` because the optional Market Data request was deliberately skipped. Credentials were checked only for presence and never printed. Runtime log review found only older already-fixed Bugs or deliberate failure-smoke entries; no new unresolved runtime defect was found.

### Change Impact Report

Primary module: central Persistence schema ownership/validation. Secondary modules: read-only diagnostics, package exports, tests and truthful docs. Public contracts add read-only `CentralSchemaInspection`, `inspect_central_schema` and `expected_schema_tables`; existing Store/result contracts are unchanged. Configuration and Schema remain unchanged at v13. GUI behavior is unchanged beyond verified startup. Permissions remain local file/diagnostic access; no Market Data network, account, broker, order, Paper or Live authority was used. Trading semantics and Risk candidates are unchanged. Migration: none. Rollback: revert the three runtime files, two regression-test additions and corresponding docs; no database downgrade is required. Blast radius: `LIMITED` runtime, `MULTI_MODULE` validation evidence.

### Compass audit

Intent alignment: the sweep improves whole-program reliability and truthful observability without starting an unapproved development phase. Architecture alignment: persistence remains the sole schema owner; diagnostics consumes its public read-only contract and neither GUI nor business domains gain SQL. Safety alignment: corrupt/incomplete schemas now fail earlier, diagnostics remains read-only, and UNKNOWN health still cannot authorize execution. Unapproved behavior added: none. Assumptions introduced: none; the supported version/table set is derived from the actual approved migrations. Compass sections updated: metadata/current verified central-persistence and diagnostics evidence only; Stable Core is unchanged. Remaining drift risk: current validation proves migration history and table presence but does not attempt automatic repair or independently fingerprint every column/index definition; such repair or deeper migration semantics would require separate scope. Bugs discovered/fixed: `BUG-20260722-009`, `BUG-20260722-010`, `BUG-20260722-011`; deferred/cannot-reproduce Bugs: none. Existing KI-0004 through KI-0008 remain unchanged. Suggested commit message: `fix: validate complete central sqlite schema`. No commit or push was performed.
