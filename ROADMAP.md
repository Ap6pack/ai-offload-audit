# Roadmap

AI Offload Audit starts as a local static-analysis and cost-attribution tool. The project should grow only where additional automation improves evidence-based tier decisions.

## Near term

- Expand provider and SDK call-site detection.
- Add stronger language-aware call-site analysis with optional parsers while preserving a dependency-free core.
- Correlate static findings with `task_id` usage telemetry.
- Add SARIF output for code-scanning workflows.
- Add configurable quality/risk policies.
- Improve confidence calibration and explainability of candidate tiers.

## Mid term

- Detect duplicated AI capabilities across multiple repositories.
- Produce estate-level cost/offload recommendations.
- Support trace ingestion from common observability and LLM telemetry formats.
- Add an evaluation runner for candidate T0/T1/T2 replacements.
- Add regression gates for model/tier changes.

## Long term

- Policy-as-code for approved maximum intelligence tiers.
- Automated routing recommendations based on measured quality, latency, cost, and risk.
- Historical tracking of realized token and dollar savings.
- Pluggable analyzers for domain-specific deterministic alternatives.

The project will not assume that frontier-model use is bad. The objective is to make its use intentional and measurable.
