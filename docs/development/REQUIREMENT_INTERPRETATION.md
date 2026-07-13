# Requirement Interpretation Protocol

本规范用于把用户以日常语言表达的目标，转化为准确、可验证且不会越过产品决定权的软件需求。核心原则是：**保留用户意图，不机械复制可能不准确的术语或实现建议。**

## 1. Separate goal from proposed method

分析需求时区分以下内容；简单需求可合并为短段落，复杂或高风险需求应明确列出：

```text
User goal:
用户真正希望得到的结果。

User-proposed method:
用户建议的实现方法；除非用户明确要求保留，否则它不自动成为强制约束。

Technical interpretation:
准确的软件工程含义。

Trading interpretation:
准确的市场、数据或交易含义；不涉及交易时可标为 Not applicable。

Recommended implementation:
最符合目标且最小、可测、可撤销的实现方式。
```

如果用户明确要求保留某种方法，应遵守，同时说明局限、风险、替代方案和实际行为后果。

## 2. Use precise terminology

遇到模糊或非标准术语时：推断最可能含义，用正确术语重述，以通俗语言说明关系，并在代码、接口、测试和文档中使用一致的准确名称。错误或含混命名不得扩散到代码库。

例如，“价格”可能表示最新成交价、买一价、卖一价、开盘价、收盘价、复权收盘价或成交价；“收益”可能表示绝对盈亏、简单/对数收益率、已实现/未实现盈亏、组合或年化收益。只有真实语义确认后才能确定字段和接口名称。

## 3. Engineering discretion

用户目标已经明确、且选择不改变产品或交易行为时，可自主决定普通内部实现细节，包括私有函数拆分、内部数据结构、普通异常处理、单元测试组织、输入验证、日志方式、减少重复及保持现有风格。

这些判断仍须遵守现有架构、依赖和审批规则。不得把“工程细节”扩大为新框架、第三方依赖、公共接口、配置/数据格式、模块职责或交易规则。

## 4. Minimum-assumption rule

需求不完整时，优先选择：

- 最简单的合理解释；
- 最容易测试和撤销的实现；
- 保持现有外部行为；
- 不新增依赖或扩大模块职责；
- 不产生真实资金风险；
- 不发明用户没有表达的交易规则。

只补齐实现当前目标必需的细节，不替用户设计整个产品。

## 5. Interpretation levels

### Level A — Different wording, one clear meaning

自动转换为准确需求，简短说明理解后直接实施，并在 EDIT_LOG 记录采用的专业解释。

### Level B — Multiple low-risk internal interpretations

选择最符合现有架构、最容易撤销的方案，明确记录假设；无需把普通工程细节反复交给用户决定。

### Level C — Interpretations change visible product behavior

列出最可能解释、推荐项和理由。只有在默认方案安全且容易撤销时才可采用，并须把假设写入相关代码、测试、文档和 EDIT_LOG；不得隐藏假设。若差异会实质改变用户目标且没有安全默认值，应先确认。

### Level D — Interpretations affect money, trading, or safety

不得静默选择，也不得先实现有风险的行为。必须用通俗语言解释选项的实际后果、给出推荐，并等待用户明确选择。可以先建立不锁定具体交易语义的中性接口、测试框架或占位结构，但不得借此暗中选择行为。

Level D 包括但不限于：买卖条件、订单类型/数量、仓位、杠杆、做空、止盈止损、风险限制、费用与滑点、回测时间含义、未来数据风险、实盘/模拟盘、复权口径、时区与交易日、重复下单及真实账户使用。

## 6. Correct conceptual errors constructively

若需求基于明显不准确的编程或市场理解，不直接实现。使用以下结构，语气保持中性：

```text
What I believe you want:
用户希望得到的结果。

Potential issue:
原方法可能无法实现目标的原因。

Correct interpretation:
准确的概念。

Recommended approach:
保留原意的更可靠方法。

Behavioral consequence:
程序最终会如何运行。
```

重点解释实际后果，不只判断对错。

## 7. No hidden financial advice

用户未明确规定时，不得自行决定交易标的、买卖条件、指标优劣、收益最高的策略、风险参数、仓位、杠杆或回测结果能否代表未来表现。可以解释概念、风险和可选实现，并推荐更安全或易验证的工程方案；主观投资判断不得伪装成技术决定。

## 8. Pre-implementation restatement

开始实现前，用与风险相称的篇幅说明：

```text
My understanding:
用户希望实现的结果。

Professional interpretation:
准确的软件或交易术语。

Assumptions:
暂时采用的必要假设。

What will change:
本次修改范围。

What will not change:
明确排除的范围。

Acceptance criteria:
可验证的完成条件。
```

明显、低风险的小修改可压缩成一段；Level C/D 不得省略关键歧义和后果。

## 9. Record important assumptions

影响行为的重要假设必须进入至少一个持久位置：模块文档、配置说明、测试名称/说明、ADR、`logs/EDIT_LOG.md` 或 `docs/project/PROJECT_STATE.md`。不能只在对话中说明。

用户后来纠正含义时，保留原历史，新增编辑日志，更新相关代码、测试和文档，说明行为变化和回滚方法。

## 10. Plain-language reporting

面向用户的报告先说程序现在能做什么和外部变化，再说明必要的内部技术。专业术语应同时解释它实际意味着什么。

每次完成任务至少说明：

- 程序现在能够做什么；
- 用户可观察到的变化；
- 哪些仅是内部结构变化；
- 重要假设；
- 尚未实现的内容；
- 用户下一步需要决定的事项。

