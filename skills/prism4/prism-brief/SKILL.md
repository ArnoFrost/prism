---
name: prism-brief
description: "Prism 4.0 Brief projection for context recovery. Use when: Prism 4.0 brief, context recovery, current slice, project brief, prism-brief"
description_zh: "Prism 4.0 Brief 投影：从当前有效工件再生成上下文恢复切片。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Brief

Use this skill to recover or refresh the current context of a Prism 4.0 topic.

## Rules

- Brief is a projection, not a source of truth. Intent, authoritative Decisions, and current non-superseded Artifacts outrank Brief when conflicts appear.
- Brief may be regenerated at any time from the current topic state.
- Prefer the canonical CLI:

```bash
prism brief project <topic_id> --root <topic_dir>
```

- If the Brief conflicts with Intent, Findings, Decision semantics, or Plan, identify the conflict as a Finding or ask for clarification. Do not silently treat Brief as authoritative.
- Do not create 3.x `focus.md` or rewrite old workflow files from this skill.

## Output

Return a compact recovery summary: current objective, important evidence, committed constraints, open risks, and the next useful action.
