# Method — Topic（创建 / 定位）

| 项 | 内容 |
|----|------|
| 触发 | 「建个专题」「新建 Topic」「开个子问题」 |
| effect | probe（read）→ create（`topic new`）；子 Topic 带 `--parent` |
| guard | 先机械探测再创建；未桥接先 `prism host attach`，不 `workspace-init`；多个活跃 Topic 不猜，问用户；Child Topic 不是 Child Plan |
| 输出 | Topic id、根路径、`references/` 预留位、下一步建议动作 |
| on-demand | [`../kernel.md`](../kernel.md) §1（Child Topic 判据）、§3（最小 Intent 口径）；`artifact-contracts/intent.md` |

## 机械事实

- 无 `--root` 时，`topic new` 在 `workspace.{code}.local/topics/{NNN}_{slug}/` 分配**新的** Topic 目录，而不是改写当前 Topic。
- `topic new` 预留空 `references/`：供人工或 Agent 放置调研、证据、外部材料；不是 Core Artifact，默认不进入 Brief 投影。
- 子 Topic 落 `children/<slug>/`，内聚 topic / intent / plans / references；findings 与 decisions 冒泡回父根。
- `topic.md` 是机械锚点与导航门牌，不是 Core Artifact role，也不是事实源。它只帮助人类知道该去哪里读：

  | 要看什么 | 去哪 |
  |----------|------|
  | 边界与完成条件 | `intent.md` |
  | 当前恢复切片 | `brief.md`（生成后） |
  | 行动结构 | `plans/` |
  | 观察建议 | `findings/` |
  | 授权承诺 | `decisions/` |
  | 调研证据 | `references/` |

  不要把 `topic.md` 扩写成 README、Scope 或 Brief。若需要更好读的边界，改 Intent；若需要恢复当前态，生成 Brief。

## 流程

```text
1. prism topic probe                # bridged: yes 才继续
2. 未桥接 → prism host attach --code CODE（只登记与桥接，不写 scope/focus）
3. prism topic new <id> --title "..." [--intent "..."]   # 或 prism topic list 定位
4. 报告 Topic id、根路径、references/ 预留位
```

probe 给出的 `next_number` 与编号倒序的 `recent:` 用于定位；不做亲和匹配，不猜「该进哪个 Topic」，多个候选时问用户。

| 意图 | 命令 |
|------|------|
| 新的协作问题空间 | `prism topic new topic:foo --title "..." --intent "..."` |
| 当前 Topic 下的子问题 | `prism topic new topic:foo.child --title "..." --parent topic:foo` |
| 测试 / 无 Workspace 的孤立 store | 显式 `--root <dir>`（协议允许，日常协作不用） |

`--intent` 收到普通单段输入时，CLI 会把尚未提供的北极星、明确非目标与关键约束收进「尚未声明」区域——这表示缺口仍然存在，不是替用户补齐边界。已有结构化 Intent 保持其事实强度与边界，不为套模板重写；不要把 current progress、active Plan 或下一步写回 Intent。

## 输出

保持回答简短：Topic 创建只是脚手架，不是规划仪式；不把 `topic.md` 当 README 扩写。
