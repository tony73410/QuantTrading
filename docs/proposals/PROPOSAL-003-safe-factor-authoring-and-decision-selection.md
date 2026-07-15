# PROPOSAL-003: Safe Factor Authoring and Decision Factor Selection

## Proposal metadata

- **Status:** IMPLEMENTED_DISABLED
- **Date:** 2026-07-14
- **User approval:** Approved Scheme A on 2026-07-14
- **Owning layer:** Factor; Algorithm Control is the management surface
- **Owning modules:** `quant_trading.factors`, `quant_trading.algorithm_control`
- **Blast radius:** MULTI_MODULE
- **Conflict assessment:** COMPATIBLE_EXTENSION

## User request and goal

The user wants to create, modify and save Factor calculation behavior in the GUI, then choose in the Decision GUI which Factors are inputs. The underlying goal is editable, understandable algorithm building without editing repository source files for every Factor.

The user described editing “logic/code.” Scheme A professionally interprets that as a small numeric expression language, not unrestricted Python source. This preserves the requested calculation control while preventing arbitrary file, network, credential, process or order access.

## Responsibilities

- Create immutable, versioned Factor definitions with explicit parameters, minimum observations, units and missing-input behavior.
- Validate and calculate definitions inside the Factor layer using a restricted expression language.
- Register every saved version as a distinct, disabled Factor component.
- Let a Decision configuration reference exact registered Factor component versions.
- Persist Factor definitions and Decision selections locally with append/version semantics.

## Explicit non-responsibilities

- No arbitrary Python execution, imports, file access, network access, SQL, GUI scripting or broker access.
- No built-in production formula, investment meaning, Decision policy, threshold, position rule, Risk value or order behavior.
- Saving or selecting a Factor does not enable it, run a Pipeline or grant Paper/Live authority.

## Contracts and dependencies

- Inputs: `MarketDataWindow`, `FactorContext`, immutable `FactorDefinition`.
- Outputs: existing `FactorResult`/`FactorSnapshot` contracts.
- Decision selection stores version-specific Factor component IDs in versioned control configuration.
- Algorithm Control may depend on the public Factor definition and expression-language validation contracts, never the concrete calculator internals.
- Factor calculation remains forbidden from importing Decision, Risk, Execution, GUI, Alpaca or SQLite.

## Capabilities and safety

- Required: `READ_STANDARDIZED_MARKET_DATA`, `CALCULATE_FACTORS`, draft configuration editing.
- Forbidden: trade-intent creation, Risk approval, Paper/Live submission and active-configuration mutation without the existing lifecycle.
- New definitions use `REGISTERED`, `enabled=false`, `execution_allowed=false`, `live_allowed=false`.

## Compatibility, migration and persistence

Existing algorithm-control JSON remains schema-compatible: older configurations load with an empty Factor selection. Definitions use a separate ignored file at `runtime/algorithm_control/factor_definitions.json`; exact Factor calculation results, when explicitly run in a future approved Pipeline, remain owned by the central SQLite Factor-history Store.

No database migration or third-party dependency is required.

## Testing and dry-run plan

- Reject Python imports, attributes, comprehensions, subscripts, unknown functions/fields and malformed calls.
- Verify deterministic Decimal calculation and explicit insufficient/missing statuses.
- Verify immutable version history, atomic persistence, restart restoration and disabled registration.
- Verify versioned Decision selection, validation and GUI visibility.
- Keep production Pipeline dry run blocked until approved Decision and Risk implementations exist.

## Rollback

Stop exposing the authoring tab and Decision selector, stop registering stored definitions, and retain the ignored definition JSON for recovery. Existing control configurations remain readable because the selection field is optional on load. No market database or Git-history operation is needed.
