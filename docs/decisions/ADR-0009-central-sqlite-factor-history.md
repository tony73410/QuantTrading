# ADR-0009: Central SQLite Factor History

## Status

Accepted

## Context

Market History already persists Bars in `runtime/data/market_history.sqlite3`, while Factor contracts had no persistence. The user approved retaining meaningful historical Factor results and every calculation run without allowing exact result duplicates to grow indefinitely.

## Options considered

1. Keep separate Market and Factor database files.
2. Create a new database path and copy/move existing Market data.
3. Reuse the existing SQLite file as one physical database while keeping Market and Factor Store interfaces independent.

## Decision

Use option 3. `quant_trading.persistence` owns the shared SQLite connection and idempotent schema initialization. Market History and Factor persistence keep separate public contracts and query responsibilities. Exact semantic Factor results are content-deduplicated; every calculation attempt remains a separate audit record.

## Rationale

This preserves existing data and paths, avoids a risky copy/rename, adds no dependency, and prevents one physical database from becoming one coupled business module. Content fingerprints retain meaningful versions while avoiding repeated identical payloads.

## Consequences

- Existing Market tables and behavior remain compatible.
- Factor provenance includes symbol, as-of, timeframe, adjustment, feed, source/configuration fingerprints and versioned results.
- Concrete SQLite remains outside the pure Factor layer.
- No production Factor is automatically created or executed.
- Automatic cleanup remains a separate open decision; this change performs no deletion.

## Reversal

Stop injecting the Factor Store and restore the previous Market-only initializer. Do not automatically drop the additive tables because they contain user history. A future physical database rename or table deletion requires a separate migration approval.
