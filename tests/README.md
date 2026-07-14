# Tests

本目录存放与正式行为对应的 pytest 测试。当前包含 `unit/market_history` 与 `integration/market_history`。

所有行情 Provider 测试使用 Fake/Mock 或替换 SDK 底层 HTTP；不得访问真实 Alpaca、真实券商账户或提交订单。运行：`.\.venv\Scripts\python.exe -m pytest -q`。
