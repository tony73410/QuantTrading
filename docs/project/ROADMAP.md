# Roadmap

本路线图不猜测交易功能，只区分已完成、已批准和待决工作。

## Completed

- 建立仓库治理和语言无关目录骨架。
- 建立首个正式模块：本地优先的股票历史数据桌面浏览器。
- 完成 QuantTrade 可视化治理路线阶段 1：统一 `AlgorithmRun`、中央 SQLite Schema v2 迁移、Factor/Decision/Risk 本地预览证据持久化和只读 Run History Explorer。全部运行仍为 `NO_EXECUTION`。
- 完成阶段 2A：中央 SQLite Schema v3、可筛选的 Factor 历史与精确版本表格比较、Decision 条件/精确 Sizing 输入持久化，以及带 `Open Run` 的只读 Factor/Decision 检查子面板。未加入 Target Position、图表/导出或交易权限。
- 完成阶段 2B：单一精确 Factor 版本与其精确最终源 Bar 价格图层、缺失/失败状态轨、presentation-only共享Plotly renderer，以及当前有界记录的原子CSV/JSON导出。中央SQLite保持Schema v3，未加入Target Position、Decision导出或交易权限。
- 完成阶段 3A：独立研究资金规划模块、显式USD现金基础、受保护的保险/战术储备、股票专属现金、精确Decimal守恒、只允许股票现金间的零和转移、中央SQLite Schema v4、Allocation Run和Capital Allocation Manager。没有默认资金、自动消费者或交易权限。
- 完成阶段 4A：独立Asset State研究模块、用户定义的符号状态图、每只股票最多一个开放周期、显式人工转换、不可变事件/快照/失败记录、确定性重放、中央SQLite Schema v5、State Run和Asset State Monitor。没有默认状态、自动Factor转换、金融状态含义或交易消费者。
- 完成阶段 5A：独立Target Position研究模块、用户定义的单调有限节点曲线、显式人工scalar/USD资本基数/当前持仓值、精确Decimal边界截断与线性插值、结构化目标/差额轨迹、中央SQLite Schema v6、Target Position Run和Target Position Laboratory。没有默认曲线、自动输入adapter、hysteresis、TradeIntent、Risk或交易消费者。

## Approved next

- 无。

## Pending user decisions

- 是否配置 Alpaca Market Data 凭据并进行真实 API 手动验证。
- 后续具体业务目标；不得从历史数据浏览器推断交易策略或实盘需求。
- 跨版本图表/排名、Decision导出、行业资金、动态权重、储备借贷、自动状态公式/阈值/饱和重置、标准化状态、Target Position自动输入/adapter/hysteresis/Decision转换、数值 Risk、完整回测整合、Accounting 持久化、Paper/Live 均需要后续独立范围与批准；阶段 5A 的完成不自动授权这些能力。

未经用户明确要求，待决事项不得自动转为实施工作。
