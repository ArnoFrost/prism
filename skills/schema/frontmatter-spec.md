# SKILL.md Frontmatter 规范

> SSOT：字段分层、书写顺序、治理归属。机器校验：`bin/validate-skills`。
> 命名（目录 = name）：见 `skill.schema.yaml` §naming。

## 字段分层

| 层 | 字段 | 必需 | 说明 |
|----|------|:----:|------|
| **A Agent** | `name` | ✓ | = 父目录 basename = IDE 软链名 |
| | `description` | ✓ | 含 `Use when:` 触发词；可多行 `\|` |
| | `description_zh` | ✓* | CodeBuddy IDE 列表；*外部 skill 强烈建议 |
| **B 归属** | `license` | 推荐 | SDK 内置默认 `MIT` |
| | `metadata` | 推荐 | `author` / `version`（dev 技能用 `dev-NN`） |
| **C 治理** | `visibility` | 镜像 | **catalog SSOT**；SKILL 可省略或须与 catalog 一致 |
| | `stability` | 镜像 | 同上 |
| **D IDE** | `user_invocable` | 可选 | 小写 `true`/`false`；slash 可发现技能建议 `true` |
| **E 公开** | `public_gate` | 条件 | 仅 `visibility: public` |

## 推荐书写顺序（自上而下）

```yaml
---
name: workflow-example
description: |
  单行或多行能力描述。Use when: 触发词1、触发词2、workflow-example
description_zh: "中文简述（IDE 列表）"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
```

**原则**：Agent 读的前三行（name / description / description_zh）靠前；治理与 IDE 扩展**后移**，避免挤占启动 token。

## 治理 SSOT（SDK 内置技能）

| 来源 | 职责 |
|------|------|
| `skills/schema/skills-catalog.yaml` | `visibility` / `stability` / 公开审计的**权威值** |
| `SKILL.md` 内 C 层字段 | **可选镜像**；省略时 validate 从 catalog 继承；写明则必须与 catalog 一致 |

外部 `prism-skills` 未入 catalog 者：须在 SKILL.md 写明 `visibility` + `stability`（默认 internal + experimental）。

## 反模式

- `user_invocable: True`（YAML 布尔请用小写 `true`）
- `visibility` 写在 `name` 之前（治理字段后移）
- `skills/workflow/foo/` + `name: workflow-foo`（目录与 name 不一致）
- SKILL 写 `visibility: internal` 但 catalog 登记 `dev`（漂移）

## 校验

```bash
bin/validate-skills --layer sdk
```
