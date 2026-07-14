# PROPOSAL-NNN: Title

## Status and identity

- Proposal ID: `PROPOSAL-NNN`
- Status: `DRAFT`
- Date:
- Author:
- User approval status: `Not requested / Pending / Approved / Rejected`
- Related ADR / Intent / Edit Log:

## Intent interpretation

### User request

### Underlying user goal

### User-suggested method

### Professional interpretation

### Recommendation

## Architecture classification

- Owning layer:
- Owning module:
- Why this belongs in the system:
- Why no existing component can own it unchanged:
- Responsibilities:
- Explicit non-responsibilities:
- Existing components affected:

## Component identity declaration

- `component_id`:
- `component_type`:
- `display_name`:
- `version`:
- `owner_layer`:
- `owner_module`:
- `description`:
- `responsibilities`:
- `non_responsibilities`:
- `input_contracts`:
- `output_contracts`:
- `allowed_dependencies`:
- `forbidden_dependencies`:
- `required_capabilities`:
- `side_effects`:
- `financial_effect`:
- `safety_level`:
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `REGISTERED / DISABLED`

## Public contracts

For every input/output include contract ID, `schema_version`, producer, consumers, `created_at_utc` semantics, source component/version, correlation ID, units, timezone, missing-value meaning, and compatibility result.

## Conflict assessment

- Result: `NO_CONFLICT / COMPATIBLE_EXTENSION / REQUIRES_ADAPTER / REQUIRES_MIGRATION / REQUIRES_REPLACEMENT / ARCHITECTURE_CONFLICT / PERMISSION_CONFLICT / SAFETY_CONFLICT / NEEDS_USER_DECISION`
- Layer conflict:
- Responsibility conflict:
- Dependency/cycle conflict:
- Permission/authority conflict:
- Data-contract/units/timezone conflict:
- Configuration/default conflict:
- Runtime/duplicate/idempotency conflict:
- Safety/Live/leverage/shorting/risk-limit conflict:
- Parallel-component combination rule:
- Recommended resolution:
- User decision required:

## Financial, risk, and safety meaning

- Financial meaning:
- Risk implications:
- Safety implications:
- Can it create exposure?
- Can it approve/reduce/reject risk?
- Can it build/submit an order?
- Does it affect Live eligibility?
- Manual confirmation behavior:

## Change Impact Report

- Primary module:
- Secondary modules:
- Public contracts:
- Configuration:
- Database:
- GUI:
- Tests:
- Documentation:
- Permissions:
- Trading semantics:
- Safety behavior:
- Migration:
- Rollback:
- Expected blast radius: `LOCAL / LIMITED / MULTI_MODULE / SYSTEM_WIDE`

## Compatibility and migration

- Backward compatibility:
- Adapters required:
- Data/configuration migration:
- Old/new comparison method:
- Prevention of duplicate runtime outputs/orders:

## Validation and activation

- Unit-test plan:
- Integration-test plan:
- Architecture-test plan:
- Dry-run plan:
- Historical-simulation plan:
- Paper-validation plan:
- Manual activation approval:
- Live approval: `Not requested` by default
- Evidence required for each state transition:

## Rollback and deprecation

- Disable feature flag:
- Restore previous active configuration:
- Restore previous component version:
- Restore contract adapter:
- Reverse database migration:
- Deprecation replacement:
- Remaining callers/configurations:
- Removal conditions:

## Documentation impact

## Approval record

Do not mark this proposal `APPROVED` or activate the component unless the user explicitly approved the recorded behavior and the approval evidence is linked here.
