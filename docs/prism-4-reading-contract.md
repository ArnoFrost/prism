---
status: draft
target: Prism 4.0 Reference Experience
type: guide
created: 2026-08-21
source:
  - ./prism-4-refoundation-alignment.md
  - ./prism-4-architecture-guide.md
---

# Prism 4.0 Reading Contract

> 本文定义 Prism Reference Experience 的候选阅读合同：语义正确的协作状态，应怎样被低成本理解、恢复和继续。
>
> 它不是 Protocol Core，不新增 Artifact、Capability、Payload、Operation 或 relation，也不冻结 Markdown 标题与术语表面写法。

## 1. 为什么需要阅读合同

Protocol Semantics 先保证状态成立：信息属于正确的 Artifact，authority、evolution、provenance 和 Parent / Child 边界没有被改写。

但“状态正确”还不能证明“交接有效”。读者可能看得到全部来源，却仍要重新推导：现在发生了什么、哪些判断有效、已经承诺什么、下一步从哪里继续。

Reference Experience 因此需要在协议与样式之间承担一层稳定责任：

```text
Protocol Semantics
        ↓
Cognitive / Reading Contract
        ↓
Presentation Style
```

- **Protocol Semantics**：状态怎样成立，哪些表达不可越界。
- **Reading Contract**：读者需要回答什么，信息应怎样分层交付。
- **Presentation Style**：使用普通 Markdown、Obsidian、Web UI 或其他形式呈现。

Style 可以强化层级，不能替代层级；阅读合同可以约束参考体验，不能反向定义 Core。

## 2. 两个独立的质量属性

### Traceability

回答“这条状态从哪里来”：

- 能否识别来源 Artifact、Topic 和 Capability；
- 能否区分事实、判断、建议与承诺；
- 能否沿 relation、Invocation 或 reference 回到依据；
- 投影是否保留了来源和事实强度。

### Recoverability

回答“回来以后怎样继续”：

- 能否在短时间内复述目标、当前阶段、主要风险与下一步；
- 最重要的判断是否足够早出现；
- 是否需要重新推导文档已经拥有的信息；
- 是否能从概览自然下钻，而不是被迫通读全部细节。

两者不能互相替代。只有来源、没有主线，会得到可审计但难接手的文档；只有摘要、没有来源，会得到好读但不可信的文档。

## 3. 渐进展开

Prism 产物不通过删除事实获得简洁，而通过信息层级降低首轮认知负担。

| 阅读层 | 读者任务 | 内容要求 |
|---|---|---|
| First glance | 判断这是什么、最重要的结论是什么 | 标题、首句或简短总判断 |
| Scan | 复述主线、风险和下一步 | heading、段首、地图、状态摘要 |
| Read | 理解原因、依赖、证据和取舍 | 完整正文与必要护栏 |
| Drill down | 核实来源和历史 | Artifact id、reference、relation、Invocation 或 evidence |

“详细”不等于“复杂”。当读者可以先看主线、再按需进入细节时，完整 Plan 或长 Findings 仍然可以好用。

## 4. 各 Artifact 的认知任务

### Intent — Orientation / Boundary

读完后应能回答：

1. 为什么存在这个 Topic？
2. 什么属于边界内，什么明确不做？
3. 哪些约束不能违反？
4. 什么条件下 Topic 可以结束？

Intent 不保存当前进度。首屏应先给目的与边界；来源材料、约束细节和完成条件可以继续展开。未声明内容应保持诚实，但不必用成排空章节淹没已有信息。

### Plan — Execution

读完后应能回答：

1. 预期结果是什么？
2. 行动顺序、依赖和假设是什么？
3. 每个阶段留下什么，怎样验证？
4. 哪些风险、停止条件或 Decision Gate 会改变路线？

Plan 保留微观、可评估的执行事实。复杂 Plan 先提供顶层行动地图，再展开阶段细节；Brief 负责恢复当前切片，不通过压薄 Plan 换取简短。

Plan Artifact 记录行动模型，不记录每一次状态跳动。同一段连续执行中的阶段切换留在临时执行清单；只有路线改变、跨 session / handoff 或恢复将读错时，才需要新的 durable snapshot。Child Topic 表达需要独立 Intent 与长期演进的子问题，不是 Plan phase。测试矩阵、A/B 与 fixture 默认属于 reference / temp。

### Findings — Attention / Sensemaking

读完后应能回答：

1. 当前最值得注意的判断是什么？
2. 哪些事实支撑它，强度如何？
3. 如果不处理会影响什么？
4. 建议动作是什么，哪些仍然不确定？

Findings 先帮助读者把握局势，再展开证据。多个发现只有在 owner、验证、Decision gate 和 supersede 节奏大致一致时，才收在同一 Artifact。

### Brief — Recovery

读完后应能回答：

1. 为什么做、边界在哪里？
2. 当前在哪个阶段，什么算本阶段结束？
3. 已经承诺了什么？
4. 当前风险与未决是什么？
5. 下一步从哪里继续？

Brief 是当前有效状态的可再生成投影。它降低认知分辨率，但不能改变来源强度；Parent / Child 状态、Clarify payload 与 Decision commitment 必须保持原边界。

### Decision — Commitment

读完后应能回答：

1. 被授权的承诺是什么？
2. 谁或什么 authority 使它成立？
3. 它适用于哪个 Topic 和边界？
4. 哪些候选、依据或历史被接受、拒绝或取代？

Decision 的首屏优先突出 commitment 和适用范围。Style 或投影不能把 Child Decision 自动写成 Parent commitment。

## 5. 工程表达规则

1. **正文先写主题事实。** 不用“本轮”“基于上述分析”等句子代替真实承接。
2. **一个句子避免装入过多逻辑动作。** 来源、判断、影响和建议可以相邻，但不必挤进同一句。
3. **协议护栏靠近误读点。** role、authority、evolution 已由 frontmatter 表达时，正文不重复自证；只有事实强度、适用范围或 commitment 容易被误读时，补一次短说明。
4. **自然中文不等于口语化。** 保留工程术语和精确边界，减少机械排比、宣传措辞、重复总结和为了完整而制造的空话。
5. **Style Profile 只做可逆增强。** Callout、表格、图标和高亮可以帮助 Scan，但不能成为唯一语义载体。

Humanizer 或其他去 AI 写作规则可以作为编辑检查清单，不能成为 Prism Runtime 的依赖，也不能覆盖 Fidelity 检查。

## 6. 理解型 Eval

### 30 秒恢复

让读者在限定时间内回答该 Artifact 的核心认知问题，记录实际复述、遗漏和误读，不只记录主观偏好。

### Scan

只允许阅读标题、callout、表格、heading 和段首，检查是否仍能复述主线。

### Fidelity

对比投影或改写前后：role、authority、来源、事实强度、边界、约束和不确定性是否保持不变。任何语义漂移都不能用“更好读”抵消。

### Drill-down

从首屏判断出发，检查是否能回到对应章节、来源 Artifact 和已有 evidence / Invocation。历史材料没有 provenance 时，不补造链路。

机器测试适合守来源、角色、强度和投影规则；恢复速度、遗漏与自然度仍需真实 dogfood。两者应分开记录。

## 7. 当前采用状态

本合同目前是 Reference Experience 草案，已经得到 Brief 八段式投影、Plan 双层阅读和第一轮 Findings 格式的部分支持。Intent 与 Findings 的跨 Topic A/B、Child Decision 误读测试尚未结束。

因此当前可以把它用于设计和评估，但不能据此：

- 宣布最终 Terminology Freeze；
- 新增 Readability / Summary Artifact；
- 新增 Briefing Capability；
- 新增 progress primitive、lifecycle DSL 或 relation vocabulary；
- 把 Markdown 参考格式解释为 Protocol ontology。

是否将本草案提升为稳定 Reference Experience 合同，应在跨 Topic A/B 与理解型 Eval 后单独确认。
