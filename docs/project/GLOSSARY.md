# Glossary

- **Formal code / 正式代码**：可被产品运行路径调用的实现，只能位于 `src/`。
- **Module / 模块**：具有明确职责、公共接口、依赖边界及对应文档的正式代码单元。
- **Public interface / 公共接口**：其他模块或外部调用方被允许依赖的稳定入口、数据结构或行为约定。
- **Runtime artifact / 运行产物**：执行时产生的日志、缓存、临时状态或报告，不属于源代码。
- **ADR**：Architecture Decision Record，用于记录影响长期结构的重要决定。
- **Paper trading / 模拟交易**：不向真实市场提交订单的模拟执行模式；它不等同于实盘授权。
- **Live trading / 实盘交易**：连接真实账户或可能影响真实资金的操作，始终需要明确批准和显式保护。
- **Execution environment / 执行环境**：未来订单执行所针对的隔离环境；当前默认标识为 Alpaca Paper，Alpaca Live 关闭。环境标识不代表执行模块已经实现。
- **Manual confirmation / 人工确认**：任何未来订单提交前必须由用户明确检查和确认；当前默认要求开启。
- **Bar / K线数据点**：某个固定时间粒度内的开盘、最高、最低、收盘、成交量及可选 VWAP/成交笔数汇总，不是逐笔成交。
- **Timeframe / 时间粒度**：每根 Bar 聚合的时间长度；当前为 1 Day、1 Week 或 1 Month。
- **Adjustment / 价格调整（复权）**：针对拆股、分红等公司行动调整历史价格的口径；不同口径不得混用。
- **Feed / 数据源线路**：Alpaca 提供的行情来源，例如 IEX 或 SIP；不同 Feed 的覆盖和权限可能不同。
- **Coverage / 本地覆盖区间**：已成功完整请求并写入的 `[start, end)` 时间范围；周末/假日没有 Bar 不代表 Coverage 损坏。
- **Force Refresh / 强制刷新**：不先删除旧数据，重新请求所选范围并在验证成功后 upsert；失败保留旧数据。
