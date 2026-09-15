# Contributing

Contributions are welcome.

## Development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e .
python -m unittest discover -s tests -v
```

## Design principles

1. **Capability first.** Classify the work being done, not the vendor/model name.
2. **Deterministic before probabilistic.** If ordinary software can reliably solve the task, prefer it.
3. **Measured quality.** Never claim that a smaller model is sufficient without an evaluation gate.
4. **Advisory by default.** Static findings are candidates for review, not automatic rewrites.
5. **Local and private.** The core scanner must not require sending source code to a third party.
6. **Provider neutral.** New detectors should not favor one model vendor.

Please include tests for new provider patterns, tier signals, or report behavior.
