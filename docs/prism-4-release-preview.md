---
status: draft
audience: maintainer
type: guide
---

# Prism 4.0 更新预览：给 3.x 深度使用者的变化清单

> 编辑草稿，面向 Prism 开发者、维护者与 3.x 深度使用者。这里挑选会改变日常协作方式的功能，不重复产品介绍，也不宣布 4.0 stable 已发布。

如果你熟悉 3.x，这次最值得关注的不是新术语的数量，而是三个变化：**只保留值得恢复的状态；接受的是具体方案，不是一份文件的名字；恢复视图不能把建议或无效状态写成承诺。**

## 先分清交付状态

| 内容 | 状态 | 阅读方式 |
|---|---|---|
| 三入口、Conversation Choice Capture、本地参考安装与按通道更新 | 已在 Canary 发行线交付，仍属实验体验 | 可用于试用，不等于 stable 承诺 |
| Plan acceptance 行动模型绑定、Decision 校验贯穿 CLI 与 Brief | 纳入 4.0.0-canary.6 | 以该不可变 Tag 的发布为准，上一枚 Tag 不包含 |
| Markdown Presentation Profile v0 | 指南草案及相关解析支持纳入 4.0.0-canary.6 | 不是已完成读者验证的稳定呈现合同 |
| 跨领域适用性、新用户上手成本、长期恢复收益 | 尚待真实使用验证 | 不用代码测试通过替代体验证据 |

具体发行归属以 [CHANGELOG](../CHANGELOG.md) 的版本条目为准。本预览按主题组织，不能替代版本记录；未来更新以上状态时，不把“源码实现”直接改称“已发布”。

## 1. 三个入口，不再要求走完整条工作流

**过去的摩擦**：熟悉 3.x 的使用者往往要先判断所处阶段、该走哪个 workflow，再开始实际讨论。

**现在怎么用**：`/prism` 处理恢复、Topic、澄清与状态整理；`/prism-review` 独立审视问题；`/prism-plan` 设计行动结构。Review 产出 Findings，不自动变成批准的工作，也不自动串起下一步。

**一个例子**：你只想审视当前方案，可以直接做 Review。发现的问题能被当前 Plan 吸收，就更新方案并留下必要理由；不必为了凑齐流程另建一套澄清记录和 Decision。

**升级注意**：这不是旧 workflow 命令的别名层。旧入口已经退出 4.0 活跃分发面，项目协作约定需要随迁移调整。入口用法见[上手指南](./onboarding.md)。

## 2. Plan 可以持续修订，接受结果只覆盖当时的行动模型

**过去的摩擦**：阶段变化容易变成新文件、新编号；文件名没变又容易让人误以为以前的接受仍然覆盖现在的方案。

**现在怎么用**：同一目标优先原地修订。确需整体替代时显式 supersedes；只有目标正交、范围互斥且独立验收时才保留兄弟 Plan。普通进度变化不要求新的 durable snapshot。

接受结果则绑定具体行动模型：目标、步骤、顺序、依赖、验收或重要风险变化，会让 acceptance stale。Plan 可以仍然是当前方案，但不再据此获得执行授权。

**一个例子**：把步骤标为已完成、补执行证据，可以保留 acceptance；把“人工确认后切换”改成“直接切换”，需要重新接受。两者都不要求为了更新而新建 Plan 编号。

**升级注意**：未知正文保守地参与行动模型判断；不能把实质方案变化包装成格式调整。旧 acceptance 缺少必要绑定信息时也会失效。细节见 [Plan Contract](../skills/prism4/artifact-contracts/plan.md)。

## 3. 人类选择有落点，无效承诺也有明确去处

**过去的摩擦**：讨论中的候选、记录下来的选择与真正可指导执行的授权，容易在恢复时被混为一谈。

**现在怎么用**：Conversation Choice Capture 忠实记录已经发生的人类选择，形成 target-bound evidence。Plan 可以直接基于有效 evidence 接受，不必为每次接受生成 Decision；Decision 只承接效力超出单一 Plan 生命周期的承诺。

4.0.0-canary.6 把已有规则接到产品表面：`prism store validate` 聚合报告合同问题；Brief 只把有效的 current Decision 列入“已承诺”。无效状态仍可观察，但不会被自动删除、改成历史或提升为承诺。

**一个例子**：一个手写 Decision 缺少授权证据，Brief 会显示简短诊断；完整问题交给 `store validate`。一份合法的新 Decision 取代旧件后，旧件保留在历史导航，不再被当成当前缺陷。

**升级注意**：current Decision 的 canonical form 是 `committed` 加有效 evidence；可被未来取代不要求写成 `supersedable`。这仍是 trusted-local 语义治理，不是作者身份认证或防恶意 writer 的安全系统。写法见 [Decision Contract](../skills/prism4/artifact-contracts/decision.md)。

## 4. 恢复时先看主线，必要时再下钻

**过去的摩擦**：来源材料齐全，不代表跨 session 回来后容易接手；另一种极端是摘要太短，理由和边界一起丢了。

**现在怎么用**：Brief 从当前状态生成目标、阶段、完成信号、承诺、风险与下一步；完整行动模型仍在 Plan。Findings 只保留尚不能吸收的重要判断和关键证据，Decision 保持稀少。Artifact Role 是可用工具，不是建 Topic 后必须填满的清单。

呈现上使用可移植 Markdown；标准 GitHub Alert 可以强调已有内容，但不会创造新的 authority。个人仍可在 Obsidian 中增强阅读，不必把插件、CSS 或特定语法变成公共文档依赖。

**一个例子**：隔一段时间回来，先看 Brief 当前阶段，再进入 Plan 检查依赖和验证；不要重新从聊天里拼装方案，也不要把 Brief 当成另一份事实源。

**升级注意**：这是已经建立的阅读结构，不是“恢复速度已提升多少”的实测结论。相关草案见 [Reading Contract](./prism-4-reading-contract.md) 与 [Presentation Profile](./prism-markdown-presentation-profile.md)。

## 5. 产品更新与个人环境维护分开

**过去的摩擦**：SDK、个人 Skills、DotFiles 与 Workspace 混在同一条更新叙事里，使用者不容易判断自己更新的是产品版本还是个人工作环境。

**现在怎么用**：最小参考安装是 SDK + uv；Workspace 默认本地存储，Vault、外部 Skills 与 Env 是可选项。产品安装跟随不可变 Tag 与显式选择的通道，内置三个入口跟随 SDK 发布；个人扩展不被产品 updater 顺带拉取。

**一个例子**：managed 安装使用 `prism update` 跟随所选通道，使用 `prism update status` 查看状态；贡献者的分支 checkout 仍属于源码维护，不被默认当成某次正式发行。

**升级注意**：Canary 不等于 stable，CI green 也不等于已发布。已有 3.x 状态不是通过“更新 SDK”自动转换；迁移仍要归档旧状态，再重建真正需要继续的问题。见[迁移指南](./migration.md)与[发行说明](./release-process.md)。

## 给准备从 3.x 过来的你

不必先把全部旧 Topic 搬过来。先选一个仍在推进、值得跨 session 恢复的问题，保留其目标、边界、必要方案和未决证据；旧流程记录保留在历史中。

试用时观察两件事：你是否少维护了无价值的状态，以及回来以后是否更容易知道哪些判断仍有效。若没有，不用为“符合 4.0”继续补文件——这些反例比一套看起来完整的工件更有价值。
