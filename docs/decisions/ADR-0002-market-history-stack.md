# ADR-0002: Market History Browser Technology Stack

## Status

Accepted

## Context

首个获批正式模块需要桌面 GUI、交互金融图表、Alpaca 历史行情、本地持久化和自动化测试。此前仓库没有语言或框架选择。

## Options considered

1. 用户明确授权的 Python + PySide6/QWebEngineView + Plotly + alpaca-py + pandas + SQLite + pytest。
2. Web 控制面板、其他行情提供商或服务器数据库。
3. 继续只保留治理骨架。

## Decision

采用选项 1，仅用于 `market_history` 模块。Python 版本声明为 3.11–3.14，当前在 3.14.5 验证。SQLite 使用标准库，不引入 ORM；GUI 与 Provider/Store/Service/Chart 分层。

## Rationale

该组合完全来自用户明确授权，支持桌面交互、离线缓存和可替换 Provider，并避免未要求的 Web 框架、数据库服务和交易连接。

## Consequences

- 增加五项直接依赖和 Python 项目配置。
- PySide6 安装体积较大；QWebEngine 需要可用桌面图形环境。
- Alpaca Feed、延迟和历史范围受账户权限约束。
- `alpaca-py` 包含 WebSocket 传递依赖，但本模块只调用 REST Market Data。
- 本决定不授权交易 API、策略、信号、回测、订单或实盘。

## Reversal

若未来替换 GUI、Provider 或存储，应创建新的 ADR，保持现有公共模型或明确迁移影响；不得静默改变缓存唯一键、时间语义或公共接口。
