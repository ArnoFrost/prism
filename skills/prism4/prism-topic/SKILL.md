---
name: prism-topic
description: "Prism 4.0 Topic boundary management. Use when: Prism 4.0 topic, create topic, list topic, 子 Topic, prism-topic"
description_zh: "Prism 4.0 Topic 边界管理：创建、列出和定位 4.0 协作问题空间。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Topic

Use this skill only for Prism 4.0 topics backed by `prism4-state.json`.

## Rules

- Topic is the durable collaboration boundary. Do not create a `Task` hierarchy for 4.0; use child Topics for durable subproblems and Plan Items for ordinary execution steps.
- Prefer the canonical CLI:

```bash
prism topic list
prism topic new <topic_id> --title "<title>" --root <topic_dir> --intent "<intent>"
```

- Resolve the topic root from the user's explicit path first. If omitted, run `prism topic list` from the project root and choose the only active 4.0 topic when unambiguous.
- Do not call `workflow-intake`, create `scope.md`, `focus.md`, `task.index.md`, `wave`, `reviews/`, or `decisions/` for a 4.0 Topic.
- If the requested work belongs to an old 3.x workspace, stop and say this skill is for 4.0 only; legacy handling should use explicit `prism legacy ...` or old workflow skills.

## Output

Report the Topic id, root, and current next useful action. Keep the answer short; Topic creation is scaffolding, not a planning ceremony.
