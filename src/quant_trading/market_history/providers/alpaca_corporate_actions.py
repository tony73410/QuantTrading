"""Read-only Alpaca corporate-action evidence adapter.

The adapter uses Alpaca's Market Data corporate-actions endpoint only.  It has
no account, order, position or Trading API capability.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from alpaca.data.enums import CorporateActionsType
from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.data.requests import CorporateActionsRequest

from ..research_evidence import (
    ResearchCorporateActionEvent,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceError,
    ResearchEvidenceMode,
)


_SUPPORTED_TYPES = {
    CorporateActionsType.FORWARD_SPLIT.value,
    CorporateActionsType.REVERSE_SPLIT.value,
    CorporateActionsType.CASH_DIVIDEND.value,
    CorporateActionsType.STOCK_DIVIDEND.value,
}

_ACTION_TYPE_ALIASES = {
    "forward_split": "forward_split",
    "forward_splits": "forward_split",
    "reverse_split": "reverse_split",
    "reverse_splits": "reverse_split",
    "cash_dividend": "cash_dividend",
    "cash_dividends": "cash_dividend",
    "stock_dividend": "stock_dividend",
    "stock_dividends": "stock_dividend",
}


class AlpacaCorporateActionProvider:
    """Fetch corporate actions without importing any Alpaca Trading client."""

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self._credentials_present = bool(api_key and secret_key)
        self._client = client
        if client is None and self._credentials_present:
            self._client = CorporateActionsClient(api_key, secret_key)

    @property
    def available(self) -> bool:
        return self._client is not None

    def fetch_snapshot(
        self,
        symbol: str,
        start: date,
        end: date,
        *,
        evidence_mode: ResearchEvidenceMode,
        requested_at_utc: datetime | None = None,
    ) -> ResearchCorporateActionSnapshot:
        if self._client is None:
            raise ResearchEvidenceError("Alpaca Market Data credentials are unavailable")
        if start > end:
            raise ResearchEvidenceError("corporate-action range is reversed")
        normalized = symbol.strip().upper()
        requested = requested_at_utc or datetime.now(UTC)
        request = CorporateActionsRequest(
            symbols=[normalized],
            types=list(CorporateActionsType),
            start=start,
            end=end,
            limit=1000,
        )
        response = self._client.get_corporate_actions(request)
        received = datetime.now(UTC)
        groups = response if isinstance(response, dict) else response.data
        raw_events: list[dict[str, Any]] = []
        for group_name in sorted(groups):
            for item in groups[group_name]:
                payload = item if isinstance(item, dict) else item.model_dump(mode="json")
                raw_events.append(dict(payload))
        raw_events.sort(
            key=lambda item: (
                str(item.get("process_date") or item.get("ex_date") or ""),
                str(item.get("id") or ""),
            )
        )
        events = tuple(
            self._convert_event(index, normalized, payload)
            for index, payload in enumerate(raw_events, 1)
        )
        response_fingerprint = self._hash(raw_events)
        query_identity = self._hash({
            "symbols": [normalized], "types": sorted(item.value for item in CorporateActionsType),
            "start": start.isoformat(), "end": end.isoformat(), "limit": 1000,
        })
        return ResearchCorporateActionSnapshot(
            uuid4(), "alpaca_market_data", query_identity, requested, received,
            start, end, response_fingerprint, evidence_mode, events,
        )

    @classmethod
    def _convert_event(
        cls, ordinal: int, requested_symbol: str, payload: dict[str, Any]
    ) -> ResearchCorporateActionEvent:
        provider_action_type = str(
            payload.get("corporate_action_type") or payload.get("type") or "unknown"
        )
        action_type = _ACTION_TYPE_ALIASES.get(
            provider_action_type, provider_action_type
        )
        event_symbol = str(
            payload.get("symbol")
            or payload.get("source_symbol")
            or payload.get("acquiree_symbol")
            or payload.get("old_symbol")
            or requested_symbol
        ).upper()
        ratio = cls._ratio(payload)
        return ResearchCorporateActionEvent(
            ordinal=ordinal,
            provider_event_id=str(payload.get("id") or cls._hash(payload)),
            symbol=event_symbol,
            action_type=action_type,
            declaration_date=cls._date(payload.get("declaration_date")),
            ex_date=cls._date(payload.get("ex_date")),
            effective_date=cls._date(payload.get("effective_date")),
            process_date=cls._date(payload.get("process_date")),
            ratio_text=ratio,
            raw_event_fingerprint=cls._hash(payload),
            supported=action_type in _SUPPORTED_TYPES,
        )

    @staticmethod
    def _ratio(payload: dict[str, Any]) -> str | None:
        if payload.get("new_rate") is not None and payload.get("old_rate") is not None:
            old = Decimal(str(payload["old_rate"]))
            if old == 0:
                return None
            return str(Decimal(str(payload["new_rate"])) / old)
        if payload.get("rate") is not None:
            return str(Decimal(str(payload["rate"])))
        return None

    @staticmethod
    def _date(value: object) -> date | None:
        if value is None or value == "":
            return None
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    @staticmethod
    def _hash(payload: object) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


__all__ = ["AlpacaCorporateActionProvider"]
