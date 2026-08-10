# ADR-0032: Keep the First Daily Volatility Profile Robust, Complete and Non-Trading

- Status: Accepted
- Date: 2026-08-06
- Decision owner: User
- Related: `PROPOSAL-027`, `INTENT-037`, `DEC-014`, ADR-0029–0031

## Context

P23-1 and P26 preserve exact per-date R1 evidence, but no durable contract summarized what is normal daily movement for one stock. The validated AAPL spectral spans describe multi-session oscillation and did not establish qualified cross-window support, so blending those spans into a daily scale would add unsupported financial meaning. A later reversal/state/trading design needs a stable versioned input without silently choosing a latest study, tolerating missing dates or using the current evaluation close.

## Options considered

1. Use one R1 window or a spectral amplitude directly.
2. Blend trend MAD and spectral amplitude into one score.
3. Use the complete explicit P26 study, exact prior-session R1 v1.0.0 trend-standardized MAD, median across 60/120/250 windows per date and median across dates; retain spectral fields as secondary evidence only.
4. Defer every aggregation and keep Phase 5B scale entirely manual.

## Decision

Accept option 3 as locked component `factor.daily_volatility_profile.p23_1f.v1@1.0.0`:

- exactly one explicitly selected immutable P26 study with 20–250 complete sessions;
- exactly R1 v1.0.0 and valid W60/W120/W250 evidence for every session;
- `m[t] = median(s[t,60], s[t,120], s[t,250])` and `profile_log_scale = median(m[t])`;
- temporal raw MAD and `1.4826` standardized MAD as descriptive stability evidence;
- `exp(k)-1` and `1-exp(-k)` as explanatory one-scale price fractions only;
- zero scale is stored as `ZERO_PROFILE_SCALE` with `usable_as_positive_scale=false`; no floor is invented;
- spectral period/amplitude/status is preserved as `SECONDARY_ONLY` and never enters the controlling scale;
- exact definition/study/point/source-operation/IEEE evidence, immutable attempts/results and `VOLATILITY_PROFILE_RESEARCH` Runs persist in additive central Schema v16;
- the existing Factor page owns the read-only inspector; no launcher entry or new top-level module is added.

The implementation remains `DISABLED / NO_EXECUTION`, `execution_allowed=false`, `live_allowed=false`, and has no automatic consumer.

## Rationale

Medians limit sensitivity to one window or date without inventing weights. Prior-session R1 preserves the no-current-session source boundary. Complete-study admission makes the denominator explicit and reproducible. Keeping spectral evidence separate respects the observed lack of qualified AAPL cross-window support and leaves later reversal mathematics as an independent user decision.

## Consequences

Central SQLite advances from v15/99 to v16/104 with five additive tables and zero backfill. Identical source evidence reuses one deterministic immutable result while each request retains a separate attempt and Run. The Run History Explorer links the profile Run to its P26 parent and all contributing child Runs. Missing, reordered, incompatible or tampered sources fail closed and durable failures remain searchable.

Local AAPL validation reused study `3411fd6d-ee64-5e44-bd26-3f25068dce52` without network access and produced result `6ae54c4a-8d3b-5ae1-8c82-4bb2fb5bbef5`; fresh-process reload preserved `profile_log_scale=0.013404769735102143` / `0x1.b73f5bcfb3ca8p-7`. This is evidence of the implementation, not a reversal threshold, prediction or trading approval.

## Reversal

Operational rollback hides/disables the P23-1F registration and GUI while retaining immutable Schema v16 Runs/results for audit. Schema rollback requires stopping writers and restoring the verified pre-migration v15 backup with matching v15 code; code rollback alone is not a database downgrade. Any formula, partial-grid rule, amplitude blend or consumer requires a new version/proposal and may not overwrite v1 evidence.
