# ADR-0014: Separate Asset/Market Factors and trace Decision sizing

Status: Accepted — 2026-07-15

Asset Factors remain single-symbol. Market Factors aggregate exact Asset Factor results and never own account state. Cash, equity and holdings enter Decision only as immutable context. Decision sizing is a proposed positive USD notional with traceable references; Risk cannot increase it. GUI editors remain definition-only and Simulation remains isolated from operational execution.
