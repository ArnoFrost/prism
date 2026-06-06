# Tidy Maintainer Reference

> 第三层维护面 — CLI fallback、类比教学、目录元信息。Happy path **不必读取**本文件。

## CLI fallback

`prism tidy` 不可用时：

```bash
uv run python {skill_dir}/scripts/tidy.py <project_dir> [--fix] [--topic <topic_dirname>]
```

## 与 code-simplifier 的对应关系

| code-simplifier | workflow-tidy |
|----------------|----------------|
| 保持功能不变，只改写法 | 保持决策不变，只改状态 |
| 消除冗余嵌套 | 消除过时指针 |
| 对齐编码规范 | 对齐 frontmatter 规范 |
| review 通过后执行 | decision 落地后执行 |
| 自主修改代码 | 自主修改元数据（语义变更仅报告） |

## 目录结构

```
workflow/tidy/
├── SKILL.md
├── references/
│   └── tidy-maintainer.md    # 本文件
└── scripts/
    ├── tidy.py
    └── sniff_lib.py          → ../../shared/sniff_lib.py
```

## archive 与 review 延伸

| 技能 | 与 tidy 的关系 |
|------|----------------|
| **review** | review 落盘后，tidy 同步 review.index / grandfather README |
| **scope** | tidy 不改 scope，只报告 scope checkbox 状态 |
| **archive** | tidy 可作为归档前预检；整 topic 归档用 `prism archive` |
