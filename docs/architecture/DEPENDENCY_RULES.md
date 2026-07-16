# Dependency Rules

- Asset Factor is single-symbol and cannot depend on Market Factor, Decision, account state, Risk or Execution.
- Market Factor may consume public exact Asset Factor results; it cannot consume accounts or produce intents.
- Decision may read Asset/Market Factor contracts and read-only Portfolio sizing context; it cannot modify accounting.
- Risk may only preserve or reduce a proposed notional, never increase it.

本文件保存仓库级通用规则。当前模块的具体允许/禁止依赖、依赖矩阵和自动检查以唯一主要架构文件 [`OVERVIEW.md`](OVERVIEW.md) 为准。

## Required

- Restricted Factor definitions, syntax validation and evaluation belong to `quant_trading.factors`. Algorithm Control may edit public contracts and issue typed preview requests; local evaluation must be delegated to application orchestration, not implemented in GUI callbacks.
- Decision configuration may reference exact registered Factor component IDs only. Selection does not activate a Factor, define Decision logic or bypass Risk.

- `quant_trading.persistence` may implement public Store Protocols and use public Market/Factor models, but it must not own formulas, Decision/Risk logic, GUI, Providers or execution. Pure Factor code must not import the concrete SQLite adapter.

- 模块通过明确公共接口通信，共享数据结构必须有明确字段或类型约定。
- 依赖方向应可被 `MODULE_MAP.md` 和模块文档解释，并保持无环。
- 编排层只组织流程，不隐藏策略、风险、仓位或订单规则。
- 算法依赖保持 `factors → public FactorSnapshot → decision → immutable TradeIntent → risk → RiskDecision`；上游层不得反向依赖下游层。
- Risk只能保持、降低、延迟或阻止上游意图，不能扩大/反转风险、直接下单或修改Factor/Decision；未来Execution不得接受未经Risk批准的普通`TradeIntent`。
- Portfolio Accounting依赖方向为`Execution events → append-only Ledger → Accounting → immutable snapshots → Risk/GUI queries`。Ledger不得依赖GUI；Accounting不得依赖具体Broker/Execution；Risk不得调用Ledger/Accounting写接口；GUI不得访问Ledger存储实现、SQL或Broker。
- `execution.paper`与`execution.live`是同一Execution所有者下的同级环境边界，当前必须保持无接口、无副作用、无相互导入和默认禁用；目录存在不代表任何订单权限。
- 能归入现有职责的需求优先扩展现有模块；新增模块需先审批。
- `algorithm_control`只管理公开元数据、配置版本、生命周期、验证、预览请求和审计；不得依赖具体Alpaca Provider、历史SQLite Store或未来Execution Provider。`orchestration`可通过窄Store工厂/公开接口组合本地预览，但不得联网或构造订单。
- `launcher`只维护静态可信GUI入口并启动独立进程；不得导入功能GUI、Provider、Store、算法、Risk或Execution实现。未来独立GUI功能应登记入口和测试，不得把业务逻辑放进主菜单。
- 算法参数界面必须由`ParameterSchema`生成；不得按算法名称写`if/elif`并把公式或交易规则藏入GUI。

## Admission and capability enforcement

- Every extensible component declares an `owner_layer`, canonical responsibility, non-responsibility, versioned input/output contracts, allowed/forbidden dependencies and required capabilities.
- Registration rejects duplicate IDs, unknown contracts, wrong ownership, excess capability, non-Execution execution authority, and Live eligibility while Live is disabled.
- New components are disabled by default. Code existence, credentials, saved configuration and GUI selection do not constitute activation authority.
- One active Primary Decision policy and one Execution Provider per environment are defaults. Multiple Risk rules use the strictest result; conflicting Decision outputs block.
- A complete runtime Pipeline is blocked if Factor/Decision/Risk stages are missing, locked safety is disabled, contracts are invalid, permissions conflict, or Live/automatic submission becomes enabled unexpectedly.
- Public contract compatibility must be assessed before changing schema meaning. Major changes require migration; type/shape changes require an adapter or migration.

## Prohibited

- Executing arbitrary Python, imports, attributes, filesystem/network/process access or broker calls from GUI-authored Factor text.
- Silently overwriting an authored Factor version or letting a Decision selection float to a later Factor version.

- 调用其他模块的私有实现或建立循环依赖。
- 在配置层、脚本目录或测试代码中藏入正式业务逻辑。
- 让正式代码依赖 `tests/`、`runtime/` 或 `archive/`。
- 建立职责不明的 `utils`/通用垃圾桶。
- 长期跨模块传递字段不明确的任意字典或隐式全局状态。
- 静默改变公共接口、模块职责或依赖方向。
- 让Decision批准自己的交易、Risk调用具体券商/SQLite/GUI、或Execution绕过`RiskApprovedTradeIntent`类型门。
- 让Paper与Live实现、配置、凭据、endpoint或运行状态相互导入或静默共用；Live不得因Paper测试或包存在而获得资格。
- 让订单生命周期事件改变现金/持仓、覆盖历史账本、让Broker核对静默修正本地历史，或让GUI直接编辑会计状态。
- 让控制中心Preview/Dry Run获得订单执行资格，或让Save/Apply因凭据存在而触发交易。

新增依赖前应说明必要性、方向、接口、失败方式、兼容影响和测试覆盖；第三方依赖的增删升级必须先获批准。
