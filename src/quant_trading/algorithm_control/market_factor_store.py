"""Atomic JSON persistence for immutable Market Factor definitions."""
import json,os
from datetime import datetime
from pathlib import Path
from threading import RLock
from uuid import UUID
from quant_trading.factors.market import MarketAggregation,MarketFactorDefinition
class JsonMarketFactorDefinitionStore:
    schema_version=1
    def __init__(self,path): self.path=Path(path); self._lock=RLock()
    def list_definitions(self):
        with self._lock:
            if not self.path.exists(): return ()
            raw=json.loads(self.path.read_text(encoding="utf-8"))
            if raw.get("schema_version")!=1: raise ValueError("unsupported Market Factor schema")
            return tuple(self._decode(x) for x in raw.get("definitions",()))
    def save_definition(self,item):
        with self._lock:
            existing=self.list_definitions()
            if any(x.definition_id==item.definition_id or (x.market_factor_id==item.market_factor_id and x.version==item.version) for x in existing): raise ValueError("Market Factor version already exists")
            self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix(".tmp"); tmp.write_text(json.dumps({"schema_version":1,"definitions":[self._encode(x) for x in (*existing,item)]},ensure_ascii=False,indent=2),encoding="utf-8"); os.replace(tmp,self.path)
    @staticmethod
    def _encode(x): return {"definition_id":str(x.definition_id),"market_factor_id":x.market_factor_id,"version":x.version,"display_name":x.display_name,"description":x.description,"source_factor_component_id":x.source_factor_component_id,"source_factor_name":x.source_factor_name,"source_factor_version":x.source_factor_version,"symbols":list(x.symbols),"aggregation":x.aggregation.value,"created_at_utc":x.created_at_utc.isoformat(),"created_by":x.created_by,"change_reason":x.change_reason}
    @staticmethod
    def _decode(x): return MarketFactorDefinition(UUID(x["definition_id"]),x["market_factor_id"],int(x["version"]),x["display_name"],x["description"],x["source_factor_component_id"],x["source_factor_name"],x["source_factor_version"],tuple(x["symbols"]),MarketAggregation(x["aggregation"]),datetime.fromisoformat(x["created_at_utc"]),x["created_by"],x["change_reason"])
