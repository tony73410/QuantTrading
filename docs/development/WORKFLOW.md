# Development Workflow

## 1. Inspect

阅读根 `AGENTS.md`、文档索引、项目状态、相关模块/ADR、代码和最近相关编辑记录；运行 `git status`（若已初始化），识别并保护用户未提交修改。涉及 Alpaca 时分别检查 Market Data、Paper Execution 和 Live Execution 角色，不得因存在 API Key 推断订单授权。

## 2. Restate

按照 `REQUIREMENT_INTERPRETATION.md` 区分用户目标、用户建议的方法、专业解释和推荐实现。简述需求、包含范围、不包含范围、必要假设和验收条件；对 Level C/D 歧义说明不同选择的实际后果，Level D 在用户明确选择前不得实施有风险行为。

## 3. Impact analysis

列出涉及文件/模块、接口、依赖、配置、数据和交易安全影响；判断是否触发审批。任何 Alpaca Live、自动订单提交、风险限制或执行接口变化都必须单独识别。

## 4. Plan

给出小步计划。触发审批事项时，按 `AGENTS.md` 的七项说明模板停止并等待批准。

## 5. Implement

进行最小、局部、可解释的修改；保持现有风格，不清理或重构无关内容，不覆盖用户工作。

## 6. Validate

运行最相关测试及必要的格式、类型、静态分析、接口兼容和 diff 检查。交易相关配置还必须验证默认 Paper、Live 关闭、自动提交关闭、人工确认开启，以及测试不访问真实账户或提交订单。失败必须如实区分新引入与既有问题。

## 7. Document

同步受影响的模块文档、项目状态、必要的 CHANGELOG/ADR，并向 `logs/EDIT_LOG.md` 追加一条覆盖全部改动文件的记录。

## 8. Report

报告 Summary、Files added/modified/deleted/renamed、Tests/checks executed、Results、Behavior/interface/dependency impact、Documentation updated、Known risks、Rollback method、Suggested commit message。

原则：一个任务，一组相关改动，一个清晰目的。
