# Compact Maintainer Reference

> 维护者参考。Happy path 优先读 `SKILL.md`；本文件承载参数、字段枚举与实现边界，避免主入口过载。

## 1. References 加载策略

| 阶段 | 必读 | 说明 |
|------|------|------|
| preview | `SKILL.md` + `references/compact-policy.md` | Phase 2 分类前必须读 policy protected 矩阵 |
| apply | preview 必读 + `references/compact-template.md` | Gate B 前读取模板，规范 result / manifest 记录 |
| backup | `scripts/compact_backup.py --help` | 仅确认参数与输出路径，不替代用户 apply 授权 |

原则：compact 不追 Required Reads=1；安全与恢复优先于行数压缩。

## 2. 参数

| 参数 | 说明 | 默认 / 规则 |
|------|------|-------------|
| `topic_dir` | topic 目录路径 | 必填 |
| `--preview` | 只输出 compact plan | 默认行为；writes=0 |
| `--apply` | 执行用户确认范围内的整理动作 | 必须已有 preview + Gate A + Gate B |
| `--backup-root` | 备份目录 | `{topic_dir}/.compact_backups/` |
| `--keep-recent` | 保留最近 N 个决策 / 评审在 active 上下文 | 建议默认 `3` |

`compact_backup.py` 当前 fallback：

```bash
uv run python skills/workflow/workflow-compact/scripts/compact_backup.py "{topic_dir}"
```

## 3. 反例

| 反例 | 正确处理 |
|------|----------|
| 把 `digest.md` 当 compact 后长期事实源 | digest 只是对外交接切片，非 SSOT |
| 无 preview 直接移动文件 | 拒绝；先输出 compact_plan |
| 无 backup manifest 直接 apply | 拒绝；先运行 backup gate |
| 为省 token 改写 `decisions/*.md` / `reviews/r*.md` 正文 | 禁止；权威工件 protected |
| 把 cold storage 与 workspace `archive/` 混用 | compact 仅 topic 内维护；整 topic 结束转 workflow-archive |
| 顺手修 README / review.index 指针 | 建议 workflow-tidy，不在 compact 内修 |
| 顺手勾 scope V 或 rewrite focus | 转 workflow-scope；compact 不改语义合同 |

## 4. `backup_manifest.json` 字段枚举

`compact_backup.py` 输出 manifest 至时间戳备份目录。实现应至少保留并可读以下信息：

| 字段 | 含义 |
|------|------|
| `target` / `source` | 原始 topic 路径 |
| `backup_dir` | 备份目录 |
| `created_at` | 创建时间 |
| `file_count` | 备份文件数量 |
| `total_bytes` | 总字节数 |
| `files[]` | 相对路径、大小、sha256 |
| `restore_hint` | 恢复提示 |

apply 结果中的 `compact_result.backup_manifest` 必须指向该 manifest。

## 5. 目录结构 / 脚本路径

```text
workflow/workflow-compact/
├── SKILL.md                         # 主入口：preview-first + Gate A/B
├── references/
│   ├── compact-policy.md            # protected / active / cold / summarize / delete-candidate 矩阵
│   ├── compact-template.md          # preview/result 输出模板
│   └── compact-maintainer.md        # 本文件
└── scripts/
    └── compact_backup.py            # Gate B 备份门禁
```

相关边界：

| 技能 | 关系 |
|------|------|
| `workflow-digest` | 对外摘要；compact 不写 digest |
| `workflow-tidy` | 机械对齐；compact 只建议 tidy |
| `workflow-scope` | 合同更新；compact 不改 scope/focus 语义 |
| `workflow-archive` | 整 topic 生命周期移动；compact 不调用 archive/reactivate |
