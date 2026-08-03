# PROPOSAL-025: P23-1E-A Manual Latest-Session Spectral Preview Runner

## Status and identity

- Proposal ID: `PROPOSAL-025`
- Status: `APPROVED / IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-02
- User approval status: `Approved 2026-08-02; inclusive-window amendment B approved 2026-08-02`
- Proposal-creation approval: `Approved 2026-08-02`
- Implementation approval: `Granted 2026-08-02`
- Author: Codex
- Design baseline: `PROPOSAL-023` planning revision `1.24`
- Existing implementation baseline: `PROPOSAL-024` P23-1A–D, locked and disabled
- Proposed implementation slice: `P23-1E-A`
- Safety classification: `RESEARCH_ONLY / NO_EXECUTION`
- Proposed blast radius: `MULTI_MODULE`, divided into bounded implementation gates

The user approved implementation of this proposal on 2026-08-02, including its four recommended choices and at most one post-test read-only AAPL validation. During the pre-implementation audit the user selected amendment B: retain the existing immutable R1 v1.0.0 definition/history and add a new immutable R1 v1.1.0 definition whose 60/120/250 windows include the latest completed evaluation session. The approval does not grant component activation, Trading API access or any trading behavior.

## Intent interpretation

### User goal

Make the already implemented P23-1 mathematical engine usable for one real, manually requested stock preview. The user should be able to select one stock, intentionally prepare exact evidence, run the locked algorithm, preserve the result and inspect its period, amplitude, MAD, warnings, status and complete Run history.

### Existing verified capability and overlap

PROPOSAL-024 already provides:

- the locked disabled `P23-1 Spectral Volatility Research R1 v1.0.0` definition;
- exact XNYS calendar, explicit symbol mapping, Raw/Split Daily Bar, corporate-action and evidence-mode contracts;
- `SpectralMarketEvidenceBuilder`;
- the pure `SpectralVolatilityEngine`;
- `SpectralVolatilityService.preview(...)`, which creates a `FACTOR_PREVIEW` Run, persists the complete evidence graph and preserves invalid/failed operations;
- central SQLite Schema v14 storage and exact reload;
- a read-only P23-1 Factor inspector with filtering, Open Run and CSV/JSON export; and
- a Market-Data-only Alpaca corporate-action provider.

The missing capability is composition. No current application service prepares all required real evidence for an explicit user request and then calls the existing preview service. The current GUI intentionally has no Run action.

This proposal reuses the existing engine, service, evidence model, v14 tables and inspector. It does not create another spectral formula, result format, Factor owner or database.

### Current-data constraint

At the PROPOSAL-024 checkpoint, the active database contained one locked P23-1 definition and its three windows but zero spectral operations. The local Market History cache contained much broader Raw Daily coverage than Split Daily coverage, and contained no standalone frozen P23-1 calendar or corporate-action snapshots. Therefore a truthful runner cannot assume that selecting a symbol is enough. It must either use a complete exact persisted evidence bundle or perform an explicit read-only evidence acquisition requested by the user. Missing corporate-action evidence must never be silently interpreted as “no corporate actions.”

## Proposed outcome

After implementation and validation, the user could:

1. open the existing P23-1 Factor subtab;
2. enter one stock symbol;
3. see the exact locked R1 v1.1.0 definition, fixed feed, evidence mode and inclusive evaluation-session rule before running;
4. explicitly choose local exact evidence or an intentional read-only Market Data fetch;
5. start one background preview request;
6. receive a visible completed, warning, invalid or failed outcome;
7. inspect the persisted operation and window evidence;
8. open the associated Run; and
9. restart the application and reload the same immutable history.

The proposal does not promise that every symbol can run from the current local cache. Insufficient or inconsistent evidence is a valid, persisted failure.

## Architecture classification

### Ownership

- Primary owner of the new capability: `quant_trading.orchestration`
- Mathematical owner, unchanged: `quant_trading.factors`
- Evidence acquisition and freezing owner: `quant_trading.market_history`
- Durable storage adapter: `quant_trading.persistence`
- Neutral lifecycle and failure history: `quant_trading.run_history`
- GUI/controller/background-worker presentation: `quant_trading.algorithm_control`

The earlier P23-1 implementation correctly used Factors as its primary owner because it introduced mathematics and typed Factor evidence. This proposal introduces no mathematics. Its new responsibility is coordinating existing owners, so Orchestration is the primary owner for this slice.

### Responsibilities

The proposed runner may:

- validate one explicit user request;
- resolve the latest completed XNYS session;
- obtain or reuse exact Raw and Split Daily evidence;
- obtain or reuse exact corporate-action evidence;
- construct an immutable `SpectralMarketEvidenceBundle`;
- call the existing `SpectralVolatilityService` with the exact locked definition;
- expose progress and final references to the GUI; and
- preserve preparation and calculation failures in Run History.

### Non-responsibilities

The runner must not:

- calculate spectral mathematics itself;
- choose a “best” period, window, parameter set or algorithm version;
- rank symbols or compare dates/definitions;
- convert evidence into reversal, cycle or Asset State authority;
- calculate Target Position or cash allocation;
- produce a Decision, TradeIntent or Risk-approved object;
- access an Alpaca account, position, buying-power, order or fill endpoint;
- run automatically, on a timer or in the background without an explicit click;
- enable Paper, Live or order submission; or
- mutate either locked R1 definition or overwrite v1.0.0 history.

No new top-level module is proposed. No dependency-direction change is allowed: GUI depends on a runner port, not concrete Market Data, Factor engine, SQLite or Alpaca classes.

## Component identity declaration

- `component_id`: `orchestration.manual_spectral_preview.p25_ea.v1`
- `component_type`: `ORCHESTRATION`
- `display_name`: `P23-1 Manual Latest-Session Preview Runner`
- `version`: `1.0.0`
- `owner_layer`: `ORCHESTRATION`
- `owner_module`: `quant_trading.orchestration`
- `description`: coordinate one explicit latest-session evidence preparation and the existing locked P23-1 preview
- `responsibilities`: request validation, evidence-preparation coordination, exact Factor-service invocation and outcome correlation
- `non_responsibilities`: mathematics, signal/state/position/cash/Risk/order/execution authority
- `input_contracts`: proposed `ManualSpectralPreviewRequest@1`; existing exact definition and public Market History evidence ports
- `output_contracts`: proposed `ManualSpectralPreviewOutcome@1`; existing `SpectralVolatilityOperation@1` reference and Run ID
- `allowed_dependencies`: public `market_history`, `factors`, `run_history` contracts and injected clock/ID services
- `forbidden_dependencies`: GUI implementation, concrete SQLite, concrete Alpaca provider, Asset State, Target Position, Decision, Risk, Backtesting, Portfolio Accounting and Execution
- `required_capabilities`: read exact locked definition; prepare/reuse bounded research evidence; invoke one `NO_EXECUTION` Factor preview; record Run outcome
- `side_effects`: on explicit request only, may append Market History cache/fetch history, Run History and P23 v14 research evidence through injected owners
- `financial_effect`: none
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

This runner component is separate from the existing locked Factor component only by responsibility, not by mathematical version. It cannot register, activate or replace a Factor definition.

## Recommended exact first-version semantics

The following semantics are the approved implementation baseline:

| Concern | Recommended fixed behavior |
|---|---|
| Request scope | exactly one explicit symbol |
| Definition | new exact locked `P23-1 R1 v1.1.0` ID and version; visibly displayed; v1.0.0 retained unchanged |
| Venue/calendar | explicit U.S. stock/ETF mapping to `US_EQUITIES_REGULAR_V1` / XNYS |
| Feed | `IEX` only in this first slice |
| Timeframe | completed `Daily` only |
| Evaluation session | latest recognized XNYS session whose official close is not later than request time |
| Observation range | exact trailing 250 completed XNYS sessions including and ending on the evaluation session |
| Adjustments | paired `Raw` and `Split`; no dividend price adjustment |
| Evidence mode for newly fetched evidence | visibly fixed `RETROSPECTIVE_ADJUSTED` |
| Missing sessions | fail the affected window visibly; no interpolation, forward fill, skip or nearest-date substitution |
| User action | one deliberate click; no automatic refresh or schedule |
| Result authority | descriptive research evidence only; component stays `DISABLED / NO_EXECUTION` |

`RETROSPECTIVE_ADJUSTED` is required because a newly fetched historical response and corporate-action response may be observed after the evaluation session. Such evidence is useful for current research but cannot prove what was knowable at that historical close and must not be labeled point-in-time or backtest-safe.

The exact 250-session inclusive input supplies all 60/120/250 calculations from one aligned evidence bundle. R1 v1.1.0 changes only this versioned observation-cutoff rule; the Fourier/Welch/MAD/amplitude formulas and approved window shapes remain unchanged. Extra calendar sessions may be generated only to locate the exact trailing range; extra Bars must not silently enter the calculation bundle.

## Proposed acquisition modes

### `LOCAL_ONLY`

- Makes no network request.
- May use only a complete exact persisted P23-1 evidence bundle exposed through a public query contract.
- Does not treat generic cached Bars alone as sufficient when exact frozen corporate-action or provenance evidence is absent.
- Fails visibly when the complete bundle does not exist or does not match symbol, feed, definition and requested session.

### `FETCH_AND_FREEZE_READ_ONLY`

- Runs only after an explicit user click.
- Uses existing Alpaca Market Data credentials and only Historical Stock Data and Corporate Actions APIs.
- Requests paired IEX Raw/Split Daily Bars and corporate actions for the exact bounded range.
- May add valid fetched Bars, Coverage and Fetch History to the existing Market History cache under current cache semantics.
- Freezes the successful exact evidence into the existing P23-1 v14 operation graph.
- Does not use Alpaca Trading clients or account/order endpoints.
- Does not grant standing permission for background refresh, batch requests or later automatic use.

Credentials remain optional. Missing credentials produce a visible failure and do not fall back to fabricated evidence.

## Proposed public contracts

Names are provisional until implementation review, but their semantics must remain explicit and typed.

### `ManualSpectralPreviewRequest@1`

- `operation_id`
- `session_id`
- `request_id`
- `symbol`
- exact `definition_id`
- exact `definition_version`
- `acquisition_mode`
- `feed` fixed to IEX for version 1
- `requested_at_utc`
- `created_by`
- optional user reason/note

The request must not contain arbitrary Factor parameters or a default/latest-definition shortcut.

### `PreparedSpectralPreviewInput@1`

- normalized symbol;
- exact evaluation session and `as_of_utc`;
- exact definition ID/version;
- evidence bundle ID and content fingerprint;
- calendar/mapping/corporate-action snapshot IDs;
- acquisition mode and evidence mode; and
- preparation warnings.

This is an orchestration DTO. It does not duplicate Bars or calculate Factor output.

### `ManualSpectralPreviewOutcome@1`

- request/operation/attempt identifiers;
- Run ID;
- preparation status;
- existing `SpectralVolatilityOperation` reference when calculation started;
- stable error code and user-readable summary; and
- `Open Run` target.

The outcome contains no position, cash, action, Risk approval or order field.

### Compatibility rule

The existing `SpectralVolatilityPreviewCommand@1`, `SpectralMarketEvidenceBundle@1`, `SpectralVolatilityOperation@1`, generic `AlgorithmRun` and v14 storage remain authoritative. If implementation can compose them without changing a public contract, it must do so. Any discovered need to change their financial/data meaning stops implementation for a proposal revision.

All proposed contracts use `schema_version=1`, UUID identities, UTC-aware timestamps and the request's `session_id`/`request_id` correlation. `requested_at_utc` is when the user action is accepted; `created_at_utc` on prepared evidence is when the immutable bundle is assembled; Factor operation timestamps retain their existing service semantics. Market prices remain exact Decimal/string evidence in existing contracts, spectrum values remain existing float/IEEE-754 evidence, and the proposed runner adds no new monetary or position unit. Missing evidence is a typed failure, never zero, empty corporate-action meaning or inferred success. Compatibility is additive while the existing contract meanings remain unchanged.

## Proposed lifecycle

```text
Explicit user click
    ↓
Validate symbol + exact locked definition + acquisition mode
    ↓
Resolve latest completed XNYS session and exact 250 sessions
    ↓
Acquire or reuse Raw/Split Daily + corporate-action evidence
    ↓
Freeze calendar, mapping and evidence bundle
    ↓
Call existing SpectralVolatilityService.preview(...)
    ↓
Persist v14 operation + Factor Preview Run
    ↓
Reload existing P23-1 inspector and enable Open Run/export
```

Only one request may be in progress in the panel at a time. The Run control is disabled while that request is active. A second intentional run creates a new operation and Run; it never overwrites the first.

An identical retry using the same `operation_id` and command fingerprint returns the first operation. Reusing the same ID with different content fails as a conflict. A new user rerun receives a new ID even if the symbol and evidence are identical, preserving a separate audit event.

## Run and failure history

Preparation may fail before the existing Factor service receives a complete bundle. Those failures must still create a searchable `FACTOR_PREVIEW` Run with a failed `MARKET_DATA` stage, stable error code, request/symbol/definition bindings where available and no false Factor result.

Successful preparation continues through the existing `MARKET_DATA → FACTOR` Run path. Implementation must not create two successful top-level Runs for one click. If reuse of the current service lifecycle cannot satisfy that invariant without a public-contract change, implementation stops and this proposal is revised before coding farther.

Required distinguishable failure classes include:

- invalid or unsupported symbol/mapping;
- no completed session;
- credentials unavailable;
- local exact evidence unavailable;
- Raw evidence unavailable;
- Split evidence unavailable;
- corporate-action evidence unavailable or unsupported;
- provider/network failure;
- missing expected session;
- Raw/Split/session/feed misalignment;
- evidence observed too late for a requested point-in-time claim;
- definition/evidence/operation conflict;
- calculation invalid/failed; and
- persistence failure.

Errors must be human-readable in the GUI and structured in Run History. They must not expose secrets, authorization headers or full external payloads.

## Persistence and database impact

- No Schema v15 is proposed.
- No central SQLite migration is proposed.
- Existing v14 tables store successful, warning, invalid and calculation-failed P23-1 operations.
- Existing Run History tables store preparation-stage failures and messages.
- Existing Market History Bar/Coverage/Fetch History tables may receive valid explicitly fetched Raw/Split data under current semantics.
- Historical results are immutable and are never silently replaced by a new fetch or rerun.
- No standalone corporate-action cache, configuration format or retention/deletion policy is introduced.

If implementation proves that the required exact failure or evidence history cannot be represented safely in Schema v14, work must stop. A revised migration proposal and explicit user approval would then be required.

## GUI admission

The existing P23-1 Factor subtab may gain a compact “manual preview” area containing:

- symbol input;
- exact locked component/definition/version display;
- fixed IEX, Daily, XNYS and `RETROSPECTIVE_ADJUSTED` display;
- acquisition-mode selector;
- a clear read-only-network warning for fetch mode;
- one explicit `准备证据并运行` action;
- progress/cancel presentation where safely supported;
- final status, warning/error code and Run ID; and
- existing history reload, details, Open Run and export behavior.

The GUI may validate presentation-level required fields and dispatch a typed request. It must not select sessions, fetch Market Data, build evidence, calculate spectra, access SQLite or branch on mathematical output.

The work stays inside the existing Algorithm Control entry and Factor page. It does not add a new launcher entry or independent window.

## Conflict assessment

- Result: `NEEDS_USER_DECISION` before implementation; `COMPATIBLE_EXTENSION` if all recommended choices are approved unchanged
- Layer conflict: none under the proposed ownership; calculation outside Factors is forbidden
- Responsibility conflict: the runner composes existing owners and does not replace them
- Dependency/cycle conflict: none if Orchestration uses public Market History/Factor/Run ports and GUI uses only the runner port
- Permission/authority conflict: explicit read-only Market Data acquisition requires user approval; Trading API access remains forbidden
- Data-contract/units/timezone conflict: none under existing UTC/XNYS/Daily/Raw+Split contracts; false point-in-time labeling is forbidden
- Configuration/default conflict: no active/default Factor; IEX/R1/latest-session behavior is explicit runner-version metadata
- Runtime/duplicate/idempotency conflict: one successful top-level Run per click and existing operation fingerprint rules are mandatory
- Safety/Live/leverage/shorting/risk-limit conflict: none because there is no financial output or execution capability
- Parallel-component combination rule: results remain separate immutable P23-1 operations and are not automatically combined, ranked or consumed
- Recommended resolution: implement the approved four bounded choices and amendment B through gates P25-A–D sequentially
- User decision required: resolved 2026-08-02 for this scope; any broader mode, schema, consumer or activation still requires separate approval

### Existing owner conflicts

- Reimplementing spectral calculations in Orchestration or GUI would conflict with Factors and is forbidden.
- Fetching Alpaca data directly from GUI would conflict with Market History and is forbidden.
- Treating generic cached Bars as complete corporate-action evidence would conflict with the approved provenance rules and is forbidden.
- Creating a second P23 result database would conflict with central Persistence and is forbidden.
- Turning a period/amplitude result into State, Target Position, Decision or Risk output would exceed this proposal and is forbidden.

### Authority boundaries

- Market Data permission does not imply account, order or execution permission.
- A completed preview does not activate the Factor.
- `Open Run`, export or rerun does not authorize trading.
- The `ALPACA_PAPER` environment label does not make this an execution capability.

No current component must be replaced or superseded. The smallest compatible path is to compose the existing public P23-1 contracts and add only the missing evidence-preparation/runner boundary.

## Financial, risk, and safety meaning

- Financial meaning: descriptive historical price-rhythm and robust residual-volatility evidence only
- Risk implications: none; it does not evaluate, approve, reduce or reject a TradeIntent
- Safety implications: explicit/manual/fail-closed evidence acquisition; truthful retrospective label; immutable audit history
- Can it create exposure? No
- Can it approve/reduce/reject risk? No
- Can it build/submit an order? No
- Does it affect Live eligibility? No
- Manual confirmation behavior: the user must explicitly trigger each preview; that click authorizes only the selected research evidence request, not trading

## Change Impact Report

| Area | Proposed impact |
|---|---|
| Primary module | `orchestration`: manual preview coordination contract/service |
| Secondary modules | `market_history`, `factors`, `persistence`, `run_history`, `algorithm_control` |
| Public contracts | small typed request/outcome and evidence-preparation/query ports; existing P23 contracts preserved |
| Configuration | no new financial/default parameter; IEX/R1/latest-session semantics are fixed and visible for this version |
| Database | Schema v14 unchanged; existing Market History and P23/Run tables only |
| GUI | one manual-run area in the existing P23-1 Factor subtab |
| Tests | unit, repository/query, integration, GUI controller/worker and architecture/governance |
| Documentation | proposal, Compass, Roadmap, Project State; implementation would later update affected module docs and Edit Log |
| Permissions | optional explicit per-click read-only Alpaca Market Data acquisition; no Trading API |
| Trading semantics | none; no signal, position, action or approval |
| Safety behavior | disabled, manual, fail closed, no automatic network or execution |
| Migration | none proposed |
| Rollback | remove composition/run controls while retaining immutable prior Runs/results |
| Blast radius | `MULTI_MODULE`, bounded by sequential gates |

## Proposed implementation gates

Implementation was approved on 2026-08-02 and proceeds sequentially. A failed gate stops later gates.

### Gate P25-A: contracts and evidence preparation

- Add typed runner request/outcome and acquisition-mode contracts.
- Add a Market History-owned preparation service over public store/provider/calendar/corporate-action ports.
- Add exact latest-completed-session and trailing-250-session validation.
- Add local-only and explicit read-only-fetch fixture tests.
- Keep all runtime composition disabled and GUI unchanged.

Acceptance: exact evidence can be prepared from deterministic fakes; missing/misaligned evidence fails visibly; no Factor calculation, SQLite implementation or GUI logic leaks into Market History.

### Gate P25-B: orchestration and Run history

- Add a runner service that prepares evidence and invokes the existing Factor service.
- Preserve one successful top-level Run per click.
- Persist preparation-stage failure Runs without fabricating a Factor operation.
- Compose the locked definition explicitly; never select latest/active implicitly.

Acceptance: fake-provider end-to-end operation reloads exactly from Schema v14; failure Runs reload with stable codes; idempotency and conflicts are deterministic.

### Gate P25-C: GUI and disabled composition

- Add the manual preview controls and background worker/controller.
- Display all fixed semantics and network boundary before dispatch.
- Reload/select the persisted result and support existing Open Run/export.
- Keep the component disabled and unconsumed.

Acceptance: GUI controller tests cover success, warning, failure, duplicate-click suppression and restart reload; architecture tests prove no provider/engine/SQL logic exists in widgets.

### Gate P25-D: bounded real validation

Only after A–C fixture, integration, architecture and migration-contract tests pass, perform at most one user-authorized read-only AAPL IEX preview through the actual GUI/service composition. Record exact request dimensions, returned counts, Run ID, evidence mode and absence of Trading API access. Do not print or persist credentials.

Acceptance: one operation is reloadable after restart, its Run chain opens, database integrity/foreign-key checks remain clean and no account/order endpoint was accessed.

## Validation plan

At minimum:

- latest completed session tests for ordinary days, pre-close requests, weekends, holidays and early closes;
- exact 250-session range and 60/120/250 window containment;
- Raw/Split/feed/session alignment and known-gap failures;
- local-only complete, incomplete and absent evidence;
- fetch mode with available/missing credentials and provider failures;
- corporate-action empty-response, supported-event and unsupported-event evidence;
- retrospective label and rejection of a false point-in-time claim;
- request validation, idempotent retry and same-ID conflict;
- successful/warning/invalid/failed Run reload;
- v14 repository regression with no migration;
- one-successful-Run-per-click invariant;
- GUI worker success/failure/duplicate-click/close behavior;
- Factor/Market History/Orchestration/GUI dependency architecture tests;
- complete targeted integration; and
- architecture/governance suite plus `git diff --check`.

Ordinary automated tests must use deterministic fakes and must not depend on credentials or network access.

## Compatibility, migration and rollback

The proposal is additive. Existing read-only history, exports, engine calculations, generic Factor contracts, Market History browser and all Phase 1–6E research behavior remain unchanged.

No historical row is rewritten. No database downgrade is needed because no schema change is proposed. Runtime rollback removes or disables the new coordinator composition and manual Run controls; already persisted Runs and P23 operations remain valid evidence readable by the existing inspector.

If the fixed IEX/latest-session/retrospective semantics need to change later, create a new versioned request/runner policy. Do not silently reinterpret prior operations.

## Explicit exclusions

This proposal does not include:

- full P23-1E historical multi-date or multi-version comparison;
- scoring, ranking, parameter optimization or automatic winner selection;
- wavelet research;
- MAD/reversal multiplier selection;
- automatic cycle/state transitions or confirmation rules;
- target-position curves, position values or cash allocation;
- Decision, TradeIntent, Risk approval or numerical Risk changes;
- Backtesting integration;
- Portfolio Accounting persistence;
- broker account, buying power, positions, orders or fills;
- Paper or Live execution;
- automatic/scheduled refresh;
- batch-symbol runs;
- a new database schema; or
- component activation.

## Approval record and required user decisions

Recorded decision:

- 2026-08-02: user approved creation of PROPOSAL-025 only.
- 2026-08-02: user approved PROPOSAL-025 implementation and its four recommended choices.
- 2026-08-02: after the pre-implementation conflict was explained, user selected amendment B. R1 v1.0.0 remains immutable and uses its prior-session cutoff; new R1 v1.1.0 includes the latest completed evaluation session in each trailing window. No spectral formula or trading authority changes.

The following approved choices govern implementation:

1. Use the smaller single-symbol/latest-completed-session/manual-only P23-1E-A slice, leaving full historical comparison/scoring for a later proposal.
2. Allow `FETCH_AND_FREEZE_READ_ONLY` only after an explicit click, using existing Alpaca Historical Stock Data and Corporate Actions credentials, while keeping `LOCAL_ONLY` available and forbidding automatic/background network access.
3. Fix version 1 of the runner to IEX, exact locked R1 v1.1.0, exact inclusive trailing 250 XNYS sessions and visible `RETROSPECTIVE_ADJUSTED` semantics, using existing Schema v14 with no migration.
4. After all deterministic tests pass, allow at most one bounded read-only AAPL validation through the completed composition; this would be a separate validation action, not standing network or trading authority.

All four choices and amendment B are approved. This record grants no authority beyond the stated implementation and bounded read-only validation.

## Implementation result

PROPOSAL-025 is implemented and verified as the bounded `P23-1E-A` manual runner. The earlier immutable R1 v1.0.0 definition and results retain their prior-session cutoff. A new immutable R1 v1.1.0 definition includes the latest completed evaluation session in each exact 60/120/250-session window; no Fourier, Welch, MAD, amplitude, dominance or cross-window formula changed.

The implemented path is:

```text
explicit user click
→ Orchestration manual-preview coordinator
→ Market History exact-evidence preparation
→ complete local frozen bundle, or one explicit read-only fetch-and-freeze
→ existing Factor preview service and one top-level FACTOR_PREVIEW Run
→ existing Schema v14 immutable operation/result graph
→ existing Factor-page inspector and Open Run
```

Evidence preparation fixes IEX, Daily, Raw plus Split, `US_EQUITIES_REGULAR_V1`, `RETROSPECTIVE_ADJUSTED`, the latest completed XNYS session and the exact inclusive trailing 250 sessions. `LOCAL_ONLY` fails if the exact frozen bundle is absent or incomplete. `FETCH_AND_FREEZE_READ_ONLY` is initiated only by the explicit button and uses Alpaca Historical Stock Data and Corporate Actions; it never constructs or calls a Trading client. Preparation/definition failures still create searchable failed Runs with a failed `MARKET_DATA` stage. Successful retrospective Runs preserve the explicit `RETROSPECTIVE_ADJUSTED` warning.

No Schema v15 or database migration was required. Schema remains v14 with 94 required logical tables. The Algorithm Control GUI reuses the existing P23-1 Factor subtab, runs work in a background worker, rejects duplicate clicks, reloads the persisted result and opens the owning Run. No new Launcher entry or standalone window was created.

Deterministic verification completed on 2026-08-02: the full suite passed **547 tests** with one pre-existing upstream WebSocket warning; compilation and database integrity checks passed. The one approved real validation used AAPL only and completed with warnings under Run `97448eba-e403-4be9-96a9-5c6cf8b52695`, operation `5380fd0e-51c4-418f-ae8e-50a7ab42ba8e`, R1 v1.1.0, as-of `2026-07-31T20:00:00Z`, 250 exact observations and valid 60/120/250 windows. A fresh process reloaded the exact operation and Run. The window candidates were approximately 20, 40 and 83.33 sessions, but cross-window consensus was `insufficient_qualified_windows`; this is descriptive research evidence and generated no State, Target Position, Decision, Risk approval, order or trade.

Three implementation defects were confirmed and fixed with regression coverage: `BUG-20260802-001`, `BUG-20260802-002` and `BUG-20260802-003`. The component remains locked/disabled, `execution_allowed=false`, `live_allowed=false`. Full historical comparison/scoring and every exclusion above remain unimplemented and require separate approval.
