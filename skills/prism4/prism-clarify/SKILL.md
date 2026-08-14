---
name: prism-clarify
description: "Prism 4.0 Clarify capability for one blocking question and optional semantic payload. Use when: Prism 4.0 clarify, blocking ambiguity, proposed patch, decision candidate, prism-clarify"
description_zh: "Prism 4.0 Clarify 能力：一次澄清一个阻塞歧义，并可选留下语义候选 payload。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Clarify

Use this skill when a Prism 4.0 topic is blocked by a human choice or ambiguous commitment.

## Rules

- Ask one question at a time. Investigate facts first; only ask the user for choices you cannot infer safely.
- Clarify may output semantic payloads such as `proposed-patch` or `decision-candidate`. These are candidates, not committed Decisions.
- Persist only when the user asks, or when the current work needs a durable 4.0 trace:

```bash
prism capability run clarify <topic_id> --root <topic_dir> --question "<question>" --proposed-patch "<patch>"
prism capability run clarify <topic_id> --root <topic_dir> --question "<question>" --decision-candidate "<candidate>"
```

- A committed Decision requires explicit authority. Do not treat an answer, recommendation, or candidate payload as a Decision unless the authority boundary is clear.
- Do not call 3.x `workflow-clarify`, create handoff files, or write scope/focus/task/wave artifacts.

## Output

Give the recommended answer briefly, then ask the single blocking question. After the user answers, restate what changed and whether anything still blocks progress.
