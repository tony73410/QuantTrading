"""Private, source-neutral structural Risk gate shared by approved source families."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _StructuralGateRule:
    rule_id: str
    rule_version: str
    rule_name: str
    evaluation_order: int
    status: str
    input_summary: str
    expected_condition: str
    reason_codes: tuple[str, ...]
    severity: str
    stop_processing: bool


@dataclass(frozen=True, slots=True)
class _StructuralGateOutcome:
    status: str
    rules: tuple[_StructuralGateRule, ...]
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]


def evaluate_structural_manual_review_gate(
    *,
    source_summary: str,
    execution_environment: str,
    live_trading_enabled: bool,
    automatic_submission_enabled: bool,
    manual_confirmation_required: bool,
    execution_capability_implemented: bool,
) -> _StructuralGateOutcome:
    """Evaluate the locked three-rule sequence without source-family knowledge."""

    rules = [
        _StructuralGateRule(
            "SOURCE_CHAIN_INTEGRITY", "1", "Source chain integrity", 1, "passed",
            source_summary,
            "All immutable Decision and upstream identities agree",
            ("SOURCE_CHAIN_VERIFIED",), "info", False,
        )
    ]
    safe = (
        execution_environment != "alpaca_live"
        and not live_trading_enabled
        and not automatic_submission_enabled
        and manual_confirmation_required
        and not execution_capability_implemented
    )
    if not safe:
        rules.append(
            _StructuralGateRule(
                "NON_EXECUTION_SAFETY_STATE", "1", "Non-execution safety state", 2,
                "blocked",
                f"environment={execution_environment}; live={live_trading_enabled}; "
                f"automatic={automatic_submission_enabled}; manual={manual_confirmation_required}; "
                f"execution_capability={execution_capability_implemented}",
                "Live and automatic submission disabled, execution absent, manual confirmation required",
                ("UNSAFE_EXECUTION_STATE",), "critical", True,
            )
        )
        return _StructuralGateOutcome(
            "blocked", tuple(rules), ("UNSAFE_EXECUTION_STATE",),
            ("Risk review blocked by non-execution safety state.",),
        )
    rules.extend(
        (
            _StructuralGateRule(
                "NON_EXECUTION_SAFETY_STATE", "1", "Non-execution safety state", 2,
                "passed",
                f"environment={execution_environment}; live=false; automatic=false; "
                "manual=true; execution_capability=false",
                "Live and automatic submission disabled, execution absent, manual confirmation required",
                ("NON_EXECUTION_STATE_VERIFIED",), "info", False,
            ),
            _StructuralGateRule(
                "NUMERICAL_RISK_POLICY_AVAILABILITY", "1",
                "Numerical Risk policy availability", 3, "manual_review",
                "approved numerical policy=absent",
                "An explicitly approved numerical Risk policy is required before financial approval",
                ("NUMERICAL_RISK_POLICY_NOT_AVAILABLE", "MANUAL_REVIEW_REQUIRED"),
                "warning", True,
            ),
        )
    )
    return _StructuralGateOutcome(
        "manual_review_required", tuple(rules),
        ("MANUAL_REVIEW_REQUIRED", "NO_NUMERICAL_RISK_POLICY"),
        ("Requested notional remains unapproved research evidence.",),
    )


__all__ = ["evaluate_structural_manual_review_gate"]
