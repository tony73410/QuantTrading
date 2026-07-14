# Module Documentation

当前正式模块：`market-history.md`。其他模块仍必须由实际、已批准需求驱动；不得预建假设性的策略、风险或订单模块。

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
