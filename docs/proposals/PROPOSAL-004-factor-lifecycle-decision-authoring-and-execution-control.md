# PROPOSAL-004: Factor 生命周期、交易决策编辑与执行控制六阶段计划

## Status and identity

- Proposal ID: `PROPOSAL-004`
- Status: `DRAFT`
- Date: 2026-07-14
- Author: Codex
- User approval status: `Not requested for implementation`
- Related proposal: [`PROPOSAL-003`](PROPOSAL-003-safe-factor-authoring-and-decision-selection.md)
- Related modules: [`factor-authoring.md`](../modules/factor-authoring.md), [`factors.md`](../modules/factors.md), [`trading-decision.md`](../modules/trading-decision.md), [`algorithm-control-gui.md`](../modules/algorithm-control-gui.md), [`execution-environments.md`](../modules/execution-environments.md)
- Related architecture: [`OVERVIEW.md`](../architecture/OVERVIEW.md)
- Related EDIT_LOG entry: `EDIT-20260714-032`

## 1. Purpose

本计划用于保存用户提出的下一阶段方向，并把未来修改拆成六个可独立验收、可暂停、可回滚的阶段。它不是实施授权，也不表示其中任何交易行为已经启用。

计划要解决四个用户目标：

1. 已创建且满意的 Factor 能够长期保存、查看版本和恢复；
2. 不再使用的 Factor 可以安全停用或归档，而不是破坏历史；
3. 用户可以在 GUI 中选择 Factor，并编辑“如何根据 Factor 形成交易意图”的 Decision Policy；
4. 未来 Execution GUI 与 Decision GUI 分开，Execution 只处理风险批准后的执行配置，不直接读取 Factor 或创造交易逻辑。

## 2. Current verified baseline

### Already implemented

- GUI 可以把受限数值表达式保存为不可变 Factor 定义版本，例如 `factor_x v1`、`factor_x v2`。
- Factor 定义保存在本机 `runtime/algorithm_control/factor_definitions.json`，程序重启后仍可恢复。
- Factor 定义默认 `REGISTERED`/disabled，保存不等于启用。
- Algorithm Control 可以保存不可变组件配置版本，并保留修改原因与审计记录。
- Decision 配置可以选择精确的 Factor 组件版本 ID。
- Factor 计算结果具备中央 SQLite 持久化合同与实现，但普通 GUI 流程尚未运行正式 Factor Pipeline。
- Factor、Decision、Risk 合同和顺序编排已经存在；Execution 目前只有空白、禁用的 Paper/Live 同级边界。

### Not implemented

- Factor 定义没有受支持的删除、归档或恢复入口。
- GUI 没有用真实本地行情运行 Factor 并生成激活证据的工作台。
- 没有正式 Decision Policy，也没有在 GUI 中编辑 Decision 条件/行为的安全规则语言。
- Algorithm Control 的启用配置尚未连接到一个正式运行的生产 Factor/Decision Pipeline。
- 没有订单构造、Paper 下单、Live 下单、账户或持仓连接。
- 没有 Execution 逻辑编辑 GUI。

## 3. Intent interpretation

### User request

保存多个满意的 Factor；理解 Factor 是否能够删除；明确禁用 Factor 对 Decision/Execution 的影响；未来在 GUI 中使用多个 Factor 编辑行为逻辑，并为执行层提供相似管理界面。

### Underlying user goal

用户希望不修改仓库源代码也能逐步建立、试验、保存和管理自己的算法，同时清楚知道每个版本是否正在参与计算，以及它是否可能影响交易。

### User-suggested method

在“执行层 GUI”中选择 Factor 并编辑行为。

### Professional interpretation

“根据 Factor 决定行为”属于 **Trading Decision Layer**，不属于 Execution Layer。Execution Layer 只能处理已经通过 Risk 的批准对象，不得读取 Factor 或自行生成买卖意图。

正确边界：

```text
Market Data
  → Factor Definition / FactorSnapshot
  → Decision Policy / TradeIntent
  → RiskDecision / ApprovedTradeIntent
  → Order Construction
  → Paper or Live Execution Provider
```

### Recommendation

- 扩展现有 Scheme A，不创建第二套 Factor 编辑系统。
- Factor 历史默认使用归档/停用，不提供普通永久删除。
- Decision 逻辑使用受限、结构化、可验证的规则编辑器，不执行任意 Python。
- Execution GUI 独立建设，且不允许访问 FactorSnapshot 或原始 TradeIntent。
- 每一阶段完成后仍保持新组件 disabled；“代码完成”与“允许参与 Pipeline”分开批准。

## 4. Architecture classification

- Primary classification: Cross-cutting GUI/control-plane extension
- Owning layers: Factor、Trading Decision、Execution；Risk 保持既有独立裁决权
- Primary module: `quant_trading.algorithm_control`
- Secondary modules: `quant_trading.factors`, `quant_trading.decision`, `quant_trading.risk`, `quant_trading.orchestration`, future `quant_trading.execution`
- Expected blast radius if all phases are implemented: `SYSTEM_WIDE`
- Required execution mode: each phase separately classified; Phases 3–5 are expected to require `DEEP`

### Responsibilities

- 管理不可变 Factor/Decision/Execution 配置版本和生命周期；
- 生成可审查的 Factor 预览证据；
- 编辑和验证 Decision Policy；
- 展示 Risk 前后的结果差异；
- 管理 Execution 的环境和授权状态；
- 阻止未验证、冲突或越权组件进入 Pipeline。

### Explicit non-responsibilities

- 不发明 Factor 公式、阈值、权重、仓位、止损或买卖规则；
- 不让 GUI 执行任意 Python、SQL、网络请求或券商调用；
- 不让 Decision 自行批准 Risk；
- 不让 Execution 直接读取 Factor 或接受未经 Risk 批准的 TradeIntent；
- 不启用 Paper 下单、Live Trading 或自动订单提交。

### Component identity declarations

本提案描述多个既有所有者的兼容扩展，不创建一个跨层“万能组件”。实施前每个实际组件仍需独立元数据：

| Planned component | Type / owner | Inputs | Outputs | Required capabilities | Initial state |
|---|---|---|---|---|---|
| Factor lifecycle manager | GUI/Control Plane · `algorithm_control` | immutable Factor metadata and references | versioned lifecycle metadata/audit | view/edit draft configuration | `DISABLED` |
| Factor evidence workbench | GUI orchestration · `algorithm_control` | exact Factor version + approved MarketDataWindow | preview/evidence record | preview only, calculate through public Factor interface | `DISABLED` |
| Decision policy definition/editor | Decision + GUI management surface | exact Factor contract declarations and user-authored restricted rules | immutable Decision Policy definition | read FactorSnapshot, create TradeIntent in preview | `REGISTERED` |
| Decision/Risk dry-run coordinator | Orchestration | FactorSnapshot, Decision Policy, Risk context | TradeIntent + RiskDecision | run preview/dry run only | `DISABLED` |
| Execution control surface | Execution + GUI management surface | Risk-approved public contract and environment status | configuration/preview/audit only in this proposal | view/edit disabled execution configuration | `DISABLED` |

共同声明：`default_enabled=false`、`execution_allowed=false`、`live_allowed=false`。任何未来可提交订单的 Provider 必须另立提案并获得独立批准。

Allowed dependencies follow the canonical one-way flow through public interfaces. Forbidden dependencies include GUI → concrete Alpaca/SQLite, Decision → raw Market Data/SQLite/Risk/Execution, and Execution → Factor or unreviewed TradeIntent.

## 5. Six-phase implementation plan

### Phase 1 — Factor 版本库与生命周期管理

#### Goal

让用户清楚查看、保存、停用、归档和恢复 Factor，同时保护历史可追溯性。

#### Planned GUI behavior

- Factor 列表按 `factor_id` 分组显示所有版本；
- 展示版本、表达式摘要、参数、创建时间、修改原因、内容哈希和状态；
- 区分 `Saved`、`Validated`、`Enabled for Preview`、`Disabled`、`Archived`、`Deprecated`；
- 显示该版本被哪些 Decision 配置引用；
- 支持“禁用”“归档”“恢复”；
- 默认隐藏已归档版本，但允许用户查看；
- 不提供一键永久删除。

#### Deletion policy

- 已被 Decision、FactorSnapshot、审计或配置历史引用的版本不得永久删除；
- 普通删除操作转换为归档，不修改原始定义；
- 若未来提供永久删除，只允许删除从未被引用、从未计算、从未激活的内容，并要求单独审批和二次确认；
- 任何删除不得通过直接修改 JSON 实现。

#### Data and compatibility

- 优先向生命周期状态存储增加独立元数据，不重写不可变定义内容；
- 旧定义没有生命周期字段时按 `REGISTERED/DISABLED` 读取；
- 不删除现有 JSON 或 SQLite 历史。

#### Acceptance criteria

- 重启后版本和状态仍存在；
- 新版本不覆盖旧版本；
- 禁用/归档不删除历史计算结果；
- 被引用版本的依赖关系对用户可见；
- 恢复通过新审计记录完成。

#### Rollback

停止展示生命周期操作，继续以只读方式加载全部现有定义；保留新增元数据供以后恢复。

### Phase 2 — Factor 验证与证据工作台

#### Goal

补齐当前“启用需要证据，但 GUI 尚不能生成证据”的缺口。

#### Planned GUI behavior

- 选择 Factor 精确版本；
- 选择股票、时间范围、Timeframe、Adjustment 和 Feed；
- 优先读取本地 Market History；
- 显示输入数据范围、样本数、Factor 值、状态、单位、质量标志和错误；
- 支持多次预览并保留 Request ID/Correlation ID；
- 明确显示 `NO EXECUTION`；
- 只有验证成功才产生可用于下一生命周期状态的证据记录。

#### Required semantic decisions before implementation

- Daily/Weekly/Monthly Bar 在什么时刻视为完成并可供 `as_of_utc` 使用；
- 分钟 Bar 是否只使用常规交易时段；
- 调整后价格用于历史 Factor 时的 point-in-time 语义；
- 用户改变日期范围时采用哪个默认 `as_of_utc`。

这些含义可能影响前视偏差，未经用户确认不得静默决定。

#### Acceptance criteria

- 表达式验证和真实数据计算明确分开；
- 无证据不能启用；
- 数据不足返回明确状态，不伪造为零；
- 预览不调用 Decision、Risk 或 Execution；
- 预览不访问真实券商或提交订单。

#### Rollback

关闭工作台入口，保留只读预览记录；Factor 定义和 Market History 不受影响。

### Phase 3 — Trading Decision Policy 编辑器

#### Goal

让用户在 Decision GUI 中选择精确 Factor 版本，并定义如何把 FactorSnapshot 转换为未执行的 TradeIntent。

#### Planned capabilities

- 新建不可变 Decision Policy 版本；
- 选择一个或多个精确 Factor 版本；
- 为每个输入声明所需状态、单位和新鲜度；
- 使用结构化条件编辑器表达比较和组合条件；
- 保存条件、参数、原因代码和版本；
- 预览“原始 Factor → Decision 结果”；
- 输出只允许 `TradeIntent` 或 `NO_DECISION`，不构造订单；
- 新 Policy 默认 `REGISTERED/DISABLED`。

#### Rule-language safety boundary

- 不接受任意 Python、import、文件、网络、SQL 或系统命令；
- 不直接访问 Market History、SQLite 或 Alpaca；
- Decision 只能读取公开 `FactorSnapshotCollection`；
- Decision 不能修改 FactorSnapshot；
- Decision 不能调用 Risk 或 Execution。

#### User decisions required before behavioral implementation

- 允许哪些 Decision action；
- 多个条件如何组合；
- 缺失、无效或过期 Factor 时是拒绝、等待还是人工复核；
- 是否允许同一资产多个 Policy 并行；
- 仓位或数量是否属于此阶段；若属于，具体单位和含义是什么。

AI 不会自行填入买入阈值、卖出阈值、权重或仓位规则。

#### Acceptance criteria

- Decision Policy 可使用 Fake FactorSnapshot 独立测试；
- 替换 Factor 实现不要求修改 Decision Policy 引擎；
- 每个结果能追溯到 Factor 版本和 Policy 版本；
- 禁用或归档的 Factor 不能用于新激活配置；
- 保存 Policy 不等于激活或执行。

#### Rollback

禁用新 Policy 和编辑器入口，恢复上一不可变 Active 配置；不删除历史 Policy 或 Factor。

### Phase 4 — 冲突处理、Risk Gate 与完整 Dry Run

#### Goal

验证多 Factor、多条件和 Decision 输出在进入 Risk 前后都可解释，并确保冲突不会随机进入执行。

#### Planned behavior

- 检测缺失/禁用/版本不兼容的 Factor；
- 检测同一资产相反 TradeIntent；
- 没有 Decision Coordinator 时最多允许一个 Primary Decision Policy；
- 相反意图标记 `CONFLICT` 并停止；
- 所有 TradeIntent 必须交给 Risk Engine；
- GUI 同时显示原始 Decision、RiskDecision、批准后的值与原因代码；
- Pipeline Dry Run 停止在 RiskDecision，不提交订单。

#### Acceptance criteria

- Decision 不能绕过 Risk；
- Risk 可以拒绝、缩小或延迟，但不能增加原始风险；
- 禁用 Factor 会阻止依赖它的 Decision 激活；
- 已保存历史配置不被删除；
- 所有冲突都有稳定 Conflict ID 和用户可理解说明。

#### Rollback

停用新 Pipeline 配置，恢复此前的只读 Algorithm Control 状态；Risk 安全不变量保持锁定。

### Phase 5 — 独立 Execution Control GUI

#### Goal

为未来执行能力提供独立、受 Risk Gate 保护的管理界面；它不是 Decision 编辑器。

#### Planned scope

- 显示 Paper/Live 两个独立环境；
- 显示当前 Execution Provider、连接状态和授权状态；
- 管理人工确认要求、自动提交开关和 Live 资格状态；
- 只接受 `ApprovedTradeIntent` 或未来版本化的风险批准合同；
- 显示订单构造预览、环境、RiskDecision ID 和审计信息；
- 第一版保持订单提交按钮不可用，直到执行合同、风险限制和用户授权分别完成。

#### Forbidden behavior

- 不选择或读取 Factor；
- 不创建 TradeIntent；
- 不修改 Decision 或 Risk 结果；
- 不接受普通、未经 Risk 批准的 TradeIntent；
- 不因存在 Alpaca Key 而启用 Paper/Live 提交；
- 不把 Paper 与 Live 凭据、endpoint、状态或日志混用。

#### Approval gates

任何 Paper 订单提交需要独立用户批准。任何 Live 能力还需要单独的 Live 配置、金额/持仓/亏损保护、紧急停止、醒目界面和额外明确批准。本提案不请求这些授权。

#### Acceptance criteria for the disabled control surface

- GUI 可清楚显示 `Paper submission OFF`、`Live OFF`、`Automatic submission OFF`、`Manual confirmation ON`；
- 未经 Risk 批准的对象在类型和运行时验证中均被拒绝；
- 没有 Factor/Decision 逻辑进入 Execution 模块；
- 测试完全使用 Fake Provider，绝不访问 Alpaca 或提交订单。

#### Rollback

隐藏 Execution GUI 并保持两个执行环境 disabled；保留配置和审计记录，不修改账户或订单数据。

### Phase 6 — 全面测试、文档和安全验收

#### Goal

证明六阶段结果符合用户意图、架构边界和安全不变量，而不仅是 GUI 看起来可用。

#### Test groups

- Factor version/lifecycle unit tests；
- Factor preview and evidence tests with Fake/local data；
- Decision rule parser/evaluator unit tests；
- Decision configuration and immutable history tests；
- Decision conflict and missing-Factor tests；
- Factor → Decision → Risk Dry Run integration tests；
- Execution admission tests with Fake Provider；
- Architecture tests prohibiting Factor/Decision/Risk/Execution reverse imports；
- Persistence restart, corruption and rollback tests；
- GUI tests for save, archive, restore, preview and safe blocked states。

#### Mandatory safety verification

- Live Trading remains off；
- automatic submission remains off；
- Paper submission remains off unless separately approved later；
- credentials do not grant trading authority；
- no unrestricted Python is executed；
- no Decision bypasses Risk；
- no Execution component reads Factor；
- no test accesses a real broker or sends an order。

#### Documentation and audit

实施时按每个阶段分别更新模块文档、PROJECT_STATE、必要的 Compass/架构/ADR、BUG_LOG 和 append-only EDIT_LOG。只有真实完成并验证的能力才从 Planned 改为 Implemented。

## 6. Public contracts

预计复用或版本化扩展以下合同：

- `FactorDefinition` / `FactorSnapshot`
- lifecycle metadata for immutable Factor component versions
- `DecisionPolicyDefinition` — planned, exact schema not approved
- `TradeIntent`
- `RiskDecision` / `ApprovedTradeIntent`
- `OrderRequest` / `ExecutionResult` — planned, not implemented

所有跨层合同应包含版本、创建时间、来源组件/版本和 correlation ID。任何字段意义变化必须先检查生产者、消费者和迁移要求。

## 7. Capability and permission boundaries

| Layer | Allowed | Forbidden |
|---|---|---|
| Factor | 读取标准化 Market Data、计算 Factor | TradeIntent、Risk、订单、券商 |
| Decision | 读取 FactorSnapshot、创建 TradeIntent | 原始行情、SQLite、Risk 批准、订单提交 |
| Risk | 批准、拒绝、缩小、延迟或暂停 | 增加风险、创造 Alpha、提交订单 |
| Execution | 构造/提交已批准订单（未来） | 读取 Factor、接受未审查意图、覆盖 Risk |
| GUI | 编辑 Draft、预览、Dry Run、展示状态 | 直接调用券商、绕过 Risk、自动启用 Live |

## 8. Conflict assessment

- Result: `NEEDS_USER_DECISION`
- Layer conflict: 用户所说的“执行层使用 Factor 决定行为”必须归属 Decision 层；否则构成架构冲突。
- Responsibility conflict: 复用现有 Factor authoring 和 Decision selector，不创建平行实现。
- Dependency/cycle conflict: GUI 通过 Controller/Application Service 调用；Decision 不导入具体 Factor 实现；Execution 不导入 Factor。
- Permission conflict: Decision 无 Risk/Execution 权限；Execution 无 Factor/Decision 权限。
- Data-contract conflict: Decision Policy 定义合同和 ApprovedTradeIntent/Order 合同尚未批准。
- Configuration conflict: 同一作用域默认只允许一个 Primary Decision Policy。
- Runtime conflict: 相反 Decision 输出默认阻止，不进行投票、平均或随机选择。
- Safety conflict: Paper/Live/automatic submission 均保持关闭。
- User decisions required: Phase 2 时间语义、Phase 3 Decision 规则语义、永久删除条件、任何 Paper/Live 执行授权。

## 9. Change Impact Report

- Primary module: `quant_trading.algorithm_control`
- Secondary modules: Factor, Decision, Risk, orchestration, future Execution
- Public contracts: lifecycle metadata, planned Decision definition, future approved execution contracts
- Configuration: immutable Factor/Decision/Execution configuration namespaces
- Database: no migration approved; assess whether lifecycle/evidence remains control JSON or moves to central SQLite before implementation
- GUI: Factor library, Factor workbench, Decision editor, Conflict/Risk view, Execution control
- Tests: unit, integration, architecture and GUI
- Documentation: module docs, Project State, Compass/architecture/ADR only when actual behavior changes
- Permissions: no new trading authority in this proposal
- Trading semantics: Decision semantics remain unspecified until user decisions are recorded
- Safety behavior: fail closed; Live and automatic submission remain off
- Migration: additive/versioned; retain old definitions/configurations
- Rollback: feature flags, restore prior immutable configuration, hide new GUI surfaces, retain history
- Expected blast radius: `SYSTEM_WIDE` for the complete six-phase program; implement and approve one phase at a time

## 9.1 Financial, risk, and safety meaning

- Financial meaning: Phases 1–2 manage and preview strategy-neutral Factor definitions. Phase 3 may define desired behavior only after the user specifies its financial semantics. Phases 4–5 preserve Risk and execution boundaries.
- Risk implications: no numerical limit is selected here; every future TradeIntent remains subject to independent Risk review.
- Can it create exposure? Not as planned/disabled. A future Decision Policy can only create an unexecuted intent after separate approval.
- Can it approve/reduce/reject risk? Only the existing Risk layer, not these GUI editors.
- Can it build/submit an order? No under this proposal. Execution contracts and submission remain Not implemented.
- Does it affect Live eligibility? No. `live_allowed=false` throughout.
- Manual confirmation: remains required; this plan cannot switch it off.

## 9.2 Compatibility and migration

- Backward compatibility: additive lifecycle and definition records must continue reading existing Scheme A definitions and configurations.
- Adapters required: likely Market History → point-in-time-safe `MarketDataWindow`; exact design waits for Phase 2 time-semantics approval.
- Data/configuration migration: none approved. Any move from JSON control data to SQLite requires a separately reviewed migration plan.
- Old/new comparison: immutable version IDs, content hashes, preview evidence and correlation IDs allow side-by-side comparison.
- Duplicate prevention: only one Primary Decision Policy is allowed without an approved coordinator; Dry Run cannot submit; Execution rejects unreviewed inputs.

## 10. Recommended implementation order and gates

```text
Phase 1 approved and verified
  ↓
Phase 2 time semantics approved and preview evidence verified
  ↓
Phase 3 Decision behavior explicitly specified and approved
  ↓
Phase 4 complete Dry Run through Risk
  ↓
Phase 5 disabled Execution control surface
  ↓
Phase 6 full regression and documentation audit
```

No later phase should be treated as approved merely because an earlier phase was completed.

## 10.1 Validation and activation evidence

- Unit tests: lifecycle transitions, restricted parsers, deterministic evaluation, invalid/missing inputs and authority rejection.
- Integration tests: local Market Data → Factor preview; FactorSnapshot → Decision → Risk dry run; disabled Execution admission with Fake inputs.
- Architecture tests: preserve the one-way Factor → Decision → Risk → Execution boundary and prohibit GUI access to concrete providers/stores.
- Historical simulation: required before any Decision Policy can leave Dry Run; exact simulation semantics need user approval.
- Paper validation: not part of initial implementation; requires separate approval after Risk and execution contracts exist.
- Manual activation: required for each component and exact version.
- Live approval: `Not requested`.
- Evidence transitions: implementation/tests permit `REGISTERED`; real-data preview evidence may permit preview; historical evidence may permit Dry Run; Paper and Active require separate future approvals.

## 11. Rollback and deprecation

- Disable each new GUI feature independently.
- Restore prior immutable configuration rather than overwriting history.
- Archive/deprecate components before any deletion proposal.
- Retain Factor definitions, FactorSnapshot history, Decision configs and audit records.
- Never use `git reset --hard` or database deletion as a product rollback.
- Paper/Live execution remains unavailable throughout rollback.

## 12. Approval record

The user requested that this plan be written and saved for later use. That request approves the planning document only. It does **not** approve implementation, Factor deletion, Decision rules, position semantics, Paper submission, Live Trading, or automatic order submission.

## 13. Documentation impact when implemented

Each approved phase must update only the documents whose actual semantics changed: relevant module docs and EDIT_LOG for ordinary extensions; PROJECT_STATE when verified capabilities change; Compass/canonical architecture/ADR only for approved semantic, contract, dependency or authority changes. CHANGELOG receives only user-visible or version-significant completed behavior. Planned text must never be described as implemented.
