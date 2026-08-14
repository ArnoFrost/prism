---
name: prism-review
description: "Prism 4.0 Review 能力：审视当前状态并产出 Findings，不自动形成决策。Use when: Prism 4.0 review、findings、risk review、semantic review、评审、prism-review"
description_zh: "Prism 4.0 Review 能力：审视当前状态并产出 Findings，不自动形成决策。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Review — 产出 Findings 的审视能力

使用本技能执行一次有边界的 Prism 4.0 Review，产出 Findings。

## 规则

- Review 是一个 Capability。其输出是 Findings：观察、风险、缺口、冲突、假设、取舍点或建议，用于暴露理解上的相关变化。
- Findings 是建议性的。它们不授权实施、不修改 Intent，也不构成 Decision。
- 当活跃状态尚不清晰时，先用 `prism brief project <topic_id> --root <topic_dir>` 恢复上下文。
- 仅在用户要求、或当前工作需要持久化 4.0 痕迹时才落盘：

```bash
prism capability run review <topic_id> --root <topic_dir> --body "<finding body>"
```

- 不要创建 3.x 的 `reviews/rXX.md`、`review.index.md`、Gate 4、dXX、scope/focus、task 或 wave 产物。

## 输出

先给出最强 Findings 及其对下一步的影响。当区分重要时，把事实与建议分开。
