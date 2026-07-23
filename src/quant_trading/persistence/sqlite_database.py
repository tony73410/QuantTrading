"""Central SQLite file management without feature-specific query logic."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path


SCHEMA_VERSION = 13


_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at_utc TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_bars (
    symbol TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    open TEXT NOT NULL,
    high TEXT NOT NULL,
    low TEXT NOT NULL,
    close TEXT NOT NULL,
    volume INTEGER NOT NULL CHECK (volume >= 0),
    vwap TEXT,
    trade_count INTEGER CHECK (trade_count IS NULL OR trade_count >= 0),
    source TEXT NOT NULL,
    fetched_at_utc TEXT NOT NULL,
    PRIMARY KEY (symbol, timestamp_utc, timeframe, adjustment, feed)
);

CREATE INDEX IF NOT EXISTS idx_market_bars_lookup
ON market_bars (symbol, timeframe, adjustment, feed, timestamp_utc);

CREATE TABLE IF NOT EXISTS data_coverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    coverage_start_utc TEXT NOT NULL,
    coverage_end_utc TEXT NOT NULL,
    last_successful_fetch_utc TEXT NOT NULL,
    CHECK (coverage_start_utc < coverage_end_utc),
    UNIQUE (
        symbol, timeframe, adjustment, feed,
        coverage_start_utc, coverage_end_utc
    )
);

CREATE INDEX IF NOT EXISTS idx_data_coverage_lookup
ON data_coverage (
    symbol, timeframe, adjustment, feed,
    coverage_start_utc, coverage_end_utc
);

CREATE TABLE IF NOT EXISTS fetch_history (
    request_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    requested_start_utc TEXT NOT NULL,
    requested_end_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL,
    rows_received INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_fetch_history_lookup
ON fetch_history (symbol, timeframe, adjustment, feed, started_at_utc);

CREATE TABLE IF NOT EXISTS factor_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    calculated_at_utc TEXT NOT NULL,
    source_data_start_utc TEXT,
    source_data_end_utc TEXT,
    configuration_fingerprint TEXT NOT NULL,
    source_data_fingerprint TEXT NOT NULL,
    content_fingerprint TEXT NOT NULL UNIQUE,
    schema_version INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    CHECK (
        (source_data_start_utc IS NULL AND source_data_end_utc IS NULL)
        OR
        (source_data_start_utc IS NOT NULL AND source_data_end_utc IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_factor_snapshots_lookup
ON factor_snapshots (
    symbol, timeframe, adjustment, feed, as_of_utc
);

CREATE TABLE IF NOT EXISTS factor_results (
    snapshot_id TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    factor_version TEXT NOT NULL,
    value_type TEXT,
    value_text TEXT,
    unit TEXT,
    parameters_json TEXT NOT NULL,
    lookback INTEGER,
    status TEXT NOT NULL,
    quality_flags_json TEXT NOT NULL,
    calculated_at_utc TEXT NOT NULL,
    source_data_start_utc TEXT,
    source_data_end_utc TEXT,
    PRIMARY KEY (snapshot_id, factor_name),
    FOREIGN KEY (snapshot_id) REFERENCES factor_snapshots(snapshot_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_factor_results_lookup
ON factor_results (factor_name, factor_version, snapshot_id);

CREATE TABLE IF NOT EXISTS factor_calculation_runs (
    run_id TEXT PRIMARY KEY,
    correlation_id TEXT,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL,
    snapshot_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES factor_snapshots(snapshot_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_factor_calculation_runs_lookup
ON factor_calculation_runs (symbol, timeframe, adjustment, feed, as_of_utc);
"""


_SCHEMA_V2 = """
CREATE TABLE algorithm_runs (
    run_id TEXT PRIMARY KEY,
    parent_run_id TEXT,
    run_type TEXT NOT NULL,
    status TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    market_data_as_of_utc TEXT,
    portfolio_snapshot_id TEXT,
    configuration_snapshot_id TEXT,
    strategy_version_id TEXT,
    trigger_source TEXT NOT NULL,
    execution_mode TEXT NOT NULL CHECK (execution_mode = 'no_execution'),
    created_by TEXT NOT NULL,
    software_version TEXT NOT NULL,
    source_revision TEXT,
    worktree_state TEXT NOT NULL,
    notes TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    CHECK (
        (status IN ('pending', 'running') AND completed_at_utc IS NULL)
        OR
        (status NOT IN ('pending', 'running') AND completed_at_utc IS NOT NULL)
    )
);

CREATE INDEX idx_algorithm_runs_list
ON algorithm_runs (started_at_utc DESC, run_type, status);
CREATE INDEX idx_algorithm_runs_request
ON algorithm_runs (session_id, request_id);

CREATE TABLE algorithm_run_symbols (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    PRIMARY KEY (run_id, symbol),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT
);

CREATE INDEX idx_algorithm_run_symbols_symbol
ON algorithm_run_symbols (symbol, run_id);

CREATE TABLE algorithm_run_bindings (
    binding_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    binding_type TEXT NOT NULL,
    binding_key TEXT NOT NULL,
    binding_version TEXT,
    source_reference TEXT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    UNIQUE (run_id, binding_type, binding_key, binding_version)
);

CREATE INDEX idx_algorithm_run_bindings_run
ON algorithm_run_bindings (run_id, binding_type);

CREATE TABLE algorithm_run_stages (
    stage_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_name TEXT NOT NULL,
    sequence INTEGER NOT NULL CHECK (sequence > 0),
    status TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    result_type TEXT,
    result_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    UNIQUE (run_id, sequence),
    CHECK (
        (status IN ('pending', 'running') AND completed_at_utc IS NULL)
        OR
        (status NOT IN ('pending', 'running') AND completed_at_utc IS NOT NULL)
    )
);

CREATE INDEX idx_algorithm_run_stages_run
ON algorithm_run_stages (run_id, sequence);

CREATE TABLE algorithm_run_messages (
    message_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_id TEXT,
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT
);

CREATE INDEX idx_algorithm_run_messages_run
ON algorithm_run_messages (run_id, severity, created_at_utc);

CREATE TABLE decision_results (
    decision_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    policy_parameters_json TEXT NOT NULL,
    status TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT
);

CREATE INDEX idx_decision_results_run
ON decision_results (run_id, as_of_utc, status);

CREATE TABLE decision_factor_snapshots (
    decision_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    PRIMARY KEY (decision_id, snapshot_id),
    FOREIGN KEY (decision_id) REFERENCES decision_results(decision_id) ON DELETE RESTRICT,
    FOREIGN KEY (snapshot_id) REFERENCES factor_snapshots(snapshot_id) ON DELETE RESTRICT
);

CREATE TABLE trade_intents (
    intent_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    action TEXT NOT NULL,
    current_exposure TEXT,
    target_exposure TEXT,
    desired_change TEXT,
    exposure_unit TEXT,
    confidence TEXT,
    reason_codes_json TEXT NOT NULL,
    factor_snapshot_id TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    requested_notional TEXT,
    notional_currency TEXT,
    sizing_mode TEXT,
    sizing_expression TEXT,
    sizing_references_json TEXT NOT NULL,
    FOREIGN KEY (decision_id) REFERENCES decision_results(decision_id) ON DELETE RESTRICT,
    FOREIGN KEY (factor_snapshot_id) REFERENCES factor_snapshots(snapshot_id) ON DELETE RESTRICT
);

CREATE INDEX idx_trade_intents_decision
ON trade_intents (decision_id, symbol, action);

CREATE TABLE risk_decisions (
    risk_decision_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    source_trade_intent_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    evaluated_at_utc TEXT NOT NULL,
    decision TEXT NOT NULL,
    current_exposure TEXT,
    original_target TEXT,
    approved_target TEXT,
    original_quantity TEXT,
    approved_quantity TEXT,
    exposure_unit TEXT,
    risk_status TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    requires_manual_review INTEGER NOT NULL,
    system_paused INTEGER NOT NULL,
    symbol_paused INTEGER NOT NULL,
    risk_policy_name TEXT NOT NULL,
    risk_policy_version TEXT NOT NULL,
    configuration_version TEXT NOT NULL,
    portfolio_snapshot_id TEXT NOT NULL,
    account_snapshot_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    earliest_execution_utc TEXT,
    original_notional TEXT,
    approved_notional TEXT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_trade_intent_id) REFERENCES trade_intents(intent_id) ON DELETE RESTRICT
);

CREATE INDEX idx_risk_decisions_run
ON risk_decisions (run_id, symbol, decision, evaluated_at_utc);

CREATE TABLE risk_rule_results (
    risk_decision_id TEXT NOT NULL,
    evaluation_order INTEGER NOT NULL CHECK (evaluation_order >= 0),
    rule_name TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    approved_target TEXT,
    approved_quantity TEXT,
    approved_notional TEXT,
    warnings_json TEXT NOT NULL,
    earliest_execution_utc TEXT,
    PRIMARY KEY (risk_decision_id, evaluation_order),
    FOREIGN KEY (risk_decision_id) REFERENCES risk_decisions(risk_decision_id) ON DELETE RESTRICT
);

ALTER TABLE factor_calculation_runs
ADD COLUMN algorithm_run_id TEXT REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT;

ALTER TABLE factor_calculation_runs
ADD COLUMN stage_id TEXT REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT;

CREATE INDEX idx_factor_calculation_runs_algorithm_run
ON factor_calculation_runs (algorithm_run_id, stage_id);
"""


_SCHEMA_V3 = """
ALTER TABLE decision_results
ADD COLUMN trace_status TEXT NOT NULL DEFAULT 'trace_not_captured'
    CHECK (trace_status IN ('captured', 'not_evaluated', 'trace_not_captured'));

CREATE TABLE decision_condition_results (
    decision_id TEXT NOT NULL,
    evaluation_order INTEGER NOT NULL CHECK (evaluation_order >= 0),
    factor_component_id TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    factor_version TEXT NOT NULL,
    factor_snapshot_id TEXT NOT NULL,
    input_value TEXT NOT NULL,
    input_unit TEXT,
    factor_status TEXT NOT NULL,
    operator TEXT NOT NULL CHECK (operator IN ('<', '<=', '==', '>=', '>')),
    threshold TEXT NOT NULL,
    matched INTEGER NOT NULL CHECK (matched IN (0, 1)),
    PRIMARY KEY (decision_id, evaluation_order),
    FOREIGN KEY (decision_id) REFERENCES decision_results(decision_id) ON DELETE RESTRICT,
    FOREIGN KEY (factor_snapshot_id) REFERENCES factor_snapshots(snapshot_id) ON DELETE RESTRICT
);

CREATE INDEX idx_decision_condition_factor
ON decision_condition_results (factor_name, factor_version, matched, decision_id);

CREATE TABLE trade_intent_sizing_inputs (
    intent_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    source_group TEXT NOT NULL CHECK (source_group IN ('asset', 'market', 'account', 'position')),
    input_name TEXT NOT NULL,
    value_text TEXT NOT NULL,
    PRIMARY KEY (intent_id, ordinal),
    FOREIGN KEY (intent_id) REFERENCES trade_intents(intent_id) ON DELETE RESTRICT,
    UNIQUE (intent_id, input_name)
);

CREATE INDEX idx_trade_intent_sizing_inputs_intent
ON trade_intent_sizing_inputs (intent_id, source_group);

CREATE INDEX idx_factor_history_research
ON factor_calculation_runs (symbol, as_of_utc DESC, status, algorithm_run_id);

CREATE INDEX idx_decision_history_research
ON decision_results (policy_name, policy_version, as_of_utc DESC, status, trace_status);
"""


_SCHEMA_V4 = """
CREATE TABLE capital_plans (
    plan_id TEXT PRIMARY KEY,
    plan_version INTEGER NOT NULL CHECK (plan_version > 0),
    predecessor_plan_id TEXT,
    name TEXT NOT NULL,
    reason TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    account_cash_basis TEXT NOT NULL,
    basis_source TEXT NOT NULL CHECK (basis_source = 'research_input'),
    source_snapshot_id TEXT,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (predecessor_plan_id) REFERENCES capital_plans(plan_id)
        ON DELETE RESTRICT,
    CHECK (source_snapshot_id IS NULL)
);

CREATE INDEX idx_capital_plans_list
ON capital_plans (created_at_utc DESC, name, plan_version);

CREATE TABLE capital_plan_buckets (
    bucket_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    bucket_type TEXT NOT NULL CHECK (
        bucket_type IN ('locked_reserve', 'tactical_reserve', 'asset_cash')
    ),
    symbol TEXT,
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    initial_balance TEXT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES capital_plans(plan_id) ON DELETE RESTRICT,
    CHECK (
        (bucket_type = 'asset_cash' AND symbol IS NOT NULL AND symbol <> '')
        OR
        (bucket_type <> 'asset_cash' AND symbol IS NULL)
    )
);

CREATE UNIQUE INDEX uq_capital_plan_locked_reserve
ON capital_plan_buckets (plan_id)
WHERE bucket_type = 'locked_reserve';

CREATE UNIQUE INDEX uq_capital_plan_tactical_reserve
ON capital_plan_buckets (plan_id)
WHERE bucket_type = 'tactical_reserve';

CREATE UNIQUE INDEX uq_capital_plan_asset_symbol
ON capital_plan_buckets (plan_id, symbol)
WHERE bucket_type = 'asset_cash';

CREATE INDEX idx_capital_plan_buckets_plan
ON capital_plan_buckets (plan_id, bucket_type, symbol);

CREATE TABLE capital_allocation_transfers (
    transfer_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    source_bucket_id TEXT NOT NULL,
    destination_bucket_id TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    reason TEXT NOT NULL,
    occurred_at_utc TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    validation_status TEXT NOT NULL CHECK (validation_status = 'accepted'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (plan_id) REFERENCES capital_plans(plan_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_bucket_id) REFERENCES capital_plan_buckets(bucket_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (destination_bucket_id) REFERENCES capital_plan_buckets(bucket_id)
        ON DELETE RESTRICT,
    CHECK (source_bucket_id <> destination_bucket_id)
);

CREATE INDEX idx_capital_transfers_plan
ON capital_allocation_transfers (plan_id, occurred_at_utc, transfer_id);

CREATE TABLE capital_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    sequence INTEGER NOT NULL CHECK (sequence >= 0),
    run_id TEXT NOT NULL,
    predecessor_snapshot_id TEXT,
    causal_transfer_id TEXT,
    created_at_utc TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    expected_total TEXT NOT NULL,
    actual_total TEXT NOT NULL,
    difference TEXT NOT NULL,
    conservation_status TEXT NOT NULL CHECK (conservation_status = 'valid'),
    conservation_summary TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (plan_id) REFERENCES capital_plans(plan_id) ON DELETE RESTRICT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (predecessor_snapshot_id) REFERENCES capital_snapshots(snapshot_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (causal_transfer_id) REFERENCES capital_allocation_transfers(transfer_id)
        ON DELETE RESTRICT,
    UNIQUE (plan_id, sequence),
    CHECK (
        (sequence = 0 AND predecessor_snapshot_id IS NULL AND causal_transfer_id IS NULL)
        OR
        (sequence > 0 AND predecessor_snapshot_id IS NOT NULL AND causal_transfer_id IS NOT NULL)
    )
);

CREATE INDEX idx_capital_snapshots_plan
ON capital_snapshots (plan_id, sequence DESC);

CREATE TABLE capital_snapshot_balances (
    snapshot_id TEXT NOT NULL,
    bucket_id TEXT NOT NULL,
    balance TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, bucket_id),
    FOREIGN KEY (snapshot_id) REFERENCES capital_snapshots(snapshot_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (bucket_id) REFERENCES capital_plan_buckets(bucket_id)
        ON DELETE RESTRICT
);

CREATE TABLE capital_allocation_operations (
    operation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (
        operation_type IN ('plan_create', 'transfer')
    ),
    status TEXT NOT NULL CHECK (
        status IN ('completed', 'invalid_input', 'failed')
    ),
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    currency TEXT NOT NULL,
    reason TEXT NOT NULL,
    requested_plan_id TEXT,
    resolved_plan_id TEXT,
    result_snapshot_id TEXT,
    transfer_id TEXT,
    plan_name TEXT,
    account_cash_basis_text TEXT,
    locked_reserve_text TEXT,
    tactical_reserve_text TEXT,
    source_bucket_id TEXT,
    destination_bucket_id TEXT,
    amount_text TEXT,
    error_code TEXT,
    error_summary TEXT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_plan_id) REFERENCES capital_plans(plan_id) ON DELETE RESTRICT,
    FOREIGN KEY (result_snapshot_id) REFERENCES capital_snapshots(snapshot_id)
        ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND resolved_plan_id IS NOT NULL
            AND result_snapshot_id IS NOT NULL AND error_code IS NULL
            AND error_summary IS NULL)
        OR
        (status <> 'completed' AND error_code IS NOT NULL
            AND error_summary IS NOT NULL)
    ),
    CHECK (
        operation_type <> 'transfer'
        OR (source_bucket_id IS NOT NULL AND destination_bucket_id IS NOT NULL
            AND amount_text IS NOT NULL)
    )
);

CREATE INDEX idx_capital_operations_plan
ON capital_allocation_operations (
    resolved_plan_id, requested_plan_id, requested_at_utc DESC
);

CREATE TABLE capital_operation_asset_inputs (
    operation_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    symbol TEXT NOT NULL,
    amount_text TEXT NOT NULL,
    PRIMARY KEY (operation_id, ordinal),
    FOREIGN KEY (operation_id) REFERENCES capital_allocation_operations(operation_id)
        ON DELETE RESTRICT
);
"""


_SCHEMA_V5 = """
CREATE TABLE asset_state_definitions (
    definition_id TEXT PRIMARY KEY,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    predecessor_definition_id TEXT,
    name TEXT NOT NULL,
    reason TEXT NOT NULL,
    initial_state_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('available', 'archived')),
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (predecessor_definition_id)
        REFERENCES asset_state_definitions(definition_id) ON DELETE RESTRICT
);

CREATE INDEX idx_asset_state_definitions_list
ON asset_state_definitions (created_at_utc DESC, name, definition_version);

CREATE TABLE asset_state_definition_states (
    definition_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    state_key TEXT NOT NULL,
    display_label TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (definition_id, ordinal),
    UNIQUE (definition_id, state_key),
    FOREIGN KEY (definition_id)
        REFERENCES asset_state_definitions(definition_id) ON DELETE RESTRICT
);

CREATE TABLE asset_state_definition_edges (
    definition_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    source_state_key TEXT NOT NULL,
    destination_state_key TEXT NOT NULL,
    PRIMARY KEY (definition_id, ordinal),
    UNIQUE (definition_id, source_state_key, destination_state_key),
    FOREIGN KEY (definition_id)
        REFERENCES asset_state_definitions(definition_id) ON DELETE RESTRICT,
    CHECK (source_state_key <> destination_state_key)
);

CREATE TABLE asset_state_cycles (
    cycle_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    status TEXT NOT NULL CHECK (status IN ('open', 'closed')),
    opened_run_id TEXT NOT NULL,
    opened_at_utc TEXT NOT NULL,
    opened_by TEXT NOT NULL,
    opening_reason TEXT NOT NULL,
    closed_run_id TEXT,
    closed_at_utc TEXT,
    closed_by TEXT,
    closing_reason TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (definition_id)
        REFERENCES asset_state_definitions(definition_id) ON DELETE RESTRICT,
    FOREIGN KEY (opened_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (closed_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    CHECK (
        (status = 'open' AND closed_run_id IS NULL AND closed_at_utc IS NULL
            AND closed_by IS NULL AND closing_reason IS NULL)
        OR
        (status = 'closed' AND closed_run_id IS NOT NULL AND closed_at_utc IS NOT NULL
            AND closed_by IS NOT NULL AND closing_reason IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_asset_state_open_cycle_symbol
ON asset_state_cycles (symbol) WHERE status = 'open';

CREATE INDEX idx_asset_state_cycles_list
ON asset_state_cycles (symbol, status, opened_at_utc DESC, cycle_id);

CREATE TABLE asset_state_cycle_events (
    event_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    cycle_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('started', 'closed')),
    state_key TEXT NOT NULL,
    occurred_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (cycle_id) REFERENCES asset_state_cycles(cycle_id) ON DELETE RESTRICT,
    UNIQUE (cycle_id, event_type)
);

CREATE TABLE asset_state_transitions (
    transition_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    cycle_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    predecessor_snapshot_id TEXT NOT NULL,
    predecessor_sequence INTEGER NOT NULL CHECK (predecessor_sequence >= 0),
    previous_state_key TEXT NOT NULL,
    new_state_key TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK (trigger_type = 'manual_research'),
    occurred_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    note TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (cycle_id) REFERENCES asset_state_cycles(cycle_id) ON DELETE RESTRICT,
    FOREIGN KEY (definition_id)
        REFERENCES asset_state_definitions(definition_id) ON DELETE RESTRICT,
    FOREIGN KEY (predecessor_snapshot_id)
        REFERENCES asset_state_snapshots(snapshot_id) ON DELETE RESTRICT,
    CHECK (previous_state_key <> new_state_key),
    UNIQUE (cycle_id, predecessor_sequence)
);

CREATE INDEX idx_asset_state_transitions_cycle
ON asset_state_transitions (cycle_id, predecessor_sequence, occurred_at_utc);

CREATE TABLE asset_state_transition_evidence (
    transition_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN ('algorithm_run', 'factor_calculation')
    ),
    evidence_id TEXT NOT NULL,
    source_component TEXT,
    source_version TEXT,
    PRIMARY KEY (transition_id, ordinal),
    UNIQUE (transition_id, evidence_kind, evidence_id),
    FOREIGN KEY (transition_id)
        REFERENCES asset_state_transitions(transition_id) ON DELETE RESTRICT,
    CHECK (source_version IS NULL OR source_component IS NOT NULL)
);

CREATE TABLE asset_state_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    cycle_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    sequence INTEGER NOT NULL CHECK (sequence >= 0),
    current_state_key TEXT NOT NULL,
    predecessor_snapshot_id TEXT,
    causal_transition_id TEXT,
    created_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (cycle_id) REFERENCES asset_state_cycles(cycle_id) ON DELETE RESTRICT,
    FOREIGN KEY (definition_id)
        REFERENCES asset_state_definitions(definition_id) ON DELETE RESTRICT,
    FOREIGN KEY (predecessor_snapshot_id)
        REFERENCES asset_state_snapshots(snapshot_id) ON DELETE RESTRICT,
    FOREIGN KEY (causal_transition_id)
        REFERENCES asset_state_transitions(transition_id) ON DELETE RESTRICT,
    UNIQUE (cycle_id, sequence),
    CHECK (
        (sequence = 0 AND predecessor_snapshot_id IS NULL AND causal_transition_id IS NULL)
        OR
        (sequence > 0 AND predecessor_snapshot_id IS NOT NULL AND causal_transition_id IS NOT NULL)
    )
);

CREATE INDEX idx_asset_state_snapshots_cycle
ON asset_state_snapshots (cycle_id, sequence DESC);

CREATE TABLE asset_state_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (
        operation_type IN ('definition_save', 'cycle_start', 'transition', 'cycle_close')
    ),
    status TEXT NOT NULL CHECK (status IN ('completed', 'invalid_input', 'failed')),
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    definition_name TEXT,
    predecessor_definition_id TEXT,
    initial_state_key TEXT,
    symbol TEXT,
    requested_definition_id TEXT,
    resolved_definition_id TEXT,
    requested_cycle_id TEXT,
    cycle_id TEXT,
    predecessor_snapshot_id TEXT,
    requested_state_key TEXT,
    note TEXT,
    result_snapshot_id TEXT,
    transition_id TEXT,
    cycle_event_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_definition_id)
        REFERENCES asset_state_definitions(definition_id) ON DELETE RESTRICT,
    FOREIGN KEY (cycle_id) REFERENCES asset_state_cycles(cycle_id) ON DELETE RESTRICT,
    FOREIGN KEY (result_snapshot_id)
        REFERENCES asset_state_snapshots(snapshot_id) ON DELETE RESTRICT,
    FOREIGN KEY (transition_id)
        REFERENCES asset_state_transitions(transition_id) ON DELETE RESTRICT,
    FOREIGN KEY (cycle_event_id)
        REFERENCES asset_state_cycle_events(event_id) ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status <> 'completed' AND error_code IS NOT NULL AND error_summary IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_asset_state_completed_operation
ON asset_state_operations (operation_id) WHERE status = 'completed';

CREATE INDEX idx_asset_state_operations_lookup
ON asset_state_operations (operation_id, cycle_id, requested_at_utc, attempt_id);

CREATE TABLE asset_state_operation_state_inputs (
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    state_key TEXT NOT NULL,
    display_label TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (attempt_id, ordinal),
    FOREIGN KEY (attempt_id) REFERENCES asset_state_operations(attempt_id) ON DELETE RESTRICT
);

CREATE TABLE asset_state_operation_edge_inputs (
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    source_state_key TEXT NOT NULL,
    destination_state_key TEXT NOT NULL,
    PRIMARY KEY (attempt_id, ordinal),
    FOREIGN KEY (attempt_id) REFERENCES asset_state_operations(attempt_id) ON DELETE RESTRICT
);

CREATE TABLE asset_state_operation_evidence_inputs (
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN ('algorithm_run', 'factor_calculation')
    ),
    evidence_id TEXT NOT NULL,
    source_component TEXT,
    source_version TEXT,
    PRIMARY KEY (attempt_id, ordinal),
    FOREIGN KEY (attempt_id) REFERENCES asset_state_operations(attempt_id) ON DELETE RESTRICT,
    CHECK (source_version IS NULL OR source_component IS NOT NULL)
);
"""


_SCHEMA_V6 = """
CREATE TABLE target_position_definitions (
    definition_id TEXT PRIMARY KEY,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    predecessor_definition_id TEXT,
    name TEXT NOT NULL,
    reason TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('non_increasing', 'non_decreasing')),
    minimum_fraction_text TEXT NOT NULL,
    neutral_fraction_text TEXT NOT NULL,
    maximum_fraction_text TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('available', 'archived')),
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (predecessor_definition_id)
        REFERENCES target_position_definitions(definition_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_position_definitions_list
ON target_position_definitions (created_at_utc DESC, name, definition_version);

CREATE TABLE target_position_definition_knots (
    definition_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    state_value_text TEXT NOT NULL,
    target_fraction_text TEXT NOT NULL,
    PRIMARY KEY (definition_id, ordinal),
    UNIQUE (definition_id, state_value_text),
    FOREIGN KEY (definition_id)
        REFERENCES target_position_definitions(definition_id) ON DELETE RESTRICT
);

CREATE TABLE target_position_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('definition_save', 'preview')),
    status TEXT NOT NULL CHECK (status IN ('completed', 'invalid_input', 'failed')),
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    definition_name TEXT,
    direction TEXT,
    minimum_fraction_text TEXT,
    neutral_fraction_text TEXT,
    maximum_fraction_text TEXT,
    predecessor_definition_id TEXT,
    requested_definition_id TEXT,
    resolved_definition_id TEXT,
    research_state_value_text TEXT,
    research_capital_basis_usd_text TEXT,
    current_position_value_usd_text TEXT,
    as_of_utc TEXT,
    result_calculation_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_definition_id)
        REFERENCES target_position_definitions(definition_id) ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status <> 'completed' AND error_code IS NOT NULL AND error_summary IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_target_position_completed_operation
ON target_position_operations (operation_id) WHERE status = 'completed';

CREATE INDEX idx_target_position_operations_lookup
ON target_position_operations (operation_id, requested_at_utc DESC, attempt_id);

CREATE TABLE target_position_operation_knots (
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    state_value_text TEXT NOT NULL,
    target_fraction_text TEXT NOT NULL,
    PRIMARY KEY (attempt_id, ordinal),
    FOREIGN KEY (attempt_id)
        REFERENCES target_position_operations(attempt_id) ON DELETE RESTRICT
);

CREATE TABLE target_position_operation_evidence_inputs (
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN ('algorithm_run', 'factor_calculation')
    ),
    evidence_id TEXT NOT NULL,
    source_component TEXT,
    source_version TEXT,
    PRIMARY KEY (attempt_id, ordinal),
    FOREIGN KEY (attempt_id)
        REFERENCES target_position_operations(attempt_id) ON DELETE RESTRICT,
    CHECK (source_version IS NULL OR source_component IS NOT NULL)
);

CREATE TABLE target_position_results (
    calculation_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    as_of_utc TEXT NOT NULL,
    research_state_value_text TEXT NOT NULL,
    research_capital_basis_usd_text TEXT NOT NULL,
    current_position_value_usd_text TEXT NOT NULL,
    target_fraction_text TEXT NOT NULL,
    target_position_value_usd_text TEXT NOT NULL,
    adjustment_value_usd_text TEXT NOT NULL,
    adjustment_direction TEXT NOT NULL CHECK (
        adjustment_direction IN ('none', 'increase', 'decrease')
    ),
    evaluation_mode TEXT NOT NULL CHECK (
        evaluation_mode IN ('lower_endpoint', 'exact_knot', 'interpolated', 'upper_endpoint')
    ),
    lower_knot_ordinal INTEGER NOT NULL CHECK (lower_knot_ordinal >= 0),
    upper_knot_ordinal INTEGER NOT NULL CHECK (upper_knot_ordinal >= lower_knot_ordinal),
    lower_state_value_text TEXT NOT NULL,
    upper_state_value_text TEXT NOT NULL,
    lower_target_fraction_text TEXT NOT NULL,
    upper_target_fraction_text TEXT NOT NULL,
    interpolation_numerator_text TEXT NOT NULL,
    interpolation_denominator_text TEXT NOT NULL,
    interpolation_weight_text TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (definition_id)
        REFERENCES target_position_definitions(definition_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_position_results_list
ON target_position_results (definition_id, as_of_utc DESC, calculation_id);

CREATE TABLE target_position_result_evidence (
    calculation_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN ('algorithm_run', 'factor_calculation')
    ),
    evidence_id TEXT NOT NULL,
    source_component TEXT,
    source_version TEXT,
    PRIMARY KEY (calculation_id, ordinal),
    FOREIGN KEY (calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    CHECK (source_version IS NULL OR source_component IS NOT NULL)
);
"""


_SCHEMA_V7 = """
CREATE TABLE standardized_state_definitions (
    definition_id TEXT PRIMARY KEY,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    predecessor_definition_id TEXT,
    name TEXT NOT NULL,
    reason TEXT NOT NULL,
    formula_id TEXT NOT NULL CHECK (
        formula_id = 'price_minus_reference_over_positive_scale'
    ),
    price_currency TEXT NOT NULL CHECK (price_currency = 'USD'),
    output_unit TEXT NOT NULL CHECK (output_unit = 'dimensionless'),
    price_source TEXT NOT NULL CHECK (price_source = 'manual_research'),
    reference_source TEXT NOT NULL CHECK (reference_source = 'manual_research'),
    risk_scale_source TEXT NOT NULL CHECK (risk_scale_source = 'manual_research'),
    status TEXT NOT NULL CHECK (status IN ('available', 'archived')),
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (predecessor_definition_id)
        REFERENCES standardized_state_definitions(definition_id) ON DELETE RESTRICT
);

CREATE INDEX idx_standardized_state_definitions_list
ON standardized_state_definitions (created_at_utc DESC, name, definition_version);

CREATE TABLE standardized_state_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('definition_save', 'preview')),
    status TEXT NOT NULL CHECK (status IN ('completed', 'invalid_input', 'failed')),
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    definition_name TEXT,
    predecessor_definition_id TEXT,
    requested_definition_id TEXT,
    resolved_definition_id TEXT,
    symbol TEXT,
    manual_price_usd_text TEXT,
    manual_reference_price_usd_text TEXT,
    manual_risk_scale_usd_text TEXT,
    as_of_utc TEXT,
    result_calculation_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_definition_id)
        REFERENCES standardized_state_definitions(definition_id) ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status <> 'completed' AND error_code IS NOT NULL AND error_summary IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_standardized_state_completed_operation
ON standardized_state_operations (operation_id) WHERE status = 'completed';

CREATE INDEX idx_standardized_state_operations_lookup
ON standardized_state_operations (
    operation_id, symbol, requested_at_utc DESC, attempt_id
);

CREATE TABLE standardized_state_operation_evidence_inputs (
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN ('algorithm_run', 'factor_calculation')
    ),
    evidence_id TEXT NOT NULL,
    source_component TEXT,
    source_version TEXT,
    PRIMARY KEY (attempt_id, ordinal),
    FOREIGN KEY (attempt_id)
        REFERENCES standardized_state_operations(attempt_id) ON DELETE RESTRICT,
    CHECK (source_version IS NULL OR source_component IS NOT NULL)
);

CREATE TABLE standardized_state_results (
    calculation_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL CHECK (definition_version > 0),
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    manual_price_usd_text TEXT NOT NULL,
    manual_reference_price_usd_text TEXT NOT NULL,
    manual_risk_scale_usd_text TEXT NOT NULL,
    price_deviation_usd_text TEXT NOT NULL,
    standardized_state_text TEXT NOT NULL,
    formula_id TEXT NOT NULL CHECK (
        formula_id = 'price_minus_reference_over_positive_scale'
    ),
    price_currency TEXT NOT NULL CHECK (price_currency = 'USD'),
    output_unit TEXT NOT NULL CHECK (output_unit = 'dimensionless'),
    price_source TEXT NOT NULL CHECK (price_source = 'manual_research'),
    reference_source TEXT NOT NULL CHECK (reference_source = 'manual_research'),
    risk_scale_source TEXT NOT NULL CHECK (risk_scale_source = 'manual_research'),
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (definition_id)
        REFERENCES standardized_state_definitions(definition_id) ON DELETE RESTRICT
);

CREATE INDEX idx_standardized_state_results_list
ON standardized_state_results (
    symbol, definition_id, as_of_utc DESC, calculation_id
);

CREATE TABLE standardized_state_result_evidence (
    calculation_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN ('algorithm_run', 'factor_calculation')
    ),
    evidence_id TEXT NOT NULL,
    source_component TEXT,
    source_version TEXT,
    PRIMARY KEY (calculation_id, ordinal),
    FOREIGN KEY (calculation_id)
        REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT,
    CHECK (source_version IS NULL OR source_component IS NOT NULL)
);
"""


_SCHEMA_V8 = """
CREATE TABLE target_position_linked_preview_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    parent_run_id TEXT NOT NULL UNIQUE,
    source_stage_id TEXT NOT NULL,
    target_stage_id TEXT,
    child_run_id TEXT,
    child_stage_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('completed', 'invalid_input', 'failed')),
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    requested_source_calculation_id TEXT NOT NULL,
    requested_target_definition_id TEXT NOT NULL,
    research_capital_basis_usd_text TEXT NOT NULL,
    current_position_value_usd_text TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    resolved_source_run_id TEXT,
    resolved_source_stage_id TEXT,
    resolved_source_definition_id TEXT,
    resolved_source_definition_version INTEGER CHECK (
        resolved_source_definition_version IS NULL
        OR resolved_source_definition_version > 0
    ),
    resolved_symbol TEXT,
    resolved_source_as_of_utc TEXT,
    resolved_standardized_state_text TEXT,
    resolved_target_definition_id TEXT,
    resolved_target_definition_version INTEGER CHECK (
        resolved_target_definition_version IS NULL
        OR resolved_target_definition_version > 0
    ),
    target_result_calculation_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (child_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_source_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_source_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_source_definition_id)
        REFERENCES standardized_state_definitions(definition_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_target_definition_id)
        REFERENCES target_position_definitions(definition_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_result_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status <> 'completed' AND error_code IS NOT NULL AND error_summary IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_target_position_linked_completed_operation
ON target_position_linked_preview_operations (operation_id)
WHERE status = 'completed';

CREATE INDEX idx_target_position_linked_operations_lookup
ON target_position_linked_preview_operations (
    operation_id, resolved_symbol, requested_at_utc DESC, attempt_id
);

CREATE TABLE target_position_standardized_state_links (
    link_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    parent_run_id TEXT NOT NULL UNIQUE,
    source_stage_id TEXT NOT NULL,
    target_stage_id TEXT NOT NULL,
    child_run_id TEXT NOT NULL UNIQUE,
    child_stage_id TEXT NOT NULL,
    source_calculation_id TEXT NOT NULL,
    source_run_id TEXT NOT NULL,
    source_result_stage_id TEXT NOT NULL,
    source_definition_id TEXT NOT NULL,
    source_definition_version INTEGER NOT NULL CHECK (source_definition_version > 0),
    symbol TEXT NOT NULL,
    source_as_of_utc TEXT NOT NULL,
    standardized_state_text TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL UNIQUE,
    target_definition_id TEXT NOT NULL,
    target_definition_version INTEGER NOT NULL CHECK (target_definition_version > 0),
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (child_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_calculation_id)
        REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_result_stage_id)
        REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (source_definition_id)
        REFERENCES standardized_state_definitions(definition_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_definition_id)
        REFERENCES target_position_definitions(definition_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_position_standardized_links_lookup
ON target_position_standardized_state_links (
    symbol, source_definition_id, target_definition_id,
    source_as_of_utc DESC, link_id
);
"""


_SCHEMA_V9 = """
CREATE TABLE target_adjustment_decision_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT NOT NULL UNIQUE,
    target_stage_id TEXT NOT NULL,
    decision_stage_id TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('intent_created', 'hold', 'invalid_input', 'failed')
    ),
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    requested_target_position_link_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    resolved_target_position_link_id TEXT,
    resolved_linked_target_operation_id TEXT,
    resolved_linked_parent_run_id TEXT,
    resolved_linked_source_stage_id TEXT,
    resolved_linked_target_stage_id TEXT,
    resolved_target_child_run_id TEXT,
    resolved_target_child_stage_id TEXT,
    resolved_standardized_state_calculation_id TEXT,
    resolved_standardized_state_run_id TEXT,
    resolved_standardized_state_stage_id TEXT,
    resolved_standardized_state_definition_id TEXT,
    resolved_standardized_state_definition_version INTEGER CHECK (
        resolved_standardized_state_definition_version IS NULL
        OR resolved_standardized_state_definition_version > 0
    ),
    resolved_standardized_state_created_at_utc TEXT,
    resolved_target_calculation_id TEXT,
    resolved_target_definition_id TEXT,
    resolved_target_definition_version INTEGER CHECK (
        resolved_target_definition_version IS NULL
        OR resolved_target_definition_version > 0
    ),
    resolved_target_created_at_utc TEXT,
    resolved_symbol TEXT,
    resolved_as_of_utc TEXT,
    resolved_standardized_state_text TEXT,
    resolved_research_capital_basis_usd_text TEXT,
    resolved_current_position_value_usd_text TEXT,
    resolved_target_fraction_text TEXT,
    resolved_target_position_value_usd_text TEXT,
    resolved_adjustment_value_usd_text TEXT,
    resolved_source_direction TEXT CHECK (
        resolved_source_direction IS NULL
        OR resolved_source_direction IN ('increase', 'decrease', 'none')
    ),
    resolved_link_created_at_utc TEXT,
    resolved_source_schema_version INTEGER,
    resolved_target_schema_version INTEGER,
    resolved_link_schema_version INTEGER,
    resolved_currency TEXT,
    resolved_state_unit TEXT,
    resolved_input_schema_version INTEGER,
    decision_result_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_target_position_link_id)
        REFERENCES target_position_standardized_state_links(link_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_linked_parent_run_id)
        REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_target_child_run_id)
        REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_standardized_state_run_id)
        REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_standardized_state_calculation_id)
        REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT,
    CHECK (
        (status IN ('intent_created', 'hold')
            AND decision_result_id IS NOT NULL
            AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status IN ('invalid_input', 'failed')
            AND decision_result_id IS NULL
            AND error_code IS NOT NULL AND error_summary IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_target_adjustment_decision_completed_operation
ON target_adjustment_decision_operations (operation_id)
WHERE status IN ('intent_created', 'hold');

CREATE INDEX idx_target_adjustment_decision_operations_lookup
ON target_adjustment_decision_operations (
    operation_id, resolved_symbol, requested_at_utc DESC, attempt_id
);

CREATE TABLE target_adjustment_decision_results (
    decision_result_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    target_position_link_id TEXT NOT NULL,
    linked_target_operation_id TEXT NOT NULL,
    linked_parent_run_id TEXT NOT NULL,
    linked_source_stage_id TEXT NOT NULL,
    linked_target_stage_id TEXT NOT NULL,
    target_child_run_id TEXT NOT NULL,
    target_child_stage_id TEXT NOT NULL,
    standardized_state_calculation_id TEXT NOT NULL,
    standardized_state_run_id TEXT NOT NULL,
    standardized_state_stage_id TEXT NOT NULL,
    standardized_state_definition_id TEXT NOT NULL,
    standardized_state_definition_version INTEGER NOT NULL CHECK (
        standardized_state_definition_version > 0
    ),
    standardized_state_created_at_utc TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL,
    target_definition_id TEXT NOT NULL,
    target_definition_version INTEGER NOT NULL CHECK (target_definition_version > 0),
    target_created_at_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    standardized_state_text TEXT NOT NULL,
    research_capital_basis_usd_text TEXT NOT NULL,
    current_position_value_usd_text TEXT NOT NULL,
    target_fraction_text TEXT NOT NULL,
    target_position_value_usd_text TEXT NOT NULL,
    adjustment_value_usd_text TEXT NOT NULL,
    source_direction TEXT NOT NULL CHECK (
        source_direction IN ('increase', 'decrease', 'none')
    ),
    link_created_at_utc TEXT NOT NULL,
    source_schema_version INTEGER NOT NULL CHECK (source_schema_version = 1),
    target_schema_version INTEGER NOT NULL CHECK (target_schema_version = 1),
    link_schema_version INTEGER NOT NULL CHECK (link_schema_version = 1),
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    state_unit TEXT NOT NULL CHECK (state_unit = 'dimensionless'),
    input_schema_version INTEGER NOT NULL CHECK (input_schema_version = 1),
    status TEXT NOT NULL CHECK (status IN ('intent_created', 'hold')),
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease', 'hold')),
    reason_codes_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    software_version TEXT NOT NULL,
    source_revision TEXT,
    worktree_state TEXT NOT NULL,
    policy_id TEXT NOT NULL CHECK (policy_id = 'decision.target_adjustment_preview'),
    policy_version TEXT NOT NULL CHECK (policy_version = '1.0.0'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_position_link_id)
        REFERENCES target_position_standardized_state_links(link_id) ON DELETE RESTRICT,
    FOREIGN KEY (linked_parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_calculation_id)
        REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    CHECK (
        (status = 'hold' AND action = 'hold')
        OR
        (status = 'intent_created' AND action IN ('increase', 'decrease'))
    )
);

CREATE INDEX idx_target_adjustment_decision_results_lookup
ON target_adjustment_decision_results (
    symbol, target_definition_id, target_definition_version,
    as_of_utc DESC, decision_result_id
);

CREATE TABLE target_adjustment_trade_intents (
    intent_id TEXT PRIMARY KEY,
    decision_result_id TEXT NOT NULL UNIQUE,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    target_position_link_id TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    current_exposure_usd_text TEXT NOT NULL,
    target_exposure_usd_text TEXT NOT NULL,
    desired_change_usd_text TEXT NOT NULL,
    requested_notional_usd_text TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    policy_id TEXT NOT NULL CHECK (policy_id = 'decision.target_adjustment_preview'),
    policy_version TEXT NOT NULL CHECK (policy_version = '1.0.0'),
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (decision_result_id)
        REFERENCES target_adjustment_decision_results(decision_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_position_link_id)
        REFERENCES target_position_standardized_state_links(link_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_trade_intents_lookup
ON target_adjustment_trade_intents (symbol, action, as_of_utc DESC, intent_id);

CREATE TABLE target_adjustment_decision_source_links (
    source_link_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    decision_result_id TEXT NOT NULL UNIQUE,
    decision_run_id TEXT NOT NULL UNIQUE,
    decision_stage_id TEXT NOT NULL,
    target_position_link_id TEXT NOT NULL,
    linked_target_operation_id TEXT NOT NULL,
    linked_parent_run_id TEXT NOT NULL,
    target_child_run_id TEXT NOT NULL,
    standardized_state_run_id TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL,
    standardized_state_calculation_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (decision_result_id)
        REFERENCES target_adjustment_decision_results(decision_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_position_link_id)
        REFERENCES target_position_standardized_state_links(link_id) ON DELETE RESTRICT,
    FOREIGN KEY (linked_parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_calculation_id)
        REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_decision_source_links_lookup
ON target_adjustment_decision_source_links (
    target_position_link_id, linked_parent_run_id, target_child_run_id,
    standardized_state_run_id
);
"""


_SCHEMA_V10 = """
CREATE TABLE target_adjustment_risk_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT NOT NULL UNIQUE,
    decision_stage_id TEXT NOT NULL,
    risk_stage_id TEXT,
    requested_intent_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('manual_review_required', 'blocked', 'invalid_input', 'failed')),
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    resolved_source_json TEXT,
    safety_snapshot_json TEXT,
    resolved_symbol TEXT,
    resolved_action TEXT CHECK (resolved_action IS NULL OR resolved_action IN ('increase', 'decrease')),
    resolved_as_of_utc TEXT,
    review_result_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (risk_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    CHECK (
        (status IN ('manual_review_required', 'blocked') AND risk_stage_id IS NOT NULL
            AND resolved_source_json IS NOT NULL AND safety_snapshot_json IS NOT NULL
            AND review_result_id IS NOT NULL AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status IN ('invalid_input', 'failed') AND review_result_id IS NULL
            AND error_code IS NOT NULL AND error_summary IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_target_adjustment_risk_completed_operation
ON target_adjustment_risk_operations (operation_id)
WHERE status IN ('manual_review_required', 'blocked');

CREATE INDEX idx_target_adjustment_risk_operations_lookup
ON target_adjustment_risk_operations (operation_id, resolved_symbol, status, requested_at_utc DESC);

CREATE TABLE target_adjustment_risk_review_results (
    review_result_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    source_json TEXT NOT NULL,
    safety_snapshot_json TEXT NOT NULL,
    safety_snapshot_id TEXT NOT NULL,
    decision_result_id TEXT NOT NULL,
    intent_id TEXT NOT NULL UNIQUE,
    decision_run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    current_exposure_usd_text TEXT NOT NULL,
    target_exposure_usd_text TEXT NOT NULL,
    desired_change_usd_text TEXT NOT NULL,
    requested_notional_usd_text TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('manual_review_required', 'blocked')),
    reason_codes_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    software_version TEXT NOT NULL,
    approved_notional_usd_text TEXT CHECK (approved_notional_usd_text IS NULL),
    risk_approved_intent_id TEXT CHECK (risk_approved_intent_id IS NULL),
    gate_id TEXT NOT NULL CHECK (gate_id = 'risk.target_adjustment_manual_review_gate'),
    gate_version TEXT NOT NULL CHECK (gate_version = '1.0.0'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_result_id) REFERENCES target_adjustment_decision_results(decision_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (intent_id) REFERENCES target_adjustment_trade_intents(intent_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_risk_results_lookup
ON target_adjustment_risk_review_results (symbol, action, status, as_of_utc DESC, review_result_id);

CREATE TABLE target_adjustment_risk_rule_results (
    rule_result_id TEXT PRIMARY KEY,
    review_result_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    rule_id TEXT NOT NULL CHECK (rule_id IN ('SOURCE_CHAIN_INTEGRITY', 'NON_EXECUTION_SAFETY_STATE', 'NUMERICAL_RISK_POLICY_AVAILABILITY')),
    rule_version TEXT NOT NULL CHECK (rule_version = '1'),
    rule_name TEXT NOT NULL,
    evaluation_order INTEGER NOT NULL CHECK (evaluation_order BETWEEN 1 AND 3),
    status TEXT NOT NULL CHECK (status IN ('passed', 'manual_review', 'blocked')),
    input_summary TEXT NOT NULL,
    expected_condition TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    stop_processing INTEGER NOT NULL CHECK (stop_processing IN (0, 1)),
    evaluated_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    UNIQUE (review_result_id, evaluation_order),
    UNIQUE (review_result_id, rule_id),
    FOREIGN KEY (review_result_id) REFERENCES target_adjustment_risk_review_results(review_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT
);

CREATE TABLE target_adjustment_risk_source_links (
    source_link_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    review_result_id TEXT NOT NULL UNIQUE,
    risk_run_id TEXT NOT NULL UNIQUE,
    risk_stage_id TEXT NOT NULL,
    decision_result_id TEXT NOT NULL,
    intent_id TEXT NOT NULL UNIQUE,
    decision_run_id TEXT NOT NULL,
    linked_parent_run_id TEXT NOT NULL,
    target_child_run_id TEXT NOT NULL,
    standardized_state_run_id TEXT NOT NULL,
    target_position_link_id TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL,
    standardized_state_calculation_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (review_result_id) REFERENCES target_adjustment_risk_review_results(review_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (risk_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (risk_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_result_id) REFERENCES target_adjustment_decision_results(decision_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (intent_id) REFERENCES target_adjustment_trade_intents(intent_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (linked_parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_position_link_id) REFERENCES target_position_standardized_state_links(link_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id) REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_calculation_id) REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_risk_source_links_lookup
ON target_adjustment_risk_source_links (decision_run_id, linked_parent_run_id, target_child_run_id, standardized_state_run_id);
"""


_SCHEMA_V11 = """
CREATE TABLE single_asset_exposure_cap_definitions (
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL CHECK (definition_version >= 1),
    predecessor_version INTEGER,
    symbol TEXT NOT NULL,
    max_target_exposure_usd_text TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('saved', 'archived')),
    reason TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    software_version TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    PRIMARY KEY (definition_id, definition_version),
    FOREIGN KEY (definition_id, predecessor_version)
        REFERENCES single_asset_exposure_cap_definitions(definition_id, definition_version)
        ON DELETE RESTRICT,
    CHECK (
        (definition_version = 1 AND predecessor_version IS NULL)
        OR predecessor_version = definition_version - 1
    )
);

CREATE INDEX idx_single_asset_exposure_cap_definitions_lookup
ON single_asset_exposure_cap_definitions
    (symbol, status, definition_id, definition_version DESC);

CREATE TABLE target_adjustment_exposure_cap_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('definition_save', 'definition_archive', 'preview')),
    status TEXT NOT NULL CHECK (status IN ('completed', 'blocked', 'invalid_input', 'failed')),
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    requested_review_result_id TEXT,
    requested_definition_id TEXT,
    requested_definition_version INTEGER,
    requested_symbol TEXT,
    requested_max_target_exposure_usd_text TEXT,
    resolved_definition_id TEXT,
    resolved_definition_version INTEGER,
    resolved_source_json TEXT,
    current_safety_snapshot_json TEXT,
    resolved_symbol TEXT,
    resolved_action TEXT CHECK (resolved_action IS NULL OR resolved_action IN ('increase', 'decrease')),
    resolved_as_of_utc TEXT,
    preview_result_id TEXT,
    disposition TEXT CHECK (disposition IS NULL OR disposition IN ('manual_review_required', 'blocked_by_exposure_cap')),
    error_code TEXT,
    error_summary TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_definition_id, resolved_definition_version)
        REFERENCES single_asset_exposure_cap_definitions(definition_id, definition_version)
        ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status IN ('blocked', 'invalid_input', 'failed')
            AND error_code IS NOT NULL AND error_summary IS NOT NULL
            AND preview_result_id IS NULL AND disposition IS NULL)
    )
);

CREATE UNIQUE INDEX uq_target_adjustment_exposure_cap_terminal_operation
ON target_adjustment_exposure_cap_operations (operation_id)
WHERE status IN ('completed', 'blocked');

CREATE INDEX idx_target_adjustment_exposure_cap_operations_lookup
ON target_adjustment_exposure_cap_operations
    (operation_id, operation_type, status, resolved_symbol, requested_at_utc DESC);

CREATE TABLE target_adjustment_exposure_cap_results (
    preview_result_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    source_json TEXT NOT NULL,
    phase6a_review_result_id TEXT NOT NULL,
    phase6a_run_id TEXT NOT NULL,
    phase6a_stage_id TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    current_exposure_usd_text TEXT NOT NULL,
    target_exposure_usd_text TEXT NOT NULL,
    original_requested_notional_usd_text TEXT NOT NULL,
    max_target_exposure_usd_text TEXT NOT NULL,
    cap_constrained_candidate_notional_usd_text TEXT NOT NULL,
    reduction_usd_text TEXT NOT NULL,
    disposition TEXT NOT NULL CHECK (disposition IN ('manual_review_required', 'blocked_by_exposure_cap')),
    reason_codes_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    software_version TEXT NOT NULL,
    component_id TEXT NOT NULL CHECK (component_id = 'risk.target_adjustment_single_asset_exposure_cap_preview'),
    component_version TEXT NOT NULL CHECK (component_version = '1.0.0'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_review_result_id)
        REFERENCES target_adjustment_risk_review_results(review_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (definition_id, definition_version)
        REFERENCES single_asset_exposure_cap_definitions(definition_id, definition_version)
        ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_exposure_cap_results_lookup
ON target_adjustment_exposure_cap_results
    (symbol, action, disposition, definition_id, definition_version, as_of_utc DESC);

CREATE TABLE target_adjustment_exposure_cap_rule_results (
    rule_result_id TEXT PRIMARY KEY,
    preview_result_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    rule_id TEXT NOT NULL CHECK (rule_id = 'MAX_TARGET_EXPOSURE_USD'),
    rule_version TEXT NOT NULL CHECK (rule_version = '1'),
    evaluation_order INTEGER NOT NULL CHECK (evaluation_order = 1),
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    current_exposure_usd_text TEXT NOT NULL,
    target_exposure_usd_text TEXT NOT NULL,
    original_requested_notional_usd_text TEXT NOT NULL,
    max_target_exposure_usd_text TEXT NOT NULL,
    cap_constrained_candidate_notional_usd_text TEXT NOT NULL,
    reduction_usd_text TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('passed_within_cap', 'reduced_to_cap', 'blocked_no_increase_capacity', 'preserved_risk_reducing_direction')),
    reason_codes_json TEXT NOT NULL,
    stop_processing INTEGER NOT NULL CHECK (stop_processing = 1),
    evaluated_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (preview_result_id)
        REFERENCES target_adjustment_exposure_cap_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT
);

CREATE TABLE target_adjustment_exposure_cap_source_links (
    source_link_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    preview_result_id TEXT NOT NULL UNIQUE,
    exposure_cap_run_id TEXT NOT NULL UNIQUE,
    exposure_cap_stage_id TEXT NOT NULL,
    phase6a_review_result_id TEXT NOT NULL,
    phase6a_run_id TEXT NOT NULL,
    phase6a_stage_id TEXT NOT NULL,
    decision_run_id TEXT NOT NULL,
    linked_parent_run_id TEXT NOT NULL,
    target_child_run_id TEXT NOT NULL,
    standardized_state_run_id TEXT NOT NULL,
    decision_result_id TEXT NOT NULL,
    intent_id TEXT NOT NULL,
    target_position_link_id TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL,
    standardized_state_calculation_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (preview_result_id)
        REFERENCES target_adjustment_exposure_cap_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (exposure_cap_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (exposure_cap_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_review_result_id)
        REFERENCES target_adjustment_risk_review_results(review_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (linked_parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_result_id)
        REFERENCES target_adjustment_decision_results(decision_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (intent_id)
        REFERENCES target_adjustment_trade_intents(intent_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_position_link_id)
        REFERENCES target_position_standardized_state_links(link_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_calculation_id)
        REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_exposure_cap_source_links_lookup
ON target_adjustment_exposure_cap_source_links
    (phase6a_run_id, decision_run_id, linked_parent_run_id, target_child_run_id, standardized_state_run_id);
"""


_SCHEMA_V12 = """
CREATE TABLE research_asset_cash_floor_definitions (
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL CHECK (definition_version >= 1),
    predecessor_version INTEGER,
    symbol TEXT NOT NULL,
    minimum_research_asset_cash_usd_text TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('saved', 'archived')),
    reason TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    software_version TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    PRIMARY KEY (definition_id, definition_version),
    FOREIGN KEY (definition_id, predecessor_version)
        REFERENCES research_asset_cash_floor_definitions(definition_id, definition_version)
        ON DELETE RESTRICT,
    CHECK (
        (definition_version = 1 AND predecessor_version IS NULL)
        OR predecessor_version = definition_version - 1
    )
);

CREATE INDEX idx_research_asset_cash_floor_definitions_lookup
ON research_asset_cash_floor_definitions
    (symbol, status, definition_id, definition_version DESC);

CREATE TABLE target_adjustment_cash_floor_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('definition_save', 'definition_archive', 'preview')),
    status TEXT NOT NULL CHECK (status IN ('completed', 'blocked', 'invalid_input', 'failed')),
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    requested_phase6b_result_id TEXT,
    requested_definition_id TEXT,
    requested_definition_version INTEGER,
    requested_symbol TEXT,
    requested_minimum_research_asset_cash_usd_text TEXT,
    resolved_definition_id TEXT,
    resolved_definition_version INTEGER,
    resolved_source_json TEXT,
    current_safety_snapshot_json TEXT,
    resolved_symbol TEXT,
    resolved_action TEXT CHECK (resolved_action IS NULL OR resolved_action IN ('increase', 'decrease')),
    resolved_as_of_utc TEXT,
    preview_result_id TEXT,
    disposition TEXT CHECK (disposition IS NULL OR disposition IN ('manual_review_required', 'blocked_by_research_cash_floor')),
    error_code TEXT,
    error_summary TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_definition_id, resolved_definition_version)
        REFERENCES research_asset_cash_floor_definitions(definition_id, definition_version)
        ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND error_code IS NULL AND error_summary IS NULL)
        OR
        (status IN ('blocked', 'invalid_input', 'failed')
            AND error_code IS NOT NULL AND error_summary IS NOT NULL
            AND preview_result_id IS NULL AND disposition IS NULL)
    )
);

CREATE UNIQUE INDEX uq_target_adjustment_cash_floor_terminal_operation
ON target_adjustment_cash_floor_operations (operation_id)
WHERE status IN ('completed', 'blocked');

CREATE INDEX idx_target_adjustment_cash_floor_operations_lookup
ON target_adjustment_cash_floor_operations
    (operation_id, operation_type, status, resolved_symbol, requested_at_utc DESC);

CREATE TABLE target_adjustment_cash_floor_results (
    preview_result_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    source_json TEXT NOT NULL,
    phase6b_preview_result_id TEXT NOT NULL,
    phase6b_run_id TEXT NOT NULL,
    phase6b_stage_id TEXT NOT NULL,
    phase6a_review_result_id TEXT NOT NULL,
    phase6a_run_id TEXT NOT NULL,
    phase6a_stage_id TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_version INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    research_capital_basis_usd_text TEXT NOT NULL,
    current_exposure_usd_text TEXT NOT NULL,
    phase6b_candidate_notional_usd_text TEXT NOT NULL,
    minimum_research_asset_cash_usd_text TEXT NOT NULL,
    pre_action_research_cash_usd_text TEXT NOT NULL,
    cash_capacity_usd_text TEXT NOT NULL,
    cash_floor_constrained_candidate_notional_usd_text TEXT NOT NULL,
    post_action_research_cash_usd_text TEXT NOT NULL,
    remaining_shortfall_usd_text TEXT NOT NULL,
    reduction_usd_text TEXT NOT NULL,
    disposition TEXT NOT NULL CHECK (disposition IN ('manual_review_required', 'blocked_by_research_cash_floor')),
    reason_codes_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    software_version TEXT NOT NULL,
    component_id TEXT NOT NULL CHECK (component_id = 'risk.target_adjustment_research_asset_cash_floor_preview'),
    component_version TEXT NOT NULL CHECK (component_version = '1.0.0'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_preview_result_id)
        REFERENCES target_adjustment_exposure_cap_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_review_result_id)
        REFERENCES target_adjustment_risk_review_results(review_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (definition_id, definition_version)
        REFERENCES research_asset_cash_floor_definitions(definition_id, definition_version)
        ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_cash_floor_results_lookup
ON target_adjustment_cash_floor_results
    (symbol, action, disposition, definition_id, definition_version, as_of_utc DESC);

CREATE TABLE target_adjustment_cash_floor_rule_results (
    rule_result_id TEXT PRIMARY KEY,
    preview_result_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    rule_id TEXT NOT NULL CHECK (rule_id = 'MIN_RESEARCH_ASSET_CASH_USD'),
    rule_version TEXT NOT NULL CHECK (rule_version = '1'),
    evaluation_order INTEGER NOT NULL CHECK (evaluation_order = 2),
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    research_capital_basis_usd_text TEXT NOT NULL,
    current_exposure_usd_text TEXT NOT NULL,
    phase6b_candidate_notional_usd_text TEXT NOT NULL,
    minimum_research_asset_cash_usd_text TEXT NOT NULL,
    pre_action_research_cash_usd_text TEXT NOT NULL,
    cash_capacity_usd_text TEXT NOT NULL,
    cash_floor_constrained_candidate_notional_usd_text TEXT NOT NULL,
    post_action_research_cash_usd_text TEXT NOT NULL,
    remaining_shortfall_usd_text TEXT NOT NULL,
    reduction_usd_text TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('passed_at_or_above_cash_floor', 'reduced_to_cash_floor', 'blocked_no_research_cash_capacity', 'preserved_research_cash_increasing_direction')),
    reason_codes_json TEXT NOT NULL,
    stop_processing INTEGER NOT NULL CHECK (stop_processing = 1),
    evaluated_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (preview_result_id)
        REFERENCES target_adjustment_cash_floor_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT
);

CREATE TABLE target_adjustment_cash_floor_source_links (
    source_link_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    preview_result_id TEXT NOT NULL UNIQUE,
    cash_floor_run_id TEXT NOT NULL UNIQUE,
    cash_floor_stage_id TEXT NOT NULL,
    phase6b_preview_result_id TEXT NOT NULL,
    phase6b_run_id TEXT NOT NULL,
    phase6b_stage_id TEXT NOT NULL,
    phase6a_review_result_id TEXT NOT NULL,
    phase6a_run_id TEXT NOT NULL,
    phase6a_stage_id TEXT NOT NULL,
    decision_run_id TEXT NOT NULL,
    linked_parent_run_id TEXT NOT NULL,
    target_child_run_id TEXT NOT NULL,
    standardized_state_run_id TEXT NOT NULL,
    decision_result_id TEXT NOT NULL,
    intent_id TEXT NOT NULL,
    target_position_link_id TEXT NOT NULL,
    target_calculation_id TEXT NOT NULL,
    standardized_state_calculation_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (preview_result_id)
        REFERENCES target_adjustment_cash_floor_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (cash_floor_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (cash_floor_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_preview_result_id)
        REFERENCES target_adjustment_exposure_cap_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_review_result_id)
        REFERENCES target_adjustment_risk_review_results(review_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (linked_parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_result_id)
        REFERENCES target_adjustment_decision_results(decision_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (intent_id)
        REFERENCES target_adjustment_trade_intents(intent_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_position_link_id)
        REFERENCES target_position_standardized_state_links(link_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_calculation_id)
        REFERENCES target_position_results(calculation_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_calculation_id)
        REFERENCES standardized_state_results(calculation_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_cash_floor_source_links_lookup
ON target_adjustment_cash_floor_source_links
    (phase6b_run_id, phase6a_run_id, decision_run_id, linked_parent_run_id, target_child_run_id, standardized_state_run_id);
"""


_SCHEMA_V13 = """
CREATE TABLE target_adjustment_research_asset_cash_operations (
    attempt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'blocked', 'invalid_input', 'failed')),
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    requested_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    requested_phase6c_result_id TEXT NOT NULL,
    requested_capital_plan_id TEXT NOT NULL,
    requested_capital_snapshot_id TEXT NOT NULL,
    resolved_source_json TEXT,
    current_safety_snapshot_json TEXT,
    resolved_symbol TEXT,
    resolved_action TEXT CHECK (resolved_action IS NULL OR resolved_action IN ('increase', 'decrease')),
    resolved_as_of_utc TEXT,
    preview_result_id TEXT,
    disposition TEXT CHECK (disposition IS NULL OR disposition IN ('manual_review_required', 'blocked_by_research_asset_cash')),
    error_code TEXT,
    error_summary TEXT,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    CHECK (
        (status = 'completed' AND error_code IS NULL AND error_summary IS NULL
            AND preview_result_id IS NOT NULL AND disposition IS NOT NULL)
        OR
        (status IN ('blocked', 'invalid_input', 'failed')
            AND error_code IS NOT NULL AND error_summary IS NOT NULL
            AND preview_result_id IS NULL AND disposition IS NULL)
    )
);

CREATE UNIQUE INDEX uq_target_adjustment_research_asset_cash_terminal_operation
ON target_adjustment_research_asset_cash_operations (operation_id)
WHERE status IN ('completed', 'blocked');

CREATE INDEX idx_target_adjustment_research_asset_cash_operations_lookup
ON target_adjustment_research_asset_cash_operations
    (operation_id, status, resolved_symbol, requested_at_utc DESC);

CREATE TABLE target_adjustment_research_asset_cash_results (
    preview_result_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    stage_id TEXT NOT NULL,
    source_json TEXT NOT NULL,
    phase6c_preview_result_id TEXT NOT NULL,
    phase6c_run_id TEXT NOT NULL,
    phase6c_stage_id TEXT NOT NULL,
    phase6b_run_id TEXT NOT NULL,
    phase6a_run_id TEXT NOT NULL,
    capital_plan_id TEXT NOT NULL,
    capital_plan_version INTEGER NOT NULL,
    capital_snapshot_id TEXT NOT NULL,
    capital_snapshot_run_id TEXT NOT NULL,
    asset_cash_bucket_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    phase6c_candidate_notional_usd_text TEXT NOT NULL,
    selected_asset_cash_balance_usd_text TEXT NOT NULL,
    asset_cash_constrained_candidate_notional_usd_text TEXT NOT NULL,
    hypothetical_post_candidate_asset_cash_usd_text TEXT NOT NULL,
    reduction_usd_text TEXT NOT NULL,
    research_cash_reserved INTEGER NOT NULL CHECK (research_cash_reserved = 0),
    disposition TEXT NOT NULL CHECK (disposition IN ('manual_review_required', 'blocked_by_research_asset_cash')),
    reason_codes_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    software_version TEXT NOT NULL,
    component_id TEXT NOT NULL CHECK (component_id = 'risk.target_adjustment_research_asset_cash_availability_preview'),
    component_version TEXT NOT NULL CHECK (component_version = '1.0.0'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6c_preview_result_id)
        REFERENCES target_adjustment_cash_floor_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6c_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6c_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_plan_id) REFERENCES capital_plans(plan_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_snapshot_id) REFERENCES capital_snapshots(snapshot_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_snapshot_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (asset_cash_bucket_id) REFERENCES capital_plan_buckets(bucket_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_snapshot_id, asset_cash_bucket_id)
        REFERENCES capital_snapshot_balances(snapshot_id, bucket_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_research_asset_cash_results_lookup
ON target_adjustment_research_asset_cash_results
    (symbol, action, disposition, capital_plan_id, capital_snapshot_id, as_of_utc DESC);

CREATE TABLE target_adjustment_research_asset_cash_rule_results (
    rule_result_id TEXT PRIMARY KEY,
    preview_result_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    rule_id TEXT NOT NULL CHECK (rule_id = 'MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD'),
    rule_version TEXT NOT NULL CHECK (rule_version = '1'),
    evaluation_order INTEGER NOT NULL CHECK (evaluation_order = 3),
    action TEXT NOT NULL CHECK (action IN ('increase', 'decrease')),
    phase6c_candidate_notional_usd_text TEXT NOT NULL,
    selected_asset_cash_balance_usd_text TEXT NOT NULL,
    pre_candidate_asset_cash_usd_text TEXT NOT NULL,
    asset_cash_constrained_candidate_notional_usd_text TEXT NOT NULL,
    hypothetical_post_candidate_asset_cash_usd_text TEXT NOT NULL,
    reduction_usd_text TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('passed_within_research_asset_cash', 'reduced_to_research_asset_cash', 'blocked_no_research_asset_cash', 'preserved_research_asset_cash_increasing_direction')),
    reason_codes_json TEXT NOT NULL,
    research_cash_reserved INTEGER NOT NULL CHECK (research_cash_reserved = 0),
    stop_processing INTEGER NOT NULL CHECK (stop_processing = 1),
    evaluated_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (preview_result_id)
        REFERENCES target_adjustment_research_asset_cash_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT
);

CREATE TABLE target_adjustment_research_asset_cash_source_links (
    source_link_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    preview_result_id TEXT NOT NULL UNIQUE,
    asset_cash_run_id TEXT NOT NULL UNIQUE,
    asset_cash_stage_id TEXT NOT NULL,
    phase6c_preview_result_id TEXT NOT NULL,
    phase6c_run_id TEXT NOT NULL,
    phase6c_stage_id TEXT NOT NULL,
    phase6b_run_id TEXT NOT NULL,
    phase6a_run_id TEXT NOT NULL,
    decision_run_id TEXT NOT NULL,
    linked_parent_run_id TEXT NOT NULL,
    target_child_run_id TEXT NOT NULL,
    standardized_state_run_id TEXT NOT NULL,
    capital_plan_id TEXT NOT NULL,
    capital_snapshot_id TEXT NOT NULL,
    capital_snapshot_run_id TEXT NOT NULL,
    asset_cash_bucket_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    FOREIGN KEY (preview_result_id)
        REFERENCES target_adjustment_research_asset_cash_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (asset_cash_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (asset_cash_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6c_preview_result_id)
        REFERENCES target_adjustment_cash_floor_results(preview_result_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6c_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6c_stage_id) REFERENCES algorithm_run_stages(stage_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6b_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (phase6a_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (linked_parent_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_child_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (standardized_state_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_plan_id) REFERENCES capital_plans(plan_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_snapshot_id) REFERENCES capital_snapshots(snapshot_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_snapshot_run_id) REFERENCES algorithm_runs(run_id) ON DELETE RESTRICT,
    FOREIGN KEY (asset_cash_bucket_id) REFERENCES capital_plan_buckets(bucket_id) ON DELETE RESTRICT,
    FOREIGN KEY (capital_snapshot_id, asset_cash_bucket_id)
        REFERENCES capital_snapshot_balances(snapshot_id, bucket_id) ON DELETE RESTRICT
);

CREATE INDEX idx_target_adjustment_research_asset_cash_source_links_lookup
ON target_adjustment_research_asset_cash_source_links
    (phase6c_run_id, phase6b_run_id, phase6a_run_id, capital_snapshot_run_id);
"""


_MIGRATIONS = {
    1: ("central market-data and factor-history schema", _SCHEMA_V1),
    2: ("unified non-executing algorithm run history", _SCHEMA_V2),
    3: ("Factor research history and durable Decision traces", _SCHEMA_V3),
    4: ("research capital allocation and conservation evidence", _SCHEMA_V4),
    5: ("manual asset-state definitions, cycles and replay evidence", _SCHEMA_V5),
    6: ("bounded target-position definitions and manual research previews", _SCHEMA_V6),
    7: ("manual standardized-price-state definitions and structured previews", _SCHEMA_V7),
    8: ("typed standardized-state to target-position research links", _SCHEMA_V8),
    9: ("typed linked-target adjustment Decision research evidence", _SCHEMA_V9),
    10: ("target-adjustment Risk manual-review evidence", _SCHEMA_V10),
    11: ("single-asset exposure-cap definitions and numerical Risk preview evidence", _SCHEMA_V11),
    12: ("research asset cash-floor definitions and order-2 Risk preview evidence", _SCHEMA_V12),
    13: ("research capital-plan asset-cash order-3 Risk preview evidence", _SCHEMA_V13),
}


@dataclass(frozen=True, slots=True)
class CentralSchemaInspection:
    """Read-only comparison of one database with the application schema contract."""

    supported_version: int
    applied_versions: tuple[int, ...]
    expected_tables: frozenset[str]
    actual_tables: frozenset[str]

    @property
    def current_version(self) -> int:
        return max(self.applied_versions, default=0)

    @property
    def expected_versions(self) -> tuple[int, ...]:
        return tuple(range(1, self.supported_version + 1))

    @property
    def missing_tables(self) -> frozenset[str]:
        return self.expected_tables - self.actual_tables

    @property
    def is_current_and_complete(self) -> bool:
        return (
            self.applied_versions == self.expected_versions
            and not self.missing_tables
        )


@lru_cache(maxsize=None)
def expected_schema_tables(target_version: int = SCHEMA_VERSION) -> frozenset[str]:
    """Return table names produced through one persistence-owned schema version."""

    if target_version < 0 or target_version > SCHEMA_VERSION:
        raise ValueError("target schema version is outside the supported range")
    with closing(sqlite3.connect(":memory:")) as connection:
        for version_number in range(1, target_version + 1):
            connection.executescript(_MIGRATIONS[version_number][1])
        return frozenset(
            row[0]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                """
            )
        )


def inspect_central_schema(
    connection: sqlite3.Connection,
    *,
    expected_version: int = SCHEMA_VERSION,
) -> CentralSchemaInspection:
    """Inspect migration history and required tables without modifying the database."""

    actual_tables = frozenset(
        row[0]
        for row in connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        )
    )
    applied_versions: tuple[int, ...] = ()
    if "schema_migrations" in actual_tables:
        applied_versions = tuple(
            int(row[0])
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
        )
    return CentralSchemaInspection(
        expected_version,
        applied_versions,
        expected_schema_tables(expected_version),
        actual_tables,
    )


class CentralSQLiteDatabase:
    """Own connections and idempotent schema initialization for one local file."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        backup_directory: Path | str | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.backup_directory = (
            Path(backup_directory)
            if backup_directory is not None
            else self.database_path.parent / "backups"
        )

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            existing_version = self._current_version(connection)
            if existing_version > SCHEMA_VERSION:
                raise sqlite3.DatabaseError(
                    "database schema is newer than this application supports"
                )
            if existing_version:
                self._validate_schema_contract(connection, existing_version)
            before_counts = self._table_counts(connection)
            if 0 < existing_version < SCHEMA_VERSION:
                self._backup_before_migration(connection, existing_version)
            for target_version in range(existing_version + 1, SCHEMA_VERSION + 1):
                description, migration_sql = _MIGRATIONS[target_version]
                try:
                    connection.executescript("BEGIN IMMEDIATE;\n" + migration_sql)
                    connection.execute(
                        """
                        INSERT INTO schema_migrations (
                            version, applied_at_utc, description
                        ) VALUES (?, ?, ?)
                        """,
                        (
                            target_version,
                            datetime.now(UTC).isoformat(timespec="microseconds"),
                            description,
                        ),
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
            self._validate_after_migration(connection, before_counts)

    @staticmethod
    def _current_version(connection: sqlite3.Connection) -> int:
        exists = connection.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_migrations'
            """
        ).fetchone()
        if not exists:
            return 0
        row = connection.execute(
            "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
        ).fetchone()
        return int(row["version"])

    @staticmethod
    def _table_counts(connection: sqlite3.Connection) -> dict[str, int]:
        tables = tuple(
            row["name"]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                  AND name <> 'schema_migrations'
                ORDER BY name
                """
            )
        )
        return {
            table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in tables
        }

    def _backup_before_migration(
        self,
        connection: sqlite3.Connection,
        existing_version: int,
    ) -> Path:
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        target = self.backup_directory / (
            f"{self.database_path.stem}.schema-v{existing_version}-to-v{SCHEMA_VERSION}."
            f"{timestamp}.sqlite3"
        )
        with closing(sqlite3.connect(target)) as backup:
            connection.backup(backup)
            integrity = backup.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.DatabaseError("pre-migration backup integrity check failed")
        return target

    @staticmethod
    def _validate_schema_contract(
        connection: sqlite3.Connection,
        expected_version: int,
    ) -> None:
        schema = inspect_central_schema(
            connection,
            expected_version=expected_version,
        )
        if schema.applied_versions != schema.expected_versions:
            raise sqlite3.DatabaseError(
                "database schema migration history is incomplete: "
                f"found {schema.applied_versions}, expected {schema.expected_versions}"
            )
        if schema.missing_tables:
            raise sqlite3.DatabaseError(
                "database schema is missing required tables: "
                + ", ".join(sorted(schema.missing_tables))
            )

    @staticmethod
    def _validate_after_migration(
        connection: sqlite3.Connection,
        before_counts: dict[str, int],
    ) -> None:
        CentralSQLiteDatabase._validate_schema_contract(connection, SCHEMA_VERSION)
        after_counts = CentralSQLiteDatabase._table_counts(connection)
        for table, count in before_counts.items():
            if after_counts.get(table) != count:
                raise sqlite3.DatabaseError(
                    f"migration changed existing row count for {table}"
                )
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise sqlite3.DatabaseError("migration produced foreign-key violations")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise sqlite3.DatabaseError("database integrity check failed after migration")
