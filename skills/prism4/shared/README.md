# Shared Kernel（非 Public Skill）

> 定位：Alignment §3.2 定义的 Skill-facing kernel。从 Protocol Semantics 受控消费跨 Skill 不变量；不是第二语义 SSOT，不定义 Artifact 格式（→ [`artifact-contracts/`](../artifact-contracts/)），不定义 CLI 参数（→ CLI Contract / `bin/README.md`）。
>
> **分发**：`bin/relink` 跳过本目录——Shared 不是 Public 入口。当前 P5 三入口和 SDK 中保留的旧 wrappers 都可消费本合同；`/prism` 按需加载 `methods/` 下的 method references。

## 结构

| 文件 | 承载 |
|------|------|
| [kernel.md](./kernel.md) | 跨 Skill 最小不变量（九节）；Skills 引用，不再各自内联复述 |
| [methods/topic.md](./methods/topic.md) | Topic 创建 method reference（facade lazy-load 单元） |
| [methods/recover.md](./methods/recover.md) | 零写入恢复 method reference |
| [methods/clarify.md](./methods/clarify.md) | 单问澄清 method reference |
| [methods/maintain.md](./methods/maintain.md) | preview-first 整理 method reference |
| [methods/absorb.md](./methods/absorb.md) | 结论吸收 / Decision 固化 method reference |

## 引用规则

1. 每个 SKILL.md 在规则区开头引用一次本 kernel，不再复述 authority / 吸收 / 投影 / 3.x 兼容等协议纪律。
2. method reference 只定义：触发、effect、guard、输出、所需 on-demand references；正文方法（如 Review 的总分总）留在各自 SKILL.md。
3. 本目录不出现 Artifact frontmatter 字段定义、CLI 参数清单或 Capability 的完整合同——那些各自有唯一归属层。
