# Suggested Repo Control

After measurement is working, add an `ai-task-manifest.json` to every AI-enabled repository.

Example:

```json
{
  "tasks": [
    {
      "task_id": "normalize_finding",
      "owner": "security-engineering",
      "current_tier": 4,
      "approved_max_tier": 2,
      "fallback_tier": 4,
      "quality_gate": {
        "metric": "schema_valid_and_field_accuracy",
        "minimum": 0.98
      }
    }
  ]
}
```

The manifest creates an explicit contract:

- What AI capability exists?
- Why does it exist?
- What is the cheapest validated tier?
- When may it escalate?
- Who owns it?
- How do we know it still performs correctly?

Eventually CI can flag:
- a new direct frontier-provider call with no registered task
- a task exceeding its approved tier
- missing telemetry
- model/version drift
- a T4 task that has never been reevaluated

Start with visibility before enforcement.
