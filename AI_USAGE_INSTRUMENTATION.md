# AI Usage Instrumentation Standard

Static code scanning can tell us **where** models appear to be used. It cannot reliably tell us **how much they cost** unless the applications expose usage.

Use one common event schema across all projects.

## Event schema

Emit one event per model request:

```json
{
  "timestamp": "2026-09-15T12:00:00Z",
  "project": "example-service",
  "task_id": "normalize_finding",
  "provider": "provider-name",
  "model": "model-name",
  "input_tokens": 1234,
  "output_tokens": 212,
  "cached_input_tokens": 0,
  "latency_ms": 842,
  "success": true,
  "fallback_used": false,
  "requested_tier": 2,
  "executed_tier": 4,
  "quality_outcome": "accepted",
  "request_id": "optional-provider-request-id"
}
```

Do **not** log secrets, API keys, full prompts, or sensitive payloads merely to calculate spend.

## Minimum fields

At minimum capture:

- project
- task_id
- provider
- model
- input tokens
- output tokens
- latency
- success/failure

`task_id` is the key field. Provider dashboards can show model spend; they usually cannot tell you **which business capability consumed it**.

## Why task_id matters

Bad:

```text
model = frontier-model
monthly spend = $2,400
```

Useful:

```text
normalize_finding      $620
route_request           $410
summarize_report        $830
architecture_reasoning  $540
```

Now the audit can attack the $620 normalization problem with T0/T1 methods while leaving the $540 architecture workload alone if frontier reasoning is justified.

## Recommended control point

Long term, route model access through a shared internal client/gateway rather than letting every repo call providers directly.

```text
application
    ↓
AI client / gateway
    ↓
task_id + policy + telemetry
    ↓
T0 / T1 / T2 / T3 / T4 provider
```

This gives one place to:

- enforce tier routing
- collect token usage
- calculate cost
- redact sensitive data
- apply retries/timeouts
- record model/version
- enforce allowed providers
- perform confidence escalation
- A/B test replacements
- shut off unjustified frontier calls
