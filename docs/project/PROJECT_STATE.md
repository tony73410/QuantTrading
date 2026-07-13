# Project State

## Current phase

Repository foundation and development governance.

## Implemented capabilities

- 仓库级工作规则、文档索引、ADR 机制、编辑日志规范及目录职责说明。
- 需求解释协议：区分用户目标与建议方法，按风险等级处理歧义，并要求通俗汇报和持久记录重要假设。
- 交易能力：**Not implemented**。

## Active modules

无。`src/` 中没有正式程序模块。

## Public interfaces

无。

## Current technology decisions

- 仅采用语言无关的治理文档结构。
- 安全边界默认为 DEVELOPMENT / BACKTEST / PAPER-TRADING ONLY。
- 配置、正式源码、测试、脚本、运行产物和归档内容使用独立目录。
- Git 默认分支为 `main`；提交身份仅在本项目生效；远程 `origin` 指向 `https://github.com/tony73410/QuantTrading.git`。

## Pending decisions

- 编程语言、测试工具、交易框架、数据库、数据源和券商接口。
- 首个业务需求和由该需求驱动的模块划分。

## Known limitations

- 尚无业务代码、自动化测试、构建流程或运行入口。

## Next approved work

无。等待用户明确下一项需求；不得自行进入业务开发。

## Last verified date

2026-07-13 11:42:34 -07:00（Git 初始化与项目配置）
