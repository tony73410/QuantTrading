# Testing Standards

修改或新增正式行为时，测试至少考虑正常输入、边界输入、无效输入、失败路径和关键旧行为回归。

## Rules

- 测试与实现一同提交，并对应模块职责和公共接口。
- 测试应可重复、隔离，普通测试不依赖不稳定外部服务。
- 禁止使用真实券商账户、真实凭据或真实交易接口。
- 不为通过测试而删除测试、弱化断言或无说明跳过失败测试。
- 不将未运行的测试记录为 Passed。
- 无法执行时说明原因、替代检查及剩余风险。

## Future structure

`unit/`、`integration/`、`regression/`、`end_to_end/`、`fixtures/` 和 `mocks/` 仅在实际测试需求出现时创建，不提前制造空结构。端到端交易测试也必须保持安全、隔离且非实盘。

当前 `market_history` 使用 pytest，已建立 unit 与 integration 测试。Provider 测试必须使用 Fake/Mock 或替换官方 SDK 底层 HTTP，禁止真实网络。GUI 使用 Qt offscreen 烟雾检查补充自动化单元测试；真实显示环境的人工视觉检查必须单独报告。

每个确认 Bug 必须先在 `logs/BUG_LOG.md` 分配 `BUG-YYYYMMDD-NNN`，可自动测试的修复必须增加以场景命名的回归测试。常规测试不得读取用户真实凭据；可选 `quant_trading.diagnostics --network` 不是自动测试，只能由用户主动运行，并且只能访问 Market Data。
