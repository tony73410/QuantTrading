# Repository Instructions

本文件是仓库级强制工作规则入口。[`PROJECT_COMPASS.md`](PROJECT_COMPASS.md) 是项目意图、当前语义、安全不变量和 AI 自审的中心入口；[`docs/architecture/OVERVIEW.md`](docs/architecture/OVERVIEW.md) 是唯一主要架构来源。开始任何重要任务前必须先阅读三者，再阅读[文档索引](docs/INDEX.md)、相关模块文档、项目状态及最近相关编辑日志；结束前同步受影响文档，并向 `logs/EDIT_LOG.md` 追加真实记录。

不得把以前 AI 的假设、建议、对话记忆或已经生成的代码自动视为用户决定。代码可以证明当前行为，但不能自动证明该行为符合用户意图。

## Project boundary

- 用户决定产品、市场、资产、数据、策略、信号、仓位、风险、订单和实盘启用方式。
- 实现只覆盖用户当前明确要求；不得发明或调整交易功能、公式、参数或语义。
- 默认执行环境标识为 **ALPACA PAPER**，但当前执行功能尚未实现；自动订单提交和 Alpaca Live Trading 必须关闭，任何未来订单都要求人工确认。配置 Alpaca Key 不等于获得订单或实盘授权。
- Alpaca Market Data 与未来 Alpaca Execution 必须保持独立模块边界。没有明确批准、独立 Live 配置和完整风险保护，不得连接实盘账户或操作真实资金订单。
- 不因顺手清理或追求整洁而扩大范围。编辑、测试或审查中发现的错误和可信潜在缺陷必须先写入 `logs/BUG_LOG.md`；当前仍影响用户的问题同时摘要到 `KNOWN_ISSUES.md`。

## Required workflow

### Task execution mode

Before inspecting or implementing a task, classify it using the lowest safe mode and report `Task mode`, `Primary module`, `Expected files changed`, `Tests to run`, and `Documents to update`.

- **FAST** — small, local, low-risk work such as text/layout changes, an isolated bug fix, small logging improvement, or a change confined to one module. Inspect only directly relevant files, run directly relevant tests, and update only `logs/EDIT_LOG.md`. Do not read/update the full project governance set unless the change actually alters project behavior or evidence reveals a broader conflict.
- **STANDARD** — ordinary feature work inside an existing module boundary, such as an approved Factor implementation, Risk rule, GUI panel, service extension, or configuration field. Read `PROJECT_COMPASS.md` and the canonical architecture summary, inspect the owner and direct dependencies, run targeted unit/integration tests, and update the module document plus Edit Log. Do not perform a full-project audit without evidence of a broader conflict.
- **DEEP** — high-impact or cross-cutting work such as adding/removing a major layer, changing public contracts/dependency direction/database schema, adding a broker or execution environment, changing Risk authority, or enabling submission/Live. Perform full impact/permission analysis, migration and rollback planning, broad validation, Compass/architecture updates, and an ADR when appropriate.

If a FAST or STANDARD task discovers a serious architecture, permission, public-contract, migration, financial-semantics, or trading-safety conflict, stop the implementation and recommend escalation to DEEP. Do not silently expand scope. Documentation updates are proportional: FAST does not update Compass, architecture, ADR, Project State or Changelog unless actual project behavior changed; STANDARD updates only affected module/workflow documentation; DEEP updates semantic and architecture sources as required.

1. 阅读 `PROJECT_COMPASS.md`，确认 Stable Core、相关 Active Intent、假设、开放决定和漂移风险。
2. 阅读主要架构文件，确认职责归属、公共接口、允许/禁止依赖、数据流和架构不变量。
3. 检查 Git 状态、用户未提交改动、相关代码、文档、最近相关编辑记录和 Bug Log；识别当前任务是否触发已知或新潜在缺陷。
4. 复述真实目标、范围、不包含项、假设和验收条件，并分析文件、接口、依赖、配置及数据影响。
5. 完成简短的 Pre-Implementation Compass Audit 和架构影响检查；若触发审批边界或高风险歧义，先停止并请求批准。
6. 以最小步骤实施，不引入未请求行为；确认的新Bug若可安全局部修复，则修复根因并加回归测试，否则按Bug Log规则记录Deferred/Cannot reproduce及规避方法。
7. 验证最相关测试、架构检查、静态检查和 diff，不虚报未运行的检查。
8. 更新模块文档、项目状态及必要的 Compass/架构/CHANGELOG/ADR，最后追加 `logs/EDIT_LOG.md`。
9. 完成 Post-Implementation Compass Audit 和 Bug discovery audit，并报告本次发现/修复/延期的Bug ID（没有则明确说明）、文件变化、检查结果、影响、风险、回滚方式和建议提交信息。

详细流程见 `docs/development/WORKFLOW.md`。

## Compass self-audit

重要任务实施前必须简短回答：用户的真实目标是什么；哪些 Stable Core 原则适用；什么既有行为必须保持；采用了什么假设；是否可能改变金融含义；是否需要批准；什么证据能证明完成。无需向用户输出冗长内部推理，但结论必须可审查。

重要任务完成后的最终报告必须包含 `Compass audit`，以证据说明：Intent alignment、Architecture alignment、Safety alignment、Unapproved behavior added、Assumptions introduced、Compass sections updated、Remaining drift risk。不得只写“Compliant”。

当项目含义、默认值、主要架构、已批准能力、重要假设、外部服务角色或安全边界变化时，更新 Compass 的 Evolving Project State。普通内部实现变化不强制更新 Compass。Stable Core 只能按照 Compass Change Proposal 流程并获得用户明确批准后修改。

发现模块职责漂移、GUI承载策略/订单逻辑、行情与执行混合、Paper/Live混用、默认值未批准变化、建议冒充决定或文档无证据声称完成时，标记 **POTENTIAL PROJECT DRIFT**；不要直接大范围重构，先说明影响、最小修复和审批需求。

## Change admission and conflict prevention

Before implementing any significant new Factor, Decision policy, Risk rule, Provider, GUI capability, data contract, or execution-related component, use the canonical process in `docs/proposals/README.md`:

`Idea → Interpretation → Classification → Conflict analysis → Architecture proposal → User approval → Isolated disabled implementation → Validation → Dry Run → Paper validation → Separate activation approval`.

The pre-implementation report must answer: What is the user's actual goal? Which layer owns the feature? Does an existing component already own the responsibility? Which versioned public contracts and capabilities are required? Does it cross an authority boundary, bypass Risk, conflict with an active component, change financial meaning/defaults, or require migration? What is the default disabled state, test evidence, rollback path, and approval status?

Every important change must include a `Change Impact Report`: Primary/Secondary modules, public contracts, configuration, database, GUI, tests, documentation, permissions, trading semantics, safety behavior, migration, rollback, and blast radius (`LOCAL`, `LIMITED`, `MULTI_MODULE`, `SYSTEM_WIDE`). `SYSTEM_WIDE`, architecture, permission, or safety conflicts stop before implementation until explicitly approved.

Implementation does not grant runtime or trading authority. AI recommendations are never approval. New components default `REGISTERED`/`DISABLED`, `execution_allowed=false`, and `live_allowed=false`; they may advance only with required evidence and explicit approval. Pipeline admission must fail closed for invalid metadata, incompatible contracts, excess capability, multiple disallowed Primary components, missing Risk review, unresolved blocking conflicts, or unsafe Live/automatic-submission state.

## Requirement interpretation

- 先区分用户目标、用户建议的方法、准确的软件解释、准确的交易解释和推荐实现；保留用户意图，不机械复制含混术语。
- Level A/B 的低风险解释采用最小假设、可测试且易撤销的方案，并记录必要假设。
- Level C 的产品行为歧义必须说明选项、推荐及实际后果；不得把假设隐藏在实现中。
- Level D 的资金、交易或安全歧义不得静默选择，必须解释后等待用户明确决定。
- 普通内部工程细节可自主判断，但不得借此新增交易规则、依赖、公共接口、模块职责或其他需审批事项。
- 面向用户使用通俗语言；代码、接口和文档使用准确、一致的专业名称。

完整规则见 `docs/development/REQUIREMENT_INTERPRETATION.md`。

## Approval required before implementation

以下事项必须先说明 Proposed change、Reason、Affected files/modules、Alternatives considered、Compatibility impact、Risks、Rollback method，并等待批准：

- 新顶层目录或主要模块；删除、移动或重命名正式文件或功能；
- 公共接口、模块职责、依赖方向、配置格式、持久化结构或数据迁移；
- 第三方依赖、语言、框架、数据库、核心库或外部服务的增删升级；
- 跨模块大范围重构；交易策略、风险、仓位或订单语义变更；
- 真实凭据、外部交易服务、实盘启用；可能破坏 Git 历史的操作。

当前明确需求内的小范围、非破坏性修改无需重复审批。

## Architecture and modules

- 重要修改前必须阅读 `docs/architecture/OVERVIEW.md` 并回答：哪个模块拥有该职责；现有模块是否已提供；是否跨越边界、增加依赖、形成循环或改变公共接口；能否用更小的局部修改完成；架构文档是否需要更新。
- 影响分析必须列出 Primary module、Secondary modules、Public interfaces、Configuration、Database、Tests、Documentation 与 Expected blast radius（small/medium/large）。目标是小而可预测的影响范围。
- 如果一个简单功能需要修改多个无关模块，先暂停，说明耦合与最小方案；未经批准不得借此进行大范围重构。
- 正式代码仅放在 `src/`；模块由实际需求驱动，不预建假设性业务模块。
- 新模块实施前必须定义职责/非职责、输入/输出、公共接口、依赖/被依赖关系、副作用和测试，并建立 `docs/modules/<module-name>.md`。
- 模块只通过公共接口通信；禁止循环依赖、跨模块调用私有实现及静默改变公共接口。
- 配置不含业务逻辑；`scripts/`、`runtime/`、`archive/` 均不是正式源代码目录；测试不得成为运行依赖。
- 不创建无边界的 `utils` 垃圾桶；共享结构应明确，避免长期传递字段不明的任意字典。
- 三层算法不变量：`factors`不得导入或知道`decision`/`risk`；`decision`只能依赖公开Factor模型/接口，不得依赖具体Factor实现、原始行情、SQLite、`risk`或券商；`risk`只能依赖公开Factor/Decision合同和抽象状态接口，不得依赖具体Provider、Store、GUI或Execution。
- `TradeIntent`只是建议意图，不是订单、风险批准或成交。所有未来可执行意图必须经过独立Risk层；Risk可否决、延迟、暂停或降低风险，但不得扩大/反转原始意图、产生Alpha或直接下单。未来Execution只能接受类型明确的Risk-approved对象，不能接受普通`TradeIntent`。
- Risk配置必须与Factor/Decision配置分离并具有版本；未获用户批准不得填写金额、比例、亏损、回撤、杠杆或保证金限制。Live与自动提交仍关闭，Emergency automatic liquidation尚未实现。
- 算法控制中心只管理Registry元数据、`ParameterSchema`、Draft/Saved/Active版本、验证、NO EXECUTION预览和审计；GUI不得包含公式、Decision/Risk规则、行情/API/SQL或执行逻辑，也不得按组件名称写分支。
- 控制中心的Save、Apply和Restore必须留下不可变版本及原因；Locked安全不变量不能停用。凭据、配置激活或Preview/Dry Run均不得成为订单授权。

主要架构来源为 `docs/architecture/OVERVIEW.md`；通用约束与模块模板见 `docs/architecture/DEPENDENCY_RULES.md`、`docs/modules/README.md`。只有确有模块特殊规则时才建议添加嵌套 `AGENTS.md`。

## Tests and documentation

- 新增或修改正式行为必须覆盖正常、边界、无效、失败和关键回归路径。
- 禁止为通过测试而删除/弱化/无说明跳过测试；普通测试不得依赖真实账户或不稳定外部服务。
- 无法运行测试时，说明原因、替代检查和剩余风险。
- 每个确认并修复的Bug必须有回归测试；发现但尚未确认或无法安全修复的问题也必须先记录，禁止为显得完成而猜测性修改或虚假标记Fixed。
- 职责、接口、配置、运行方式、输入输出、依赖、数据格式、限制或测试方法变化时，同步文档。
- 未实现内容必须标记 `Planned`、`Proposed` 或 `Not implemented`。

详见 `docs/development/TESTING_STANDARDS.md` 与 `docs/development/DOCUMENTATION_STANDARDS.md`。

## Git, secrets, and records

- 不假设工作区干净，不覆盖或丢弃用户未提交修改。
- 未经明确要求，不 commit、push、pull、merge、rebase、reset、强制 checkout、force push、删分支或改写历史。
- 不提交密钥、账户、密码、token、私钥、真实账户信息或敏感日志；未来示例只写变量名和安全说明。
- Paper 与 Live 凭据、endpoint、状态和日志不得混用；运行日志必须明确环境，且不得包含 Secret 或完整授权头。
- `logs/EDIT_LOG.md` 只追加逻辑变更记录，不重写历史；所有改动文件必须列入对应记录。
- `logs/BUG_LOG.md` 是发现错误与可信潜在缺陷的唯一开发历史；不删除旧记录。程序运行日志、Bug历史、当前Known Issues和代码Edit历史必须分开。
- `CHANGELOG.md` 只记用户可见或版本重要变化；`docs/project/PROJECT_STATE.md` 只描述当前真实状态。
