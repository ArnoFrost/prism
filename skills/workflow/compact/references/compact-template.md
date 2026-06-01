# Compact Template — Preview 输出骨架

## Markdown 骨架

```markdown
# Compact Preview — {topic}

## 结论

- 是否建议 compact：否 / 继续观察 / 需要 review
- 原因：{一句话}
- 写入：0（preview-only）

## 认知熵来源

| 熵源 | 现象 | 证据 |
|------|------|------|
| context_entropy | 跨会话恢复需要读太多材料 | ... |
| decision_entropy | 已定结论被重复讨论 | ... |

## 分类结果

| 类别 | 文件 / 目录 | 理由 | 建议 |
|------|-------------|------|------|
| protected | `scope.md` | 合同面 SSOT | 只读 |
| active | `focus.md` | 当前工作集 | 保留 |
| cold | `references/old.md` | 历史输入，当前不必读 | 仅列候选 |
| summarize | `reviews/r01_*.md` | 长评审，可保留 TL;DR 指针 | 建议摘要，不改原文 |
| delete-candidate | `tmp.md` | 临时重复文件 | 仅列出，不删除 |

## Next Step

- 建议：observe / review / defer
- 若要写入任何文件：先发起 review / decision，不在 compact preview 中执行。
```

## YAML 骨架

```yaml
compact_plan:
  topic: "{topic}"
  mode: preview
  writes: 0
  recommend_apply: false
  entropy_sources:
    - context_entropy
  protected: []
  active: []
  cold: []
  summarize: []
  delete_candidates: []
  next_step: observe
```

## 样本记录字段

用于 041 task-4 wave-5：

| 字段 | 说明 |
|------|------|
| 项目 / 场景 | compact preview 应用在哪个 topic / 任务 |
| 进入前上下文 | Agent 接手前需要读什么 |
| 主要熵源 | context / decision / attention / structure |
| Prism 机制 | compact preview 与 focus / decision / task 的关系 |
| 正样本 | 是否降低恢复或误路由成本 |
| 负样本 | 是否增加解释或维护成本 |
| 代理指标 | 恢复耗时 / 误路由 / 重复解释 / focus rewrite / scope 密度 |
| 后续建议 | observe / review / defer |
