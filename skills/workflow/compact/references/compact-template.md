# Compact Templates

## Preview 输出模板

```markdown
# Compact Preview — {topic}

## 结论

- 是否建议 compact：是 / 否
- 原因：{一句话}
- 写入风险：低 / 中 / 高

## 分类结果

| 类别 | 文件 / 目录 | 理由 | 建议动作 |
|------|-------------|------|----------|
| protected | `scope.md` | 合同面 SSOT | 只读 |
| active | `README.md` | 当前恢复入口 | 保留 |
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
