# Module Documentation

- `visualization.md` — presentation-only shared Plotly/QWebEngine renderer; it owns no chart meaning, data query, algorithm or persistence behavior.

- `factor-authoring.md` — restricted expression definitions, immutable disabled Factor versions, and exact Decision Factor-version selection.

- `central-persistence.md` — shared local SQLite Schema v6, versioned migrations, independent Run/Factor/Decision/Risk/Capital/Asset State/Target Position persistence and typed research-query adapters.
- `target-position.md` — bounded manual target-level research owner with immutable curve definitions, exact Decimal traces and no runtime consumer.
- `capital-allocation.md` — immutable research cash plans, protected reserve/asset buckets, exact conservation, append-only transfers and typed Store/query contracts.
- `asset-state.md` — versioned user-defined symbolic states, one open cycle per symbol, append-only manual transitions and deterministic replay; no automatic trading meaning.
- `run-history.md` — neutral NO EXECUTION Run lifecycle/query owner, linked Factor/Decision research evidence and Run History Explorer contract.

当前正式模块文档：

- `main-launcher.md` — QuantTrade主要桌面入口和未来独立GUI功能登记规则；
- `market-history.md` — 历史行情、缓存和GUI；
- `factors.md` — 单资产、策略中立的因子合同和无公式引擎；
- `trading-decision.md` — 只消费FactorSnapshot的非执行决策合同和无规则引擎；
- `risk-control.md` — 位于TradeIntent与未来Order Construction之间的独立风险合同和无数值规则引擎；
- `analysis-decision-pipeline.md` — 只负责Factor → Decision或Factor → Decision → Risk调用顺序的编排边界。
- `execution-environments.md` — Paper与Live两个同级、空白、禁用的未来执行环境边界；不含订单能力。
- `algorithm-control-gui.md` — 只负责组件元数据、通用参数、配置版本、验证、安全预览和审计的独立GUI管理面。
- `idea-notebook.md` — Algorithm Control内的被动本地想法笔记；不注册、不计算，也不进入回测或交易流程。

Factors/Decision/Risk/Orchestration以及空白Paper/Live Execution边界由用户明确批准建立，但当前没有正式因子公式、交易规则、数值风险规则、订单或执行行为。其他模块仍必须由实际、已批准需求驱动。

## Before adding a module

先提出并获得批准，说明：名称、职责、明确非职责、输入、输出、公共接口、现有依赖、允许的调用方、副作用和测试方法。若现有模块足以承载需求，不创建新模块。

## Required module document

每个正式模块对应 `docs/modules/<module-name>.md`，至少包含：

```markdown
# <Module name>

## Purpose
## Responsibilities
## Non-responsibilities
## Public interfaces
## Inputs
## Outputs
## Dependencies
## Side effects
## Failure modes
## Configuration
## Tests
## Known limitations
```

内容必须描述实际状态；尚未实现的内容明确标注 `Proposed`、`Planned` 或 `Not implemented`。内部实现可在不改变外部行为时演进，公共接口不得静默改变。
