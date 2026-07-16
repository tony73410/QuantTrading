# PROPOSAL-005: Portfolio Accounting Layer and Trading Ledger

## Status and identity

- Proposal ID: `PROPOSAL-005`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-15
- Author: Codex implementing an explicit user request
- User approval status: Approved in the 2026-07-15 task prompt
- Related ADR: ADR-0012

## Intent interpretation

Create one Portfolio Accounting domain with separate Trading Ledger and Accounting responsibilities, typed public contracts, in-memory scaffolding, reconciliation/query boundaries, tests, documentation, and a read-only existing-GUI tab. Do not implement broker synchronization, execution, full financial conventions, tax, margin, or Live behavior.

## Architecture classification

- Owning layer/module: Portfolio / `quant_trading.portfolio_accounting`
- Responsibilities: append immutable facts; derive local state; report reconciliation differences; provide read-only snapshots.
- Non-responsibilities: signals, Decision, Risk approval, orders, execution, broker clients, GUI business logic, financial-convention invention.
- Existing overlap: trace-only Decision/Risk snapshots remain unchanged; new contracts are additive and require a future explicit adapter for runtime Risk evaluation.

## Component identity declaration

- component_id: `portfolio.accounting.scaffold.v1`
- owner_layer/module: Portfolio / `quant_trading.portfolio_accounting`
- input/output: version-1 typed Ledger facts → immutable accounting/reconciliation/query read models
- allowed dependencies: stdlib and its own public contracts
- forbidden dependencies: concrete broker, Execution, GUI, SQL, Alpaca, Factor/Decision implementation
- side effects: in-memory append only
- default_enabled: false
- execution_allowed: false
- live_allowed: false
- initial_state: DISABLED architecture scaffold

## Conflict assessment

- Result: `COMPATIBLE_EXTENSION`
- No owner/cycle/permission/safety conflict. Same-named trace envelopes are not replaced. No configuration, database, runtime output, broker event, or order path exists.

## Financial, risk, and safety meaning

Only confirmed fills and explicit signed cash facts affect the minimal replay. Unfilled/rejected orders do not. Shorting and all advanced accounting conventions fail closed or remain uncalculated. Risk reads snapshots only. Live and automatic submission remain disabled.

## Change Impact Report

- Primary: Portfolio Accounting
- Secondary: Risk public read boundary; Algorithm Control read-only GUI; governance/docs/tests
- Public contracts: additive version-1 models/Protocols
- Configuration/database/migration: none
- Permissions: none added
- Trading semantics: explicit order-versus-fill distinction only; no order authority
- Rollback: remove additive files/references; no data migration
- Expected blast radius: `MULTI_MODULE`

## Validation and activation

Unit tests cover append/idempotency/correction/Decimal/replay and reconciliation. Architecture tests protect Ledger, Accounting, GUI, Risk, and Execution boundaries. No Dry Run, Paper validation, activation, or Live approval is requested or granted.
