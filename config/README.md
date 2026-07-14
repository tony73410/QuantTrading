# Configuration

本目录保留给未来获批的非敏感配置；当前历史数据模块不使用仓库内配置文件，而是从操作系统环境变量读取 Alpaca **Market Data** 凭据和可选缓存参数。

应用代码中的安全默认值明确记录：主要券商为 Alpaca、目标执行环境为 `ALPACA_PAPER`、自动下单关闭、Live 关闭、人工确认开启。这些是角色和安全状态，不代表 Paper 账户已连接或执行功能已实现。

根目录 `.env.example` 只列 Alpaca 变量名、安全说明和非敏感默认值；当前实现仅将其用于 Market Data。Key 存在不代表 Paper 或 Live 订单授权。程序不会自动加载该文件，也不接受 Fidelity 用户名、密码、双重认证信息或 API Key。真实 `.env`、API key、secret、账户、密码、token 和私钥不得提交。变量说明见 `docs/modules/market-history.md`。配置格式的改变属于审批事项。
