# Project State

## Current phase

Governed stock historical data browser, separately testable Factor/Decision/Risk contracts, and an independent Algorithm Control Center; no production algorithm, numerical risk policy, account connection, order, or execution module.

## Implemented capabilities

- 仓库级工作规则、文档索引、ADR 机制、编辑日志规范及目录职责说明。
- 根目录 `PROJECT_COMPASS.md`：保存用户批准的 Stable Core、当前系统语义、Active Intent、Assumption Register、Open Decisions、漂移检测及 AI 实施前后审查规则；详见 ADR-0003。
- `docs/architecture/OVERVIEW.md` 是唯一主要架构来源：基于实际代码记录模块职责/非职责、公共接口、依赖矩阵、数据流、不变量、变更影响范围和已知漂移风险；详见 ADR-0004。
- 需求解释协议：区分用户目标与建议方法，按风险等级处理歧义，并要求通俗汇报和持久记录重要假设。
- PySide6 桌面控制面板：覆盖 11 个 GICS 大类行业、共 110 个常见美股代码的本地前缀自动补全，以及粒度对应的快捷/自定义范围、10/30 分钟、1 小时、日/周/月、复权、Feed、K线/折线/OHLC、字段、成交量、范围滑块及更新控制；已有图表后切换时间范围或粒度会自动后台加载。
- Alpaca Market Data Provider（分钟/小时默认限纽约常规时段）、SQLite 本地缓存、Coverage/Fetch History、粒度隔离、缺失区间补齐、尾部重叠刷新、离线回退和 Plotly 交互图表。
- 应用角色明确分离：主要行情数据提供商和计划主要券商均为 Alpaca，默认目标环境为 `ALPACA_PAPER`。
- Paper execution、账户、持仓和订单能力均为 **Not implemented**；自动下单关闭、Live 关闭、人工确认开启。
- Fidelity 保留为非默认的可选手动兼容状态；未连接、未启用且不读取凭据。
- pytest 单元、集成与架构测试；架构测试使用标准库 AST 检查循环/非法跨层 import，真实网络被禁止。
- 统一 Debug 基础设施：稳定 Error Code、Session ID/Request ID、用户友好诊断、Secret 脱敏、UTC 结构化 `app.log`/`error.log` 轮转日志、全局/Worker 异常记录和只读诊断命令。
- `logs/BUG_LOG.md` 是编辑、测试、审查和运行中发现的确认错误与可信潜在缺陷的唯一开发历史；未来任务必须报告发现/修复/延期状态，Fixed必须有真实验证证据。
- 三层算法基础：`quant_trading.factors`输出版本化、策略中立FactorSnapshot；`quant_trading.decision`只消费公开FactorSnapshot并输出不可变、非执行TradeIntent；`quant_trading.risk`独立裁决并输出RiskDecision，只能保持/降低/阻止风险；`quant_trading.orchestration`只组织调用顺序。当前没有正式公式、Decision Policy或数值Risk Policy。
- 独立算法控制中心：Registry驱动Factor/Decision/Risk元数据与通用参数界面，区分Draft/Saved/Active、保留不可变配置历史、验证依赖、锁定安全不变量，并在后台运行NO EXECUTION预览。当前正式算法列表为空，不伪造生产结果。
- 交易能力：**Not implemented**。

- Change Admission / Conflict Prevention is implemented in `quant_trading.algorithm_control`: typed component ownership, capabilities and public-contract declarations; disabled-by-default activation evidence; registration conflict checks; fail-closed pre-run Pipeline validation; and a read-only GUI Conflict Center. No production algorithm was activated.

## Active modules

- `quant_trading.market_history` — 股票历史数据浏览器；见 `docs/modules/market-history.md`。
- `quant_trading.factors` — 单资产因子合同、注册器和无公式引擎；见 `docs/modules/factors.md`。
- `quant_trading.decision` — 非执行交易决策合同、注册器和无规则引擎；见 `docs/modules/trading-decision.md`。
- `quant_trading.risk` — 独立风险合同、注册器、保守组合引擎和Risk-approved类型门；见 `docs/modules/risk-control.md`。
- `quant_trading.orchestration` — Factor → Decision及Factor → Decision → Risk接口级编排；见 `docs/modules/analysis-decision-pipeline.md`。
- `quant_trading.algorithm_control` — 组件元数据、版本配置、验证、安全预览、审计与独立桌面GUI；见 `docs/modules/algorithm-control-gui.md`。

## Public interfaces

- Python：`HistoricalDataRequest`, `MarketBar`, `HistoricalDataService`, `HistoryController` 及 Provider/Store Protocol。
- Desktop entry point：`quant-history` 或 `python -m quant_trading.market_history`。
- Factor：`FactorCalculator`, `SingleAssetFactorEngine`, `FactorResult`, `FactorSnapshot`, `FactorSnapshotCollection`。
- Decision：`TradingDecisionPolicy`, `TradingDecisionEngine`, `DecisionResult`, `TradeIntent`。
- Risk：`RiskPolicy`, `RiskEngine`, `RiskDecision`, `RiskApprovedTradeIntent`及中性上下文/Provider Protocol。
- Orchestration：`AnalysisDecisionPipeline`, `TradingEvaluationPipeline`。
- Algorithm Control：`AlgorithmComponentRegistry`, `ParameterSchema`, `ConfigurationService`, `AlgorithmControlController`, `AlgorithmControlPanel`；入口`quant-algorithm-control`或`python -m quant_trading.algorithm_control`。

- Change Admission public interfaces: `ChangeAdmissionService`, `ChangeProposal`, `ChangeImpactReport`, `ConflictAssessment`, `PipelineAdmissionResult`, `DataContractDeclaration`, `Capability`, and `FeatureState`; proposal workflow in `docs/proposals/README.md`.

## Current technology decisions

- Python 支持范围为 3.11–3.14；当前实际验证版本为 3.14.5。
- 历史数据模块采用 PySide6/QWebEngineView、Plotly、官方 `alpaca-py`、pandas、标准库 SQLite 和 pytest。
- 内部时间与数据库时间统一为 UTC；历史请求区间为 `[start, end)`。
- 价格字段以十进制文本保存到 SQLite；图表展示时转换为浮点数。
- 默认数据库为 `runtime/data/market_history.sqlite3`，运行日志为 `runtime/logs/app.log` 与 `runtime/logs/error.log`；这些运行产物不提交 Git。
- 算法控制状态独立保存在`runtime/algorithm_control/control_state.json`，使用原子替换、不可变版本和审计记录；不保存凭据，也不与行情SQLite混合。
- 安全边界默认为 DEVELOPMENT / BACKTEST / PAPER-TRADING ONLY。
- `MarketDataProviderType`、`BrokerageType` 与 `ExecutionEnvironment` 使用独立枚举；默认值分别为 `ALPACA`、`ALPACA` 和 `ALPACA_PAPER`。
- 当前 Alpaca 环境变量只用于 Market Data；Key 存在不会启用 Paper/Live 下单。项目不读取或保存 Fidelity 用户名、密码、双重认证信息或 API Key。
- 配置、正式源码、测试、脚本、运行产物和归档内容使用独立目录。
- 当前依赖方向经代码与自动检查验证为 `UI → Controller → Service → Protocols ← Provider/Store`，Controller 另依赖 Chart Builder；`app.py` 是唯一具体组装入口。
- 算法依赖方向为 `MarketDataWindow → factors → FactorSnapshot → decision → TradeIntent → risk → RiskDecision`；上游不反向依赖下游，Risk不依赖具体Factor/Decision实现、Market History、SQLite、GUI、Alpaca或Execution。
- Git 默认分支为 `main`；提交身份仅在本项目生效；远程 `origin` 指向 `https://github.com/tony73410/QuantTrading.git`。

## Pending decisions

- 当前环境曾完成 Alpaca IEX 只读验证；其他电脑/进程是否配置凭据以及 SIP 等 Feed 权限仍取决于本地环境和账户订阅，不能从仓库推断。
- 自动本地数据保留与清理目标已由用户提出，但具体期限、不可逆删除、Coverage同步和持久化结构方案尚未批准；当前 **Not implemented**，见 Compass DEC-001 / INTENT-005。
- 后续业务需求及其技术选择；本次决定不自动扩展到交易、策略或其他模块。
- Market History Bar如何按各粒度/交易日历映射为Factor `available_at_utc`尚待决定；为防止前视偏差，目前不自动连接两者，见Compass DEC-005。
- 复权历史对未来Factor/回测的point-in-time语义尚未批准；当前合同只记录Adjustment，不声明其可用于无前视偏差回测，见Compass DEC-006。
- 正式因子公式、参数、缺失值政策、Decision Policy、阈值、仓位/组合语义均待用户逐项批准；当前只有合同和Fake测试。
- 最大仓位/订单、现金、Buying Power、亏损、回撤、集中度、杠杆、保证金和紧急自动降仓规则/数值均待用户逐项批准；当前Risk无生产规则，见Compass DEC-007。
- 未来若提出 Paper 账户、订单或自动执行需求，必须先单独定义 execution 模块、订单模型、人工确认和风险边界并重新审批；当前没有此模块。
- Alpaca Live 的独立凭据/endpoint、风险限制、资金限制、每日亏损限制、最大持仓、额外确认和紧急停止方案均待未来明确批准。

## Known limitations

- 只读诊断已用现有凭据成功验证 AAPL IEX Market Data；SIP 等 Feed 仍取决于用户订阅权限。
- 未在实际物理显示器进行人工视觉验收；offscreen GUI 烟雾测试通过但产生 GPU 回退提示。
- 没有安装包分发、自动更新、选择性缓存删除或实时 WebSocket 行情。
- 本地股票代码建议目录不会自动同步上市、退市、代码或行业分类变化；列表之外的代码仍可自由输入。
- 正在执行的同步 Alpaca HTTP 请求无法安全中途取消，窗口关闭可能等待请求结束；见 KI-0006 / BUG-20260713-005。
- 分钟/小时常规时段使用固定 09:30–16:00 纽约时间窗口，当前不能识别提前收盘日；见 KI-0007。
- Factor/Decision/Risk尚未接入Market History运行流程或结果持久化；控制中心只管理元数据和配置，不代表算法可供实际交易。
- 没有正式Factor/Decision/Risk组件，因此对应控制页为空或仅显示锁定系统安全项，Pipeline Dry Run不可运行。
- Risk的Account/Portfolio/OpenOrders Provider只有抽象Protocol；没有账户连接。Emergency de-risking当前只会暂停新Intent，自动平仓Not implemented。

## Next approved work

无后续功能阶段获批。存储清理为 **Proposed, not approved**；Paper execution、策略、回测和 Live 均不得自行开始。

## Last verified date

2026-07-14 (Change Admission and Conflict Center verified; full-suite result is recorded in EDIT-20260714-026; Live and automatic submission remain disabled.)
