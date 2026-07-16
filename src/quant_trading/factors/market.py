"""Versioned cross-asset Market Factor contracts and deterministic aggregation."""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID
from .models import FactorResult, FactorStatus

_ID=re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
class MarketAggregation(StrEnum):
    MEAN="mean"; SUM="sum"; MINIMUM="minimum"; MAXIMUM="maximum"; COUNT="count"

@dataclass(frozen=True,slots=True)
class MarketFactorDefinition:
    definition_id: UUID; market_factor_id: str; version: int; display_name: str; description: str
    source_factor_component_id: str; source_factor_name: str; source_factor_version: str
    symbols: tuple[str,...]; aggregation: MarketAggregation; created_at_utc: datetime; created_by: str; change_reason: str
    def __post_init__(self):
        identifier=self.market_factor_id.strip().lower()
        if not _ID.fullmatch(identifier): raise ValueError("market_factor_id is malformed")
        if self.version<1: raise ValueError("Market Factor version must be positive")
        symbols=tuple(x.strip().upper() for x in self.symbols)
        if not symbols or any(not x for x in symbols) or len(symbols)!=len(set(symbols)): raise ValueError("Market Factor requires a unique explicit symbol universe")
        for field in ("display_name","description","source_factor_component_id","source_factor_name","source_factor_version","created_by","change_reason"):
            if not getattr(self,field).strip(): raise ValueError(f"{field} must not be empty")
        if self.created_at_utc.tzinfo is None: raise ValueError("created_at_utc must include a timezone")
        object.__setattr__(self,"market_factor_id",identifier); object.__setattr__(self,"symbols",symbols); object.__setattr__(self,"created_at_utc",self.created_at_utc.astimezone(UTC))
    @property
    def component_id(self): return f"user_market_factor.{self.market_factor_id}.v{self.version}"

@dataclass(frozen=True,slots=True)
class MarketFactorResult:
    market_factor_name: str; market_factor_version: str; as_of_utc: datetime; value: Decimal|None; status: FactorStatus
    source_factor_component_id: str; symbols: tuple[str,...]

class MarketFactorCalculator:
    def __init__(self,definition: MarketFactorDefinition): self.definition=definition
    def calculate(self,results: tuple[FactorResult,...],*,as_of_utc: datetime)->MarketFactorResult:
        by_symbol={x.symbol:x for x in results}
        if len(results)!=len(by_symbol): return self._result(None,FactorStatus.INVALID_INPUT,as_of_utc)
        if set(by_symbol)!=set(self.definition.symbols): return self._result(None,FactorStatus.INSUFFICIENT_DATA,as_of_utc)
        selected=tuple(by_symbol[x] for x in self.definition.symbols)
        if any(x.as_of_utc!=as_of_utc or x.status is not FactorStatus.VALID or x.factor_name!=self.definition.source_factor_name or x.factor_version!=self.definition.source_factor_version or not isinstance(x.value,(Decimal,int)) or isinstance(x.value,bool) for x in selected): return self._result(None,FactorStatus.INVALID_INPUT,as_of_utc)
        values=tuple(Decimal(x.value) for x in selected); aggregation=self.definition.aggregation
        value=Decimal(len(values)) if aggregation is MarketAggregation.COUNT else sum(values,Decimal(0)) if aggregation is MarketAggregation.SUM else sum(values,Decimal(0))/Decimal(len(values)) if aggregation is MarketAggregation.MEAN else min(values) if aggregation is MarketAggregation.MINIMUM else max(values)
        return self._result(value,FactorStatus.VALID,as_of_utc)
    def _result(self,value,status,as_of): return MarketFactorResult(self.definition.market_factor_id,str(self.definition.version),as_of,value,status,self.definition.source_factor_component_id,self.definition.symbols)
