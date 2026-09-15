# AI Offload Audit

**AI Offload Audit** is a local, provider-neutral repository scanner for finding places where expensive AI/model calls may be replaceable by deterministic software or smaller models.

Its core question is simple:

> **What is the least expensive mechanism that can perform this capability at the required quality and risk level?**

The project does **not** assume that local models are always better. It identifies candidates and provides a repeatable evaluation framework so teams can measure quality before changing production traffic.

## Why this exists

AI-enabled applications often send work to a frontier model simply because an LLM is already available. Over time, model calls can accumulate around tasks that ordinary software, a classifier, an embedding model, or a small language model could perform more cheaply and consistently.

Examples include parsing, validation, field normalization, database lookups, deterministic scoring, routing, classification, bounded extraction, and schema generation.

AI Offload Audit helps make those decisions visible.

## The tier model

| Tier | Default mechanism | Typical use |
|---|---|---|
| **T0** | Deterministic software / native tools | Parsing, validation, transforms, lookups, rules, math, exact matching, schema enforcement |
| **T1** | Tiny model / classifier | Routing, labeling, intent detection, simple extraction, narrow classification |
| **T2** | Specialized SLM | Domain extraction, summarization, mapping, interpretation, constrained generation |
| **T3** | Larger local reasoning model | Correlation, multi-document synthesis, complex code/domain analysis |
| **T4** | Frontier model | Novel reasoning, ambiguity, high-impact decisions, difficult planning |

A task does not have to walk through every tier. The objective is the **cheapest validated tier**, not blindly preferring local inference.

## What T0 actually means

T0 is much broader than regular expressions. It includes any capability where ordinary software can produce a reliable answer, such as:

- JSON/YAML/XML/CSV parsing and schema validation
- IP, CIDR, URL, UUID, timestamp, semver, and identifier handling
- MIME/file-type detection and archive inspection
- hashing, checksums, signatures, encoding/decoding
- canonicalization and normalization
- SQL/graph/database queries
- API and authoritative-data lookups
- deterministic risk/scoring formulas
- sorting, filtering, joins, deduplication, and diffing
- policy/rules engines and workflow state machines
- template rendering and strict output construction
- invoking an existing library, CLI, or service that already knows the answer

Natural-language input does not automatically make a problem an LLM problem.

## Privacy

The scanner runs **locally** and requires no model API or external service. Repository contents are not transmitted anywhere by the core tool.

## Install

Requires Python 3.10+.

```bash
git clone <your-fork-or-repository-url>
cd ai-offload-audit
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e .
```

Then:

```bash
ai-offload-audit /path/to/repository
```

Or without installation:

```bash
PYTHONPATH=src python -m ai_offload_audit /path/to/repository
```

## Basic usage

```bash
ai-offload-audit /path/to/repo \
  --out ai-offload-report.md \
  --json ai-offload-report.json
```

The report identifies likely model-call sites, examines nearby capability signals, and assigns a **candidate** T0–T4 tier with rationale and a recommended next test.

It is intentionally advisory. Static analysis cannot prove that a model can be removed safely.

## Cost overlay

Static analysis tells you *where* models may be unnecessary. Usage telemetry tells you *what is worth fixing first*.

Optional usage JSONL:

```json
{"task_id":"normalize_record","model":"example-model","input_tokens":1200,"output_tokens":220,"calls":5000}
```

Optional pricing JSON:

```json
{
  "example-model": {
    "input_per_million_usd": 1.00,
    "output_per_million_usd": 4.00
  }
}
```

Run:

```bash
ai-offload-audit /path/to/repo \
  --usage examples/sample-usage.jsonl \
  --pricing examples/sample-pricing.json \
  --out ai-offload-report.md \
  --json ai-offload-report.json
```

Prices are supplied by the user because provider pricing changes. The tool does not hard-code or silently fetch pricing.

## What it detects

The initial scanner recognizes patterns associated with:

- OpenAI-compatible APIs
- Anthropic
- Amazon Bedrock
- Google GenAI
- LiteLLM
- LangChain/LangGraph-style invocation
- Ollama
- vLLM / local OpenAI-compatible servers
- Hugging Face Transformers
- generic chat-completion/model invocation patterns

It scans common Python, JavaScript/TypeScript, Go, Rust, Java, C#, shell, YAML, JSON, TOML, and Markdown files.

## Recommended audit workflow

1. **Inventory** AI/model calls.
2. **Instrument** each call with a stable `task_id`, tokens, latency, outcome, and provider/model.
3. **Rank** workloads by real spend and volume.
4. **Challenge T0 first.** Ask whether ordinary software already solves the task.
5. **Challenge T1 next.** Test rules, classical ML, embeddings, rerankers, or tiny models.
6. **Benchmark T2/T3** against a gold dataset.
7. **Keep T4** when frontier reasoning is genuinely required.
8. **Route low-confidence cases upward** instead of forcing a cheap tier to answer everything.
9. **Re-evaluate periodically** as models, prices, and workloads change.

See [EVALUATION_CHECKLIST.md](EVALUATION_CHECKLIST.md) for the complete review checklist.

## Usage instrumentation

Provider billing dashboards often show *which model* consumed money but not *which application capability* caused the spend.

A useful event contains at least:

```json
{
  "project": "example-service",
  "task_id": "normalize_record",
  "provider": "provider-name",
  "model": "model-name",
  "input_tokens": 1234,
  "output_tokens": 212,
  "latency_ms": 842,
  "success": true
}
```

That makes analyses such as this possible:

```text
normalize_record        $620/month
route_request           $410/month
summarize_document      $830/month
architecture_reasoning  $540/month
```

Now a team can optimize the $620 deterministic-looking workload without blindly touching the $540 complex-reasoning workload.

See [AI_USAGE_INSTRUMENTATION.md](AI_USAGE_INSTRUMENTATION.md).

## Portfolio view

Aggregate reports across unrelated repositories:

```bash
python aggregate_ai_offload_reports.py \
  ../service-a/ai-offload-report.json \
  ../service-b/ai-offload-report.json \
  ../service-c/ai-offload-report.json \
  --out ai-offload-portfolio.md
```

This creates an estate-level view of candidate tiers and, when usage telemetry is provided, the highest-cost tasks.

## CI

Two GitHub Actions workflows are included:

- `ci.yml` — tests the project on supported Python versions.
- `ai-offload-audit.yml` — runs the audit against pull requests and uploads the generated report.

The default workflow is visibility-only. It does not block a build because a frontier-model call exists.

## Governance

A mature implementation can give each AI-backed capability a small manifest defining:

- stable task ID
- owner
- current and approved tiers
- model/provider
- quality gate
- fallback/escalation tier
- review date

See [REPO_GOVERNANCE.md](REPO_GOVERNANCE.md).

## Limitations

This is an early static-analysis tool, not a semantic compiler.

- It can miss dynamically constructed model calls.
- It can produce false positives from documentation or wrapper functions.
- Nearby keywords do not prove that a lower tier will meet production quality.
- Cost analysis is only as accurate as the usage and pricing data supplied.
- A recommendation to evaluate T0/T1/T2 is **not** a recommendation to remove human review or safety controls.

Treat findings as an engineering backlog, then validate them with tests and real workload data.

## Development

```bash
pip install -e .
python -m unittest discover -s tests -v
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
