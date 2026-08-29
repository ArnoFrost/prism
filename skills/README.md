# skills/ — 技能层

SDK 内置的 4.0 semantic skills 是唯一分发面。3.x `workflow/` / `workspace/` 已随 prism-4 分支剔除（终态见 git tag `legacy-3x-final`）。

## 目录结构

```
skills/
├── README.md
├── schema/
│   ├── skill.schema.yaml
│   ├── frontmatter-spec.md
│   ├── skills-catalog.yaml
│   └── dist-whitelist.yaml
├── templates/
│   └── SKILL.template.md
└── prism4/                 # 4.0 SDK skill inventory（不等于当前 profile）
    ├── prism/
    ├── prism-review/
    ├── prism-plan/
    ├── prism-topic/        # control / compatibility / rollback source
    ├── prism-brief/        # control / compatibility / rollback source
    ├── prism-clarify/      # control / compatibility / rollback source
    └── prism-compress/     # control / compatibility / rollback source
```

## 技能分类

| 类别 | 位置 | 技能 |
|------|------|------|
| prism4 | `skills/prism4/` | prism / prism-review / prism-plan + 四个旧 wrappers source |
| dev ops | `~/prism-skills` (外部) | prism-maintain（个人多端全环境同步与冲突处理） |
| utility | `~/prism-skills` (外部) | commit, digest, learnnote, humanizer 等 |

## 4.0 semantic skill surface

当前 `prism-4` 分支处于 **P5 optimistic dogfood**。`dist-whitelist.yaml` 是唯一分发面 authority，当前 profile 为：`prism / prism-review / prism-plan`。这仍是 experimental 安装面，不代表 P6 最终 cutover。

| Skill | 触发 | 输入 | 产出 |
|-------|------|------|------|
| `prism` | `/prism` | state-operation intent / Topic state | effect-first Recover / Topic / Clarify / Maintain / Absorb route |
| `prism-review` | `/prism-review` | 当前材料 / 风险或校准问题 | Findings |
| `prism-plan` | `/prism-plan` | Intent / Decisions / runtime context / optional Plan | advisory Plan |

旧 wrappers `prism-topic / prism-brief / prism-clarify / prism-compress` 仍保留在 SDK，作为 controls / compatibility / rollback source，**不属于当前默认 distribution profile**。所有 Skills 继续使用 `bin/prism` 的 4.0 reference adapter，不创建 3.x `scope.md` / `focus.md` / `task.index.md` / `wave` 工件。

## SDK 与外部技能的关系

```
~/prism/skills/     (SDK 内置)   — 4.0 semantic skills（随 SDK 版本发布；3.x 已剔除）
~/prism-skills/     (外部注入)   — 个人工具 + dev ops（独立 Git，可分发）
iCloud vault        (Workspace)  — 项目状态（iCloud 同步）
```

SDK 内置技能只定义 canonical 语义能力与实验 packaging。个人可在 `~/prism-skills` 中追加 Style Profile 类技能（例如 Obsidian/OFM 呈现偏好），用来增强 Prism Artifact 的阅读性；这类 profile 默认不启用，不进入 Core，也不得改变 Artifact/Decision/Brief/Findings 的语义。

内置技能通过 SDK `bin/relink` 分发到 IDE 环境；外部技能通过 `prism-skills` 自带 `relink` 分发。SDK 分发面只有 `prism4`：

```
~/.codex/skills/prism         -> ~/prism/skills/prism4/prism/
~/.codex/skills/prism-review  -> ~/prism/skills/prism4/prism-review/
~/.codex/skills/prism-plan    -> ~/prism/skills/prism4/prism-plan/

```

## SKILL.md 规范

技能遵循 [agentskills.io](https://agentskills.io/specification) 官方规范，详见：

- **字段分层与书写顺序**：[`schema/frontmatter-spec.md`](schema/frontmatter-spec.md)（`visibility` / `stability` / `user_invocable` / `description_zh` 治理字段后移）
- **机器 schema**：`schema/skill.schema.yaml`
- **模板**：`templates/SKILL.template.md`

### 命名铁律（目录 = name = IDE 链名）

| 检查项 | 规则 |
|--------|------|
| 父目录 | `prism-brief/`（不是 `brief/`） |
| frontmatter `name` | `prism-brief`（与父目录一致） |
| IDE 软链 | `~/.codex/skills/prism-brief` → 同上目录 |
| 触发 | `/prism-brief` |

`bin/validate-skills` 与 Codex 均校验 **name === 父目录 basename**。外部 `prism-skills` 顶层目录同理（`commit/` → `name: commit`）。

## 治理与 SSOT

- 人类文档分类与读序：[docs/README.md](../docs/README.md)
- CLI 入口：[bin/README.md](../bin/README.md) · 4.0 语义地基：[docs/prism-4-refoundation-alignment.md](../docs/prism-4-refoundation-alignment.md)
- **SDK 内置技能治理**：`schema/skills-catalog.yaml` 是 identity / `visibility` / `stability` / source / review metadata 的权威值；`SKILL.md` 可省略 C 层字段（validate 从 catalog 继承），写明则必须与 catalog 一致（见 `frontmatter-spec.md`）
- **SDK 当前分发**：`schema/dist-whitelist.yaml` 是 Distribution Profile SSOT；Catalog 不定义 Skill 是否进入当前 profile
- **外部 prism-skills**：未入 catalog 者须在 `SKILL.md` 写明 `visibility` + `stability`（默认 `internal` + `experimental`）
- 只有通过审计并满足 `public_gate` 的技能，才可标记为 `visibility=public`
- Skill 存不存在看 Catalog / repository reality；当前 profile 分不分发只看 `dist-whitelist.yaml`
