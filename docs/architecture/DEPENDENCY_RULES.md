# Dependency Rules

本文件保存仓库级通用规则。当前模块的具体允许/禁止依赖、依赖矩阵和自动检查以唯一主要架构文件 [`OVERVIEW.md`](OVERVIEW.md) 为准。

## Required

- 模块通过明确公共接口通信，共享数据结构必须有明确字段或类型约定。
- 依赖方向应可被 `MODULE_MAP.md` 和模块文档解释，并保持无环。
- 编排层只组织流程，不隐藏策略、风险、仓位或订单规则。
- 算法依赖保持 `factors → public FactorSnapshot → decision → immutable TradeIntent → risk → RiskDecision`；上游层不得反向依赖下游层。
- Risk只能保持、降低、延迟或阻止上游意图，不能扩大/反转风险、直接下单或修改Factor/Decision；未来Execution不得接受未经Risk批准的普通`TradeIntent`。
- 能归入现有职责的需求优先扩展现有模块；新增模块需先审批。
- `algorithm_control`只管理公开元数据、配置版本、验证、安全预览和审计；不得依赖具体Alpaca Provider、历史SQLite Store或未来Execution Provider。
- 算法参数界面必须由`ParameterSchema`生成；不得按算法名称写`if/elif`并把公式或交易规则藏入GUI。

## Admission and capability enforcement

- Every extensible component declares an `owner_layer`, canonical responsibility, non-responsibility, versioned input/output contracts, allowed/forbidden dependencies and required capabilities.
- Registration rejects duplicate IDs, unknown contracts, wrong ownership, excess capability, non-Execution execution authority, and Live eligibility while Live is disabled.
- New components are disabled by default. Code existence, credentials, saved configuration and GUI selection do not constitute activation authority.
- One active Primary Decision policy and one Execution Provider per environment are defaults. Multiple Risk rules use the strictest result; conflicting Decision outputs block.
- A complete runtime Pipeline is blocked if Factor/Decision/Risk stages are missing, locked safety is disabled, contracts are invalid, permissions conflict, or Live/automatic submission becomes enabled unexpectedly.
- Public contract compatibility must be assessed before changing schema meaning. Major changes require migration; type/shape changes require an adapter or migration.

## Prohibited

- 调用其他模块的私有实现或建立循环依赖。
- 在配置层、脚本目录或测试代码中藏入正式业务逻辑。
- 让正式代码依赖 `tests/`、`runtime/` 或 `archive/`。
- 建立职责不明的 `utils`/通用垃圾桶。
- 长期跨模块传递字段不明确的任意字典或隐式全局状态。
- 静默改变公共接口、模块职责或依赖方向。
- 让Decision批准自己的交易、Risk调用具体券商/SQLite/GUI、或Execution绕过`RiskApprovedTradeIntent`类型门。
- 让控制中心Preview/Dry Run获得订单执行资格，或让Save/Apply因凭据存在而触发交易。

新增依赖前应说明必要性、方向、接口、失败方式、兼容影响和测试覆盖；第三方依赖的增删升级必须先获批准。
