"""Versioned public-contract declarations and compatibility checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ContractStatus(StrEnum):
    IMPLEMENTED = "implemented"
    PLANNED = "planned"


class CompatibilityResult(StrEnum):
    COMPATIBLE = "compatible"
    REQUIRES_ADAPTER = "requires_adapter"
    REQUIRES_MIGRATION = "requires_migration"


@dataclass(frozen=True, slots=True)
class DataContractDeclaration:
    contract_id: str
    schema_version: str
    python_type: str
    producer_layer: str
    consumer_layers: tuple[str, ...]
    created_at_semantics: str
    source_component_semantics: str
    source_version_semantics: str
    correlation_id_semantics: str
    status: ContractStatus

    @property
    def major_version(self) -> int:
        return int(self.schema_version.split(".", 1)[0])


class DataContractRegistry:
    def __init__(self, declarations: tuple[DataContractDeclaration, ...] = ()) -> None:
        self._items: dict[str, DataContractDeclaration] = {}
        for declaration in declarations:
            self.register(declaration)

    def register(self, declaration: DataContractDeclaration) -> None:
        if not declaration.contract_id.strip() or declaration.contract_id in self._items:
            raise ValueError(f"invalid or duplicate contract: {declaration.contract_id}")
        if not declaration.schema_version.strip() or not declaration.python_type.strip():
            raise ValueError("contract version and python_type are required")
        self._items[declaration.contract_id] = declaration

    def get(self, contract_id: str) -> DataContractDeclaration:
        try:
            return self._items[contract_id]
        except KeyError as exc:
            raise ValueError(f"unknown public contract: {contract_id}") from exc

    def contains(self, contract_id: str) -> bool:
        return contract_id in self._items

    def compare(self, current_id: str, proposed: DataContractDeclaration) -> CompatibilityResult:
        current = self.get(current_id)
        if current.major_version != proposed.major_version:
            return CompatibilityResult.REQUIRES_MIGRATION
        if current.python_type != proposed.python_type:
            return CompatibilityResult.REQUIRES_ADAPTER
        return CompatibilityResult.COMPATIBLE

    @property
    def declarations(self) -> tuple[DataContractDeclaration, ...]:
        return tuple(self._items.values())


def default_contract_registry() -> DataContractRegistry:
    def declaration(contract_id: str, python_type: str, producer: str, consumers: tuple[str, ...], status: ContractStatus = ContractStatus.IMPLEMENTED) -> DataContractDeclaration:
        return DataContractDeclaration(
            contract_id=contract_id,
            schema_version="1.0",
            python_type=python_type,
            producer_layer=producer,
            consumer_layers=consumers,
            created_at_semantics="Recorded by the producing component; exact field is defined by the typed contract.",
            source_component_semantics="Declared by component metadata and producing engine identity.",
            source_version_semantics="Declared by component/policy/rule version fields.",
            correlation_id_semantics="Trace ID or referenced upstream snapshot/intent ID; adapters must preserve it.",
            status=status,
        )

    return DataContractRegistry((
        declaration("NoInput", "None", "none", ()),
        declaration("NoOutput", "None", "none", ()),
        declaration("SystemSafetyState", "algorithm_control.ComponentMetadata", "risk", ("configuration",)),
        declaration("LockedEnabledState", "algorithm_control.ConfigurationRecord", "risk", ("configuration", "gui")),
        declaration("MarketDataWindow", "quant_trading.factors.models.MarketDataWindow", "market_data", ("factor",)),
        declaration("FactorSnapshot", "quant_trading.factors.models.FactorSnapshot", "factor", ("decision", "risk")),
        declaration("TradeIntent", "quant_trading.decision.models.TradeIntent", "decision", ("risk",)),
        declaration("RiskDecision", "quant_trading.risk.models.RiskDecision", "risk", ("execution", "gui")),
        declaration("ApprovedTradeIntent", "quant_trading.risk.models.RiskApprovedTradeIntent", "risk", ("execution",)),
        declaration("OrderRequest", "Not implemented", "execution", ("execution",), ContractStatus.PLANNED),
        declaration("ExecutionResult", "Not implemented", "execution", ("gui", "audit"), ContractStatus.PLANNED),
    ))
