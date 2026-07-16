"""Atomic local JSON persistence for immutable simulation strategies."""
from __future__ import annotations
import json, os
from datetime import datetime
from pathlib import Path
from threading import RLock
from uuid import UUID
from .strategy_definitions import SimulationStrategyDefinition

class JsonSimulationStrategyStore:
    schema_version = 1
    def __init__(self, path: Path | str) -> None: self.path=Path(path); self._lock=RLock()
    def list_definitions(self) -> tuple[SimulationStrategyDefinition, ...]:
        with self._lock:
            if not self.path.exists(): return ()
            raw=json.loads(self.path.read_text(encoding="utf-8"))
            if raw.get("schema_version") != self.schema_version: raise ValueError("unsupported simulation-strategy schema version")
            return tuple(self._decode(item) for item in raw.get("definitions", ()))
    def save_definition(self, definition: SimulationStrategyDefinition) -> None:
        with self._lock:
            items=self.list_definitions()
            if any(x.definition_id==definition.definition_id or (x.strategy_id==definition.strategy_id and x.version==definition.version) for x in items): raise ValueError("simulation strategy version already exists")
            self.path.parent.mkdir(parents=True, exist_ok=True); temporary=self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"schema_version":1,"definitions":[self._encode(x) for x in (*items,definition)]},ensure_ascii=False,indent=2),encoding="utf-8"); os.replace(temporary,self.path)
    @staticmethod
    def _encode(x):
        return {"definition_id":str(x.definition_id),"strategy_id":x.strategy_id,"version":x.version,"display_name":x.display_name,"description":x.description,"buy_decision_component_id":x.buy_decision_component_id,"sell_decision_component_id":x.sell_decision_component_id,"created_at_utc":x.created_at_utc.isoformat(),"created_by":x.created_by,"change_reason":x.change_reason,"universe":x.universe,"allocation":x.allocation,"fill_model":x.fill_model,"cost_model":x.cost_model,"research_only":x.research_only,"execution_allowed":x.execution_allowed,"live_allowed":x.live_allowed}
    @staticmethod
    def _decode(x):
        return SimulationStrategyDefinition(UUID(x["definition_id"]),x["strategy_id"],int(x["version"]),x["display_name"],x["description"],x["buy_decision_component_id"],x["sell_decision_component_id"],datetime.fromisoformat(x["created_at_utc"]),x["created_by"],x["change_reason"],x["universe"],x["allocation"],x["fill_model"],x["cost_model"],bool(x["research_only"]),bool(x["execution_allowed"]),bool(x["live_allowed"]))
