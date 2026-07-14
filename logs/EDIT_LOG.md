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
