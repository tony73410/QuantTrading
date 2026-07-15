# PROPOSAL-002: Paper and Live Execution Boundaries

## Status and identity

- Proposal ID: `PROPOSAL-002`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-14
- Author: Codex
- User approval status: Approved in the current request
- Related ADR / Intent / Edit Log: ADR-0010 / INTENT-014 / EDIT-20260714-030

## Intent interpretation

### User request

Create two sibling layers for simulated trading and real-money trading. Most future code testing will occur in the simulated layer. Add no behavior yet.

### Underlying user goal

Prevent future Paper testing work from becoming mixed with or accidentally activating Live execution.

### User-suggested method

Create two same-level layers.

### Professional interpretation

Create declaration-only `quant_trading.execution.paper` and `quant_trading.execution.live` sibling packages under one Execution ownership boundary.

### Recommendation

Create only package identity, documentation and structural tests. Add no contracts, clients, endpoints, credentials, account access, order behavior or activation.

## Architecture classification

- Owning layer: Execution
- Owning module: `quant_trading.execution`
- Why this belongs in the system: future broker execution needs explicit environment separation after Risk review.
- Why no existing component can own it unchanged: Execution was planned but no package existed; Market Data, Decision and Risk are forbidden owners.
- Responsibilities: reserve isolated Paper and Live namespaces.
- Explicit non-responsibilities: all account, order, broker, strategy, Risk and activation behavior.
- Existing components affected: architecture/governance documents and tests only.

## Component identity declaration

- `component_id`: `execution.paper.boundary`, `execution.live.boundary`
- `component_type`: Execution namespace boundary
- `display_name`: Paper Execution / Live Execution
- `version`: `0`
- `owner_layer`: Execution
- `owner_module`: `quant_trading.execution.paper` / `.live`
- `description`: empty sibling namespaces only
- `responsibilities`: environment ownership separation
- `non_responsibilities`: executable behavior of every kind
- `input_contracts`: none
- `output_contracts`: none
- `allowed_dependencies`: none
- `forbidden_dependencies`: each other; Market Data; GUI; SQLite; Decision; raw `TradeIntent`; concrete broker SDK
- `required_capabilities`: none
- `side_effects`: none
- `financial_effect`: none
- `safety_level`: Paper boundary safe/inactive; Live boundary safety-critical/inactive
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

None. `ApprovedTradeIntent`, `OrderRequest`, `ExecutionResult`, account/order interfaces and provider contracts remain Planned/Not implemented.

## Conflict assessment

- Result: `COMPATIBLE_EXTENSION`
- Layer conflict: none; both remain inside the existing planned Execution owner.
- Responsibility conflict: none; no behavior is implemented.
- Dependency/cycle conflict: prevented by empty packages and architecture tests.
- Permission/authority conflict: no capabilities are declared or granted.
- Data-contract/units/timezone conflict: not applicable.
- Configuration/default conflict: no configuration changes; Live remains false.
- Runtime/duplicate/idempotency conflict: no runtime path exists.
- Safety/Live/leverage/shorting/risk-limit conflict: no financial semantics or Live activation exists.
- Parallel-component combination rule: one sibling owns Paper, the other Live; neither is active.
- Recommended resolution: preserve strict environment separation in all later proposals.
- User decision required: obtained for boundary creation only; future behavior still requires separate approval.

## Financial, risk, and safety meaning

- Financial meaning: none.
- Risk implications: no path may bypass `RiskApprovedTradeIntent` in future.
- Safety implications: package existence must never imply authority.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No; Live remains disabled.
- Manual confirmation behavior: unchanged and still required.

## Change Impact Report

- Primary module: `quant_trading.execution`
- Secondary modules: architecture/governance documentation and architecture tests
- Public contracts: none
- Configuration: none
- Database: none
- GUI: none
- Tests: structural import/content checks
- Documentation: Compass, architecture, Project State, module/proposal/ADR indexes
- Permissions: none granted
- Trading semantics: none
- Safety behavior: Live and automatic submission remain disabled
- Migration: none
- Rollback: remove empty packages and associated records; no data/config rollback
- Expected blast radius: `MULTI_MODULE` documentation, zero runtime behavior

## Compatibility and migration

Backward compatible; no adapters, data migration, configuration migration or runtime comparison are needed. No output or order can be duplicated because neither package runs.

## Validation and activation

- Unit-test plan: none; no behavior.
- Integration-test plan: none; no flow.
- Architecture-test plan: verify sibling presence, empty implementation and no cross-import.
- Dry-run plan: Not implemented.
- Historical-simulation plan: Not implemented.
- Paper-validation plan: requires a future approved Proposal.
- Manual activation approval: not requested.
- Live approval: Not requested.
- Evidence required for each state transition: future contracts, Risk gate, Fake tests, Paper-only credentials/configuration and explicit approval.

## Rollback and deprecation

Remove the declaration-only package files and references. No feature flag, active configuration, database migration, caller or public contract exists.

## Documentation impact

Record the two boundaries as implemented but empty; keep all execution capabilities Not implemented.

## Approval record

The user explicitly approved creating only the two sibling layers on 2026-07-14 and explicitly deferred all contents.
