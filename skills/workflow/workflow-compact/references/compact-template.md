# Compact Templates

## Preview 输出模板

```markdown
# Compact Preview — {topic}

## 结论

- 是否建议 compact：否 / 继续观察 / 需要 review / 可进入 apply
- 原因：{一句话}
- 写入风险：低 / 中 / 高

## 认知熵来源

| 熵源 | 现象 | 证据 |
|------|------|------|
| context_entropy | 跨会话恢复需要读太多材料 | ... |
| decision_entropy | 已定结论被重复讨论 | ... |

## 分类结果

| 类别 | 文件 / 目录 | 理由 | 建议动作 |
|------|-------------|------|----------|
| protected | `scope.md` | 合同面 SSOT | 只读 |
| active | `focus.md` | 当前工作集 | 保留 |
| cold | `reviews/raw/` | 原始角色报告，平时不必读取 | 备份后冷存 |
| summarize | `reviews/r01_*.md` | 长评审，可保留 TL;DR 指针 | 生成摘要，不改原文 |
| delete-candidate | `temp/foo.md` | 临时重复文件 | 仅列出，不删除 |

## Proposed Writes

| 文件 | 动作 | 风险 |
|------|------|------|
| — | — | — |

## Apply 前置门禁

- [ ] 用户确认 apply 范围
- [ ] 已运行 compact backup
- [ ] 已记录 backup manifest 路径
- [ ] 无 hard delete
```

## Preview YAML 骨架

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
  proposed_writes: []
  requires_backup: true
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
| 后续建议 | observe / review / defer / apply |

## Apply 结果模板

```markdown
# Compact Result — {topic}

## Backup

- manifest: `{backup_manifest}`
- backup_dir: `{backup_dir}`
- restore: `{restore_hint}`

## Changes

| 文件 | 动作 | 说明 |
|------|------|------|
| — | — | — |

## Untouched Delete Candidates

- `{path}` — 首版只列出，不删除

```yaml
compact_result:
  topic: "{topic}"
  mode: apply
  backup_manifest: "{backup_manifest}"
  files_changed: []
  files_moved: []
  delete_candidates_left_untouched: []
  restore_hint: "{restore_hint}"
```
```
