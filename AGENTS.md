# Repository Instructions

本文件是仓库级强制规则入口。开始任何任务前，先阅读本文件、[文档索引](docs/INDEX.md)、相关模块文档、项目状态及最近相关编辑日志；结束前同步受影响文档，并向 `logs/EDIT_LOG.md` 追加真实记录。

## Project boundary

- 用户决定产品、市场、资产、数据、策略、信号、仓位、风险、订单和实盘启用方式。
- 实现只覆盖用户当前明确要求；不得发明或调整交易功能、公式、参数或语义。
- 默认运行边界为 **DEVELOPMENT / BACKTEST / PAPER-TRADING ONLY**。没有明确授权，不得使用真实凭据、连接实盘账户或操作真实订单。
- 不因顺手清理或追求整洁而扩大范围；无关问题记录到 `KNOWN_ISSUES.md`。

## Required workflow

1. 检查 Git 状态、用户未提交改动、相关代码、文档和编辑记录。
2. 复述范围、不包含项、假设和验收条件，并分析文件、接口、依赖、配置及数据影响。
3. 以最小步骤实施；若触发审批边界，先停止并请求批准。
4. 验证最相关测试、静态检查和 diff，不虚报未运行的检查。
5. 更新模块文档、项目状态及必要的 CHANGELOG/ADR，最后追加 `logs/EDIT_LOG.md`。
6. 报告文件变化、检查结果、影响、风险、回滚方式和建议提交信息。

详细流程见 `docs/development/WORKFLOW.md`。

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

- 正式代码仅放在 `src/`；模块由实际需求驱动，不预建假设性业务模块。
- 新模块实施前必须定义职责/非职责、输入/输出、公共接口、依赖/被依赖关系、副作用和测试，并建立 `docs/modules/<module-name>.md`。
- 模块只通过公共接口通信；禁止循环依赖、跨模块调用私有实现及静默改变公共接口。
- 配置不含业务逻辑；`scripts/`、`runtime/`、`archive/` 均不是正式源代码目录；测试不得成为运行依赖。
- 不创建无边界的 `utils` 垃圾桶；共享结构应明确，避免长期传递字段不明的任意字典。

详见 `docs/architecture/DEPENDENCY_RULES.md` 与 `docs/modules/README.md`。只有确有模块特殊规则时才建议添加嵌套 `AGENTS.md`。

## Tests and documentation

- 新增或修改正式行为必须覆盖正常、边界、无效、失败和关键回归路径。
- 禁止为通过测试而删除/弱化/无说明跳过测试；普通测试不得依赖真实账户或不稳定外部服务。
- 无法运行测试时，说明原因、替代检查和剩余风险。
- 职责、接口、配置、运行方式、输入输出、依赖、数据格式、限制或测试方法变化时，同步文档。
- 未实现内容必须标记 `Planned`、`Proposed` 或 `Not implemented`。

详见 `docs/development/TESTING_STANDARDS.md` 与 `docs/development/DOCUMENTATION_STANDARDS.md`。

## Git, secrets, and records

- 不假设工作区干净，不覆盖或丢弃用户未提交修改。
- 未经明确要求，不 commit、push、pull、merge、rebase、reset、强制 checkout、force push、删分支或改写历史。
- 不提交密钥、账户、密码、token、私钥、真实账户信息或敏感日志；未来示例只写变量名和安全说明。
- `logs/EDIT_LOG.md` 只追加逻辑变更记录，不重写历史；所有改动文件必须列入对应记录。
- `CHANGELOG.md` 只记用户可见或版本重要变化；`docs/project/PROJECT_STATE.md` 只描述当前真实状态。
