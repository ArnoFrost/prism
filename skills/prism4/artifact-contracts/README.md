# Artifact 写法合同（4.0 稳定态）

> **定位**：本目录是各 Artifact 的写法合同——frontmatter 字段、正文结构、承载边界、生命周期与通用示例。它是产物格式的唯一权威来源；CLI 与 Skill 文档不得另行定义同一套格式。
> **协议级纪律**（可重建性测试、Intent–Plan SSOT、收缩口径、Projection 口径）见 SDK 根 `AGENTS.md` §Artifact 语义纪律；本目录是其在写作层的展开。

## 总则（五条）

1. **Persist irreducible state. Derive the rest.** 可由足够强的 Agent 基于现有事实与 repository reality 安全、低成本、可靠重建的内容，默认投影，不持久化。
2. **Roles are available, not mandatory.** Role 是语义工具，不是 Topic 创建后的文件 checklist；简单 Topic 可以只有 Topic + 一条 Finding 就结束。
3. **Intent = 目标与边界 SSOT；Plan = 当前实施方案 SSOT。** Plan 不得自行改变 Intent；跨方案有效的约束归 Intent，仅本方案有效的约束归 Plan。
4. **吸收转写硬标准。** 被吸收不是删除：吸收者必须写清"采用什么 + 为何采用 + 存在实质替代方案时为何不采用"，否则源文件不可退档。
5. **投影可再生。** Brief / Roadmap / Status / Index 是投影，随时可删可再生成，不成为第二事实源。

## 文件清单

| 文件 | 承载 |
|------|------|
| [intent.md](./intent.md) | Intent 写法合同 |
| [plan.md](./plan.md) | Plan 写法合同 |
| [finding.md](./finding.md) | Finding 写法合同 |
| [decision.md](./decision.md) | Decision 写法合同 |
| [brief.md](./brief.md) | Brief 投影写法合同 |

## 使用方式

- Agent 写 / 改 Artifact 时按对应合同执行；格式疑问以本目录为准，不猜、不模仿陈旧样本。
- 编号约定在 store 内全局递增：`intent:iNN` / `plan:pNN` / `finding:fNN` / `decision:dNN` / `clarify:cNN`。ref 是 store 全局唯一键，可用 `prism artifact next-id <topic_id> --role <role>` 机械化取号（topic 参数仅作存在性校验），避免手算幻觉与跨 Topic 碰撞。
- 不需要的 Artifact 不落盘（总则 2）；落盘即按合同写全，不留空壳字段。

## 工程产物语言规则

Prism 工件先交付状态，再解释协议。正文采用中性、直接的技术中文：

- 首段先写当前判断或目的，不用"本轮将""下面来看"等路标式开场。
- 写清主语、动作、证据和影响，少用"相关能力""综合推进""进一步提升"等抽象占位词。
- frontmatter 已表达 role、authority、evolution 时，正文不逐段重复"不构成授权""可再生成"等协议自证。只有存在真实误读风险时才补一句边界。
- 不为了整齐强行三段式、否定排比或同义词轮换；列表长度由事实决定。
- 先保留事实强度、来源、assumption、风险和 Decision 边界，再调整语气。自然不等于模糊。
- 表格、callout、粗体和标题只强化已有层级，不承担唯一语义；纯 Markdown 仍应可读。

反向检出类工具（如 humanizer）可以作为清单参考，但不是 Prism runtime dependency，也不自动改写 Artifact：技术文档保持克制，不强行加入第一人称、情绪或个性；协议原语、代码符号和有用的阶段标题不因"去 AI 味"被改名。
