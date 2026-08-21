# Brief — Prism 产物可读性统一与历史回溯

> 本 Brief 是用于上下文恢复的投影，不是事实源。
> 与 Intent、Decision 或来源 Findings 冲突时，以后者为准。

## 目标

- Intent 只保存稳定、权威的宏观边界；
- Plan 保存当前阶段的微观行动模型与事实性验证；
- Findings 保存可追溯的观察、判断与建议，并按共享演进边界组织；
- Brief 不创造事实，只按明确来源投影当前有效状态；
- 中文去人机味与 Obsidian 样式只优化表达，不反向决定语义边界。
- 边界：Prism 产物可读性统一与历史回溯 Intent
- 当前落点：Topic 刚创建；后续由 Findings、Decision、Plan 与 Brief 补足当前态。

## 验收

- 新 Intent 不再生成 `## 当前落点`。
- Brief 的每一阅读区都能说明 source role、source topic 与有效性规则。
- Parent Brief 只采用自己的 Intent / active Plan。
- Child Findings / Decisions 冒泡时保留来源，不伪装成 Parent 自己的承诺或事实。
- Clarify 不跨无关 Topic 泄漏。
- Brief 无 Plan 时明确写“尚未形成当前阶段路线”，不产生虚假导航。
- Brief 不拥有或补写 Intent、Decision、Plan、Findings 中不存在的新事实。
- 首屏能看到目标边界、当前阶段、完成信号、风险与下一步。
- 完整 Plan 仍能回答“谁做什么、依赖什么、产出什么、如何验证”。
- Findings 的标题、摘要和 F 项不重复表达同一判断。
- 样式关闭后，纯 Markdown 仍可顺畅阅读；Obsidian callout 只提供强调，不承载唯一语义。

## 合同验收

- 未声明。

## 已承诺

- 暂无当前有效 Decision。

## 进度

- `plan:p02` Intent Plan Findings Brief 状态边界调整方案（最小校准）
  1. 建立最小投影 fixture，至少覆盖以下场景：
  - 当前 Topic 有 Intent、无 Plan；
  - 当前 Topic 有 active Plan；
  - Parent 与 Child 各自有 Intent；
  - Parent 与 Child 各自有 active Plan；
  - Child 有 Findings / Decision；
  - 两个无关 Topic 各自有 pending Clarify；
  - active、superseded 与 historical Artifact 并存；
  - 存量 Intent 仍包含 `## 当前落点`。
  2. 为当前错误建立失败断言：
  - 无 Plan 时不得提示“见当前 Plan”；
  - Parent Brief 必须使用 Parent 自己的 Intent / Plan；
  - Child Intent / Plan 不得进入 Parent 的目标、阶段、验证与下一步；
  - Child Findings / Decisions 冒泡时带来源 Topic；
  - Clarify 只出现在适用 Topic 的 Brief；
  - `当前落点` 不再作为 Brief 当前状态输入。
  3. 保存一组“旧 Brief”快照，仅用于 A/B 与回归说明，不把旧排版当成必须兼容的协议。
  1. 在协议对齐文档和参考格式中明确四类 Artifact：
  - Intent：目的、北极星、边界、约束、Topic 完成条件；
  - Plan：阶段目标、步骤、依赖、事实/假设、输出、验证、风险、decision gate；
  - Findings：论点、依据、影响、不确定项、建议，按共享演进节奏分组；
  - Brief：从当前有效状态再生成，不拥有新事实。
  2. 冻结 Brief 来源矩阵：
  - 目标与边界 ← 当前 Topic 自己的 Intent；
  - 当前阶段 / 本阶段完成信号 / 下一步 ← 当前 Topic 自己的 active Plan；
  - 已承诺 ← 适用于当前 Topic 的 Decisions；
  - 风险与未决 ← 当前或允许冒泡的 Findings / Clarify，并标注来源；
  - Topic 完成条件 ← 当前 Topic 自己的 Intent；
  - 历史与导航 ← superseded / historical Artifact 与索引。
  3. 明确 `当前落点` 的迁移政策：从新 Intent 模板删除；存量内容不改写；投影器停止消费。
  4. 明确父子 Topic 规则：Artifact 的读取范围按 role 决定，不再先把 lineage 内所有工件视为同一 current 集合。
  5. 增加一个轻量 **Terminology Grammar checkpoint**，只明确概念类别和暂定映射，不展开全局 rename：
  - **Artifact**：持久协作状态，使用名词；当前映射为 Intent / Brief / Findings / Decision / Plan。
  - **Capability**：语义变换能力，使用动作；当前映射为 Review / Clarify / Plan。
  - **Payload**：invocation 中的 typed semantic result，不因方便实现而自动晋升为 Artifact；当前映射为 Understanding Update / Proposed Patch / Decision Candidate。
  - **Operation**：显式副作用或记录动作；当前映射为 Record Decision。
  - **Semantics**：协议规则，不是 Artifact 或 runtime object。
  6. 在该 checkpoint 中记录三条暂定规则：
  - Plan capability 与 Plan artifact 暂时允许同名；正式协议文本存在歧义时使用 qualified form 消歧，不因词形重叠立即改名。
  - Clarify 属于 understanding，不直接产生 committed Decision；它可以产生 Decision Candidate，commitment 仍由 authority / Decision semantics 控制。
  - 本轮不因对称性新增 Briefing Capability；是否需要该能力留待实际 dogfood 证明。
  1. 调整新 Intent 模板，移除 `## 当前落点`。
  2. 调整 Brief 投影：
  - Intent / Plan 只从 exact Topic 选择；
  - Findings / Decision 按允许的 lineage 规则收集并保留来源；
  - pending Clarify 增加 Topic provenance，并按适用 Topic 过滤；
  - 停止读取 Intent 的 `当前落点`；
  - 无 Plan 时使用诚实空状态，不引用不存在的 Plan 章节。
  3. 为 Clarify provenance 设计向后兼容：新 payload 必须写入 `topic_id`；旧 payload 缺失归属时不得默认全局展示，具体迁移策略由 DG2 确认。
  4. 暂时保留旧 Brief 标题或通过内部 source model 输出，避免“语义修复”和“版式切换”混在同一变更中。
  1. 使用同一组有效 Artifact 生成两份 Brief：
  - A：当前章节结构；
  - B：候选结构——目标与边界、当前阶段、本阶段完成信号、已承诺、风险与未决、下一步、Topic 完成条件、历史与导航。
  2. 至少用三类样本检查：
  - Topic 078：无 Decision、有多份 Findings、有 active Plan；
  - Parent / Child Topic：验证来源可见性；
  - 无 Plan 或无 Findings 的空状态 Topic。
  3. 采用固定阅读问题评估：
  - 这件事为什么做、边界是什么？
  - 当前处在哪个阶段？
  - 怎样算本阶段完成？
  - 已承诺什么、还没有承诺什么？
  - 当前最大风险和下一步是什么？
  4. 经用户确认后，再同步正式 Brief 标题、顺序、`prism-brief` 指导与快照测试。
  1. 在 `prism-review` 中加入拆分判据：需要独立 owner、独立 Decision、独立验证或可能单独被修正的发现，应拆为独立 Findings Artifact。
  2. 允许一次 Review 产生多个 F 项，但要求它们共享近似生命周期；不要机械执行“一条发现一个文件”。
  3. 为 f01 / f02 这类“局部修正”建立示例，说明现有 Artifact 保留历史，后续如何用更小粒度落盘避免重复。
  4. 保留总分总阅读结构，但减少标题清单代替判断、重复摘要和模板填充句。
  1. 明确 Plan 顶层步骤的最小稳定信息：状态、动作、依赖、产出、验证；复杂任务可继续附事实、假设、护栏、风险和 decision gate。
  2. Brief 只投影 active Plan 的阶段目标、顶层步骤状态、本阶段完成信号和最近的未完成动作；不复制嵌套实施细节。
  3. 状态值优先沿用可读 Markdown 约定，例如待执行 / 进行中 / 完成 / 延后 / 放弃；只有投影确实需要时才解析，不把它升级为 Core 状态机。
  4. 更新 `prism-plan` 的指导与示例，显式说明 Intent 宏观、Plan 微观、Brief 摘要三者关系。
  1. 对 Brief、Findings、Plan 的示例和 Skill 指导进行中文编辑：
  - 结论先行，少用路标式开场；
  - 用具体主语、动作和证据替代抽象名词堆叠；
  - 避免机械三段式、否定式排比、模糊归因和重复总结；
  - 保留风险强度、authority、source、assumption 等不可丢失信息。
  2. 使用 `humanizer` 与 `humanizer-zh` 作为反向检出清单，而不是自动改写器；每次改写都对照原事实和来源。
  3. 重新生成 Topic 078 Brief，并选择 2–3 个父子结构或空状态 Topic 做 dogfood。
  4. 执行 Skill 校验、定向测试、全量测试和 release gate；记录任何有意的快照变化。
  5. 汇总 dogfood 中出现的命名候选和歧义，供状态边界修复、Brief A/B、Review / Plan dogfood 全部完成后的独立 Terminology Freeze 使用；本 Plan 不执行最终 rename。
  - Topic 078 Brief 不再包含过期 `当前落点`；
  - Intent / Plan / Findings / Brief 的来源和边界可由示例直接辨认；
  - Plan 细节没有因可读性调整而丢失；
  - Parent / Child 与 Clarify 归属测试通过；
  - 中文阅读不依赖模板腔或过度格式化；
  - 定向测试、全量测试、Skill 校验和 release gate 全部通过。

## 未决

- `finding:f01` 3.x 与 4.0 产物可读性基线评审
- `finding:f02` Plan 微观职责与可读性范围修正
- `finding:f03` Intent Plan Findings Brief 状态边界评审

## 已消化

**Plan**
- `plan:p01` Intent Plan Findings Brief 状态边界调整方案

## 下一步

- 1. 建立最小投影 fixture，至少覆盖以下场景：
- 2. 为当前错误建立失败断言：
- 3. 保存一组“旧 Brief”快照，仅用于 A/B 与回归说明，不把旧排版当成必须兼容的协议。
- 1. 在协议对齐文档和参考格式中明确四类 Artifact：
- 2. 冻结 Brief 来源矩阵：
- 3. 明确 `当前落点` 的迁移政策：从新 Intent 模板删除；存量内容不改写；投影器停止消费。
- 4. 明确父子 Topic 规则：Artifact 的读取范围按 role 决定，不再先把 lineage 内所有工件视为同一 current 集合。
- 5. 增加一个轻量 **Terminology Grammar checkpoint**，只明确概念类别和暂定映射，不展开全局 rename：
- 6. 在该 checkpoint 中记录三条暂定规则：
- 1. 调整新 Intent 模板，移除 `## 当前落点`。
- 2. 调整 Brief 投影：
- 3. 为 Clarify provenance 设计向后兼容：新 payload 必须写入 `topic_id`；旧 payload 缺失归属时不得默认全局展示，具体迁移策略由 DG2 确认。
- 4. 暂时保留旧 Brief 标题或通过内部 source model 输出，避免“语义修复”和“版式切换”混在同一变更中。
- 1. 使用同一组有效 Artifact 生成两份 Brief：
- 2. 至少用三类样本检查：
- 3. 采用固定阅读问题评估：
- 4. 经用户确认后，再同步正式 Brief 标题、顺序、`prism-brief` 指导与快照测试。
- 1. 在 `prism-review` 中加入拆分判据：需要独立 owner、独立 Decision、独立验证或可能单独被修正的发现，应拆为独立 Findings Artifact。
- 2. 允许一次 Review 产生多个 F 项，但要求它们共享近似生命周期；不要机械执行“一条发现一个文件”。
- 3. 为 f01 / f02 这类“局部修正”建立示例，说明现有 Artifact 保留历史，后续如何用更小粒度落盘避免重复。
- 4. 保留总分总阅读结构，但减少标题清单代替判断、重复摘要和模板填充句。
- 1. 明确 Plan 顶层步骤的最小稳定信息：状态、动作、依赖、产出、验证；复杂任务可继续附事实、假设、护栏、风险和 decision gate。
- 2. Brief 只投影 active Plan 的阶段目标、顶层步骤状态、本阶段完成信号和最近的未完成动作；不复制嵌套实施细节。
- 3. 状态值优先沿用可读 Markdown 约定，例如待执行 / 进行中 / 完成 / 延后 / 放弃；只有投影确实需要时才解析，不把它升级为 Core 状态机。
- 4. 更新 `prism-plan` 的指导与示例，显式说明 Intent 宏观、Plan 微观、Brief 摘要三者关系。
- 1. 对 Brief、Findings、Plan 的示例和 Skill 指导进行中文编辑：
- 2. 使用 `humanizer` 与 `humanizer-zh` 作为反向检出清单，而不是自动改写器；每次改写都对照原事实和来源。
- 3. 重新生成 Topic 078 Brief，并选择 2–3 个父子结构或空状态 Topic 做 dogfood。
- 4. 执行 Skill 校验、定向测试、全量测试和 release gate；记录任何有意的快照变化。
- 5. 汇总 dogfood 中出现的命名候选和歧义，供状态边界修复、Brief A/B、Review / Plan dogfood 全部完成后的独立 Terminology Freeze 使用；本 Plan 不执行最终 rename。
- - Topic 078 Brief 不再包含过期 `当前落点`；
- - Intent / Plan / Findings / Brief 的来源和边界可由示例直接辨认；
- - Plan 细节没有因可读性调整而丢失；
- - Parent / Child 与 Clarify 归属测试通过；
- - 中文阅读不依赖模板腔或过度格式化；
- - 定向测试、全量测试、Skill 校验和 release gate 全部通过。
- 有仍有效 Findings；若被取舍阻塞用 `/prism-clarify`，否则按 Plan 推进

## 投影导航

- 暂无 Decision / Clarify；record 后会生成 `decisions/decision.index.md`
- Findings 投影索引：`findings/finding.index.md`
