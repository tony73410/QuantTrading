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
- 完成阶段 5B：Factor所有者内的人工标准化价格状态研究、显式正Decimal USD价格/参考/尺度、精确`D=P-R`与无量纲`S=D/K`、结构化轨迹、中央SQLite Schema v7、Standardized State Run和研究检查页。没有自动参考/尺度估计、Market Data adapter、generic FactorSnapshot、Target Position或交易消费者。
- 完成阶段 5C：显式选择一个已保存的Standardized State结果和一个既有Target Position曲线，精确复制无量纲scalar/symbol/time，以人工USD资本/当前持仓为上下文调用未改变的曲线引擎，保存父/子/源`NO_EXECUTION` Run及中央SQLite Schema v8 typed provenance，并在既有Target Position页面提供linked history/Open Run。没有估计器、自动latest/default、事实资金adapter、Decision、数值Risk或交易消费者。
- 完成阶段 5D：Decision所有者只接受一个显式选择的已完成Phase 5C link，把精确正差额映射为`INCREASE`、负差额映射为`DECREASE`、零差额映射为`HOLD`且不创建intent；非零建议USD金额精确为差额绝对值。类型独立的研究intent、四向Run导航和中央SQLite Schema v9历史已验证；仅Phase 6A非批准结构门可读取，且没有EXIT、阈值、舍入、账户事实、回测或执行消费者。
- 完成阶段 6A：Risk所有者只接受一个显式选择的非零Phase 5D专用intent，重验完整来源链和锁定非执行安全快照，按固定顺序保存三个结构规则；安全有效请求固定为`MANUAL_REVIEW_REQUIRED`，不安全运行状态为`BLOCKED`。中央SQLite Schema v10、相关Run导航和既有Risk页独立子页签已验证；无approved notional/object、数值Risk、账户事实、回测或执行消费者。
- 完成阶段 6B：Risk所有者以一个显式Phase 6A人工复核结果和同股票当前精确的不可变正Decimal USD上限版本为输入，只执行`MAX_TARGET_EXPOSURE_USD@1`：INCREASE可保持、缩小或阻止，long-only DECREASE保持。正候选仍为`MANUAL_REVIEW_REQUIRED`。Schema v11、完整Run导航和既有Risk页子页签已验证；无默认上限、approved object、账户事实、回测或执行消费者。
- 完成阶段 6C：Risk所有者以一个显式正Phase 6B人工复核候选、同股票当前精确的不可变有限非负Decimal USD底线版本和精确Phase 5C人工研究资金基数为输入，在继承的`MAX_TARGET_EXPOSURE_USD@1`规则1之后执行`MIN_RESEARCH_ASSET_CASH_USD@1`规则2。INCREASE可保持、缩小或阻止，long-only DECREASE保持；显式零有效，正候选仍为`MANUAL_REVIEW_REQUIRED`。Schema v12、完整Run导航和既有Risk页子页签已验证；无默认底线、事实现金、approved object、回测或执行消费者。
- 完成阶段 6D：Risk所有者以一个显式正Phase 6C候选、一个显式Phase 3A `RESEARCH_INPUT`计划及其精确最新守恒快照为输入，在继承规则1/2后执行`MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1`规则3。INCREASE受同股票`ASSET_CASH`规划余额限制，long-only DECREASE保持；所有结果均记录`research_cash_reserved=false`，正候选仍需人工复核。Schema v13、完整上游/Capital Snapshot Run导航和既有Risk页子页签已验证；无默认计划、资金预留/转移、事实现金、approved object、回测或执行消费者。
- 完成阶段 6E：在既有Risk页面增加只读Consolidated Risk Chain Explorer，从Phase 6D结果通过公共查询合同精确解析Phase 6C/6B/6A结果与source links，结构门与数值规则1–3分开展示，支持含可选inclusive UTC as-of边界的有界筛选、两个显式历史链的精确A/B相等性比较及九条Open Run路径。缺失/不一致证据明确失败；Schema仍为v13，无重算、写入、审批、预留、导出、回测或执行能力。

## Approved next

- 无。

## Pending user decisions

- 是否配置 Alpaca Market Data 凭据并进行真实 API 手动验证。
- 后续具体业务目标；不得从历史数据浏览器推断交易策略或实盘需求。
- 跨版本图表/排名、Decision导出、行业资金、动态权重、储备借贷、自动状态公式/阈值/饱和重置、参考/尺度估计器、Market Data adapter、自动source/curve选择、进一步Capital/Accounting adapter、hysteresis、事实/预留现金、完整数值Risk批准/更多规则组合、完整回测整合、Accounting持久化、Paper/Live均需要后续独立范围与批准；Phase 6D仅是三条有序、未消费且不预留资金的数值研究约束，不自动授权Risk批准或这些后续能力。

未经用户明确要求，待决事项不得自动转为实施工作。
