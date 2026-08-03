# PROPOSAL-023: Versioned Volatility-Aware Piecewise Cycle and Target-Position Plan

## Status and identity

- Proposal ID: `PROPOSAL-023`
- Status: `PROPOSED`
- Planning status: `DESIGN_TARGET_APPROVED`
- Implementation admission status: `BLOCKED_PENDING_SEPARATE_APPROVAL`
- Planning revision: `1.24`
- Recommended resolution package: `P23-1-R1`, `USER_APPROVED_DESIGN_BASELINE`
- Date: 2026-07-27
- Last amended: 2026-07-31
- Author: Codex
- User approval status: The user approved the recorded design direction through planning revision 1.24 and the complete `P23-1-R1` baseline, then explicitly approved `PROPOSAL-024`, the recommended explicit `US_EQUITIES_REGULAR_V1` mapping and one read-only Alpaca validation. P23-1A–D are implemented and verified disabled; P23-1E and P23-2–P23-5 remain unapproved.
- Related ADR / Intent / Edit Log: PROPOSAL-013 through PROPOSAL-024; ADR-0029; `INTENT-034`; `EDIT-20260727-001` through `EDIT-20260731-002`

This proposal records a future development target. It does not authorize source-code changes, public-contract changes, configuration, a database migration, a GUI, Backtesting integration, Paper/Live behavior, order construction or runtime activation.

### Revision history

- `1.0-plan`: recorded two completed trading-day confirmation but described the new cycle as beginning at the second confirmation close.
- `1.1-plan`: supersedes that timing description after the user's explicit clarification. The new cycle becomes operational on the next trading day (day 3), while its mathematical movement reference is the prior-cycle reversal extreme. Confirmation-day observations are held provisionally and attributed to the new cycle's accelerating progress only if confirmation succeeds. This amendment does not rewrite any runtime result because no implementation exists.
- `1.2-plan`: records the user's approval to research rolling Fourier/Welch frequency analysis as a versioned Factor for per-stock rhythm, amplitude and residual-volatility evidence. Spectral evidence cannot directly switch a cycle or create a trade, must use only trailing completed observations, must report no stable cycle when evidence is weak, and must be compared against a non-spectral baseline and a later wavelet candidate. Exact formulas, windows, thresholds and implementation remain unapproved.
- `1.3-plan`: records the user's approved initial research semantics: completed daily closes transformed to log scale; a trailing straight-line trend removed before spectral analysis; daily log returns used for residual variation; separate 60/120/250-trading-day windows; eligible periods from 4 days through one third of the window; support from at least two windows within 20%; weak/candidate/strong dominance boundaries at 15% and 30%; MAD residual scale; and a normal-range direction combining periodic amplitude with a residual-MAD buffer. The exact implementations identified below remain open and no runtime implementation is admitted.
- `1.4-plan`: records both spectral half-amplitude (trend center to peak/trough) and full peak-to-trough amplitude as separate visible evidence, and both raw MAD and a standardized MAD representation as separate visible residual evidence. The Factor does not choose which amplitude or MAD representation controls a later state/reversal rule, and this revision does not select a MAD buffer or reversal-threshold multiplier. The exact spectral-amplitude normalization and standardized-MAD transformation remain open for explicit approval.
- `1.5-plan`: records a separate unweighted ordinary least-squares straight-line trend fit for each 60/120/250-observation window. Each fit uses only completed trailing log closes, minimizes the sum of squared vertical residuals and preserves its coefficients, fitted values and point-by-point residuals. The exact horizontal time coordinate/origin remains open, so this revision does not silently choose trading-observation index versus elapsed calendar time.
- `1.6-plan`: sets the horizontal coordinate within each valid window to chronological trading-observation index `x_i = 0, 1, ..., n-1`. Weekends and recognized exchange-closure dates consume no index position; exact source session/date/Bar identities remain preserved. The treatment of an expected trading session whose Bar is genuinely missing remains open and must not be silently treated as a weekend/holiday or silently compressed.
- `1.7-plan`: when an approved session calendar says a trading session was expected but its required Bar is absent, only each window containing that gap produces a durable data-incomplete result. The window does not interpolate, invent, forward-fill or skip/compress the gap into a valid calculation; unaffected complete windows may still calculate independently. After source repair, recalculation creates a new Run/result and never overwrites the original failure. Data incompleteness is distinct from valid data with no stable spectral cycle.
- `1.8-plan`: requires a formal versioned U.S. exchange calendar rather than a Monday-through-Friday heuristic. The calendar evidence identifies regular sessions, holidays, temporary closures and early closes; every Run binds the exact calendar definition/version used. The exact library/data source, supported venue set, symbol-to-venue mapping and calendar-update/freeze policy remain open, and this planning approval does not authorize a new dependency.
- `1.9-plan`: the first P23-1 spectral candidate calculates from split-adjusted Daily close so a mechanical split is not misread as a market crash, while preserving the exact raw close, adjusted close and split-adjustment/event/source metadata. Dividend adjustment is excluded from this first candidate. Exact split-event source, point-in-time/as-of availability, revision-freeze policy and non-split corporate-action behavior remain open; no existing stored Bar is rewritten.
- `1.10-plan`: fixes the residual-scale calculation: raw MAD is `median(abs(e_i - median(e)))` over the approved residual daily log-return series, and standardized MAD is exactly `raw_mad * 1.4826`. The versioned result preserves raw MAD, standardized MAD and the constant `1.4826`; this conversion is only a normal-consistency comparison scale and is not a buffer, reversal threshold or trading multiplier. Zero/minimum-scale and numeric precision/rounding behavior remain open.
- `1.11-plan`: assigns Welch analysis the primary research role for candidate-period, dominance and cross-window-stability evidence, while preserving the corresponding full-window Fourier spectrum as a diagnostic cross-check. Both outputs and their exact method/version evidence remain visible. If their later-approved comparison says they disagree, the result records a warning and cannot be forced into a stable-cycle classification. Exact Welch segmentation/overlap/window function, full-window transform details and the disagreement comparison remain open.
- `1.12-plan`: sets the Welch segmentation direction to exactly two long overlapping views of each valid window: a leading segment and a trailing segment, each approximately two thirds of the full window and sharing approximately the middle third. The 60-day layout is two 40-day segments with 20 observations of overlap; the 120-day layout is two 80-day segments with 40 observations of overlap. For the indivisible 250-day case, the approved direction is two approximately 167-day segments with approximately 84 observations of overlap; exact integer rounding/index boundaries remain open rather than inferred. Window function, averaging and other spectral settings also remain open.
- `1.13-plan`: fixes the 250-day integer layout over trading-observation indices `0..249`: the leading segment is `0..166`, the trailing segment is `83..249`, each segment contains exactly 167 observations, and the shared overlap `83..166` contains exactly 84 observations. This resolves only the prior rounding/index decision; Welch window function, averaging/scaling and other spectral settings remain open.
- `1.14-plan`: applies a versioned Hann window to each Welch segment before its spectral calculation to reduce artificial edge discontinuity. The unmodified detrended segment values, exact Hann coefficient sequence, coefficient-applied values and window definition/parameters remain stored as separate evidence. This approval applies only to Welch; it does not select the full-window Fourier diagnostic's window. Periodic-versus-symmetric Hann convention, exact coefficient formula/library binding, normalization, averaging and scaling remain open.
- `1.15-plan`: selects the periodic Hann definition for each Welch segment: for segment length `N` and index `n = 0, ..., N-1`, `w[n] = 0.5 - 0.5*cos(2*pi*n/N)`. Here `N` is exactly 40, 80 or 167 according to the approved segment layout. Every result preserves the formula/version identifier, `N`, index-to-coefficient mapping and complete coefficient sequence. Any implementation/library must reproduce this formula and record its identity/version; no third-party dependency is admitted by this planning decision. Normalization, Welch spectrum averaging/scaling and full-window Fourier window remain open.
- `1.16-plan`: combines the leading and trailing segment power spectra by an equal-weight bin-by-bin arithmetic mean: `P_welch[k] = (P_leading[k] + P_trailing[k]) / 2`. Both individual power spectra and the averaged spectrum remain separately stored with their exact bin/frequency mappings and formula/version evidence; neither segment receives recency, quality or discretionary weighting. This approval does not select spectral normalization/scaling, define behavior when either segment spectrum is invalid, or choose the full-window Fourier diagnostic's settings.
- `1.17-plan`: fails the containing Welch window when either required segment spectrum is invalid. It must not calculate or publish an averaged Welch spectrum from only the surviving segment. Each segment's validation status, available evidence and exact failure reason remain stored together with the window-level failure; independent 60/120/250 windows that do not share the failure may still calculate. A failed calculation is distinct from a valid spectrum with no stable cycle.
- `1.18-plan`: preserves two parallel views of every valid averaged Welch spectrum. The actual-power view is corrected for Hann-window influence under a later-approved exact scaling formula and is retained for amplitude research. The relative-share view is normalized only over the later-finalized eligible period/frequency-bin set `E`: `S_welch[k] = P_welch[k] / sum(P_welch[j] for j in E)`, so eligible shares sum to `1` (100%) and provide the evidence for 15%/30% dominance classification. Neither view replaces the other. Exact Hann energy correction, one-sided-bin scaling, units, eligible-edge membership and zero-total-power status remain open.
- `1.19-plan`: when the otherwise valid actual-power spectrum has `sum(P_welch[j] for j in E) = 0`, the actual-power evidence remains valid and stored, while the relative-share result has status `ZERO_ELIGIBLE_POWER`, contains no fabricated percentage distribution and produces no 15%/30% dominance class. This is a valid calculation with no measurable power in the eligible range, not a calculation error, invalid segment or automatically stable/no-stable-cycle classification.
- `1.20-plan`: defines segment actual power as a one-sided squared-magnitude spectrum rather than power spectral density. For weighted real input `y[n]=x[n]w[n]`, future-selected FFT length `N_fft`, raw complex coefficients `Y[k]=sum(y[n]*exp(-i*2*pi*k*n/N_fft))` and Hann coherent-gain correction `C_w=abs(sum(w[n]))^2`, the two-sided base is `P_two[k]=abs(Y[k])^2/C_w`. The one-sided spectrum keeps `k=0` unchanged, doubles each positive-frequency bin with a distinct negative-frequency mirror, and, when `N_fft` is even, keeps `k=N_fft/2` unchanged. Raw complex FFT coefficients, raw squared magnitudes, `C_w`, sidedness mapping and corrected powers remain stored. Units are squared input units (`log-price-residual^2` here), not density per unit frequency. FFT length/zero-padding, frequency grid, peak neighborhood and amplitude conversion remain open.
- `1.21-plan`: sets each Welch segment's FFT length to its parent window length `W`: `N_fft=60/120/250` for segment lengths `40/80/167`. After Hann weighting, zeros are appended only at local indices `N..W-1` (`40..59`, `80..119`, `167..249`); they are marked `FFT_PADDING_ONLY`, never Market Bars or additional observations. The grid is `f[k]=k/W` cycles per completed trading observation and `T[k]=W/k` completed trading observations for `k>0`. Eligible bins satisfy the inclusive predicate `4 <= T[k] <= W/3`, giving exact sets `k=3..15`, `3..30` and `3..62`. The unpadded weighted segment, padded sequence, padding mask/range, `N_fft`, complete bin/frequency/period map and eligibility result are preserved. Padding supplies a deterministic/interpolated ruler only and cannot claim added information or true resolving power. Full-window Fourier settings, peak-neighborhood/smoothing and amplitude conversion remain open.
- `1.22-plan`: when an eligible relative-share spectrum has one unique strongest bin, that bin is the candidate center `k* = argmax(S_welch[k] for k in E)`. Its requested neighborhood is exactly `R(k*)={k*-2,k*-1,k*,k*+1,k*+2}` and its effective neighborhood is `N(k*)=R(k*) intersect E`; bins outside `E` are excluded rather than wrapped, invented or treated as zero. The result stores `P_neighborhood=sum(P_welch[j] for j in N(k*))` and `D_neighborhood=sum(S_welch[j] for j in N(k*))`, plus every center/member/contribution and requested-versus-effective range. If `R(k*)` crosses an eligible boundary, `neighborhood_truncated_at_eligible_edge=true` and the omitted bins are identified. `T[k*]` remains the candidate-center period; this revision does not smooth the spectrum or replace it with a weighted-center period. Exact tied-maximum/multiple-peak handling, optional smoothing, 15%/30% boundary inclusivity/status names, amplitude conversion and full-window Fourier settings remain open.
- `1.23-plan`: classifies a defined neighborhood share `D_neighborhood` with exact mathematical boundaries: `WEAK` when `0 <= D_neighborhood < 0.15`, `CANDIDATE` when `0.15 <= D_neighborhood < 0.30`, and `STRONG` when `0.30 <= D_neighborhood <= 1`. Therefore exactly 15% is `CANDIDATE` and exactly 30% is `STRONG`; only `CANDIDATE` and `STRONG` may supply dominance-qualified evidence to the later cross-window stability test. `ZERO_ELIGIBLE_POWER`, an unresolved tied maximum or any other case without a defined neighborhood share produces no dominance class. The classification is based on the underlying calculated share rather than a rounded display string; exact numeric representation, comparison tolerance and persisted precision remain open for implementation approval.
- `1.24-plan`: adopts `P23-1-R1` as the user-approved mathematical/data design baseline: trend-only MAD baseline; version-frozen U.S.-equity calendar and point-in-time/retrospective availability evidence; Alpaca raw/split/corporate-action provenance; project-owned NumPy FFT formulas with no SciPy runtime; no extra smoothing; eight-ULP maximum ties; 80% disjoint competing-peak ambiguity; symmetric inclusive 20% method/cross-window comparison and clique support; same-grid full-window periodic-Hann diagnostic; explicit equivalent log/price amplitude representations; sine/cosine residual fit plus trend-only/cycle-removed MAD; valid zero MAD; float64/Decimal/IEEE-hex evidence; separate statuses; specialized typed evidence; additive Schema v14; read-only inspection; and staged disabled delivery. PROPOSAL-024 has implemented this P23-1A–D subset. The baseline still selects no MAD multiplier, reversal threshold, state, target, Decision, Risk or trade.

## Intent interpretation

### User request

Record the agreed stock-cycle, stock-specific volatility, two-trading-day reversal confirmation, linear small-move trading and versioned-algorithm design as a development target and plan only. Do not implement it yet.

### Underlying user goal

Build a daily-frequency mathematical strategy that can distinguish ordinary price noise from a genuine change of cycle, continue making bounded adjustments during ordinary fluctuations, retain a stable and explainable per-stock state, and reproduce every result from exact versioned definitions and inputs.

### Agreed product and trading interpretation

The future model must preserve the following user-approved design target:

1. Each stock has an explicit current trading cycle with a formal activation time and a separately explicit fixed mathematical movement-reference price/time. For a confirmed reversal, these two times are deliberately different.
2. Cycle-relative movement is the actual relative change from the mathematical movement reference:

   ```text
   cycle_relative_change
       = (current_price - movement_reference_price)
         / movement_reference_price
   ```

   It is not the sum of daily percentage changes.
3. A small move against the current cycle does not automatically start a new cycle.
4. An upward cycle tracks its highest completed observation; a downward cycle tracks its lowest completed observation. The relevant extreme is preserved as reversal evidence.
5. Every stock uses its own versioned volatility range/risk scale. A single fixed percentage must not be silently applied to every stock.
6. Price movement that has not reached the reversal threshold remains eligible for a basic linear target-position adjustment. “Small” therefore means “does not change the cycle,” not “must be ignored.”
7. A sufficiently large movement in the established/current-cycle regime may use a faster, finite accelerating response. The eventual curve must remain bounded by explicit minimum and maximum positions.
8. Linear and accelerating responses are regions of one continuous target-position rule. Exactly one region applies to one evaluation; the two outputs are not added together or applied twice.
9. A move against the current cycle that crosses the stock-specific reversal threshold creates a reversal candidate, not an immediate cycle change.
10. Reversal confirmation requires two completed trading-day closes:
    - the first completed close beyond the threshold is confirmation day 1;
    - the next trading-day completed close must remain beyond the threshold to become confirmation day 2;
    - if that next completed close returns inside the threshold, the candidate is cancelled and the existing cycle remains open.
11. During confirmation days 1 and 2, the old cycle remains the operational state and only the basic linear target-position region may be used. The new direction's accelerating region must not be used before confirmation. Any actual Decision, Risk result or future fill from those days retains its original old-cycle/linear provenance and is never rewritten retrospectively.
12. If day 2 confirms the reversal at its close, the old cycle closes after that completed observation and the new cycle becomes operational on the next trading day, referred to as day 3. The new operational state must not be applied retroactively to confirmation days 1 or 2.
13. The new cycle's mathematical movement reference is the prior-cycle reversal extreme—the last qualifying high before a confirmed downward reversal or the last qualifying low before a confirmed upward reversal—not the day-2 close. Confirmation-day observations are stored in a provisional buffer:
    - if confirmation succeeds, both observations become immutable new-cycle mathematical evidence and day-3 accelerating progress already includes the actual movement from the reversal extreme through the day-2 close;
    - that progress is one actual reference-relative percentage, not a sum of daily percentage changes;
    - if confirmation fails, the provisional new-cycle attribution is discarded, the old cycle remains open, and the observations plus any actual linear Decisions/Risk results/fills remain in their truthful original history.
14. Each non-frozen stock may trade at most one or two times per trading day. This is a cap, not a required number of trades; zero trades remains valid. Normal operation is expected to use one opportunity, while any second opportunity requires a separately specified and versioned scheduling/use rule.
15. A frozen/sealed stock has a trade cap of zero. Its prices, volatility observations, mathematical state, reversal/recovery evidence and history continue to update so that unfreezing does not erase context.
16. Calculations express a bounded target position and the difference between target and current position. They must not repeatedly issue the same fixed-size action after the target has already been reached.
17. Formula definitions and per-stock parameter configurations are immutable and versioned. Daily observations and state calculations are results tied to the exact versions and `Run ID`; they do not create a new algorithm-definition version every day.
18. Per-stock volatility research may include a rolling Fourier/Welch spectral Factor under these approved boundaries:
    - it analyzes detrended price or return observations to estimate dominant rhythm, amplitude, spectral concentration/stability and residual volatility;
    - it uses only trailing observations that were completed and available at the evaluation time; no centered/future window is allowed;
    - it is evidence for the stock-specific volatility range and threshold research, not an independent reversal judge, Decision policy or trading signal;
    - absence of a stable frequency peak produces an explicit `NO_STABLE_CYCLE`-type research status rather than a forced period;
    - the normal volatility range must not be inferred from a spectral peak alone; unexplained/residual variation remains explicit;
    - Welch analysis is the primary research evidence for candidate period, dominance and cross-window stability because its segment averaging is intended to reduce sensitivity to one unusual part of the trailing window;
    - the corresponding full-window Fourier spectrum is calculated and saved as a diagnostic cross-check. It remains visible but cannot replace the primary Welch evidence silently;
    - when the later-approved comparison rule says Welch and the full-window Fourier diagnostic disagree, the result records a visible warning and cannot be forced into a stable-cycle classification. The exact comparison equation and status name remain open;
    - candidate versions must compare at least a non-spectral baseline, rolling Fourier/Welch analysis and a later time-localized wavelet approach over the same completed historical evidence before any method is selected.
19. The initial P23-1 research configuration direction is user-approved as follows:
    - input frequency is completed daily observations;
    - daily close is transformed to log-price scale so equal percentage changes are comparable across price levels;
    - the first spectral candidate removes a straight-line trend fitted only within the trailing window, then analyzes the remaining oscillation;
    - each 60/120/250-observation window fits its own unweighted ordinary least-squares line to the window's log closes: for the eventual approved horizontal coordinate `x_i` and log close `y_i`, choose intercept `a` and slope `b` that minimize `sum((y_i - (a + b*x_i))^2)`; save `a`, `b`, each fitted value and each residual; no future observation, cross-window shared line, deletion or hidden reweighting is permitted;
    - for a window that is valid under the later approved session-completeness policy, sort completed trading-session observations chronologically and assign `x_i = 0, 1, ..., n-1`; the intercept is therefore the fitted value at the first indexed observation and the slope is log-price change per trading observation; weekends and recognized exchange closures do not consume an index, while actual source session/date/Bar identities remain stored;
    - an apparently missing expected trading-session Bar is not covered by the weekend/closure rule. Once an approved session source identifies the date as an expected session, every 60/120/250 window containing that missing required Bar records a durable data-incomplete status plus the missing session identity and performs no valid detrending/spectral/amplitude/MAD calculation for that window;
    - no interpolation, invented close, previous-value fill, next-value fill or silent gap compression is allowed. A complete window that does not contain the gap may still calculate independently;
    - after the Market History evidence is repaired, recalculation creates a new immutable Run/result linked to the repaired exact inputs. The earlier data-incomplete result remains searchable and is not rewritten;
    - data-incomplete means the method could not be evaluated. It is not the same as a valid complete window whose evidence supports an explicit no-stable-cycle result;
    - expected-session classification must come from a formal versioned U.S. exchange calendar, not a hard-coded Monday-through-Friday test;
    - calendar evidence must represent regular sessions, exchange holidays, temporary closures and early closes. Every Factor Run stores the exact calendar definition ID/name/version and applicable venue/mapping evidence so a later replay can reproduce which sessions were expected;
    - approval of this calendar direction does not select or authorize a third-party package, external calendar service, supported exchange list, symbol-to-calendar mapping, update policy or historical-calendar correction policy;
    - the first P23-1 spectral candidate transforms the split-adjusted Daily close to log-price scale. The exact raw close and split-adjusted close are both preserved with split event/effective-date, adjustment source/version and as-of/revision evidence;
    - the raw close is audit evidence and is not silently substituted into the first candidate's spectral calculation. A missing, invalid or irreproducible required split adjustment produces an explicit non-valid result rather than a guessed adjustment;
    - dividend adjustment is not applied in the first candidate. Dividend-adjusted/total-return research, if desired later, requires a separate version and point-in-time-safe policy; this revision does not select merger, spin-off, symbol-change or other corporate-action semantics;
    - the adjustment adapter may derive a research input but cannot rewrite existing Market History Bars. Every result remains bound to exact immutable source Bars and adjustment evidence;
    - residual variation is based on daily log returns after separating the candidate periodic component;
    - 60, 120 and 250 trading-day windows are all calculated and stored separately; no window is automatically selected as the winner;
    - eligible candidate periods start at 4 trading days and end at one third of the corresponding window, giving initial research bands of 4–20, 4–40 and 4–83 trading days;
    - within each valid 60/120/250-day window, Welch is the primary source of candidate-period, dominance and cross-window-stability evidence;
    - Welch uses exactly two long overlapping views of the approved detrended trailing window: one anchored at the beginning and one anchored at the end. Each view is approximately two thirds of the full window and they share approximately the middle third;
    - the 60-day window uses two 40-observation segments with 20 observations of overlap; the 120-day window uses two 80-observation segments with 40 observations of overlap;
    - for the 250-day window indexed `0..249`, the leading segment is exactly `0..166` and the trailing segment is exactly `83..249`. Each contains 167 observations and their inclusive overlap `83..166` contains 84 observations;
    - before the Welch spectral calculation, each segment is multiplied by a versioned Hann window so the segment edges are tapered rather than treated as an abrupt artificial jump;
    - the original detrended segment values remain unchanged and stored. The exact Hann coefficient sequence, coefficient-applied segment values and window definition/parameters are also stored separately so the transformation is reproducible and inspectable;
    - this Hann approval applies only to Welch segments. It does not silently select a window for the full-window Fourier diagnostic;
    - the Welch window is the periodic Hann definition: for segment length `N` and `n = 0, ..., N-1`, `w[n] = 0.5 - 0.5*cos(2*pi*n/N)`. The approved segment layouts therefore use `N = 40`, `N = 80` or `N = 167`;
    - each result stores the exact formula/version identifier, `N`, every `n -> w[n]` mapping and the complete coefficient sequence. Any future implementation/library must reproduce this formula and bind its identity/version; this planning approval adds no dependency;
    - the two segment power spectra are combined bin by bin using the equal-weight arithmetic mean `P_welch[k] = (P_leading[k] + P_trailing[k]) / 2`;
    - the leading spectrum, trailing spectrum and averaged Welch spectrum are all stored separately with exact bin/frequency mappings and formula/version evidence. No segment receives recency, quality or discretionary weighting;
    - if either required segment spectrum is invalid, the containing Welch window is invalid and no averaged Welch spectrum may be calculated or published from only the other segment;
    - each segment's validation status, available calculation evidence and exact error reason remain stored with the window-level failure. Independent valid 60/120/250 windows may still calculate, and this calculation failure remains distinct from a valid spectrum with no stable cycle;
    - every valid averaged Welch spectrum preserves an actual-power view corrected for Hann-window influence under a separately approved exact scaling definition. This view supports later amplitude research but does not itself choose the amplitude formula;
    - it also preserves a relative-power-share view over the eligible period/frequency-bin set `E`: `S_welch[k] = P_welch[k] / sum(P_welch[j] for j in E)`. Eligible shares sum to `1` (100%) and are the planned evidence for the 15%/30% dominance classes;
    - the actual-power and relative-share views remain separate, versioned evidence and neither may replace the other;
    - if `sum(P_welch[j] for j in E) = 0`, the actual-power spectrum remains valid and stored, but the relative-share result is `ZERO_ELIGIBLE_POWER`, contains no percentage vector and emits no 15%/30% class. It is valid zero-eligible-power evidence rather than a calculation error or invalid segment;
    - `ZERO_ELIGIBLE_POWER` does not by itself assert stable cycle or no stable cycle; those remain later classification outcomes using all otherwise approved evidence;
    - for weighted real segment values `y[n]=x[n]w[n]`, use the parent window length `W` as `N_fft`: 40-observation segments use 60, 80-observation segments use 120 and 167-observation segments use 250;
    - append zeros only after the weighted segment at local indices `40..59`, `80..119` or `167..249`. These values carry `FFT_PADDING_ONLY`, are never Market Bars/observations, and do not enter the Hann coefficient or coherent-gain sums;
    - preserve raw complex `Y[k]=sum(y[n]*exp(-i*2*pi*k*n/N_fft))` over the explicitly padded sequence, raw `abs(Y[k])^2`, and `C_w=abs(sum(w[n]))^2`;
    - segment actual power uses `P_two[k]=abs(Y[k])^2/C_w`, then a one-sided mapping: `k=0` is unchanged; bins with a distinct negative-frequency mirror are doubled; if `N_fft` is even, the Nyquist bin `k=N_fft/2` is unchanged. For odd `N_fft`, every retained positive-frequency bin is doubled;
    - this is a squared-magnitude spectrum in squared input units (`log-price-residual^2` for this candidate), not power spectral density per unit frequency. The raw coefficients, correction factor, bin-mirror mapping and corrected values are all stored;
    - the Welch grid is `f[k]=k/W` cycles per completed trading observation and `T[k]=W/k` completed trading observations for `k>0`; `k=0` has no finite candidate period and is ineligible;
    - eligible bins use the inclusive predicate `4 <= T[k] <= W/3`: 60-day window `k=3..15`, 120-day window `k=3..30`, and 250-day window `k=3..62`. For 250 days, `k=62` has period `250/62` and `k=63` is below four trading observations, so no unavailable exact four-day bin is fabricated;
    - preserve the unpadded weighted segment, padded sequence, padding mask/range, `N_fft`, every bin/frequency/period mapping and each eligibility result. Padding creates only a deterministic/interpolated calculation ruler, not observations, information or increased true resolving power;
    - when the eligible relative-share vector exists and has one unique strongest bin, use `k* = argmax(S_welch[k] for k in E)` as the candidate center and retain its frequency `f[k*]` and period `T[k*]`;
    - request exactly the five-bin neighborhood `R(k*)={k*-2,k*-1,k*,k*+1,k*+2}` and calculate only the eligible intersection `N(k*)=R(k*) intersect E`. Do not wrap across either eligible edge, fabricate missing bins or insert zero contributions for out-of-range bins;
    - preserve every requested and effective bin, each bin's actual power and relative share, `P_neighborhood=sum(P_welch[j] for j in N(k*))`, and `D_neighborhood=sum(S_welch[j] for j in N(k*))`;
    - if the requested five-bin range crosses an eligible boundary, record `neighborhood_truncated_at_eligible_edge=true` and preserve the exact omitted bins. Otherwise record it as false;
    - the candidate period remains `T[k*]`; this revision does not smooth before peak selection, compute a weighted-center period or convert neighborhood power to amplitude;
    - tied-maximum/multiple-peak handling, optional smoothing, numeric comparison precision/tolerance, exact half/full-amplitude conversion and full-window Fourier settings remain separately versioned open decisions;
    - the full valid window is also analyzed by a Fourier transform and its spectrum, candidate peak, period, dominance and amplitude evidence are stored as diagnostic evidence with exact method/version settings;
    - the Factor preserves the Welch and full-window Fourier outputs side by side. A later-approved disagreement test must produce a visible warning and prevent a forced stable-cycle classification; it does not create a reversal or trade;
    - one-window evidence is a recent/candidate rhythm only; at least two windows must support similar periods before the rhythm is classified as relatively stable;
    - periods within 20% are treated as similar for the initial research classification; the exact comparison denominator/edge semantics remain to be specified;
    - when `D_neighborhood` is defined, classify it exactly as `WEAK` for `0 <= D_neighborhood < 0.15`, `CANDIDATE` for `0.15 <= D_neighborhood < 0.30`, and `STRONG` for `0.30 <= D_neighborhood <= 1`;
    - exactly 15% is `CANDIDATE`, exactly 30% is `STRONG`, and only `CANDIDATE`/`STRONG` may contribute dominance-qualified evidence to the later cross-window stability test. No display-rounded value may substitute for the underlying share;
    - `ZERO_ELIGIBLE_POWER` and any unresolved case without a defined neighborhood share emit no dominance class;
    - residual volatility uses median absolute deviation (MAD) so one extreme observation does not by itself define normal variation; the extreme observation remains immutable source evidence;
    - periodic evidence stores both the half-amplitude from the fitted trend center to a peak/trough and the full peak-to-trough amplitude; neither is silently selected as the later state/reversal input;
    - for residual daily log-return observations `e_i`, raw MAD is `median(abs(e_i - median(e)))`;
    - standardized MAD is exactly `raw_mad * 1.4826`. The constant is the rounded normal-consistency factor derived from `1 / normal_quantile(0.75) ≈ 1.482602`; every result preserves the exact configured constant `1.4826`;
    - residual evidence stores both raw MAD and standardized MAD; neither is silently selected as the later state/reversal input, and `1.4826` is not a MAD buffer, reversal-threshold or trading multiplier;
    - if raw MAD is zero, standardized MAD is also zero. Whether that is a valid zero scale, a warning or subject to a separately versioned minimum scale remains open and cannot be silently floored;
    - the planned normal range combines a periodic-amplitude term with a residual-MAD buffer; when no stable spectral cycle exists, no spectral amplitude is forced and the non-spectral/residual path remains available.

### Existing verified capability and overlap reminder

This direction overlaps existing verified, disabled research foundations:

- Phase 5B already calculates manual `(price - reference) / scale`, but does not estimate reference/scale or read Market History automatically.
- Phase 4A already preserves user-defined asset-state graphs, cycles, transitions and deterministic replay, but has no automatic financial evaluator.
- Phase 5A already evaluates immutable bounded monotone finite-knot target-position curves, and Phase 5C links one exact standardized-state result to one exact curve, but both remain manual/unconsumed research.
- Phase 5D already converts an exact target/current difference into a specialized Decision intent.
- Phase 6A–6E already preserve a manual-review/block-only Risk research chain and its inspection history.
- Unified Run History, exact-version evidence and central SQLite migration discipline already exist.

The future model should reuse these owners and public concepts through explicit adapters. It must not replace them silently, create a parallel state/target/Decision/Risk authority, or reinterpret old results.

### User-suggested method

Use a per-stock volatility range to decide whether a counter-move is small or reversal-sized; research Fourier/Welch analysis for recurring rhythm while retaining residual variation and non-spectral/wavelet comparison versions; require two trading days to confirm a reversal; use basic linear buying/selling before the threshold and a finite accelerating response in the established regime; save every new algorithm as a callable version.

### Professional interpretation

The design is a volatility-normalized, stateful, piecewise target-position policy:

```text
completed market observation
→ cycle-relative price observation and stock-specific volatility result
→ current-cycle extreme and reversal-candidate evaluation
→ provisional confirmation buffer or confirmed day-3 state activation
→ one active response region: LINEAR or ACCELERATING
→ bounded target position
→ target-current difference
→ Decision
→ independent Risk review and daily trade-cap/freeze checks
→ future Backtest fill simulation
```

The state evaluator decides whether the old cycle remains active, enters reversal watch or changes operational state on day 3 after two trading-day confirmations. It preserves the difference between operational activation time, the reversal-extreme mathematical reference and the provisional confirmation observations. The target-position owner calculates the desired holding. Decision proposes an adjustment. Risk may reduce, block or require review but may not increase or reverse that proposal. No GUI owns any of this logic.

### Recommendation

Treat this proposal as a planning umbrella and implement it later as separately approved, disabled slices. Do not attempt a single system-wide implementation. Freeze exact formulas and parameters only after historical exploration and explicit user decisions.

## Architecture classification

- Owning layer: Cross-cutting research-planning umbrella; it is not a runtime owner.
- Canonical owners:
  - `market_data` / Market History: completed Bar facts and availability metadata.
  - `factors`: cycle-relative price observations, non-spectral volatility baselines, rolling Fourier/Welch rhythm evidence, later wavelet candidate evidence and per-stock volatility-scale calculations.
  - `asset_state`: cycle identity, operational activation time, mathematical reference/extreme, provisional reversal evidence, two-day confirmation, freeze state and transitions.
  - `target_position`: continuous bounded linear/accelerating target-position definition and evaluation.
  - `decision`: target-current difference and proposed action.
  - `risk`: frozen-asset block, per-day trade cap and non-expanding independent review.
  - `orchestration`: public-contract sequencing and shared `Run ID`.
  - `persistence` / `run_history`: immutable definition, configuration, result, state and trace storage.
  - `backtesting`: future historical sequencing, simulated fills and daily-count state after separate approval.
  - `algorithm_control`: configuration and read-only inspection only.
- Why this belongs in the system: it defines the first planned automatic connection among the already-built mathematical research layers while preserving ownership, observability and reproducibility.
- Why no existing component can own it unchanged: no single existing module owns Market Data availability, Factor math, state transitions, desired holdings, Decision and Risk; placing all behavior in one owner would violate the established dependency boundaries.
- Responsibilities: record the agreed behavior, split ownership, identify proposed contracts, capture open financial decisions, define safe implementation slices and validation gates.
- Explicit non-responsibilities: choosing any unapproved formula/value, implementing code, migrating SQLite, changing current results, selecting active definitions, calculating orders, reserving cash, persisting accounting facts, Paper/Live access or runtime activation.
- Existing components affected in future: Market History, Factors, Asset State, Target Position, Decision, Risk, orchestration, persistence, Run History, Algorithm Control and Backtesting.

## Planning identity declaration

- `component_id`: `planning.quanttrade.volatility_piecewise_cycle`
- `component_type`: `PLANNING_UMBRELLA`
- `display_name`: `Volatility-Aware Piecewise Cycle and Target Position`
- `version`: `1.0.0-plan`
- `owner_layer`: `governance`
- `owner_module`: none; runtime responsibilities remain distributed among canonical owners.
- `description`: Approved design target for per-stock volatility-normalized cycles, two-day reversal confirmation and bounded piecewise target positions.
- `responsibilities`: planning, ownership allocation, versioning rules, open-decision inventory and staged admission.
- `non_responsibilities`: runtime calculation, state mutation, intent creation, Risk approval, order/fill creation or execution.
- `input_contracts`: none at runtime in this proposal.
- `output_contracts`: this proposal and related Compass/Roadmap records only.
- `allowed_dependencies`: verified project documentation and current public-concept descriptions.
- `forbidden_dependencies`: runtime code, database write paths, broker clients and execution environments.
- `required_capabilities`: none.
- `side_effects`: documentation only.
- `financial_effect`: none in the current system; future implementation can change recommended exposure and therefore requires separate approval.
- `safety_level`: `PLANNING_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `REGISTERED`

## Proposed versioned public contracts

The following names describe planning boundaries, not approved code contracts. Their exact schemas require a later proposal.

### `CycleRelativePriceObservation@1`

- Producer: Factor.
- Consumers: Asset State and research inspectors.
- Required evidence: symbol, completed observation time, exact price field, adjustment/feed identity, cycle ID, cycle operational-activation time, mathematical movement-reference price/time, current price and exact relative change.
- Time semantics: the observation must bind to a completed and available market observation; calendar and price-availability semantics remain open.
- Missing meaning: missing/invalid price or cycle reference produces a persisted invalid result, never an inferred value.

### `AssetVolatilityScaleDefinition@1` and `AssetVolatilityScaleResult@1`

- Producer: immutable Factor definition plus Factor evaluation.
- Consumers: Asset State and research inspectors.
- Required evidence: symbol, definition/configuration version, input window identity, as-of time, exact scale value/unit, calculation status and trace.
- Versioning: estimator method changes create a new definition version; a symbol parameter change creates a new per-symbol configuration version; a daily calculation creates a new result only.
- Approved research families: non-spectral baseline; rolling Fourier/Welch spectral analysis; later time-localized wavelet candidate. Approval of a research family does not select a production method.
- Approved initial research parameters: completed Daily observations; split-adjusted close as the first spectral candidate's calculation field with raw close and exact split-adjustment evidence preserved; no dividend adjustment in that candidate; log close; a separate trailing unweighted ordinary least-squares trend fit for each window with coefficients/fitted values/residuals preserved; chronological trading-observation index `0..n-1` as the horizontal coordinate, with actual session identities retained and weekends/recognized closures excluded; per-window fail-visible handling of a known expected-session missing Bar with no interpolation/skip and immutable rerun history; formal versioned U.S. exchange-calendar evidence covering regular sessions, holidays, temporary closures and early closes, with exact calendar identity/version bound to every Run; daily log-return residuals; raw MAD `median(abs(e_i - median(e)))`; standardized MAD exactly `raw_mad * 1.4826`, with both values and the constant preserved and no threshold meaning; separate 60/120/250-day windows; 4-day minimum period; maximum period equal to one third of the window; Welch as primary candidate-period/dominance/cross-window-stability evidence; exactly two leading/trailing long Welch segments, including exact 60-day 40/20, 120-day 80/40 and 250-day 167/84 layouts, with the 250-day indices fixed to leading `0..166`, trailing `83..249` and overlap `83..166`; periodic Hann `w[n] = 0.5 - 0.5*cos(2*pi*n/N)` applied only to each Welch segment for `N = 40`, `80` or `167`, with original detrended values, formula/version, `N`, exact coefficient mappings/sequence and coefficient-applied values all preserved; trailing `FFT_PADDING_ONLY` zeros producing `N_fft=W=60/120/250`, grids `f[k]=k/W` and `T[k]=W/k`, and inclusive eligible sets `k=3..15`, `3..30`, `3..62`, with all unpadded/padded/mapping evidence preserved and no added-information claim; one-sided segment squared-magnitude power using raw complex `Y[k]`, `C_w=abs(sum(w[n]))^2`, `P_two[k]=abs(Y[k])^2/C_w`, doubling mirrored positive bins but not DC or an even-`N_fft` Nyquist bin, with raw/corrected/mapping evidence preserved and units `log-price-residual^2`; exact equal-weight arithmetic averaging `P_welch[k] = (P_leading[k] + P_trailing[k]) / 2` with both individual power spectra and the averaged spectrum preserved; containing-window invalidation with no one-segment fallback when either segment spectrum is invalid, while independent windows may calculate and all segment/window validation evidence remains stored; parallel actual-power and eligible-range relative-share evidence, with `S_welch[k] = P_welch[k] / sum(P_welch[j] for j in E)`, eligible shares totaling 100%, actual power retained for amplitude research and relative shares used for 15%/30% dominance; `ZERO_ELIGIBLE_POWER` with valid actual power, no percentage vector and no dominance class when the eligible-power sum is zero, distinct from calculation failure and from stable/no-stable-cycle classification; a unique strongest eligible bin `k*` with exact requested five-bin neighborhood `k*-2..k*+2`, eligible-only effective intersection, summed actual power and relative-share dominance, preserved member contributions and explicit eligible-edge truncation evidence; exact dominance classes `WEAK` for `[0,0.15)`, `CANDIDATE` for `[0.15,0.30)` and `STRONG` for `[0.30,1]`, with only candidate/strong eligible for later cross-window support and no class when neighborhood share is undefined; full-window Fourier as a stored diagnostic cross-check with its window still open; visible warning and no forced stable-cycle classification when the later-approved comparison says they disagree; two-window stability support; 20% period similarity; both half and full peak-to-trough spectral amplitude evidence; periodic amplitude plus MAD-buffer combination direction.
- Open items: exact baseline estimator, exchange-calendar library/data source, supported venue set, symbol-to-venue mapping, calendar version/update/freeze/correction policy and exact data-incomplete status contract, split-event/adjustment data source, point-in-time availability, adjustment revision/freeze policy and other corporate-action semantics, future Hann/FFT implementation/library identity and formula validation, optional smoothing and tied-maximum/multiple-peak handling, full-window Fourier transform/window settings, the exact Welch-versus-Fourier disagreement comparison and status name, exact 20% comparison formula/edge inclusivity, exact spectral-amplitude conversion, numeric precision/rounding/comparison tolerance and zero/minimum-scale status, later consumer choice between the preserved amplitude/MAD variants, MAD buffer/threshold multiplier and combination formula, warm-up beyond window completeness, outlier status and reversal-threshold multiplier.

### `SpectralVolatilityEvidence@1`

- Producer: Factor research.
- Consumers: volatility-scale comparison service and research inspectors only; Asset State may consume only a separately approved selected volatility-scale result, not raw spectral peaks.
- Required evidence: symbol, exact completed source-observation IDs/range/session dates, raw and split-adjusted closes, split event/effective date and adjustment source/version/as-of evidence, explicit `dividend_adjusted=false`, exact exchange-calendar definition ID/name/version and venue/mapping evidence, expected-session/holiday/closure/early-close classification, price/return transformation, detrending method, the `0..n-1` trading-observation coordinate mapping, least-squares intercept/slope/fitted values/residuals, Welch primary-role marker and exact segment/overlap definition, each segment's validation status/error and all available calculation evidence, containing-window validation status/error, explicit one-segment-fallback prohibition, unmodified detrended segment values, periodic-Hann formula/version, exact `N`, every index/coefficient mapping and complete coefficient sequence, coefficient-applied values, unpadded weighted segment, padded sequence, `FFT_PADDING_ONLY` mask/range, `N_fft=W`, complete bin/frequency/period map and eligibility predicate/result, implementation/library identity/version and formula-reproduction validation, raw complex FFT coefficients and squared magnitudes, `C_w`, sidedness/mirror mapping, corrected one-sided squared-magnitude powers and squared-input units, exact leading/trailing segment power spectra when valid, equal-weight averaging formula/version and averaged Welch spectrum only when both segments are valid, eligible bin set `E`, eligible-power sum, relative-share status/formula/version and spectrum when defined, explicit absence of a percentage vector and dominance class for `ZERO_ELIGIBLE_POWER`, eligible-share sum/check, explicit actual-power-versus-relative-share purpose markers, unique center-bin identity/frequency/period when defined, requested five-bin range, effective eligible member set, each member's actual-power/relative-share contribution, summed neighborhood actual power and relative-share dominance, exact omitted edge bins and `neighborhood_truncated_at_eligible_edge`, exact 0.15/0.30 comparison operands/results and `WEAK`/`CANDIDATE`/`STRONG` class or explicit absence, full-window Fourier diagnostic-role marker and exact transform/window definition, each method's frequency grid/spectrum/candidate peak/period/dominance/amplitude evidence, their comparison inputs/result/warning, cross-window stability evidence, both half-amplitude and full peak-to-trough amplitude, residual log-return identities, residual median, raw MAD, standardized MAD and exact `1.4826` conversion evidence, status/warnings and exact definition/configuration/software versions.
- Time semantics: every source observation must have been completed and available at `as_of_utc`; rolling calculation is trailing-only and cannot revise an earlier result in place.
- Missing/weak meaning: a known expected-session missing required Bar produces a per-window durable data-incomplete result with no valid spectral calculation; insufficient observations and invalid spacing remain explicit non-valid states; a complete valid window with weak/unstable peaks produces a separate no-stable-cycle state. No default period or price is invented.
- Financial authority: none. This evidence cannot switch Asset State, choose a target position, create an intent or bypass two-day confirmation.
- Initial classification evidence: exact window length, eligible-period range, peak/dominance calculation, 15%/30% class, peer-window period/support, 20% similarity result, half/full amplitude values, raw/standardized MAD values and periodic-plus-residual normal-range trace. Both alternatives remain evidence; the Factor cannot silently select a downstream trading interpretation.

### `CycleStateDefinition@1`, `CycleStateSnapshot@1` and `ReversalEvidence@1`

- Producer: Asset State.
- Consumers: Target Position input adapter, Decision/Risk context, Backtesting and inspectors.
- Required evidence: symbol, cycle ID/direction, operational activation time, mathematical movement-reference price/time, current extreme, current state, reversal threshold source, confirmation day count, provisional observation identities, candidate start/cancel/confirm evidence, attribution/discard result, frozen status and exact definition/configuration versions.
- Activation/attribution rule: confirmation days remain old-cycle operational history; a successful day-2 close schedules new-cycle activation for day 3 and attributes the buffered observations to new-cycle mathematical progress from the prior reversal extreme without changing historical actions.
- State rule: the same completed observation and same state version must be idempotent and must not create duplicate transitions.
- Missing meaning: unavailable Factor/evidence fails closed and creates no inferred transition.

### `PiecewiseTargetPositionDefinition@1` and result

- Producer: Target Position.
- Consumers: Decision and inspectors.
- Required evidence: exact input state, region selected (`LINEAR` or `ACCELERATING`), region boundary values, intermediate calculation, minimum/neutral/maximum positions, bounded target, current position and difference.
- Continuity rule: the value at every region boundary must be continuous according to the exact versioned definition.
- Exclusivity rule: exactly one region is applied per evaluation; no double counting.
- Open items: region width, slopes, accelerating function, saturation limits, rounding and monetary/share conversion.

### `PerAssetTradingPolicyDefinition@1` and `DailyTradeCountSnapshot@1`

- Proposed owner: Risk for policy and the no-more-risk gate; the authoritative source of completed/simulated trade counts must be decided with Backtesting and future Portfolio Accounting/Execution boundaries.
- Required evidence: symbol, trading date/calendar, frozen status, allowed maximum count, count already consumed, event identities and policy version.
- Rule: the configured maximum is a cap, not a quota. Frozen means zero permitted trades.
- Open items: whether intent, Risk-reviewed candidate, planned order or fill consumes a count; cancellation/rejection treatment; exact second-opportunity schedule; timezone/calendar.

## Conflict assessment

- Result: `REQUIRES_ADAPTER`
- Layer conflict: the behavior spans existing owners; no umbrella runtime module may absorb all formulas and authority.
- Responsibility conflict: avoided only if Factor, Asset State, Target Position, Decision and Risk retain their current meanings.
- Dependency/cycle conflict: future adapters must follow the current one-way public-contract flow and must not make Factors depend on State/Decision/Risk or make GUI/Persistence own business logic.
- Permission/authority conflict: implementation can create new financial recommendations and Risk gates, so planning approval alone is insufficient.
- Data-contract/units/timezone conflict: exact price field, adjustment, market calendar, Bar completion/availability, USD/share units and rounding are unresolved.
- Configuration/default conflict: no estimator, threshold, curve, position bound, trade count or schedule has an approved default.
- Runtime/duplicate/idempotency conflict: state transitions and daily trade counting require explicit event identity and same-input replay protection.
- Safety/Live/leverage/shorting/risk-limit conflict: long-only/shorting semantics and complete Risk composition are not approved; Paper/Live and automatic submission remain unavailable.
- Parallel-component combination rule: future work extends existing canonical components. Only one exact state definition, per-symbol configuration and target-position definition may be selected for one run; there is no implicit “latest” or multi-definition merge.
- Recommended resolution: implement only through the separately approved slices below, each disabled and historically observable.
- User decision required: every implementation slice and every unresolved financial formula/parameter requires a later explicit decision/approval.

## Financial, risk, and safety meaning

- Financial meaning: future results may recommend changing a stock's target exposure according to price, volatility and cycle state.
- Risk implications: threshold, curve and daily-cap choices can materially change timing, turnover, concentration and drawdown; they must be versioned and historically compared before any activation.
- Safety implications: all new runtime components must start disabled, remain `NO_EXECUTION`, and fail closed on missing versions, incomplete observations, duplicate state events or unresolved count state.
- Can it create exposure? This planning record cannot. A future Decision result could recommend exposure only after separately approved implementation.
- Can it approve/reduce/reject risk? This record cannot. Future Risk rules may reduce/block/review but never increase or reverse the Decision.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: this proposal grants no trading confirmation or activation path.

## Change Impact Report

- Primary module: project governance/planning documentation only for this task.
- Secondary modules: none at runtime.
- Public contracts: none changed; proposed contract names are non-binding planning boundaries.
- Configuration: none.
- Database: none; central SQLite remains Schema v13.
- GUI: none.
- Tests: document/governance/link checks only for this task.
- Documentation: Proposal index, Compass, Roadmap, Glossary and Edit Log.
- Permissions: no runtime or trading permission.
- Trading semantics: approved as a future design target; current trading behavior remains unchanged because no runtime path exists.
- Safety behavior: unchanged; Paper/Live and automatic submission remain disabled/unimplemented.
- Migration: none in this task; every future persistence change requires backup, count/foreign-key validation and rollback planning.
- Rollback: remove this planning record and revert only its documentation references; no runtime state/data is affected.
- Expected blast radius: `LIMITED` for this documentation task; `SYSTEM_WIDE` if the future model were attempted as one implementation, which is prohibited by this plan.

## Staged implementation plan

Each slice requires its own scoped proposal or an approved amendment with exact contracts, migration impact and acceptance evidence. Approval of this planning umbrella does not admit any slice.

### P23-1 — Cycle-relative observation and per-stock volatility research

- Add immutable Factor-owned definitions/configurations and persisted results.
- Bind exact completed Market History observations, data availability and version evidence.
- Implement only after separate approval as comparable disabled candidates: one non-spectral baseline, one rolling Fourier/Welch spectral version and, in a later separately admitted experiment, one time-localized wavelet version.
- Preserve the approved initial 60/120/250-day configurations as separate immutable research versions/results rather than an automatic best-window selector.
- Persist dominant-period/amplitude/stability/residual evidence and explicit no-stable-cycle/data-insufficient results; never force a cycle or publish a trading action.
- Provide calculation/history inspection only.
- Do not change Asset State, Target Position, Decision or Risk.

### P23-2 — Automatic cycle and reversal-watch evaluator

- Extend the existing Asset State owner with separate operational activation and mathematical-reference semantics, reversal extreme, provisional confirmation buffer, two-trading-day confirmation, failed-candidate discard, successful attribution, day-3 activation and frozen-state evaluation.
- Persist every valid, invalid and duplicate/idempotent attempt.
- Prove that a successful confirmation initializes day-3 accelerating progress with the reference-relative movement through confirmation day 2, while neither success nor failure rewrites confirmation-period Decisions/Risk results/fills.
- Do not create a target position or action.

### P23-3 — Continuous bounded piecewise target-position curve

- Extend Target Position with one versioned continuous rule containing a basic linear region and a finite accelerating region.
- Prove boundary continuity, boundedness, monotonicity where required and exactly-one-region evaluation.
- During reversal watch, admit only the linear region.
- Do not create a Decision or Risk result.

### P23-4 — Decision linkage and Risk policy gates

- Link one exact state/target result to the existing target-current Decision meaning.
- Add frozen-stock blocking and a versioned per-day maximum trade policy after authoritative event-count semantics are approved.
- Keep every positive candidate manual-review-only and `NO_EXECUTION`.
- Do not reserve cash, create orders or activate a pipeline.

### P23-5 — Historical full-chain simulation

- After separate approval, replay completed observations through Factor → State → Target Position → Decision → Risk → simulated fills.
- Include separately approved availability/calendar, cost, slippage, count-consumption and same-day sequencing rules.
- Prove every simulated fill traces to exact market data, definitions, configuration, state, target, Decision and Risk results.
- Paper and Live remain outside this plan.

## Remaining open decisions after R1 design approval

No implementation may hide or invent answers to these items:

1. P23-1A–D implementation admission is resolved by PROPOSAL-024: all four sequential slices, explicit requested U.S. stock/ETF mapping and one read-only Alpaca verification were approved and completed. P23-1E historical comparison and wavelets remain separate proposals.
2. Exact mapping from volatility scale to reversal threshold, including any direction asymmetry and minimum/maximum threshold.
3. Exact price/adjustment/availability semantics outside the R1 first Daily split-only candidate, including any future dividend/total-return research and broader production/backtest corporate-action policy.
4. Initial cycle direction/reference/extreme rules and behavior when history is insufficient.
5. Exact linear-region width, sign/direction semantics, slope and target-position change.
6. Exact accelerating function, transition boundary, continuity condition and saturation behavior.
7. Minimum, neutral and maximum target positions, plus USD/share conversion and rounding.
8. P23-2 reversal confirmation behavior when an expected session observation is missing or trading is suspended; recognized holidays/closures already consume no observation index under R1.
9. Exact semantics for the normal first opportunity and exceptional second opportunity.
10. Which event consumes the daily cap: Decision intent, Risk-reviewed candidate, planned order, submitted order or fill; how rejected/cancelled/partial events count.
11. Frozen-state entry, exit and manual-override authority.
12. Cost, slippage, liquidity and fill sequencing for historical simulation.
13. Long-only, shorting, leverage and complete portfolio-level Risk policy.

## Recommended P23-1 resolution package R1

> **Admission state:** `USER_APPROVED_DESIGN_BASELINE`.
>
> On 2026-07-31 the user accepted this complete mathematical/data recommendation, so it now governs planning revision `1.24`. The approval is not source-code approval, dependency-installation approval, public-runtime-contract approval, Schema migration approval or activation; those changes are requested separately by `PROPOSAL-024`.

### R1 design objective and non-negotiable boundaries

The recommended first implementation should answer only:

1. whether each 60/120/250-session input window is trustworthy and complete;
2. whether the data contains one sufficiently clear repeating rhythm;
3. whether Welch and a full-window diagnostic tell a compatible story;
4. whether at least two independent windows support similar periods;
5. what equivalent periodic amplitude and residual robust scale were measured; and
6. exactly which data, formulas, versions and intermediate values produced that evidence.

It must not select a reversal threshold, switch an Asset State, calculate a target holding, create a `TradeIntent`, approve Risk, consume cash or create an order. P23-1 outputs evidence only.

### R1 resolution summary

| Open area | Recommended resolution | Why this is the smallest safe choice |
|---|---|---|
| Non-spectral baseline | Per-window trend-only daily log-residual raw MAD and standardized MAD; no periodic subtraction | supplies an honest no-cycle comparison under the already-approved trend/MAD definitions |
| Trading sessions | Direct bounded `exchange_calendars` dependency; first definition uses a named `US_EQUITIES_REGULAR_V1` schedule backed by `XNYS`, with exact package version and frozen schedule fingerprint | replaces weekday guesses while avoiding a second market-data provider; the definition is a session-schedule identity, not a claim that every symbol is NYSE-listed |
| Daily availability | `available_at_utc = max(official_session_close_utc, first_observed_at_utc)`; a Daily observation may affect only a later session | prevents same-session look-ahead and records actual local availability |
| Split evidence | Alpaca raw bars plus `adjustment=split` bars and a frozen corporate-action response snapshot; only split/reverse-split adjustments are supported in candidate 1 | reuses the current provider while keeping raw facts and adjustment evidence separate |
| Historical knowledge | distinguish `POINT_IN_TIME_OBSERVED` from `RETROSPECTIVE_ADJUSTED`; retrospective snapshots may support research but cannot prove a point-in-time backtest | Alpaca's query filters do not reconstruct when this application historically knew a later provider revision |
| FFT implementation | Direct bounded NumPy dependency; project-owned formulas call `numpy.fft.rfft`/`rfftfreq`; no SciPy runtime dependency | the approved scaling differs from library defaults and is more auditable as explicit formulas |
| Extra smoothing | none in candidate 1 | Welch averaging plus periodic Hann already supplies smoothing; another smoother would change the approved dominance meaning |
| Ties and multiple peaks | ULP-based strongest-bin tie detection; reject one-cycle interpretation when a disjoint competitor neighborhood has at least 80% of the primary neighborhood dominance | avoids arbitrary first-bin tie breaking and visible two-rhythm data being forced into one period |
| 20% cross-window rule | symmetric relative difference `2*abs(T_a-T_b)/(T_a+T_b) <= 0.20`; require one unambiguous pairwise-compatible clique of at least two windows | no window is treated as the privileged denominator and chain-like 60/120/250 disagreement is not hidden |
| Full-window diagnostic | same parent residual, periodic Hann, `N_fft=W`, same eligible bins, power, peak and dominance rules; no padding | isolates the intended difference: two-segment Welch averaging versus one full-window view |
| Welch/Fourier agreement | both must have one candidate/strong peak and periods within the same symmetric 20% rule; otherwise no stable-cycle output | a diagnostic cannot be called a cross-check if invalid, weak or conflicting evidence is ignored |
| Amplitude | `a_log=sqrt(2*P_neighborhood)` as equivalent log half-amplitude, with exact log and price-domain half/full representations stored separately | follows the approved one-sided squared-magnitude scaling without pretending the result is an observed high-low |
| Residual scale | after a qualified frequency is found, fit sine/cosine phase over the full detrended window and calculate MAD from first differences of the remaining residual; also retain the trend-only baseline MAD | makes “periodic part plus leftover noise” measurable and preserves a no-cycle comparator |
| MAD buffer multiplier | do not select one in P23-1; later compare versioned `lambda` candidates on frozen historical data and require a separate P23-2 user decision | the multiplier changes reversal frequency and therefore is a trading decision, not an engineering default |
| Numeric semantics | float64 calculation; exact input Decimal text; persisted IEEE-754 hex plus query/display value; exact underlying comparisons for 15%/30%/20%; replay tolerances do not alter classification | gives reproducibility without classifying rounded GUI text |
| Warm-up/outliers | exactly `W` complete expected sessions per window; no extra warm-up, filling, winsorizing or silent clipping; suspicious observations remain visible evidence | avoids hiding real moves or inventing a new outlier policy |
| Engineering shape | specialized immutable typed evidence, additive future Schema v14 tables, read-only Factor Laboratory/Run History views and disabled registration | the current scalar `FactorResult` cannot truthfully hold a complete spectrum and must not be broken or overloaded |

The 80% competing-peak threshold, exact cross-window rule, diagnostic gate and amplitude conversion are approved design semantics and are implemented only in the disabled P23-1 R1 research component under PROPOSAL-024. Downstream interpretation remains unapproved.

### R1.1 Market-session and availability contract

#### Calendar definition

The first candidate should define:

```text
calendar_definition_id = US_EQUITIES_REGULAR_V1
calendar_engine = exchange_calendars
calendar_name = XNYS
supported_asset_class = US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING
```

`XNYS` is recommended here as the maintained common regular-session schedule used for the first U.S.-equity research definition. The symbol mapping must say `US_EQUITIES_REGULAR_V1`; it must not falsely label every Nasdaq-listed symbol as a New York Stock Exchange listing. A symbol without an explicit supported mapping returns `UNSUPPORTED_MARKET_CALENDAR`; there is no universal-symbol fallback.

Every calculation binds:

- dependency name and exact installed version;
- calendar name and definition version;
- covered first/last session;
- canonical session date/open/close/break/early-close rows;
- SHA-256 fingerprint of those canonical rows;
- symbol-to-calendar mapping version; and
- the exact expected sessions used by each window.

A calendar correction creates a new immutable calendar snapshot and a new Run. It never edits the calendar evidence of an old result.

#### Completed and available Daily observations

For one Daily Bar:

```text
completed_at_utc = official close of its exchange session
available_at_utc = max(completed_at_utc, first_observed_at_utc)
```

`first_observed_at_utc` is an immutable ingestion fact, not the timestamp of a later cache read. A Daily Bar from session `D` is never eligible for a Decision or simulated fill in session `D`; the earliest potential consumer is the next recognized session. A historical Bar first downloaded months later remains retrospective even though its market timestamp is old.

Expected session with no required Bar produces `DATA_INCOMPLETE_EXPECTED_SESSION` for every containing window. A holiday/recognized closure consumes no observation index and is not missing. An early-close Daily Bar is complete at that session's official early close.

### R1.2 Split and corporate-action provenance

The existing Alpaca Market Data adapter remains the source of raw and split-adjusted bars. Candidate 1 requests both the exact raw series and `adjustment=split` series with the same symbol, feed, timeframe and interval. It also snapshots the related Alpaca corporate-action response, including provider event ID, action type, declaration/effective dates, ratio fields available from the provider, response receipt time and response fingerprint.

The `StockBarsRequest.asof` symbol-identity date must not be mislabeled as “information known as of.” The corporate-action request can filter events and IDs, but it does not by itself prove when an old run knew a later correction. Therefore each input bundle has one evidence mode:

- `POINT_IN_TIME_OBSERVED`: the application immutably captured all required Bar and split evidence no later than the Run's `as_of_utc`;
- `RETROSPECTIVE_ADJUSTED`: the application fetched or reconstructed some adjustment evidence later; valid for labeled research comparison only;
- `UNVERIFIED_ADJUSTMENT`: source events, ratios, identities or raw/adjusted consistency cannot be verified; the containing window is invalid.

The adjusted/raw price-ratio sequence must be piecewise consistent with the frozen split/reverse-split events. A mismatch returns `ADJUSTMENT_RECONCILIATION_FAILED`; it is never repaired silently.

Candidate 1 behavior for other actions:

- cash/stock dividend: no price adjustment, preserve `DIVIDEND_PRESENT_UNADJUSTED` warning and exact event evidence;
- spin-off, merger, symbol change, liquidation or other price/identity-changing reorganization crossing the window: `UNSUPPORTED_CORPORATE_ACTION`, invalid window;
- provider correction: new snapshot and new Run, never overwrite old evidence.

### R1.3 Exact baseline and spectral calculation

For each valid window `W in {60,120,250}`:

1. Convert the approved split-adjusted positive close to `p_t = ln(close_t)`.
2. Fit the already-approved unweighted trailing line `p_hat_t = alpha + beta*t`, `t=0..W-1`.
3. Preserve `p_t`, `p_hat_t` and detrended `x_t = p_t-p_hat_t`.
4. Baseline return residual is `b_t=x_t-x_(t-1)`.
5. Baseline raw MAD is `median(abs(b_t-median(b)))`; standardized baseline MAD is `1.4826*raw_mad`.
6. Calculate the already-approved two-segment Welch evidence exactly as planning revision 1.23 specifies.

No segment is detrended again after the parent-window least-squares removal. Candidate 1 applies no additional spectrum smoother, median filter, kernel or peak interpolation.

The implementation recommendation is one explicit project-owned numeric engine backed by a direct bounded NumPy dependency:

```text
FFT operation = numpy.fft.rfft
frequency grid = numpy.fft.rfftfreq
input dtype = float64
forward norm = backward / unscaled
```

The project formula, not a library's default Welch helper, remains authoritative. Tests must compare small arrays against a direct discrete-Fourier reference and reproduce the approved periodic-Hann coefficients, coherent-gain correction, one-sided mapping and padding rules. NumPy, Python, operating-system, processor/FFT configuration, software version and worktree identity are persisted. SciPy may be used as a documentation/reference oracle during development but is not recommended as a runtime dependency.

### R1.4 Ties, plateaus and multiple comparable peaks

For a valid nonzero eligible-power spectrum:

1. Compute all powers with float64 and persist their exact bit patterns.
2. Let `P_max` be the largest eligible-bin power.
3. A bin is numerically tied with the maximum when:

   ```text
   abs(P[k]-P_max) <= 8*ulp(P_max)
   ```

4. More than one tied strongest bin returns `TIED_STRONGEST_BINS`; preserve every tied bin and publish no single candidate period or dominance class.
5. Otherwise use the already-approved unique center and five-bin eligible neighborhood.
6. Find other eligible local maxima whose effective five-bin neighborhoods do not overlap the primary neighborhood. Preserve every competitor's center, period, members, power and dominance.
7. If the strongest disjoint competitor satisfies:

   ```text
   D_competitor / D_primary >= 0.80
   ```

   return `MULTIPLE_COMPARABLE_PEAKS`, preserve both rhythms and publish no single stable cycle. Exactly 80% is comparable.
8. A weaker competitor remains visible diagnostic evidence but does not replace the primary center.

The 80% rule is a conservative proposed ambiguity gate, not a universal scientific constant. Before later state use, sensitivity at 70%, 80% and 90% should be compared on frozen synthetic and historical research runs. Candidate 1 should not add smoothing because that would silently redefine both the peak and the approved 15%/30% dominance thresholds.

### R1.5 Full-window Fourier diagnostic and method agreement

For each valid parent window, the diagnostic uses:

- the same detrended `x_t`;
- periodic Hann `w[n]=0.5-0.5*cos(2*pi*n/W)` over all `W` observations;
- `N_fft=W` with no padding;
- the same one-sided coherent-gain-corrected squared-magnitude formula;
- the same exact eligible bins, five-bin neighborhood, dominance boundaries, tie and multiple-peak rules.

This keeps the frequency grid and scaling comparable and changes only the intended estimator structure: Welch averages two overlapping views, while the diagnostic examines the whole window once.

For a window to become cross-window-eligible:

1. Welch must have one `CANDIDATE` or `STRONG` peak.
2. Full-window Fourier must independently have one `CANDIDATE` or `STRONG` peak.
3. Their center periods must satisfy:

   ```text
   method_delta = 2*abs(T_welch-T_fourier)/(T_welch+T_fourier)
   method_delta <= 0.20
   ```

If all three hold, `method_comparison_status=AGREES`. A weak, tied, multiple, invalid or unavailable diagnostic yields its exact visible status and prevents stable classification. Two valid dominant but period-incompatible methods yield `METHOD_DISAGREEMENT`. The underlying Welch evidence remains stored in every case.

### R1.6 Cross-window 20% support and representative period

Only method-agreed windows with a Welch `CANDIDATE` or `STRONG` class enter this step. For every pair:

```text
pair_delta(a,b) = 2*abs(T_a-T_b)/(T_a+T_b)
pair_supports = pair_delta <= 0.20
```

Exactly 20% supports. All operands, unrounded delta and Boolean result are stored.

The support rule is:

- fewer than two eligible windows: `INSUFFICIENT_QUALIFIED_WINDOWS`;
- exactly one supporting pair: stable two-window evidence;
- all three pairs support: stable three-window evidence;
- two overlapping supporting pairs but the endpoint pair fails: `AMBIGUOUS_CROSS_WINDOW_SUPPORT`, not stable;
- no supporting pair: `NO_CROSS_WINDOW_SUPPORT`.

This pairwise-clique rule prevents a chain such as 60-day close to 120-day and 120-day close to 250-day, but 60-day not close to 250-day, from being reported as one coherent period.

For one unambiguous supporting set, the displayed representative period is derived by averaging frequency rather than period:

```text
f_consensus = sum(D_i*f_i)/sum(D_i)
T_consensus = 1/f_consensus
```

where `D_i` is each member's Welch neighborhood dominance. All member periods remain authoritative evidence; `T_consensus` is a research summary, not a state threshold.

### R1.7 Exact amplitude conversion

Under the approved one-sided spectrum, a bin-centered pure sine with log-price half-amplitude `a` has one-sided power `a^2/2`. Therefore the Welch neighborhood's recommended equivalent amplitude is:

```text
a_log = sqrt(2*P_neighborhood)
```

Because the two segment spectra were power-averaged, this is named `equivalent_log_half_amplitude`, not an observed or guaranteed excursion.

Persist all of these non-interchangeable views:

```text
log_half_amplitude                 = a_log
log_peak_to_trough_span            = 2*a_log
trend_to_upper_price_fraction      = exp(a_log)-1
trend_to_lower_price_fraction      = 1-exp(-a_log)
trend_center_relative_full_span    = exp(a_log)-exp(-a_log)
trough_to_peak_return_fraction     = exp(2*a_log)-1
```

No GUI may label all of them simply “波动百分比.” Each label must identify its denominator. The full-window diagnostic stores the same set from its own power. A later state policy must explicitly select a versioned representation; P23-1 selects none.

### R1.8 Periodic fit, residual MAD and later buffer calibration

When one window has method-agreed unique frequency `f*`, fit phase over the full detrended window:

```text
x_t = A_s*sin(2*pi*f* t) + A_c*cos(2*pi*f* t) + q_t
```

using unweighted least squares. Preserve coefficients, fitted periodic component and residual `q_t`. The cycle-removed daily log-return residual is:

```text
e_t = q_t-q_(t-1)
```

Store `median(e)`, raw MAD and exact `1.4826` standardized MAD. Also retain the trend-only baseline `b_t` MAD. The power-derived amplitude remains authoritative for the spectral-amplitude field; the regression amplitude/phase are separate fit diagnostics and cannot silently replace it.

`raw_mad=0` is valid evidence with `ZERO_RESIDUAL_MAD`; Factor applies no artificial floor. A later reversal policy may require a minimum price/tick/cost-aware scale, but that belongs to P23-2/Risk and needs separate approval.

P23-1 must not hard-code the periodic-plus-MAD multiplier. The recommended historical calibration protocol is:

1. preserve amplitude and MAD components separately;
2. create immutable research definitions for `lambda in {0,0.5,1,1.5,2,2.5,3}`;
3. evaluate each on identical frozen data with no trading activation;
4. report false reversal candidates, missed/late confirmed turns, time in reversal watch, turnover proxy and regime sensitivity;
5. select no winner automatically; user approval creates a later exact P23-2 definition version.

Wavelet comparison is deferred to its own later research proposal after the Welch/baseline evidence contracts are stable. It is not a blocker for P23-1.

### R1.9 Numeric, rounding and failure semantics

#### Numeric representation

- Original market prices and ratios remain their exact Decimal text.
- Log, least-squares, FFT and trigonometric calculations use float64 arrays.
- Each persisted calculation scalar has a queryable SQLite REAL value, exact IEEE-754 hexadecimal representation and display unit.
- Core vector/point evidence preserves ordered index plus float value/hex; display formatting is separate.
- `math.fsum` is used for power/share sums.
- 15%, 30% and 20% classification uses the unrounded underlying float and exact approved `<`/`<=` direction. No display rounding or replay tolerance changes a class.
- Same-environment replay requires identical statuses/classes and exact source fingerprints. Numeric comparison permits `rtol=1e-12`, `atol=1e-15`; a class/status difference is a replay failure even if scalar values are close.
- NaN, infinity, negative power, non-positive adjusted price or non-finite intermediate output fails visibly. Power/share values are not silently clipped into a legal range.

#### Separate status dimensions

Do not overload one generic status with calculation, interpretation and warning meaning:

```text
WindowCalculationStatus:
  VALID
  INSUFFICIENT_OBSERVATIONS
  DATA_INCOMPLETE_EXPECTED_SESSION
  UNSUPPORTED_MARKET_CALENDAR
  INVALID_CALENDAR_EVIDENCE
  INVALID_ADJUSTMENT_EVIDENCE
  ADJUSTMENT_RECONCILIATION_FAILED
  UNSUPPORTED_CORPORATE_ACTION
  INVALID_PRICE
  INVALID_SEGMENT
  NONFINITE_CALCULATION

RelativeShareStatus:
  VALID
  ZERO_ELIGIBLE_POWER
  NOT_CALCULATED

PeakStatus:
  UNIQUE
  TIED_STRONGEST_BINS
  MULTIPLE_COMPARABLE_PEAKS
  NOT_AVAILABLE

MethodComparisonStatus:
  AGREES
  METHOD_DISAGREEMENT
  DIAGNOSTIC_WEAK
  DIAGNOSTIC_AMBIGUOUS
  DIAGNOSTIC_UNAVAILABLE
  NOT_APPLICABLE

CrossWindowStatus:
  STABLE_TWO_WINDOWS
  STABLE_THREE_WINDOWS
  INSUFFICIENT_QUALIFIED_WINDOWS
  AMBIGUOUS_CROSS_WINDOW_SUPPORT
  NO_CROSS_WINDOW_SUPPORT
```

Warnings such as `DIVIDEND_PRESENT_UNADJUSTED`, `RETROSPECTIVE_ADJUSTED`, eligible-edge truncation and weaker competing peaks remain separate arrays. Invalid and no-stable results are persisted, searchable and reloadable.

Each window requires exactly `W` completed expected sessions. No extra warm-up is recommended. P23-1 does not interpolate, skip, winsorize, cap, replace or delete outliers. It exposes the largest residual observations and their source IDs for inspection.

### R1.10 Typed contracts and owner boundaries

The current generic scalar `FactorResult` remains backward-compatible and unchanged. P23-1 should add specialized Factor-owned public evidence rather than a nested arbitrary dictionary:

- `SpectralVolatilityDefinition@1`
- `SpectralVolatilityOperation@1`
- `SpectralMarketEvidenceBundle@1`
- `SpectralWindowEvidence@1`
- `SpectralSegmentEvidence@1`
- `SpectrumBinEvidence@1`
- `PeakNeighborhoodEvidence@1`
- `FullWindowDiagnosticEvidence@1`
- `MethodComparisonEvidence@1`
- `CrossWindowStabilityEvidence@1`
- `SpectralAmplitudeEvidence@1`
- `ResidualScaleEvidence@1`

Ownership remains:

```text
Market History public adapter
  -> immutable Bar/calendar/corporate-action evidence
Factors pure engine
  -> typed spectral results; no SQL, GUI, State, Decision or Risk
Orchestration
  -> Run/stage lifecycle and Request ID
Persistence
  -> exact typed evidence storage/reload
Run History / Factor Laboratory
  -> read-only search, display, comparison, export and Open Run
```

The component is registered `DISABLED`, `execution_allowed=false`, `live_allowed=false`; it has no Pipeline/Decision/State consumer.

### R1.11 Future central SQLite v13-to-v14 design

The recommended migration is additive and specialized. Exact DDL remains part of a later implementation-admission review. The logical tables should cover:

- immutable spectral definitions and operations;
- frozen market-calendar snapshots and symbol mappings;
- frozen corporate-action/adjustment snapshots;
- exact source-observation links;
- per-window and per-segment status/evidence;
- ordered calculation-series points;
- Welch and diagnostic spectrum bins;
- peak-neighborhood members/competitors;
- amplitude/residual-scale results;
- method comparisons and cross-window pair/support results.

Core numeric/status/lineage fields must be structured columns or ordered child rows, not one opaque explanation JSON. Optional human-readable summaries may be JSON/text but cannot replace typed evidence.

Migration admission must provide:

1. central database backup and backup verification;
2. transactional v13-to-v14 upgrade with no destructive table changes;
3. pre/post row counts for all v13 tables;
4. `PRAGMA foreign_key_check`, `integrity_check`, table/column/index completeness and Schema-version checks;
5. empty/new-database plus populated-v13 migration tests;
6. restart/reload and immutable-rerun tests;
7. failure rollback to the verified backup; and
8. no reverse deletion of historical v14 results merely to run old code.

### R1.12 Factor Laboratory and Run History inspection

The GUI is a read-only controller/view over public services. Recommended views:

- Summary: Run, symbol, as-of, definition/config/software versions, overall status, eligible windows and representative period.
- Data provenance: raw/split-adjusted prices, expected/actual sessions, early closures, first-observed times, calendar and corporate-action fingerprints, point-in-time/retrospective label.
- Window evidence: 60/120/250 status, OLS coefficients, baseline MAD, Welch/diagnostic candidates, dominance and method comparison.
- Spectrum: selectable actual power or eligible share; separate leading/trailing/average Welch and full-window diagnostic lines; eligible bins, primary five-bin neighborhood, truncation, ties and competitor peaks.
- Amplitude/residual: every named log/price amplitude representation, periodic fit, trend-only and cycle-removed MAD.
- Cross-window support: exact pair deltas, clique/ambiguity result and consensus formula inputs.
- Errors/warnings: filterable status/error codes with source IDs and Request ID.
- History/compare/export: symbol, date, definition, status, warnings and evidence-mode filters; exact-version side-by-side comparison; structured CSV/JSON export; `Open Run`.

The GUI must not fetch Alpaca data directly, calculate FFT/MAD, classify peaks or decide which version is active.

### R1.13 Validation matrix and staged delivery

#### Required deterministic tests

- exact periodic-Hann sequences for `N=40/80/167`;
- direct DFT versus NumPy FFT on small known arrays;
- bin-centered and off-bin synthetic sine recovery for each window;
- trend-only, constant, white-noise and zero-eligible-power controls;
- two comparable separated rhythms, tied/plateau maxima and weaker competitor;
- exact 15%/30%/80%/20% boundaries and just-below/above cases;
- eligible-edge five-bin truncation;
- exact amplitude recovery for known log sine and all price-domain conversions;
- baseline versus cycle-removed MAD, extreme observation and zero MAD;
- normal session, holiday, early close, temporary closure and unsupported mapping;
- missing expected Bar, insufficient history and repaired-data new Run;
- forward/reverse split with no false crash, raw/adjusted mismatch, dividend warning and unsupported reorganization;
- point-in-time versus retrospective evidence;
- Welch/Fourier agree, period-disagree, weak, tied, multiple and unavailable cases;
- two-window, three-window, chain-ambiguous and no-support cross-window cases;
- same-input repeat/reload, failure persistence and classification-preserving replay.

#### Staged implementation recommendation

1. `P23-1A`: pure typed contracts, calendar/adjustment evidence adapters and fixtures; no spectral result or Schema migration.
2. `P23-1B`: pure baseline/Welch/diagnostic numeric engine against synthetic fixtures; no persistence/GUI/consumer.
3. `P23-1C`: orchestration plus additive central v13-to-v14 persistence/reload and Run evidence.
4. `P23-1D`: Factor Laboratory and Run History read-only inspection/export.
5. `P23-1E`: frozen historical comparison report only; no State/Decision/Risk linkage.

Each slice stays disabled, has its own tests/rollback and requires the relevant approval boundary. Wavelet, P23-2 state transitions, target positions, numerical Risk, Portfolio Accounting persistence, Paper and Live remain outside.

### R1.14 Change Impact Report and approval gate

- Primary future module: `factors`.
- Secondary future modules: `market_history`, `orchestration`, `persistence`, `run_history`, `algorithm_control`.
- Public contracts: new specialized typed spectral evidence; existing generic `FactorResult` remains unchanged.
- Dependencies: proposed direct bounded NumPy and `exchange_calendars`; no SciPy runtime dependency.
- Configuration: immutable disabled definition/config versions only; no active/default strategy.
- Database: proposed additive central Schema v14 after a separately reviewed migration.
- GUI: read-only Factor Laboratory/Run History views; no formula or provider access.
- Trading semantics: research evidence only; no reversal, position, Decision, Risk approval or execution.
- Permissions/safety: `DISABLED`, `execution_allowed=false`, `live_allowed=false`, no account/order client.
- Future blast radius: `MULTI_MODULE`; staged slices keep each implementation change `LIMITED`.
- Rollback: disable registration, restore pre-migration database backup where necessary, retain immutable old definitions/results and remove no v13 history.

Formal development can begin only after:

1. the R1 mathematical/data recommendations are accepted as planning revision `1.24` (**completed 2026-07-31**);
2. a scoped P23-1 implementation-admission proposal freezes exact dependency bounds, typed fields, status enums, DDL/migration and per-slice acceptance tests (**created as `PROPOSAL-024`**);
3. the user separately approves `PROPOSAL-024`, including the new dependencies, public contracts and central v13-to-v14 migration; and
4. implementation starts disabled and does not include downstream financial consumers.

## Compatibility and migration

- Backward compatibility: existing manual Standardized State, manual Asset State, Target Position, Decision and Risk results retain their exact old definitions and histories.
- Adapters required: future explicit result-to-result adapters among Factor, Asset State, Target Position, Decision and Risk; none is created now.
- Data/configuration migration: none now. Future schemas must be additive, versioned, backed up and tested from the current Schema v13.
- Old/new comparison method: compare the new model against exact existing/manual baseline definitions and across immutable candidate versions over the same completed data and snapshots.
- Prevention of duplicate runtime outputs/orders: future operation IDs, source-result IDs, cycle/event IDs and per-day count facts must make replay idempotent. Execution remains absent.

## Validation and activation

- Unit-test plan: reference-relative formula, positive volatility scale, per-symbol version binding, trailing-only Daily spectral inputs, split-adjusted calculation plus raw/split-event provenance, a synthetic split causing no fake crash, explicit no-dividend adjustment, invalid/missing adjustment evidence, no source-Bar mutation, log transformation, independent unweighted least-squares fits and coefficient/fitted-value/residual traces for exact 60/120/250 windows, exact chronological `0..n-1` mappings, versioned calendar binding, normal sessions/holidays/temporary closures/early closes, no Monday-through-Friday fallback, weekends/recognized closures consuming no index, source dates remaining preserved, no future/cross-window/reweighted fit, a missing expected session invalidating only containing windows, no interpolation/fill/skip, unaffected-window calculation, immutable failure then repaired-input rerun, distinct data-incomplete versus no-stable-cycle states, 4-to-window/3 period eligibility, known synthetic frequency recovery, Welch-primary and full-window-Fourier-diagnostic role preservation, exactly two leading/trailing Welch segments, exact 60-day 40/20, 120-day 80/40 and 250-day `0..166`/`83..249`/84-overlap layouts, exact periodic-Hann formula for `N=40/80/167`, all `n -> w[n]` mappings and weighted values retained, any implementation/library reproducing the approved coefficients, exact trailing-zero ranges and `FFT_PADDING_ONLY` labels, exact `N_fft=60/120/250`, no padding in Hann/coherent-gain sums, `f[k]=k/W` and `T[k]=W/k`, `k=0` exclusion, inclusive eligibility and exact `3..15`/`3..30`/`3..62` sets, 250-day `k=62` inclusion/`k=63` exclusion, full unpadded/padded/grid evidence and no added-information/resolution claim, raw complex FFT and squared magnitude preservation, exact `C_w=abs(sum(w))^2`, corrected `abs(Y[k])^2/C_w`, even one-sided mirror rules, DC/Nyquist non-doubling, squared-input units and explicit non-density meaning, exact bin-by-bin equal arithmetic mean of the leading/trailing power spectra, both individual spectra and the averaged spectrum retained, no recency/quality weighting, either segment invalidating the containing window, no one-segment average fallback, segment/window failure evidence retained, other independent windows remaining calculable, calculation failure distinct from valid no-stable-cycle evidence, simultaneous actual-power and eligible-range relative-share spectra, exact `S_welch[k]` division by eligible power, valid relative shares summing to one within numeric tolerance, actual power retained for amplitude research, relative share used for dominance, neither view replacing the other, zero eligible power preserving actual power but producing `ZERO_ELIGIBLE_POWER`, no percentage vector and no 15%/30% class, zero eligible power distinct from calculation error/invalid segment/stable-or-no-stable-cycle outcome, unique strongest-bin center selection, exact five requested bins, eligible-only intersection, no wrapping or invented edge zeros, member contribution retention, exact actual-power/share sums, candidate period staying at `T[k*]`, correct edge-truncation flag and omitted-bin evidence, exact `0.15`/`0.30` boundary tests including just-below/equal/just-above values, exactly 15% as `CANDIDATE`, exactly 30% as `STRONG`, undefined neighborhood share producing no class, no display-rounded classification, no implicit smoothing/weighted-center/tie break/amplitude conversion or full-window-Fourier window, both methods and settings retained, agreement permitting only otherwise-qualified stability, disagreement producing a warning and preventing forced stability, 20% peer-window boundaries, weak/no-peak and insufficient-data states, exact residual median/raw-MAD calculation, exact `raw_mad * 1.4826`, both values/constant preserved, extreme-observation robustness, zero-MAD without an implicit floor, absence of an implicit variant or threshold multiplier selection, simultaneous half/full amplitude preservation, periodic-plus-residual trace, no direct spectral trading output, threshold boundaries, day-1/day-2 old-cycle linear behavior, successful day-3 activation, reversal-extreme reference retention, confirmation-buffer attribution, failed-candidate discard without history loss, no retrospective action rewriting, cycle restart, freeze, missing data, duplicate observation, linear/accelerating exclusivity, curve continuity/bounds and target-reached idempotence.
- Integration-test plan: exact Market History → Factor → Asset State → Target Position → Decision → Risk lineage with persisted success/invalid/failure evidence and restart reload.
- Architecture-test plan: preserve owner/dependency rules; forbid GUI/Persistence from calculating strategy behavior; forbid Factor→State/Decision/Risk reverse dependencies; forbid Risk from increasing/reversing an intent; forbid Execution imports.
- Dry-run plan: inspect complete `NO_EXECUTION` chains with exact versions, intermediate values, state transitions and rejection reasons.
- Historical-simulation plan: compare non-spectral, Welch-primary/full-window-Fourier-diagnostic and later wavelet candidate definitions on identical fixed completed datasets without changing history; test synthetic known-period/no-period controls, Welch/Fourier agreement and disagreement, gaps, regime changes, unstable frequency peaks, volatile reversals, slow drift, oscillation near thresholds, saturation, freeze and daily-cap boundaries.
- Paper-validation plan: not included or approved.
- Manual activation approval: required after implementation, validation and historical evidence; no activation is implied.
- Live approval: Not requested.
- Evidence required for each state transition: separately approved scope, exact contracts/parameters, unit/integration/architecture tests, persisted replay evidence, documentation and explicit later admission.

## Rollback and deprecation

- Disable feature flag: every future component remains `REGISTERED`/`DISABLED` and excluded from active pipeline selection.
- Restore previous active configuration: no current active strategy configuration is changed.
- Restore previous component version: immutable prior definitions remain callable; a newer version never overwrites an older version.
- Restore contract adapter: remove the separately versioned adapter and continue using existing manual research paths.
- Reverse database migration: each future slice must provide its own tested backup/rollback plan.
- Deprecation replacement: old versions may be marked deprecated only through an audited configuration/version event; their historical results remain readable.
- Remaining callers/configurations: must be enumerated by each implementation slice.
- Removal conditions: only after no active configuration references the component and retained Run/replay evidence remains intact.

## Documentation impact

This planning task updates the Proposal index, Project Compass, Roadmap, Glossary and append-only Edit Log. Runtime architecture/module documents, Project State, CHANGELOG, database schema documentation and ADRs remain unchanged because no runtime behavior, contract, schema or accepted architecture decision changes.

## Research references for the approved candidate direction

- [NumPy real-input FFT](https://numpy.org/doc/stable/reference/generated/numpy.fft.rfft.html) defines the non-negative-frequency real-input transform shape and conventions proposed for the explicit P23-1 engine.
- [NumPy real FFT frequency grid](https://numpy.org/doc/stable/reference/generated/numpy.fft.rfftfreq.html) defines bin-center frequencies used to reproduce the approved `f[k]=k/W` grid.
- [NumPy DFT conventions](https://numpy.org/doc/stable/reference/routines.fft.html) documents the exact forward-transform sign, normalization, power and real-input symmetry conventions that future formula tests must bind.
- [SciPy Welch reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html) documents overlapping modified-periodogram averaging, periodic Hann defaults, one-sided output and spectrum scaling; P23-1 still recommends project-owned explicit formulas instead of calling defaults opaquely.
- [SciPy periodic Hann reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.hann.html) distinguishes the periodic spectral-analysis window from the symmetric filter-design window.
- [SciPy spectral-analysis guide](https://docs.scipy.org/doc/scipy/tutorial/signal.html) documents periodogram/Welch smoothing and frequency-resolution trade-offs used to frame the proposed comparison.
- [`exchange_calendars`](https://github.com/gerrymanoim/exchange_calendars) provides maintained exchange sessions, opens/closes, early closes and the `XNYS` calendar proposed for the first explicit U.S.-equity regular-session definition.
- [Alpaca stock Bar request](https://alpaca.markets/sdks/python/api_reference/data/stock/requests.html) exposes feed, adjustment and symbol-identity `asof` inputs; the recommendation does not misstate symbol `asof` as historical information availability.
- [Alpaca corporate-action request](https://alpaca.markets/sdks/python/api_reference/data/corporate_actions/requests.html) exposes symbol/type/date/event-ID queries used by the proposed frozen adjustment snapshot.
- [Alpaca corporate-action availability description](https://alpaca.markets/blog/introducing-corporate-actions-api-announcements/) explains ingestion timing and historical coverage, supporting the required distinction between locally observed point-in-time evidence and later retrospective backfill.
- [Alpaca spin-off adjustment change](https://docs.alpaca.markets/us/changelog/optionally-adjust-bars-after-spin-offs) shows that adjustment behavior can expand/change, supporting exact adjustment-mode/version preservation and fail-closed handling of unsupported actions.
- [Malliavin and Mancino, Fourier method for nonparametric multivariate volatility](https://arxiv.org/abs/0908.1890) shows that Fourier-based financial-volatility estimation is a real research family, while its continuous/high-frequency setting is not silently equated with the proposed daily rhythm Factor.
- [Dynamic wavelet thresholding for non-stationary signals](https://pmc.ncbi.nlm.nih.gov/articles/PMC10670265/) supports retaining a later time-localized comparison candidate for changing financial dynamics.
- [NIST measures of scale](https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm) supports MAD as a robust exploratory scale when tails/extreme observations make standard deviation less stable.

## Approval record

On 2026-07-27 the user explicitly approved the full design direction and asked that it be recorded as a development target and plan only. The approved target includes reference-relative price change, per-stock volatility ranges, small-move linear adjustment, finite accelerating established-regime adjustment, two completed trading-day reversal confirmation, linear-only operational behavior while confirmation is pending, new-cycle operational activation on day 3, a mathematical reference at the prior reversal extreme, successful attribution of confirmation-day observations to day-3 accelerating progress without retrospective action changes, failed-candidate attribution discard, a per-stock one-or-two-trades-per-day maximum, zero trading while frozen with continued observation, bounded target-position semantics and immutable algorithm/configuration versioning. The user subsequently approved researching rolling Fourier/Welch analysis as a Factor for rhythm/amplitude/stability/residual evidence under trailing-only, no-forced-cycle, no-direct-trading and baseline/wavelet-comparison boundaries, then approved the planning-revision-1.3 Daily/log/straight-line, 60/120/250-window, 4-to-window/3-period, two-window/20%-similarity, 15%/30%-dominance, MAD-residual and periodic-plus-residual combination direction. Planning revision 1.4 additionally preserves both half/full spectral amplitude and raw/standardized MAD evidence without selecting a downstream variant or multiplier. Planning revision 1.5 selects separate trailing unweighted least-squares straight-line trend fits for the three windows. On 2026-07-28 planning revision 1.6 selects chronological trading-observation index `0..n-1` as the horizontal coordinate while retaining exact dates. On 2026-07-29 planning revision 1.7 makes a known missing expected-session Bar fail visibly per affected window, forbids interpolation/skip, permits unaffected windows, preserves the failed result and requires a new Run after repair. Planning revision 1.8 requires formal versioned U.S. exchange-calendar evidence for sessions, holidays, temporary closures and early closes, while leaving the exact dependency/source and venue mapping unapproved. Planning revision 1.9 makes split-adjusted Daily close the first spectral candidate's calculation field, preserves raw/adjustment evidence and excludes dividend adjustment while leaving point-in-time split sourcing/revision semantics open. Planning revision 1.10 fixes raw MAD and exact `1.4826` standardization while explicitly leaving buffer/threshold multipliers unapproved. Planning revision 1.11 assigns Welch the primary period/dominance/stability evidence role, preserves full-window Fourier as a diagnostic cross-check, and requires a visible warning with no forced stable-cycle classification when their later-approved comparison reports disagreement. Planning revision 1.12 selects two leading/trailing long overlapping Welch segments and fixes the 60-day 40/20 and 120-day 80/40 layouts. Planning revision 1.13 resolves the 250-day layout as leading `0..166`, trailing `83..249`, 167 observations per segment and 84 observations of overlap. Planning revision 1.14 applies a versioned Hann window only to Welch segments and preserves the unmodified values, exact coefficients and weighted values. Planning revision 1.15 selects the exact periodic-Hann formula `w[n] = 0.5 - 0.5*cos(2*pi*n/N)` for `N=40/80/167` and preserves all coefficient mappings. Planning revision 1.16 fixes the Welch combination as the equal-weight bin-by-bin arithmetic mean of the leading/trailing power spectra and preserves both individual spectra and the average. Planning revision 1.17 invalidates the containing Welch window when either segment spectrum is invalid, forbids one-segment fallback, preserves segment/window failure evidence and permits other independent windows. Planning revision 1.18 preserves parallel actual-power and eligible-range relative-share spectra and assigns amplitude/dominance research roles. Planning revision 1.19 preserves valid actual power but emits `ZERO_ELIGIBLE_POWER` with no percentage/dominance output when eligible total power is zero. Planning revision 1.20 defines actual power as the Hann-coherent-gain-corrected one-sided squared-magnitude spectrum. Planning revision 1.21 fixes trailing zero-padding to parent-window `N_fft=60/120/250`, exact trading-observation frequency/period grids and inclusive eligible bins `3..15`, `3..30`, `3..62`, while forbidding any added-data/information/resolution claim. Planning revision 1.22 fixes the unique strongest-bin center and eligible-only five-bin neighborhood, sums both actual power and relative-share dominance, records every member and explicit edge truncation. Planning revision 1.23 fixes `[0,0.15)` as `WEAK`, `[0.15,0.30)` as `CANDIDATE` and `[0.30,1]` as `STRONG`, so exact 15% and 30% enter candidate and strong respectively while undefined neighborhood share has no class.

The same instruction explicitly says not to develop it now. Therefore `PROPOSAL-023` is not implementation authorization. No formula values, default parameters, code, schema, configuration, GUI, Backtesting integration, Paper/Live behavior, orders or activation are approved by this record.

On 2026-07-30 the user asked Codex to design and record complete recommended solutions for the remaining questions. `P23-1-R1` was initially recorded as an AI recommendation only. On 2026-07-31 the user explicitly approved that package, including its 80% multiple-peak rule, symmetric 20% equations, full-window diagnostic settings, amplitude conversion, residual fit, point-in-time/retrospective evidence semantics, numeric/status rules and staged disabled direction, as the P23-1 mathematical/data design baseline. This creates planning revision `1.24`.

The initial 2026-07-31 instruction authorized creation of `PROPOSAL-024` but did not pre-approve it. The user subsequently approved that proposal explicitly. P23-1A–D dependencies, public contracts, source, Schema v14 and read-only GUI were then implemented and verified. On 2026-08-02 the user separately approved PROPOSAL-025 and amendment B; the bounded P23-1E-A manual latest-session runner and immutable inclusive-window R1 v1.1.0 were implemented and verified. Full P23-1E comparison/scoring and every P23-2+ financial/trading capability remain unapproved; no trading capability was activated.
