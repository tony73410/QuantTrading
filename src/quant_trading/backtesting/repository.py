"""Run-scoped JSON storage isolated from all operational accounting stores."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from .models import (BacktestRequest, BacktestResult, BacktestStatus, ConditionTrace,
    DecisionJournalEntry, EquityPoint, FactorTrace, JournalAction, JournalOutcome,
    SimulatedSide, SimulatedTrade)


def _json(value):
    if isinstance(value, (Decimal, UUID, date, datetime)):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    raise TypeError(type(value).__name__)


class JsonBacktestResultRepository:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def save(self, result: BacktestResult) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{result.run_id}.json"
        temporary = self.root / f".{result.run_id}.{uuid4().hex}.tmp"
        try:
            temporary.write_text(
                json.dumps(asdict(result), default=_json, indent=2),
                encoding="utf-8",
            )
            try:
                os.link(temporary, target)
            except FileExistsError as exc:
                raise FileExistsError(
                    f"backtest result {result.run_id} already exists"
                ) from exc
        finally:
            temporary.unlink(missing_ok=True)

    def get(self, run_id: UUID) -> BacktestResult:
        result = self._decode(
            json.loads((self.root / f"{run_id}.json").read_text(encoding="utf-8"))
        )
        if result.run_id != run_id:
            raise ValueError(
                f"stored run_id {result.run_id} does not match requested run_id {run_id}"
            )
        return result

    def list_results(self) -> tuple[BacktestResult, ...]:
        if not self.root.exists():
            return ()
        results = []
        for path in sorted(self.root.glob("*.json"), reverse=True):
            result = self._decode(json.loads(path.read_text(encoding="utf-8")))
            if str(result.run_id) != path.stem:
                raise ValueError(
                    f"stored run_id {result.run_id} does not match result file {path.name}"
                )
            results.append(result)
        return tuple(results)

    @staticmethod
    def _decode(data: dict) -> BacktestResult:
        request = data["request"]
        req = BacktestRequest(UUID(request["run_id"]), date.fromisoformat(request["start_date"]), date.fromisoformat(request["end_date"]), Decimal(request["initial_cash"]), request["currency"], request["short_window"], request["long_window"])
        trades = tuple(SimulatedTrade(UUID(x["trade_id"]), x["order_id"], x["symbol"], date.fromisoformat(x["signal_date"]), datetime.fromisoformat(x["filled_at_utc"]), SimulatedSide(x["side"]), Decimal(x["quantity"]), Decimal(x["price"]), Decimal(x["gross_amount"]), Decimal(x["fee_amount"]), Decimal(x["cash_effect"]), x["operation"]) for x in data["trades"])
        curve = tuple(EquityPoint(date.fromisoformat(x["trading_date"]), Decimal(x["cash"]), Decimal(x["market_value"]), Decimal(x["total_equity"])) for x in data["equity_curve"])
        journal=tuple(JsonBacktestResultRepository._journal(x) for x in data.get("decision_journal",()))
        return BacktestResult(UUID(data["run_id"]), data["environment"], data["strategy_id"], BacktestStatus(data["status"]), datetime.fromisoformat(data["started_at_utc"]), datetime.fromisoformat(data["completed_at_utc"]), req, data["symbols_requested"], data["symbols_tested"], tuple(data["symbols_skipped"]), trades, curve, Decimal(data["ending_cash"]), Decimal(data["ending_market_value"]), Decimal(data["ending_equity"]), Decimal(data["total_return"]), tuple(data["warnings"]),journal)

    @staticmethod
    def _journal(x):
        factors=tuple(FactorTrace(i["scope"],i["factor_id"],i["factor_version"],_value(i.get("value")),i["status"],datetime.fromisoformat(i["as_of_utc"]),i.get("lookback"),tuple(i.get("source_symbols",())),i.get("detail","")) for i in x.get("factor_traces",()))
        conditions=tuple(ConditionTrace(i["factor_id"],i["factor_version"],Decimal(i["actual_value"]) if i.get("actual_value") is not None else None,i["operator"],Decimal(i["threshold"]),bool(i["matched"])) for i in x.get("condition_traces",()))
        decimal_fields=("requested_notional","approved_notional","quantity","fill_price","cash_before","cash_after","position_before","position_after")
        values={name:Decimal(x[name]) if x.get(name) is not None else None for name in decimal_fields}
        return DecisionJournalEntry(UUID(x["journal_id"]),UUID(x["run_id"]),x["strategy_id"],date.fromisoformat(x["trading_date"]),x["symbol"],datetime.fromisoformat(x["as_of_utc"]),JournalAction(x["action"]),JournalOutcome(x["outcome"]),x["reason"],Decimal(x["market_open"]),Decimal(x["market_high"]),Decimal(x["market_low"]),Decimal(x["market_close"]),Decimal(x["market_volume"]),factors,conditions,x.get("sizing_mode","none"),x.get("sizing_expression"),tuple((n,Decimal(v)) for n,v in x.get("sizing_references",())),trade_id=UUID(x["trade_id"]) if x.get("trade_id") else None,**values)


def _value(value):
    if value is None or isinstance(value,(bool,int)): return value
    try: return Decimal(value)
    except Exception: return value
