# Contributing to TD-1 Simulacrum

TD-1 is intentionally strange. The engineering process should not be.

## Development setup

```bash
python -m pip install -e '.[dev]'
pytest --cov=td1_simulacrum
ruff check .
```

## Contribution rules

1. Preserve determinism unless a change explicitly introduces a modeled source of uncertainty.
2. Keep the arithmetic core independent from phenomenology and rendering.
3. Do not present subjective reports as established external causes.
4. Add tests for new machine semantics, state mappings, or parsers.
5. Label approximations and accuracy limits explicitly.
6. Do not freeze a physical encoding or hardware assumption merely because it looks elegant.
7. Any corpus-derived requirement should be traceable to source records and a validation method.

## Commit/PR expectations

A meaningful change should explain:

- what contract changed;
- why it changed;
- what tests prove the new behavior;
- whether it affects hardware parity, corpus provenance, or state serialization;
- whether the change is backwards-compatible.

## Review doctrine

Low threshold for listening. High threshold for believing. Extremely high threshold for merging.
