---
name: prism-review
description: "Prism 4.0 Review capability that exposes Findings without committing decisions. Use when: Prism 4.0 review, findings, risk review, semantic review, prism-review"
description_zh: "Prism 4.0 Review 能力：审视当前状态并产出 Findings，不自动形成决策。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Review

Use this skill for a bounded Prism 4.0 review that produces Findings.

## Rules

- Review is a Capability. Its output is Findings: observations, risks, gaps, conflicts, assumptions, trade-offs, or suggestions that expose relevant change in understanding.
- Findings are advisory. They do not authorize implementation, mutate Intent, or become Decision.
- First recover context with `prism brief project <topic_id> --root <topic_dir>` when the active state is not already clear.
- Persist only when the user asks, or when the current work needs a durable 4.0 trace:

```bash
prism capability run review <topic_id> --root <topic_dir> --body "<finding body>"
```

- Do not create 3.x `reviews/rXX.md`, `review.index.md`, Gate 4, dXX, scope/focus, task, or wave artifacts.

## Output

Lead with the strongest Findings and the implication for the next step. Separate facts from suggestions when that distinction matters.
