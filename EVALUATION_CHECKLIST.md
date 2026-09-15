# AI Offload Evaluation Checklist

Use this once per AI-backed capability, not once per model.

## 1. Define the capability

- [ ] Give the task a stable `task_id`.
- [ ] Identify every repo/service that calls it.
- [ ] Identify the current model/provider.
- [ ] Measure call volume, token volume, latency, and monthly cost.
- [ ] Capture representative inputs and accepted outputs.
- [ ] Record whether failures are reversible, detectable, and high-impact.

## 2. T0 challenge — can software already do this?

Ask these before considering *any* model:

- [ ] Is the answer defined by a grammar, schema, standard, protocol, lookup table, API, database, or mathematical rule?
- [ ] Is there an authoritative tool/library that already implements the operation?
- [ ] Is the task parsing, validation, normalization, conversion, formatting, filtering, joining, sorting, diffing, deduplication, hashing, encoding, decoding, or exact matching?
- [ ] Can a rules engine, policy engine, state machine, SQL/graph query, search index, or deterministic scoring formula answer it?
- [ ] Is the model merely deciding which existing tool to run when a small router could do so?
- [ ] Is the model being used to produce strict JSON that code could construct directly?
- [ ] Is the model being used to “look up” current facts that should come from an API/RAG/database instead?
- [ ] Can uncertainty be calculated from explicit data instead of generated linguistically?

If yes, prototype T0 before testing a model.

## 3. T1 challenge — is this only a narrow semantic decision?

Good T1 candidates:

- binary/multiclass classification
- intent detection
- route selection
- labels/tags
- simple entity type recognition
- allow/deny/needs-review decisions
- bounded extraction into a small schema
- similarity/relevance ranking where embeddings or a small cross-encoder are sufficient

Questions:

- [ ] Is the label space small and stable?
- [ ] Can the task be represented with examples?
- [ ] Is there little or no multi-step reasoning?
- [ ] Can errors be detected or escalated?
- [ ] Would a conventional ML classifier or embedding model work before an LLM?

## 4. T2 challenge — does a specialized SLM solve it?

Typical T2 work:

- domain-specific summarization
- entity/relation extraction
- schema generation from messy text
- security finding interpretation
- ATT&CK/CWE/CVE mapping where context matters
- bounded code/config explanation
- report normalization
- domain-specific question answering with RAG

Questions:

- [ ] Can a 3B–14B model meet the quality threshold?
- [ ] Can RAG/tools provide changing knowledge instead of putting facts into weights?
- [ ] Does one model support multiple capabilities, avoiding a model zoo?
- [ ] Is the output schema constrained and validated?

## 5. T3/T4 challenge — is frontier reasoning really necessary?

Use larger/local or frontier models when the task contains:

- novel or ambiguous evidence
- long-horizon planning
- cross-domain reasoning
- complex architecture
- difficult code generation/debugging
- conflicting sources
- high-impact decisions
- tasks where smaller models fail the evaluation threshold

Require an explicit reason for permanent T4 use.

## 6. Quality gate

Do not offload on intuition alone.

Record:

- [ ] gold dataset size
- [ ] acceptance metric
- [ ] required threshold
- [ ] frontier baseline
- [ ] candidate result
- [ ] latency
- [ ] failure modes
- [ ] human review rate
- [ ] escalation rate
- [ ] cost per 1,000 operations

Suggested metrics:

- exact match / schema validity
- precision / recall / F1
- ranking NDCG / MRR
- semantic similarity plus human acceptance
- task-specific pass/fail tests
- security-specific false-negative rate
- calibration / confidence accuracy

## 7. Routing policy

Preferred pattern:

```text
T0 deterministic
  ↓ if not sufficient
T1 tiny classifier
  ↓ low confidence / unsupported
T2 specialist SLM
  ↓ low confidence / conflict
T3 larger local reasoning model
  ↓ exceptional / high-impact / novel
T4 frontier model
```

A task may skip tiers. The router should choose the cheapest *validated* mechanism, not blindly walk the ladder.

## 8. Decision record

Every capability should end with:

- Current tier
- Proposed tier
- Current monthly cost
- Addressable frontier spend
- Quality baseline
- Candidate quality
- Estimated escalation rate
- Decision: `KEEP`, `OFFLOAD`, `HYBRID`, or `RETEST`
- Owner
- Review date
