# Algorithm Control Center GUI

## Purpose

Provide a separate PySide6 management application for registered Factor, Trading Decision, and Risk components. It exposes restricted Factor-definition authoring, exact Decision Factor-version selection, metadata, versioned configuration, dependency validation, safe previews, and an audit trail without evaluating Factors or owning Decision/Risk/order behavior.

## Responsibilities

- Validate component identity, ownership, public contracts and layer capabilities at registration.
- Separate implementation from activation through `REGISTERED`, preview, dry-run, Paper, Active, paused/failed and deprecated states.
- Run fail-closed Pipeline admission before a dry run and present conflicts in the Conflict Center.

- Discover components through `AlgorithmComponentRegistry` and `ComponentMetadata`.
- Generate parameter editors from typed `ParameterSchema` definitions.
- Keep Draft, Saved, and Active configuration states distinct.
- Preserve immutable configuration history; restore creates a new version.
- Validate fields, types, ranges, dependencies, and locked safety invariants.
- Run previews on a background Qt worker and label every result **NO EXECUTION**.
- Display append-only configuration and preview audit records.
- Create immutable restricted-expression Factor definitions and register every version disabled by default.
- Persist exact selected Factor component IDs in versioned Decision configuration.

## Non-responsibilities

- Arbitrary Python/source execution, Factor value calculation, strategy or decision rules.
- Numerical risk limits or risk-policy selection.
- Market-data downloads, SQLite history queries, account access, order construction, or execution.
- Paper or Live order submission and secret storage.

## Public interfaces

`AlgorithmComponentRegistry`, `ComponentMetadata`, `DataContractDeclaration`, `ChangeAdmissionService`, `ConflictAssessment`, `PipelineAdmissionResult`, `FeatureState`, `Capability`, `ParameterSchema`, `ConfigurationRecord`, `PreviewRequest`, `PreviewResult`, `ConfigurationService`, `ConfigurationValidator`, `PreviewService`, `AlgorithmControlController`, `build_controller()`, and `AlgorithmControlPanel`.

## Inputs

Registered metadata, restricted Factor definitions, user configuration edits/Factor selections/reasons, and safe preview requests. User-authored Factors may be registered but remain disabled; no production Decision or numerical Risk implementation is registered.

## Outputs

Versioned configuration, validation, audit, and non-executing preview results. A preview is never an order or execution authorization.

## Dependencies

May depend on public Factor/Decision/Risk result contracts, application safety settings, Python standard library, and PySide6. It must not depend on Alpaca clients, market-history SQLite implementation, or broker/execution providers.

## Side effects

Persists state atomically at `runtime/algorithm_control/control_state.json` and definitions at `runtime/algorithm_control/factor_definitions.json`. These ignored files are separate from `runtime/data/market_history.sqlite3` and contain no credentials.

## Failure modes

- Wrong ownership, excess permission, unknown contract or Live authority: component is `INVALID`, is not registered, and cannot run.
- Multiple Primary Decision/Execution components, missing production stages or disabled safety: Pipeline `BLOCKED` with a Conflict ID.

- Invalid/duplicate metadata: registration error.
- Invalid Draft or dependency: activation blocked with validation issues.
- Persistence failure: `QT-ALG-STORAGE-001`.
- Preview failure: `QT-ALG-PREVIEW-001`; no execution occurs.
- No production algorithm: shown honestly as Not implemented.

## Configuration

Generic schemas support integer, decimal, boolean, string, enum, date, percentage, money, duration, and list values. This module selects no financial values. New non-system components default to `REGISTERED`/disabled with no execution or Live authority and require validation evidence to advance. Four real safety invariants initialize active and locked: Risk review required, Risk cannot increase exposure, Live disabled, and automatic submission disabled.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/algorithm_control tests/architecture/test_algorithm_control_boundaries.py
```

Tests use temporary state and Fake preview executors; they access no network or order endpoint.

## Start

```powershell
.\.venv\Scripts\python.exe -m quant_trading.algorithm_control
```

## Known limitations

- The Conflict Center is read-only; it does not automatically resolve high-risk conflicts or approve proposals.
- Proposal authoring remains file-based under `docs/proposals/`; the GUI displays admission conflicts but is not an arbitrary Python/source-code editor or approval authority.

- No Factor is active automatically and no production Decision or numerical Risk implementation is registered.
- Expression validation does not fetch Market Data; real calculation preview remains Not implemented.
- Production previews report Not implemented; Pipeline Dry Run is disabled until compatible approved components exist.
- No execution, account connection, order construction, or order submission exists.
