# Review 技能维护者文档

> 面向技能维护者，Agent 执行时不需要关注。
>
> **路径变量**：本文中 `{skill_dir}` 指 SKILL.md 文件所在目录的绝对路径（Cursor skill 根 / CodeBuddy `{baseDir}`）。

## 目录结构

```
prism/skills/                         ← SDK 仓库内置
├── workflow/
│   ├── shared/                       ★ 共享模块
│   │   ├── obsidian-config.md
│   │   ├── parallel-execution.md
│   │   └── scripts/
│   │       └── prism_sync_sniff.py
│   │
│   └── review/                       ★ 本技能
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── sniff.py
│       │   └── validate_product.py
│       └── references/
│           ├── review-ofm.md
│           ├── review-templates.md
│           ├── review-maintainer.md
│           ├── obsidian-config.md    → ../../shared/obsidian-config.md  ★ 软链接
│           └── parallel-execution.md → ../../shared/parallel-execution.md  ★ 软链接
```

## 软链机制

- `references/` 下的软链接指向 `../../shared/`，由 **Git 原生跟踪**
- clone 后自动还原，无需额外脚本
- SDK `bin/relink` 将 `workflow/review/` 整体软链到 IDE skills 目录时，references 内的相对路径软链仍然有效（因为指向的 `shared/` 在仓库内）
- 保证了**技能自包含**：Agent 通过 `{skill_dir}/references/obsidian-config.md` 即可读取

## references 加载策略

| 文件 | 来源 | 何时加载 |
|------|------|---------|
| `review-ofm.md` | 本技能 | Align 阶段判定 `format=ofm` 后 |
| `review-templates.md` | 本技能 | Merge 阶段落盘前 |
| `obsidian-config.md` | shared 软链 | 需要链接规范细节时 |
| `parallel-execution.md` | shared 软链 | Align 阶段判定 `mode=full` 后 |
