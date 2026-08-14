# Prism 4.0 Refoundation Dogfood

This directory is the first Prism 4.0 dogfood topic state.

It uses the Phase 2 JSON reference adapter as an implementation choice, not as
the Prism Core storage contract.

```text
Topic: prism-4-refoundation
Adapter: prism4.reference-json
State: prism4-state.json
```

The state intentionally avoids Prism 3.x `workspace.*.local`, task, wave, and
workflow assumptions.
