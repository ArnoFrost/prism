# Shared Kernel — 跨 Skill 最小不变量

> 唯一语义来源：[`docs/prism-4-refoundation-alignment.md`](../../../docs/prism-4-refoundation-alignment.md)（§3–§7、§12、§19）与 SDK 根 `AGENTS.md` §Artifact 语义纪律。
> 本文件是供 Skill 消费的受控投影；与此二源冲突时，以后者为准并登记修正。

## 1. Topic ownership 与 Parent/Child boundary

- Topic 是持久的协作边界；runtime session identity 不定义 Topic identity。
- 耐久子问题用 Child Topic（`parent` relation）表达；普通执行颗粒留在 Plan 内。
- 判据：只有需要独立 Intent、独立演进、跨会话恢复的子问题才建 Child Topic。测试路线、A/B、fixture、短期 spike 归 `references/` 或临时目录。

## 2. Intent–Plan SSOT

- Intent 是目标与边界的唯一事实源；Plan 是当前实施方案的唯一事实源。
- Plan 无权改 Intent：边界变化先显式修订 Intent（supersedes），再校准 Plan。
- 跨方案有效的约束归 Intent；仅本方案有效的约束归 Plan。

## 3. Reconstructability / persistence

- 可由足够强的 Agent 基于现有事实与 repository reality 安全、低成本、可靠重建的状态，默认投影，不持久化。
- Role available, not mandatory：不为协议完整制造空壳 Artifact。最小 Intent 口径见 `decision:d01`（Core 允许 capture-first 无 Intent Topic；Reference Experience 在动机已知时默认写最小 Intent，未知时 Topic-only + 诚实降级）。
- 落盘即按写法合同写全；持久化判据是行动模型 / 判断是否值得恢复、审查、交接，不是任务大小。

## 4. Authority / acceptance

- Production does not imply acceptance or commitment：产物生成不等于被接受。
- Plan 初始 advisory；operative = current + valid acceptance。current set 推导 = 未被显式 supersede 且非 historical；supersedes 只由调用方显式提交；范围互斥的 sibling Plan 合法并存（`decision:d03`）。
- Decision 的 committed write 需要显式 authority evidence（human-choice 记录 / Decision / 委托上下文 ref）；`human-required` 是 requirement，不是 evidence（`decision:d04`）。

## 5. Absorption / supersession

- 吸收转写硬标准：吸收者必须写清「采用什么 + 为何采用 + 存在实质替代方案时为何不采用」；否则源文件不可退档。
- 被吸收不是删除：用 `absorbed` / `superseded` / `historical` 标注，保持可追溯。

## 6. Finding / Decision materiality

- Findings 只保留尚未被 Intent / Plan / Decision 吸收的重要悬置判断，或未来仍值得引用的关键证据；Findings 不授权实施。
- Decision 只承接效力超出单一 Plan 生命周期的承诺（判据：Plan 明天被完整重写后是否仍需保留）；方案级选择连同理由吸收进 Plan。

## 7. Projection discipline

- Brief、发现链 / 决策链索引都是投影：可随时再生成，不是事实源；与 Intent / Decision / 源工件冲突时以后者为准。
- 投影缺内容时修源工件，不手写投影补洞；不把投影扩写成历史综述。

## 8. Capability / Invocation identity

- Capability semantic identity 独立于 provider / runtime realization：`prism:review` 等身份不绑定任何 `SKILL.md`、CLI noun 或 Skill 文件清单。
- Invocation 记录 semantic provenance，不是 runtime telemetry；本地 Markdown adapter 为 weak-provenance（不落 Invocation、record 输出不带 invocation id），JSON 参考存储完整持久化并回显。

## 9. 无固定 workflow 与兼容边界

- 能力只承诺输入输出，不承诺自己在流程中的位置。能力可以准备下一次有用交互，但不得形成 Review → Clarify → Plan → Execute 固定管线；弱衔接是向人类说清交接面，不是自动编排。
- 3.x 实现已随 prism-4 分支剔除（git tag `legacy-3x-final`）：4.0 Skill 不创建 `scope.md` / `focus.md` / `task.index.md` / `wave` / `reviews/rXX.md`，不调用 `workspace-init` / `workflow-*`；旧 Topic 在本分支只读。
- 落盘权限基线：仅在用户要求或需要持久化 4.0 痕迹时写盘；整理类动作默认 preview-first（`writes=0`），apply 需显式授权。
- 公开协作正文用中文，协议原语保留英文。
