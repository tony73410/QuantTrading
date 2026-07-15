# Safe Factor Authoring

## Status

Implemented and verified as a disabled-by-default authoring capability. No authored Factor is enabled automatically and no production Decision policy exists.

## Purpose

Let the user define and revise a single-asset Factor through the Algorithm Control GUI without executing arbitrary Python code. Every save creates an immutable version that can later be selected by an explicitly implemented Decision component.

## Responsibilities

- Validate Factor identity, description, minimum observations, unit, numeric parameters and missing-input policy.
- Accept only a restricted expression language.
- Save immutable definition history at `runtime/algorithm_control/factor_definitions.json`.
- Register each version as `user_factor.<factor-id>.v<version>`, disabled by default.
- Let Decision configuration select exact Factor component versions.

## Non-responsibilities

No source-code execution, API/SQL/file access, Market Data loading, Decision rule, Risk rule, order, account or broker behavior. Saving or selecting does not activate a Factor.

## Public interfaces

`FactorDefinition`, `FactorDefinitionParameter`, `FactorDefinitionStore`, `SafeExpressionFactorCalculator`, `parse_and_validate_expression`, `FactorDefinitionService`, and `JsonFactorDefinitionStore`.

## Expression language

- Market fields: `open`, `high`, `low`, `close`, `volume`, `vwap`, `trade_count`.
- Functions: `latest`, `lag`, `mean`, `sum`, `minimum`, `maximum`, `absolute`.
- Operators: `+`, `-`, `*`, `/`, unary `+`/`-`.
- Example syntax only: `latest("close") / mean("close", window)`. This is syntax documentation, not an approved trading Factor or investment recommendation.
- Imports, attributes, comprehensions, indexing, assignment, loops and arbitrary function calls are rejected before save.

## Inputs and outputs

The calculator consumes existing `MarketDataWindow` and `FactorContext` contracts and returns `FactorResult`. Insufficient or missing data returns an explicit non-valid status with `value=None`; zero is never fabricated.

## Dependencies and side effects

Factor evaluation depends only on public Factor/Market models and standard library parsing/Decimal arithmetic. The management service depends only on public Factor definition/language contracts and the Algorithm Component Registry. Saving writes one ignored JSON file atomically; calculation itself has no persistence or external side effect.

## Configuration and versioning

Definitions and Decision selections are versioned independently. Editing an old definition creates a new version and component ID. A Decision selection references the exact selected IDs so later Factor edits do not silently change it.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/factors/test_safe_expression_factor.py tests/unit/algorithm_control/test_factor_definition_authoring.py tests/unit/algorithm_control/test_configuration_service.py tests/unit/algorithm_control/test_parameter_editor.py
```

Tests are offline and submit no orders.

## Known limitations

- The GUI validates expression structure but does not fetch Market Data or run a real calculation preview.
- No production Decision component is currently registered, so Factor selection appears only when such a component exists.
- Market History-to-Factor Bar availability semantics remain unresolved; authored Factors are not automatically run against cached history.
- The single supported missing-input policy is `return_missing_status`.
