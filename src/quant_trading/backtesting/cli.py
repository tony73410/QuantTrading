"""Explicit offline CLI for repeatable historical simulation evidence."""
from __future__ import annotations
import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from .app import build_service
from .models import BacktestRequest

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the isolated research-only SMA20/50 baseline")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--cash", type=Decimal, default=Decimal("1000000"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = build_service(args.root.resolve()).run(BacktestRequest(uuid4(), args.start, args.end, args.cash))
    print(f"run_id={result.run_id}")
    print(f"environment={result.environment} status={result.status.value}")
    print(f"symbols={result.symbols_tested}/{result.symbols_requested} skipped={len(result.symbols_skipped)}")
    print(f"trades={len(result.trades)} ending_cash={result.ending_cash} ending_market_value={result.ending_market_value}")
    print(f"ending_equity={result.ending_equity} total_return={result.total_return}")
    print("live_trading=false automatic_order_submission=false")
    return 0 if result.status.value != "blocked" else 2

if __name__ == "__main__":
    raise SystemExit(main())
